# -*- coding: utf-8 -*-
import asyncio
from collections import namedtuple
import datetime
import logging
import struct
from time import perf_counter
from typing import Any
from zlib import crc32

from aioserial import AioSerial
import serial
import serial.tools.list_ports as list_ports

from ..constants import CURI_VID
from ..constants import InstrumentConnectionStatuses
from ..constants import NUM_WELLS
from ..constants import SERIAL_COMM_BAUD_RATE
from ..constants import SERIAL_COMM_BYTESIZE
from ..constants import SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS
from ..constants import SERIAL_COMM_MAGIC_WORD_BYTES
from ..constants import SERIAL_COMM_MAX_FULL_PACKET_LENGTH_BYTES
from ..constants import SERIAL_COMM_MAX_PAYLOAD_LENGTH_BYTES
from ..constants import SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES
from ..constants import SERIAL_COMM_READ_TIMEOUT
from ..constants import SERIAL_COMM_REGISTRATION_TIMEOUT_SECONDS
from ..constants import SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS
from ..constants import SERIAL_COMM_STATUS_BEACON_TIMEOUT_SECONDS
from ..constants import SERIAL_COMM_STATUS_CODE_LENGTH_BYTES
from ..constants import SerialCommPacketTypes
from ..constants import STIM_COMPLETE_SUBPROTOCOL_IDX
from ..constants import STIM_MODULE_ID_TO_WELL_IDX
from ..constants import StimulatorCircuitStatuses
from ..constants import STM_VID
from ..exceptions import FirmwareGoingDormantError
from ..exceptions import IncorrectInstrumentConnectedError
from ..exceptions import InstrumentCommandAttemptError
from ..exceptions import InstrumentCommandResponseError
from ..exceptions import InstrumentError
from ..exceptions import InstrumentFirmwareError
from ..exceptions import NoInstrumentDetectedError
from ..exceptions import SerialCommCommandProcessingError
from ..exceptions import SerialCommCommandResponseTimeoutError
from ..exceptions import SerialCommIncorrectChecksumFromPCError
from ..exceptions import SerialCommPacketRegistrationReadEmptyError
from ..exceptions import SerialCommPacketRegistrationSearchExhaustedError
from ..exceptions import SerialCommStatusBeaconTimeoutError
from ..exceptions import SerialCommUntrackedCommandResponseError
from ..utils.aio import clean_up_tasks
from ..utils.aio import wait_tasks_clean
from ..utils.command_tracking import CommandTracker
from ..utils.data_parsing_cy import parse_stim_data
from ..utils.data_parsing_cy import sort_serial_packets
from ..utils.generic import handle_system_error
from ..utils.serial_comm import convert_semver_str_to_bytes
from ..utils.serial_comm import convert_status_code_bytes_to_dict
from ..utils.serial_comm import convert_stim_dict_to_bytes
from ..utils.serial_comm import convert_stimulator_check_bytes_to_dict
from ..utils.serial_comm import create_data_packet
from ..utils.serial_comm import get_serial_comm_timestamp
from ..utils.serial_comm import METADATA_TAGS_FOR_LOGGING
from ..utils.serial_comm import parse_end_offline_mode_bytes
from ..utils.serial_comm import parse_instrument_event_info
from ..utils.serial_comm import parse_metadata_bytes
from ..utils.serial_comm import validate_instrument_metadata


logger = logging.getLogger(__name__)

ERROR_MSG = "IN INSTRUMENT COMM"


TRACKED_EVENT_NAMES = (
    "handshake_sent",
    "command_sent",
    "stim_data_received",
    "command_response_received",
    "status_beacon_received",
)

TimepointsOfEvents = namedtuple(  # type: ignore
    "TimepointsOfEvents", TRACKED_EVENT_NAMES, defaults=[None] * len(TRACKED_EVENT_NAMES)  # type: ignore
)


COMMAND_PACKET_TYPES = frozenset(
    [
        SerialCommPacketTypes.REBOOT,
        SerialCommPacketTypes.SET_STIM_PROTOCOL,
        SerialCommPacketTypes.START_STIM,
        SerialCommPacketTypes.STOP_STIM,
        SerialCommPacketTypes.STIM_IMPEDANCE_CHECK,
        SerialCommPacketTypes.SET_SAMPLING_PERIOD,
        SerialCommPacketTypes.START_DATA_STREAMING,
        SerialCommPacketTypes.STOP_DATA_STREAMING,
        SerialCommPacketTypes.GET_METADATA,
        SerialCommPacketTypes.BEGIN_FIRMWARE_UPDATE,
        SerialCommPacketTypes.FIRMWARE_UPDATE,
        SerialCommPacketTypes.END_FIRMWARE_UPDATE,
        SerialCommPacketTypes.INIT_OFFLINE_MODE,
        SerialCommPacketTypes.END_OFFLINE_MODE,
        SerialCommPacketTypes.CHECK_CONNECTION_STATUS,
    ]
)


