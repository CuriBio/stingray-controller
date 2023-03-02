# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
from typing import Any

from aioserial import AioSerial
import serial
import serial.tools.list_ports as list_ports

from ..constants import SERIAL_COMM_BAUD_RATE
from ..constants import SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS
from ..constants import SERIAL_COMM_MAGIC_WORD_BYTES
from ..constants import SERIAL_COMM_MAX_FULL_PACKET_LENGTH_BYTES
from ..constants import SERIAL_COMM_OKAY_CODE
from ..constants import SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES
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
from ..exceptions import FirmwareUpdateCommandFailedError
from ..exceptions import InstrumentDataStreamingAlreadyStartedError
from ..exceptions import InstrumentDataStreamingAlreadyStoppedError
from ..exceptions import InstrumentFirmwareError
from ..exceptions import NoInstrumentDetectedError
from ..exceptions import SerialCommCommandProcessingError
from ..exceptions import SerialCommCommandResponseTimeoutError
from ..exceptions import SerialCommIncorrectChecksumFromPCError
from ..exceptions import SerialCommPacketRegistrationReadEmptyError
from ..exceptions import SerialCommPacketRegistrationSearchExhaustedError
from ..exceptions import SerialCommPacketRegistrationTimeoutError
from ..exceptions import SerialCommStatusBeaconTimeoutError
from ..exceptions import SerialCommUntrackedCommandResponseError
from ..exceptions import StimulationProtocolUpdateFailedError
from ..exceptions import StimulationStatusUpdateFailedError
from ..exceptions import UnrecognizedSerialCommPacketTypeError
from ..utils.command_tracking import CommandTracker
from ..utils.data_parsing_cy import parse_stim_data
from ..utils.data_parsing_cy import sort_serial_packets
from ..utils.serial_comm import convert_status_code_bytes_to_dict
from ..utils.serial_comm import convert_stimulator_check_bytes_to_dict
from ..utils.serial_comm import create_data_packet
from ..utils.serial_comm import get_serial_comm_timestamp
from ..utils.serial_comm import parse_metadata_bytes