INTERMEDIATE_FIRMWARE_UPDATE_COMMANDS = (
    "start_firmware_update",
    "send_firmware_data",
    "end_of_firmware_update",
)


class InstrumentComm:
    """Subsystem that manages communication with the Stingray Instrument."""

    def __init__(
        self,
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
        hardware_test_mode: bool = False,
    ) -> None:
        # comm queues
        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue

        # TODO try making some kind of container for all this data?
        # instrument
        self._instrument: AioSerial | VirtualInstrumentConnection | None = None
        self._instrument_error_detected = False  # Tanner (7/18/23): this flag currently only used to decide which command response to grab the system stats from when reporting a FW error
        self._hardware_test_mode = hardware_test_mode
        # instrument comm
        self._serial_packet_cache = bytes(0)
        self._command_tracker = CommandTracker()
        # instrument status
        self._is_waiting_for_reboot = False
        self._status_beacon_received_event = asyncio.Event()
        # stimulation values
        self._num_stim_protocols: int = 0
        self._protocols_running: set[int] = set()
        # firmware updating
        self._firmware_update_manager: FirmwareUpdateManager | None = None
        # comm tracking
        self._timepoints_of_events = TimepointsOfEvents()
        # used to tell instrument comm to ignore all messages when offline
        self._system_in_offline_mode: bool = False
        self._offline_state_change = asyncio.Event()

    # PROPERTIES

    @property
    def _is_updating_firmware(self) -> bool:
        return self._firmware_update_manager is not None

    @property
    def _instrument_in_sensitive_state(self) -> bool:
        return self._is_waiting_for_reboot or self._is_updating_firmware

    @property
    def _is_stimulating(self) -> bool:
        return len(self._protocols_running) > 0

    @_is_stimulating.setter
    def _is_stimulating(self, value: bool) -> None:
        if value:
            self._protocols_running = set(range(self._num_stim_protocols))
        else:
            self._protocols_running = set()

    # ONE-SHOT TASKS

    async def run(self, system_error_future: asyncio.Future[tuple[int, dict[str, str]]]) -> None:
        logger.info("Starting InstrumentComm")
        try:
            await self._setup()

            tasks = {
                asyncio.create_task(self._handle_comm_from_monitor()),
                asyncio.create_task(self._manage_online_mode_tasks()),
            }

            await wait_tasks_clean(tasks, error_msg=ERROR_MSG)
        except asyncio.CancelledError:
            logger.info("InstrumentComm cancelled")
            raise
        except BaseException as e:
            logger.exception(ERROR_MSG)
            handle_system_error(e, system_error_future)
        finally:
            self._log_dur_since_events()
            logger.info("InstrumentComm shut down")

    async def _setup(self) -> None:
        # attempt to connect to a real or virtual instrument
        await self._create_connection_to_instrument()
        # send a single handshake to speed up the magic word registration since it will prompt a response from the instrument immediately
        await self._send_data_packet(SerialCommPacketTypes.HANDSHAKE)
        # register magic word to sync with data stream before starting other tasks
        await self._register_magic_word()
        # now that the magic word is registered,
        await self._prompt_instrument_for_metadata()

        logger.info("Instrument ready")

    async def _create_connection_to_instrument(self) -> None:
        logger.info("Attempting to connect to instrument")
        # TODO could eventually allow the user to specify in a config file whether or not they want to connect to a real or virtual instrument

        # first, check for a real instrument on the serial COM ports
        for port_info in list_ports.comports():
            # Tanner (6/14/21): attempt to connect to any device with the STM vendor ID
            if port_info.vid in (STM_VID, CURI_VID):
                logger.info(f"Instrument detected with description: {port_info.description}")
                self._instrument = AioSerial(
                    port=port_info.name,
                    baudrate=SERIAL_COMM_BAUD_RATE,
                    bytesize=SERIAL_COMM_BYTESIZE,
                    timeout=SERIAL_COMM_READ_TIMEOUT,
                    stopbits=serial.STOPBITS_ONE,
                )
                break

        # if a real instrument is not found, check for a virtual instrument
        if not self._instrument:
            logger.info("No live instrument detected, checking for virtual instrument")
            virtual_instrument = VirtualInstrumentConnection()

            try:
                await virtual_instrument.connect()
            except BaseException as e:  # TODO make this a specific exception?
                raise NoInstrumentDetectedError() from e
            else:
                self._instrument = virtual_instrument

        await self._to_monitor_queue.put(
            {
                "command": "get_board_connection_status",
                "in_simulation_mode": isinstance(self._instrument, VirtualInstrumentConnection),
            }
        )

    async def _register_magic_word(self) -> None:
        logger.info("Syncing with packets from instrument")
        magic_word_test_bytes = bytearray()

        async def read_initial_bytes(magic_word_test_bytes: bytearray) -> None:
            if not self._instrument:
                raise NotImplementedError("_instrument should never be None here")

            magic_word_len = len(SERIAL_COMM_MAGIC_WORD_BYTES)

            # read bytes until enough bytes have been read
            while num_bytes_remaining := magic_word_len - len(magic_word_test_bytes):
                magic_word_test_bytes += await self._instrument.read_async(num_bytes_remaining)
                # wait 1 second between reads
                await asyncio.sleep(1)

        try:
            # Tanner (3/16/21): issue seen with simulator taking slightly longer than status beacon period to send next data packet
            await asyncio.wait_for(
                read_initial_bytes(magic_word_test_bytes), SERIAL_COMM_STATUS_BEACON_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError as e:
            # after the timeout, not having read enough bytes means that a fatal error has occurred on the instrument
            raise SerialCommPacketRegistrationReadEmptyError(list(magic_word_test_bytes)) from e

        # read more bytes until the magic word is registered, the timeout value is reached, or the maximum number of bytes are read
        async def search_for_magic_word(magic_word_test_bytes: bytes) -> None:
            if not self._instrument:
                raise NotImplementedError("_instrument should never be None here")

            num_bytes_checked = 0
            while magic_word_test_bytes != SERIAL_COMM_MAGIC_WORD_BYTES:
                # read 0 or 1 bytes, depending on what is available in serial port
                next_byte = await self._instrument.read_async(1)
                num_bytes_checked += len(next_byte)
                if next_byte:
                    # only want to run this append expression if a byte was read
                    magic_word_test_bytes = magic_word_test_bytes[1:] + next_byte
                if num_bytes_checked > SERIAL_COMM_MAX_FULL_PACKET_LENGTH_BYTES:
                    # A magic word should be encountered if this many bytes are read. If not, we can assume there is a problem with the instrument
                    raise SerialCommPacketRegistrationSearchExhaustedError()

        try:
            await asyncio.wait_for(
                search_for_magic_word(magic_word_test_bytes), SERIAL_COMM_REGISTRATION_TIMEOUT_SECONDS
            )
        except asyncio.TimeoutError as e:
            # if this point is reach it's most likely that at some point no additional bytes were being read
            raise SerialCommPacketRegistrationReadEmptyError() from e

        # put the magic word bytes into the cache so the next data packet can be read properly
        self._serial_packet_cache = SERIAL_COMM_MAGIC_WORD_BYTES

    async def _prompt_instrument_for_metadata(self) -> None:
        logger.info("Prompting instrument for metadata")
        await self._send_data_packet(SerialCommPacketTypes.GET_METADATA)
        await self._command_tracker.add(SerialCommPacketTypes.GET_METADATA, {"command": "get_metadata"})

    async def _catch_expired_command(self) -> None:
        expired_command = await self._command_tracker.wait_for_expired_command()
        # TODO raise FirmwareUpdateTimeoutError when necessary
        raise SerialCommCommandResponseTimeoutError(expired_command["command"])

    # INFINITE TASKS

    async def _handle_comm_from_monitor(self) -> None:
        while True:
            comm_from_monitor = await self._from_monitor_queue.get()
            bytes_to_send = bytes(0)
            packet_type: int | None = None

            is_offline_mode_comm = comm_from_monitor["command"] in (
                "end_offline_mode",
                "check_connection_status",
            )

            ignore_incoming_comm = not is_offline_mode_comm and self._system_in_offline_mode

            if ignore_incoming_comm:
                logger.info(
                    f"Ignoring incoming command '{comm_from_monitor['command']}' in instrument comm while offline"
                )
                return

            match comm_from_monitor:
                case {"command": "start_stim_checks", "well_indices": well_indices}:
                    packet_type = SerialCommPacketTypes.STIM_IMPEDANCE_CHECK
                    bytes_to_send = struct.pack(
                        f"<{NUM_WELLS}?",
                        *[
                            STIM_MODULE_ID_TO_WELL_IDX[module_id] in well_indices
                            for module_id in range(NUM_WELLS)
                        ],
                    )
                case {"command": "set_stim_protocols", "stim_info": stim_info}:
                    packet_type = SerialCommPacketTypes.SET_STIM_PROTOCOL
                    bytes_to_send = convert_stim_dict_to_bytes(stim_info)

                    if self._is_stimulating and not self._hardware_test_mode:
                        raise InstrumentCommandAttemptError(
                            "Cannot update stimulation protocols while stimulating"
                        )
                    self._num_stim_protocols = len(stim_info["protocols"])
                case {"command": "start_stimulation"}:
                    packet_type = SerialCommPacketTypes.START_STIM
                case {"command": "stop_stimulation"}:
                    packet_type = SerialCommPacketTypes.STOP_STIM
                case {"command": "start_firmware_update"}:
                    await self._handle_firmware_update(comm_from_monitor)
                case {
                    "command": "trigger_firmware_error",
                    "first_two_status_codes": first_two_status_codes,
                }:  # pragma: no cover
                    packet_type = SerialCommPacketTypes.TRIGGER_ERROR
                    bytes_to_send = bytes(first_two_status_codes)
                case {"command": "init_offline_mode"}:
                    packet_type = SerialCommPacketTypes.INIT_OFFLINE_MODE
                    self._system_in_offline_mode = True
                case {"command": "end_offline_mode"}:
                    packet_type = SerialCommPacketTypes.END_OFFLINE_MODE
                    # the _offline_state_change event needs to be triggered here instead of in process instrument comm because we first need to restart the task that handles instrument comm
                    self._system_in_offline_mode = False
                    self._offline_state_change.set()
                case {"command": "check_connection_status"}:
                    packet_type = SerialCommPacketTypes.CHECK_CONNECTION_STATUS
                case invalid_comm:
                    raise NotImplementedError(
                        f"InstrumentComm received invalid comm from SystemMonitor: {invalid_comm}"
                    )

            if packet_type is not None:
                await self._send_data_packet(packet_type, bytes_to_send)
                await self._command_tracker.add(packet_type, comm_from_monitor)

    async def _manage_online_mode_tasks(self) -> None:
        main_task_name = self._wait_for_offline_state_change.__name__

        # TODO clean up repetitive code
        pending = {
            asyncio.create_task(self._wait_for_offline_state_change(), name=main_task_name),
            asyncio.create_task(self._handle_sending_handshakes()),
            asyncio.create_task(self._handle_data_stream()),
            asyncio.create_task(self._handle_beacon_tracking()),
            asyncio.create_task(self._catch_expired_command()),
        }

        while True:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                task_name = task.get_name()

                if task_name == main_task_name:
                    if self._system_in_offline_mode:
                        logger.info("Cancelling online mode tasks")
                        exc = await clean_up_tasks(pending, ERROR_MSG)
                        if exc:
                            raise exc
                    elif len(pending) == 0:
                        logger.info("Creating online mode tasks")
                        pending |= {
                            asyncio.create_task(self._handle_sending_handshakes()),
                            asyncio.create_task(self._handle_data_stream()),
                            asyncio.create_task(self._handle_beacon_tracking()),
                            asyncio.create_task(self._catch_expired_command()),
                        }

                    pending |= {
                        asyncio.create_task(self._wait_for_offline_state_change(), name=main_task_name)
                    }

    async def _wait_for_offline_state_change(self) -> None:
        await self._offline_state_change.wait()
        self._offline_state_change.clear()

    async def _handle_sending_handshakes(self) -> None:
        # Tanner (3/17/23): handshakes are not tracked as commands
        while True:
            logger.debug("Sending handshake")
            await self._send_data_packet(SerialCommPacketTypes.HANDSHAKE)
            await asyncio.sleep(SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS)

    async def _handle_beacon_tracking(self) -> None:
        handshake_sent_after_miss = False

        while True:
            try:
                await asyncio.wait_for(
                    self._status_beacon_received_event.wait(), SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS + 1
                )
            except asyncio.TimeoutError as e:
                if self._instrument_in_sensitive_state:
                    # firmware updating / rebooting is complete when a beacon is received,
                    # so just wait indefinitely for the next one
                    await self._status_beacon_received_event.wait()
                    self._status_beacon_received_event.clear()
                    handshake_sent_after_miss = False
                elif handshake_sent_after_miss:
                    raise SerialCommStatusBeaconTimeoutError() from e
                else:
                    logger.info("Status Beacon overdue. Sending handshake now to prompt a response")
                    await self._send_data_packet(SerialCommPacketTypes.HANDSHAKE)
                    handshake_sent_after_miss = True
            else:
                self._status_beacon_received_event.clear()
                handshake_sent_after_miss = False

    async def _handle_data_stream(self) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        while True:
            # read all available bytes from serial buffer
            try:
                data_read_bytes = await self._instrument.read_async(self._instrument.in_waiting)
            except serial.SerialException as e:
                logger.error(f"Serial data read failed: {e}. Trying one more time")
                data_read_bytes = await self._instrument.read_async(self._instrument.in_waiting)

            # append all bytes to cache
            self._serial_packet_cache += data_read_bytes
            # return if not at least 1 complete packet available
            if len(self._serial_packet_cache) < SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES:
                # wait a little bit before reading again
                await asyncio.sleep(0.01)
                continue

            # sort packets by into packet type groups: magnetometer data, stim status, other
            sorted_packet_dict = sort_serial_packets(bytearray(self._serial_packet_cache))
            # update unsorted bytes
            self._serial_packet_cache = bytes(sorted_packet_dict["unread_bytes"])

            # process any other packets
            for other_packet_info in sorted_packet_dict["other_packet_info"]:
                timestamp, packet_type, packet_payload = other_packet_info
                try:
                    await self._process_comm_from_instrument(packet_type, packet_payload)
                except InstrumentError:
                    raise
                except Exception as e:
                    raise SerialCommCommandProcessingError(
                        f"Timestamp: {timestamp}, Packet Type: {packet_type}, Payload: {packet_payload}"
                    ) from e

            # Tanner (2/28/23): there is currently no data stream, so magnetometer packets can be completely ignored.

            await self._process_stim_packets(sorted_packet_dict["stimulation_stream_info"])

    # TEMPORARY TASKS

    async def _handle_firmware_update(self, comm_from_monitor: dict[str, Any]) -> None:
        logger.info("Beginning firmware update")

        # create FW update manager and wait for it to complete. Updates will be pushed to it from another task
        self._firmware_update_manager = FirmwareUpdateManager(comm_from_monitor)

        async for packet_type, bytes_to_send, command in self._firmware_update_manager:
            await self._send_data_packet(packet_type, bytes_to_send)
            await self._command_tracker.add(packet_type, command)

        self._firmware_update_manager = None

        await self._wait_for_reboot()

        await self._to_monitor_queue.put(
            {"command": "firmware_update_complete", "firmware_type": comm_from_monitor["firmware_type"]}
        )

    async def _wait_for_reboot(self) -> None:
        logger.info("Waiting for instrument to reboot")

        self._is_waiting_for_reboot = True

        # TODO raise InstrumentRebootTimeoutError() if this times out

        await self._status_beacon_received_event.wait()
        logger.info("Instrument completed reboot")

        self._is_waiting_for_reboot = False

    # HELPERS

    async def _send_data_packet(self, packet_type: int, data_to_send: bytes = bytes(0)) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        # update trackers if necessary
        if packet_type == SerialCommPacketTypes.HANDSHAKE:
            self._update_timepoints_of_events("handshake_sent")
        elif packet_type in COMMAND_PACKET_TYPES:
            self._update_timepoints_of_events("command_sent")

        data_packet = create_data_packet(get_serial_comm_timestamp(), packet_type, data_to_send)
        write_len = await self._instrument.write_async(data_packet)
        if write_len == 0:
            logger.error(f"Serial data write reporting no bytes written")

    async def _report_instrument_fw_error(self, error_details: dict[Any, Any]) -> None:
        await self._send_data_packet(SerialCommPacketTypes.ERROR_ACK)
        raise InstrumentFirmwareError(f"Error Details: {error_details}")

    async def _process_comm_from_instrument(self, packet_type: int, packet_payload: bytes) -> None:
        match packet_type:
            case SerialCommPacketTypes.CHECKSUM_FAILURE:
                returned_packet = SERIAL_COMM_MAGIC_WORD_BYTES + packet_payload
                raise SerialCommIncorrectChecksumFromPCError(returned_packet)
            case SerialCommPacketTypes.STATUS_BEACON:
                status_codes_dict = convert_status_code_bytes_to_dict(
                    # TODO see if removing this slice works
                    packet_payload[:SERIAL_COMM_STATUS_CODE_LENGTH_BYTES]
                )
                await self._process_status_codes(status_codes_dict, "Status Beacon")
            case SerialCommPacketTypes.HANDSHAKE:
                status_codes_dict = convert_status_code_bytes_to_dict(packet_payload)
                await self._process_status_codes(status_codes_dict, "Handshake Response")
            case SerialCommPacketTypes.GOING_DORMANT:
                going_dormant_reason = packet_payload[0]
                raise FirmwareGoingDormantError(going_dormant_reason)
            case packet_type if packet_type in COMMAND_PACKET_TYPES:
                await self._process_command_response(packet_type, packet_payload)
            case SerialCommPacketTypes.STIM_STATUS:
                raise NotImplementedError("Should never receive stim status packets when not stimulating")
            case SerialCommPacketTypes.CF_UPDATE_COMPLETE | SerialCommPacketTypes.MF_UPDATE_COMPLETE:
                if self._firmware_update_manager is None:
                    raise NotImplementedError("_firmware_update_manager should never be None here")
                await self._firmware_update_manager.complete()
            case SerialCommPacketTypes.BARCODE_FOUND:
                barcode = packet_payload.decode("ascii")
                logger.info(f"Barcode scanned by instrument: {barcode}")
                barcode_comm = {"command": "get_barcode", "barcode": barcode}
                await self._to_monitor_queue.put(barcode_comm)
            case SerialCommPacketTypes.GET_ERROR_DETAILS:
                error_details = parse_instrument_event_info(packet_payload)
                await self._report_instrument_fw_error(error_details)
            case _:
                raise NotImplementedError(f"Packet Type: {packet_type} is not defined")

        if packet_type in (
            *COMMAND_PACKET_TYPES,
            SerialCommPacketTypes.CF_UPDATE_COMPLETE,
            SerialCommPacketTypes.MF_UPDATE_COMPLETE,
            SerialCommPacketTypes.BARCODE_FOUND,
        ):
            self._update_timepoints_of_events("command_response_received")

    async def _process_command_response(self, packet_type: int, response_data: bytes) -> None:
        try:
            prev_command_info = await self._command_tracker.pop(packet_type)
        except ValueError:
            raise SerialCommUntrackedCommandResponseError(
                f"Packet Type ID: {packet_type}, Packet Body: {list(response_data)}"
            )

        match prev_command_info["command"]:
            # TODO make an enum for all these commands?
            case "get_metadata":
                metadata_dict = parse_metadata_bytes(response_data)
                metadata_dict_for_logging = {
                    METADATA_TAGS_FOR_LOGGING.get(key, key): val for key, val in metadata_dict.items()
                }
                if self._instrument_error_detected:
                    # Tanner (7/18/23): currently a handshake will always be sent before the metadata retrieval command is sent,
                    # and if there are error codes in the response to the handshake then this flag will be set and the system
                    # stats in the metadata should be reported instead of the error retrieval command
                    await self._report_instrument_fw_error(metadata_dict_for_logging)
                logger.info(f"Instrument metadata received: {metadata_dict_for_logging}")
                # validate after logging so that every value still gets logged in case of a bad value
                validate_instrument_metadata(metadata_dict)

                if not metadata_dict.pop("is_stingray"):
                    raise IncorrectInstrumentConnectedError()

                prev_command_info.update(metadata_dict)

                await self._send_data_packet(SerialCommPacketTypes.CHECK_CONNECTION_STATUS)
                await self._command_tracker.add(
                    SerialCommPacketTypes.CHECK_CONNECTION_STATUS, {"command": "check_connection_status"}
                )
            case "start_stim_checks":
                stimulator_check_dict = convert_stimulator_check_bytes_to_dict(response_data)

                stimulator_circuit_statuses: dict[int, str] = {}
                adc_readings: dict[int, tuple[int, int]] = {}

                for module_id, (adc8, adc9, status_int) in enumerate(zip(*stimulator_check_dict.values())):
                    well_idx = STIM_MODULE_ID_TO_WELL_IDX[module_id]
                    if well_idx not in prev_command_info["well_indices"]:
                        continue
                    status_str = list(StimulatorCircuitStatuses)[status_int + 1].name.lower()
                    stimulator_circuit_statuses[well_idx] = status_str
                    adc_readings[well_idx] = (adc8, adc9)

                prev_command_info["stimulator_circuit_statuses"] = stimulator_circuit_statuses
                prev_command_info["adc_readings"] = adc_readings

                logger.info(f"Stim circuit check results: {prev_command_info}")
            case "set_protocols":
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise InstrumentCommandResponseError("set_protocols")
                    prev_command_info["hardware_test_message"] = "Command failed"  # pragma: no cover
            case "start_stimulation":
                # Tanner (10/25/21): if needed, can save _base_global_time_of_data_stream here
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise InstrumentCommandResponseError("start_stimulation")
                    prev_command_info["hardware_test_message"] = "Command failed"  # pragma: no cover
                prev_command_info["timestamp"] = datetime.datetime.utcnow()
                self._is_stimulating = True
            case "stop_stimulation":
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise InstrumentCommandResponseError("stop_stimulation")
                    prev_command_info["hardware_test_message"] = "Command failed"  # pragma: no cover
                self._is_stimulating = False
            case command if command in INTERMEDIATE_FIRMWARE_UPDATE_COMMANDS:
                if self._firmware_update_manager is None:
                    raise NotImplementedError("_firmware_update_manager should never be None here")
                await self._firmware_update_manager.update(command, response_data)
            case "check_connection_status":
                prev_command_info["status"] = response_data[0]
                self._system_in_offline_mode = response_data[0] == InstrumentConnectionStatuses.OFFLINE.value
                if self._system_in_offline_mode:
                    self._offline_state_change.set()
                    logger.info("Starting up in offline mode")
            case "end_offline_mode":
                parsed_stim_dict = parse_end_offline_mode_bytes(response_data)
                prev_command_info |= {"stim_state": parsed_stim_dict}
            case "init_offline_mode":
                self._offline_state_change.set()

        if prev_command_info["command"] not in INTERMEDIATE_FIRMWARE_UPDATE_COMMANDS:
            await self._to_monitor_queue.put(prev_command_info)

    async def _process_stim_packets(self, stim_stream_info: dict[str, bytes | int]) -> None:
        if not stim_stream_info["num_packets"]:
            return

        self._update_timepoints_of_events("stim_data_received")

        # Tanner (2/28/23): there is currently no data stream, so only need to check for protocols that have completed

        protocol_statuses: dict[int, Any] = parse_stim_data(*stim_stream_info.values())

        logger.debug("Stim statuses received: %s", protocol_statuses)

        protocols_completed = [
            protocol_idx
            for protocol_idx, status_updates_arr in protocol_statuses.items()
            if status_updates_arr[1][-1] == STIM_COMPLETE_SUBPROTOCOL_IDX
        ]
        if protocols_completed:
            self._protocols_running -= set(protocols_completed)
            await self._to_monitor_queue.put(
                {"command": "stim_status_update", "protocols_completed": protocols_completed}
            )

    async def _process_status_codes(self, status_codes_dict: dict[str, int], comm_type: str) -> None:
        # placing this here so that handshake responses also set the event
        self._status_beacon_received_event.set()

        self._update_timepoints_of_events("status_beacon_received")

        status_codes_msg = f"{comm_type} received from instrument. Status Codes: {status_codes_dict}"

        if any(status_codes_dict.values()):
            logger.error(status_codes_msg)
            self._instrument_error_detected = True

            logger.error("Retrieving error details from instrument")
            await self._send_data_packet(SerialCommPacketTypes.GET_ERROR_DETAILS)
            await self._command_tracker.add(
                SerialCommPacketTypes.GET_ERROR_DETAILS, {"command": "get_error_details"}
            )
        else:
            logger.debug(status_codes_msg)

    def _update_timepoints_of_events(self, *event_names: str) -> None:
        self._timepoints_of_events = self._timepoints_of_events._replace(
            **{event: perf_counter() for event in event_names}
        )

    def _log_dur_since_events(self) -> None:
        current_timepoint = perf_counter()
        durs = {
            event_name: ("No occurrence" if event_timepoint is None else current_timepoint - event_timepoint)
            for event_name, event_timepoint in self._timepoints_of_events._asdict().items()
        }
        logger.info(f"Duration (seconds) since events: {durs}")


FirmwareUpdateItems = tuple[int, bytes, dict[str, Any]]


# TODO ADD LOGGING TO THIS
class FirmwareUpdateManager:
    def __init__(self, update_info: dict[str, Any]) -> None:
        self._file_contents = update_info.pop("file_contents")
        self._file_checksum = crc32(self._file_contents)

        self._update_type = update_info["firmware_type"]
        self._version = update_info.pop("version")

        self._command_template = update_info
        self._command_template.pop("command")

        self._packet_idx = -1

        self._sentinel = object()
        self._command_queue: asyncio.Queue[FirmwareUpdateItems | object] = asyncio.Queue()

    def __aiter__(self) -> "FirmwareUpdateManager":
        self._packet_idx = -1
        return self

    async def __anext__(self) -> FirmwareUpdateItems:
        if self._packet_idx == -1:
            command_items = self._create_initial_update_items()
            self._packet_idx += 1
        else:
            command_items = await self._command_queue.get()  # type: ignore
            if command_items is self._sentinel:
                raise StopAsyncIteration
        return command_items

    async def update(self, command: str, response_data: bytes) -> None:
        if response_data[0]:
            error_msg = command
            if command == "send_firmware_data":
                error_msg += f", packet index: {self._packet_idx}"
            raise InstrumentCommandResponseError(error_msg)

        if command != "end_of_firmware_update":
            if command == "send_firmware_data":
                self._packet_idx += 1
            await self._command_queue.put(self._create_next_update_items())

    async def complete(self) -> None:
        await self._command_queue.put(self._sentinel)

    def _create_initial_update_items(self) -> FirmwareUpdateItems:
        return (
            SerialCommPacketTypes.BEGIN_FIRMWARE_UPDATE,
            bytes([self._update_type == "channel"])
            + convert_semver_str_to_bytes(self._version)
            + len(self._file_contents).to_bytes(4, byteorder="little"),
            {**self._command_template, "command": "start_firmware_update"},
        )

    def _create_next_update_items(self) -> FirmwareUpdateItems:
        command: dict[str, Any]

        if len(self._file_contents) > 0:
            packet_type = SerialCommPacketTypes.FIRMWARE_UPDATE
            bytes_to_send = (
                bytes([self._packet_idx]) + self._file_contents[: SERIAL_COMM_MAX_PAYLOAD_LENGTH_BYTES - 1]
            )
            command = {
                "command": "send_firmware_data",
                "firmware_type": self._update_type,
                "packet_index": self._packet_idx,
            }
            self._file_contents = self._file_contents[SERIAL_COMM_MAX_PAYLOAD_LENGTH_BYTES - 1 :]
        else:
            packet_type = SerialCommPacketTypes.END_FIRMWARE_UPDATE
            bytes_to_send = self._file_checksum.to_bytes(4, byteorder="little")
            command = {"command": "end_of_firmware_update", "firmware_type": self._update_type}

        return packet_type, bytes_to_send, command


class VirtualInstrumentConnection:
    def __init__(self) -> None:
        self.reader: asyncio.StreamReader
        self.writer: asyncio.StreamWriter

        # arbitrary number, this is used by InstrumentComm when connected to a real serial device, so need to have this present on this virtual device
        self.in_waiting = 10000

    async def connect(self) -> None:
        self.reader, self.writer = await asyncio.open_connection("", 56575)

    async def read_async(self, size: int = 1) -> bytes:
        # Tanner (3/17/23): asyncio.StreamReader does not have configurable timeouts on reads, so if trying to
        # read a specific number of bytes it will block until at least one is available
        try:
            data = await self.reader.read(size)
        except Exception:  # nosec B110
            # TODO make sure to add a unit test confirming this can be cancelled correctly
            # TODO raise a different error here?
            return bytes(0)
        logger.debug("RECV: %s", list(data))
        return data

    async def write_async(self, data: bytearray | bytes | memoryview) -> int:
        try:
            self.writer.write(data)
            await self.writer.drain()
        except Exception:  # nosec B110
            # TODO make sure to add a unit test confirming this can be cancelled correctly
            # TODO raise a different error here?
            return 0
        else:
            logger.debug("SEND: %s", list(data))
            return len(data)