logger = logging.getLogger(__name__)


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
    ]
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

        # TODO reorganize these?
        # instrument
        self._instrument: AioSerial | None = None
        self._serial_packet_cache = bytes(0)
        # instrument status
        self._hardware_test_mode = hardware_test_mode
        self._status_beacon_received = asyncio.Event()
        self._is_device_connection_ready = asyncio.Event()
        self._is_waiting_for_reboot = False
        self._is_updating_firmware = False
        # stimulation values
        self._wells_assigned_a_protocol: frozenset[int] = frozenset()
        self._wells_actively_stimulating: set[int] = set()

        self._command_tracker = CommandTracker()
        # self._tasks = set()

    # PROPERTIES

    @property
    def _instrument_in_sensitive_state(self) -> bool:
        return self._is_waiting_for_reboot or self._is_updating_firmware

    @property
    def _is_stimulating(self) -> bool:
        return len(self._wells_actively_stimulating) > 0

    @_is_stimulating.setter
    def _is_stimulating(self, value: bool) -> None:
        if value:
            self._wells_actively_stimulating = set(well for well in self._wells_assigned_a_protocol)
        else:
            self._wells_actively_stimulating = set()

    # TASKS

    async def run(self) -> None:
        self._create_connection_to_instrument()

        comm_tasks = {
            asyncio.create_task(self._handle_comm_from_monitor()),
            asyncio.create_task(self._handle_handshake()),
        }

        # register magic word before starting any other tasks
        await self._register_magic_word()

        comm_tasks |= {
            asyncio.create_task(self._handle_data_stream()),
            asyncio.create_task(self._handle_command_tracking()),
            asyncio.create_task(self._handle_beacon_tracking()),
        }

        await self._get_device_metadata()

        # TODO
        # self._check_reboot_status()
        # self._check_firmware_update_status()
        # TODO ?
        # self._check_worker_thread()

        # TODO error handling, finish when first complete, etc.
        await asyncio.wait(comm_tasks)

    def _create_connection_to_instrument(self) -> None:
        for port_info in list_ports.comports():
            # Tanner (6/14/21): attempt to connect to any device with the STM vendor ID
            if port_info.vid == STM_VID:
                logger.info(f"Instrument detected with description: {port_info.description}")
                self._instrument = AioSerial(
                    port=port_info.name,
                    baudrate=SERIAL_COMM_BAUD_RATE,
                    bytesize=8,
                    timeout=0,
                    stopbits=serial.STOPBITS_ONE,
                )
                break

        if not self._instrument:
            raise NoInstrumentDetectedError()

    async def _register_magic_word(self) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        # read bytes once every second until enough bytes have been read or timeout occurs
        # Tanner (3/16/21): issue seen with simulator taking slightly longer than status beacon period to send next data packet
        magic_word_len = len(SERIAL_COMM_MAGIC_WORD_BYTES)
        seconds_remaining = SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS + 4
        magic_word_test_bytes = await self._instrument.read(size=magic_word_len)
        while (num_bytes_remaining := magic_word_len - len(magic_word_test_bytes)) and seconds_remaining:
            magic_word_test_bytes += await self._instrument.read(size=num_bytes_remaining)
            seconds_remaining -= 1
            await asyncio.sleep(1)
        if len(magic_word_test_bytes) != magic_word_len:
            # if the entire period has passed and no more bytes are available an error has occurred with the Mantarray that is considered fatal
            raise SerialCommPacketRegistrationTimeoutError(magic_word_test_bytes)

        # read more bytes until the magic word is registered, the timeout value is reached, or the maximum number of bytes are read
        async def search_for_magic_word() -> None:
            num_bytes_checked = 0
            magic_word_test_bytes = bytes(0)
            while magic_word_test_bytes != SERIAL_COMM_MAGIC_WORD_BYTES:
                # read 0 or 1 bytes, depending on what is available in serial port
                next_byte = await self._instrument.read(size=1)  # type: ignore
                num_bytes_checked += len(next_byte)
                if next_byte:
                    # only want to run this append expression if a byte was read
                    magic_word_test_bytes = magic_word_test_bytes[1:] + next_byte
                if num_bytes_checked > SERIAL_COMM_MAX_FULL_PACKET_LENGTH_BYTES:
                    # A magic word should be encountered if this many bytes are read. If not, we can assume there is a problem with the mantarray
                    raise SerialCommPacketRegistrationSearchExhaustedError()

        try:
            await asyncio.wait_for(search_for_magic_word(), SERIAL_COMM_REGISTRATION_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            # if this point is reach it's most likely that at some point no additional bytes were being read
            raise SerialCommPacketRegistrationReadEmptyError()

        # put the magic word bytes into the cache so the next data packet can be read properly
        self._serial_packet_cache = SERIAL_COMM_MAGIC_WORD_BYTES

    async def _get_device_metadata(self) -> None:
        await self._is_device_connection_ready.wait()

        await self._send_data_packet(SerialCommPacketTypes.GET_METADATA)
        await self._command_tracker.add(
            SerialCommPacketTypes.GET_METADATA,
            {"communication_type": "metadata_comm", "command": "get_metadata"},
        )

    async def _handle_comm_from_monitor(self) -> None:
        await self._from_monitor_queue.get()
        # TODO wait if self._instrument_in_sensitive_state:  ?
        # TODO add comm handling

    async def _handle_handshake(self) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        while True:
            await self._send_data_packet(SerialCommPacketTypes.HANDSHAKE)
            await asyncio.sleep(SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS)

    async def _handle_beacon_tracking(self) -> None:
        while True:
            try:
                await asyncio.wait_for(
                    self._status_beacon_received.wait(), SERIAL_COMM_STATUS_BEACON_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                if not self._instrument_in_sensitive_state:
                    raise SerialCommStatusBeaconTimeoutError()

                # firmware updating / rebooting is complete when a beacon is received,
                # so just wait indefinitely for the next one
                await self._status_beacon_received.wait()

            self._status_beacon_received.clear()

    async def _handle_command_tracking(self) -> None:
        expired_command = await self._command_tracker.wait_for_expired_command()
        raise SerialCommCommandResponseTimeoutError(expired_command["command"])

    async def _handle_data_stream(self) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        while True:
            # read all available bytes from serial buffer
            data_read_bytes = await self._instrument.read(self._instrument.in_waiting)

            # append all bytes to cache
            self._serial_packet_cache += data_read_bytes
            # return if not at least 1 complete packet available
            if len(self._serial_packet_cache) < SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES:
                return

            # sort packets by into packet type groups: magnetometer data, stim status, other
            sorted_packet_dict = sort_serial_packets(bytearray(self._serial_packet_cache))
            # update unsorted bytes
            self._serial_packet_cache = sorted_packet_dict["unread_bytes"]

            # process any other packets
            for other_packet_info in sorted_packet_dict["other_packet_info"]:
                timestamp, packet_type, packet_payload = other_packet_info
                try:
                    await self._process_comm_from_instrument(packet_type, packet_payload)
                except (
                    InstrumentFirmwareError,
                    FirmwareGoingDormantError,
                    SerialCommUntrackedCommandResponseError,
                    SerialCommIncorrectChecksumFromPCError,
                    InstrumentDataStreamingAlreadyStartedError,
                    InstrumentDataStreamingAlreadyStoppedError,
                    StimulationProtocolUpdateFailedError,
                    StimulationStatusUpdateFailedError,
                    FirmwareUpdateCommandFailedError,
                ):
                    raise
                except Exception as e:
                    raise SerialCommCommandProcessingError(
                        f"Timestamp: {timestamp}, Packet Type: {packet_type}, Payload: {packet_payload}"
                    ) from e

            # Tanner (2/28/23): there is currently no data stream, so magnetometer packets can be completely ignored.

            await self._process_stim_packets(sorted_packet_dict["stim_stream_info"])

    # HELPERS

    async def _send_data_packet(self, packet_type: int, data_to_send: bytes = bytes(0)) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        data_packet = create_data_packet(get_serial_comm_timestamp(), packet_type, data_to_send)
        await self._instrument.write_async(data_packet)

    async def _process_comm_from_instrument(self, packet_type: int, packet_payload: bytes) -> None:
        match packet_type:
            case SerialCommPacketTypes.CHECKSUM_FAILURE:
                returned_packet = SERIAL_COMM_MAGIC_WORD_BYTES + packet_payload
                raise SerialCommIncorrectChecksumFromPCError(returned_packet)
            case SerialCommPacketTypes.STATUS_BEACON:
                await self._process_status_beacon(packet_payload)
            case SerialCommPacketTypes.HANDSHAKE:
                status_codes_dict = convert_status_code_bytes_to_dict(packet_payload)
                await self._process_status_codes(status_codes_dict, "Handshake Response")
            case SerialCommPacketTypes.MAGNETOMETER_DATA:
                raise NotImplementedError(
                    "Should never receive magnetometer data packets when not streaming data"
                )
            case SerialCommPacketTypes.GOING_DORMANT:
                going_dormant_reason = packet_payload[0]
                raise FirmwareGoingDormantError(going_dormant_reason)
            case packet_type if packet_type in COMMAND_PACKET_TYPES:
                try:
                    prev_command = await self._command_tracker.pop(packet_type)
                except ValueError:
                    raise SerialCommUntrackedCommandResponseError(
                        f"Packet Type ID: {packet_type}, Packet Body: {list(packet_payload)}"
                    )

                self._process_command_response(prev_command, packet_payload)

                await self._to_monitor_queue.put(prev_command)
            case SerialCommPacketTypes.STIM_STATUS:
                raise NotImplementedError("Should never receive stim status packets when not stimulating")
            case SerialCommPacketTypes.CF_UPDATE_COMPLETE | SerialCommPacketTypes.MF_UPDATE_COMPLETE:
                await self._to_monitor_queue.put(
                    {
                        "communication_type": "firmware_update",
                        "command": "update_completed",
                        # TODO
                        # "firmware_type": self._firmware_update_type,
                    }
                )
                # TODO self._firmware_update_type = ""
                self._is_updating_firmware = False
                self._is_waiting_for_reboot = True
            case SerialCommPacketTypes.BARCODE_FOUND:
                barcode = packet_payload.decode("ascii")
                barcode_comm = {"communication_type": "barcode_comm", "barcode": barcode}
                await self._to_monitor_queue.put(barcode_comm)
            case _:
                raise UnrecognizedSerialCommPacketTypeError(f"Packet Type: {packet_type} is not defined")

    def _process_command_response(self, prev_command: dict[str, Any], response_data: bytes) -> None:
        match prev_command["command"]:
            case "get_metadata":
                prev_command["metadata"] = parse_metadata_bytes(response_data)
            case "start_stim_checks":
                stimulator_check_dict = convert_stimulator_check_bytes_to_dict(response_data)

                stimulator_circuit_statuses: dict[int, str] = {}
                adc_readings: dict[int, tuple[int, int]] = {}

                for module_id, (adc8, adc9, status_int) in enumerate(zip(*stimulator_check_dict.values()), 1):
                    well_idx = STIM_MODULE_ID_TO_WELL_IDX[module_id]
                    if well_idx not in prev_command["well_indices"]:
                        continue
                    status_str = list(StimulatorCircuitStatuses)[status_int + 1].name.lower()
                    stimulator_circuit_statuses[well_idx] = status_str
                    adc_readings[well_idx] = (adc8, adc9)

                prev_command["stimulator_circuit_statuses"] = stimulator_circuit_statuses
                prev_command["adc_readings"] = adc_readings
            case "set_protocols":
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationProtocolUpdateFailedError()
                    prev_command["hardware_test_message"] = "Command failed"  # pragma: no cover
                # remove stim info so it is not logged again
                prev_command.pop("stim_info")
            case "start_stimulation":
                # Tanner (10/25/21): if needed, can save _base_global_time_of_data_stream here
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationStatusUpdateFailedError("start_stimulation")
                    prev_command["hardware_test_message"] = "Command failed"  # pragma: no cover
                prev_command["timestamp"] = datetime.datetime.utcnow()
                self._is_stimulating = True
            case "stop_stimulation":
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationStatusUpdateFailedError("stop_stimulation")
                    prev_command["hardware_test_message"] = "Command failed"  # pragma: no cover
                self._is_stimulating = False
            case "start_firmware_update" | "send_firmware_data" | "end_of_firmware_update":
                # TODO move all of this into its own task and push messages to it?
                pass
                # if response_data[0]:
                #     error_msg = prev_command["command"]
                #     if error_msg == "send_firmware_data":
                #         error_msg += f", packet index: {self._firmware_packet_idx}"
                #     raise FirmwareUpdateCommandFailedError(error_msg)
                # if prev_command["command"] == "end_of_firmware_update":
                #     # Tanner (11/16/21): reset here instead of with the other firmware update values so that the error message above can include the packet index
                #     self._firmware_packet_idx = None
                # else:
                #     if prev_command["command"] == "send_firmware_data":
                #         if self._firmware_packet_idx is None:  # making mypy happy
                #             raise NotImplementedError("_firmware_file_contents should never be None here")
                #         self._firmware_packet_idx += 1
                #     self._handle_firmware_update()

    async def _process_stim_packets(self, stim_stream_info: dict[str, bytes | int]) -> None:
        if not stim_stream_info["num_packets"]:
            return

        # Tanner (2/28/23): there is currently no data stream, so only need to check for wells that have completed stimulation

        well_statuses: dict[int, Any] = parse_stim_data(*stim_stream_info.values())

        wells_done_stimulating = [
            well_idx
            for well_idx, status_updates_arr in well_statuses.items()
            if status_updates_arr[1][-1] == STIM_COMPLETE_SUBPROTOCOL_IDX
        ]
        if wells_done_stimulating:
            self._wells_actively_stimulating -= set(wells_done_stimulating)
            await self._to_monitor_queue.put(
                {
                    "communication_type": "stimulation",
                    "command": "status_update",
                    "wells_done_stimulating": wells_done_stimulating,
                }
            )

    async def _process_status_beacon(self, packet_payload: bytes) -> None:
        status_codes_dict = convert_status_code_bytes_to_dict(
            packet_payload[:SERIAL_COMM_STATUS_CODE_LENGTH_BYTES]
        )
        await self._process_status_codes(status_codes_dict, "Status Beacon")

    async def _process_status_codes(self, status_codes_dict: dict[str, int], comm_type: str) -> None:
        if self._is_waiting_for_reboot:
            self._is_waiting_for_reboot = False
            logger.info("Instrument completed reboot")

        if (
            status_codes_dict["main_status"] == SERIAL_COMM_OKAY_CODE
            and not self._is_device_connection_ready.is_set()
        ):
            self._is_device_connection_ready.set()

        # placing this here so that handshake responses also set the event
        self._status_beacon_received.set()

        status_codes_msg = f"{comm_type} received from instrument. Status Codes: {status_codes_dict}"
        if any(status_codes_dict.values()):
            await self._send_data_packet(SerialCommPacketTypes.ERROR_ACK)
            raise InstrumentFirmwareError(status_codes_msg)
        logger.debug(status_codes_msg)
