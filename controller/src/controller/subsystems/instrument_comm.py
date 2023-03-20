# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
import struct
from typing import Any
from zlib import crc32

from aioserial import AioSerial
import serial
import serial.tools.list_ports as list_ports

from ..constants import GENERIC_24_WELL_DEFINITION
from ..constants import NUM_WELLS
from ..constants import SERIAL_COMM_BAUD_RATE
from ..constants import SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS
from ..constants import SERIAL_COMM_MAGIC_WORD_BYTES
from ..constants import SERIAL_COMM_MAX_FULL_PACKET_LENGTH_BYTES
from ..constants import SERIAL_COMM_MAX_PAYLOAD_LENGTH_BYTES
from ..constants import SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES
from ..constants import SERIAL_COMM_REGISTRATION_TIMEOUT_SECONDS
from ..constants import SERIAL_COMM_STATUS_BEACON_TIMEOUT_SECONDS
from ..constants import SERIAL_COMM_STATUS_CODE_LENGTH_BYTES
from ..constants import SerialCommPacketTypes
from ..constants import STIM_COMPLETE_SUBPROTOCOL_IDX
from ..constants import STIM_MODULE_ID_TO_WELL_IDX
from ..constants import StimulatorCircuitStatuses
from ..constants import STM_VID
from ..exceptions import FirmwareGoingDormantError
from ..exceptions import FirmwareUpdateCommandFailedError
from ..exceptions import InstrumentFirmwareError
from ..exceptions import NoInstrumentDetectedError
from ..exceptions import SerialCommCommandProcessingError
from ..exceptions import SerialCommCommandResponseTimeoutError
from ..exceptions import SerialCommIncorrectChecksumFromPCError
from ..exceptions import SerialCommPacketRegistrationReadEmptyError
from ..exceptions import SerialCommPacketRegistrationSearchExhaustedError
from ..exceptions import SerialCommStatusBeaconTimeoutError
from ..exceptions import SerialCommUntrackedCommandResponseError
from ..exceptions import StimulationProtocolUpdateFailedError
from ..exceptions import StimulationProtocolUpdateWhileStimulatingError
from ..exceptions import StimulationStatusUpdateFailedError
from ..utils.command_tracking import CommandTracker
from ..utils.data_parsing_cy import parse_stim_data
from ..utils.data_parsing_cy import sort_serial_packets
from ..utils.generic import wait_tasks_clean
from ..utils.serial_comm import convert_semver_str_to_bytes
from ..utils.serial_comm import convert_status_code_bytes_to_dict
from ..utils.serial_comm import convert_stim_dict_to_bytes
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

        # TODO try making some kind of container for all this data?
        # instrument
        self._instrument: AioSerial | VirtualInstrumentConnection | None = None
        self._hardware_test_mode = hardware_test_mode
        # instrument comm
        self._serial_packet_cache = bytes(0)
        self._command_tracker = CommandTracker()
        # instrument status
        self._is_waiting_for_reboot = False
        self._status_beacon_received_event = asyncio.Event()
        # stimulation values
        self._wells_assigned_a_protocol: frozenset[int] = frozenset()
        self._wells_actively_stimulating: set[int] = set()
        # firmware updating
        self._firmware_update_manager: FirmwareUpdateManager | None = None

    # PROPERTIES

    @property
    def _is_updating_firmware(self) -> bool:
        return self._firmware_update_manager is not None

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

    # ONE-SHOT TASKS

    async def run(self) -> None:
        # TODO ADD MORE LOGGING
        try:
            await self._setup()

            tasks = {
                asyncio.create_task(self._handle_comm_from_monitor()),
                asyncio.create_task(self._handle_sending_handshakes()),
                asyncio.create_task(self._handle_data_stream()),
                asyncio.create_task(self._handle_beacon_tracking()),
                asyncio.create_task(self._catch_expired_command()),
            }
            await wait_tasks_clean(tasks)
        except asyncio.CancelledError:
            logger.info("InstrumentComm cancelled")
            raise
        finally:
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

        # TODO remove this when better logging is added?
        logger.info("Instrument ready")

    async def _create_connection_to_instrument(self) -> None:
        # TODO could eventually allow the user to specify in a config file whether or not they want to connect to a real or virtual instrument

        # first, check for a real instrument on the serial COM ports
        for port_info in list_ports.comports():
            # Tanner (6/14/21): attempt to connect to any device with the STM vendor ID
            if port_info.vid == STM_VID:
                logger.info(f"Instrument detected with description: {port_info.description}")
                self._instrument = AioSerial(
                    port=port_info.name,
                    baudrate=SERIAL_COMM_BAUD_RATE,
                    bytesize=8,
                    timeout=0.01,
                    stopbits=serial.STOPBITS_ONE,
                )
                return

        # if a real instrument is not found, check for a virtual instrument
        virtual_instrument = VirtualInstrumentConnection()
        try:
            await virtual_instrument.connect()
        except Exception as e:  # TODO make this a specific exception?
            raise NoInstrumentDetectedError() from e

        self._instrument = virtual_instrument

    async def _register_magic_word(self) -> None:
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
            print("RAISING ERROR")  # allow-print
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

            match comm_from_monitor:
                case {"command": "start_stim_checks", "well_indices": well_indices}:
                    packet_type = SerialCommPacketTypes.STIM_IMPEDANCE_CHECK
                    bytes_to_send = struct.pack(
                        f"<{NUM_WELLS}?",
                        *[
                            STIM_MODULE_ID_TO_WELL_IDX[module_id] in well_indices
                            for module_id in range(1, NUM_WELLS + 1)
                        ],
                    )
                case {"command": "set_stim_protocols", "stim_info": stim_info}:
                    packet_type = SerialCommPacketTypes.SET_STIM_PROTOCOL
                    bytes_to_send = convert_stim_dict_to_bytes(stim_info)
                    if self._is_stimulating and not self._hardware_test_mode:
                        raise StimulationProtocolUpdateWhileStimulatingError()
                    protocol_assignments = stim_info["protocol_assignments"]
                    self._wells_assigned_a_protocol = frozenset(
                        GENERIC_24_WELL_DEFINITION.get_well_index_from_well_name(well_name)
                        for well_name, protocol_id in protocol_assignments.items()
                        if protocol_id is not None
                    )
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
                case _:
                    raise NotImplementedError(
                        f"InstrumentComm received invalid comm from SystemMonitor: {comm_from_monitor}"
                    )

            if packet_type is not None:
                await self._send_data_packet(packet_type, bytes_to_send)
                await self._command_tracker.add(packet_type, comm_from_monitor)

    async def _handle_sending_handshakes(self) -> None:
        # Tanner (3/17/23): handshakes are not tracked as commands
        while True:
            await self._send_data_packet(SerialCommPacketTypes.HANDSHAKE)
            await asyncio.sleep(SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS)

    async def _handle_beacon_tracking(self) -> None:
        while True:
            try:
                await asyncio.wait_for(
                    self._status_beacon_received_event.wait(), SERIAL_COMM_STATUS_BEACON_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                if not self._instrument_in_sensitive_state:
                    raise SerialCommStatusBeaconTimeoutError()

                # firmware updating / rebooting is complete when a beacon is received,
                # so just wait indefinitely for the next one
                await self._status_beacon_received_event.wait()

            self._status_beacon_received_event.clear()

    async def _handle_data_stream(self) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        while True:
            # read all available bytes from serial buffer
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
                except (
                    InstrumentFirmwareError,
                    FirmwareGoingDormantError,
                    SerialCommIncorrectChecksumFromPCError,
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

    # TEMPORARY TASKS

    async def _handle_firmware_update(self, comm_from_monitor: dict[str, Any]) -> None:
        # create FW update manager, and wait for it to complete. Updates will be pushed to it from another task
        self._firmware_update_manager = FirmwareUpdateManager(comm_from_monitor)

        async for packet_type, bytes_to_send, command in self._firmware_update_manager:
            await self._send_data_packet(packet_type, bytes_to_send)
            await self._command_tracker.add(packet_type, command)

        self._firmware_update_manager = None

        await self._wait_for_reboot()

        await self._to_monitor_queue.put(
            {
                "command": "firmware_update_complete",
                "firmware_type": comm_from_monitor["firmware_type"],
            }
        )

    async def _wait_for_reboot(self) -> None:
        self._is_waiting_for_reboot = True

        # TODO raise InstrumentRebootTimeoutError() if this times out

        await self._status_beacon_received_event.wait()
        logger.info("Instrument completed reboot")

        self._is_waiting_for_reboot = False

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
                barcode_comm = {"command": "set_barcode", "barcode": barcode}
                await self._to_monitor_queue.put(barcode_comm)
            case _:
                raise NotImplementedError(f"Packet Type: {packet_type} is not defined")

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
                prev_command_info.update(parse_metadata_bytes(response_data))  # type: ignore [arg-type]  # mypy doesn't like that the keys are UUIDs here
            case "start_stim_checks":
                stimulator_check_dict = convert_stimulator_check_bytes_to_dict(response_data)

                stimulator_circuit_statuses: dict[int, str] = {}
                adc_readings: dict[int, tuple[int, int]] = {}

                for module_id, (adc8, adc9, status_int) in enumerate(zip(*stimulator_check_dict.values()), 1):
                    well_idx = STIM_MODULE_ID_TO_WELL_IDX[module_id]
                    if well_idx not in prev_command_info["well_indices"]:
                        continue
                    status_str = list(StimulatorCircuitStatuses)[status_int + 1].name.lower()
                    stimulator_circuit_statuses[well_idx] = status_str
                    adc_readings[well_idx] = (adc8, adc9)

                prev_command_info["stimulator_circuit_statuses"] = stimulator_circuit_statuses
                prev_command_info["adc_readings"] = adc_readings
            case "set_protocols":
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationProtocolUpdateFailedError()
                    prev_command_info["hardware_test_message"] = "Command failed"  # pragma: no cover
                # TODO is this necessary now?
                # remove stim info so it is not logged again
                prev_command_info.pop("stim_info")
            case "start_stimulation":
                # Tanner (10/25/21): if needed, can save _base_global_time_of_data_stream here
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationStatusUpdateFailedError("start_stimulation")
                    prev_command_info["hardware_test_message"] = "Command failed"  # pragma: no cover
                prev_command_info["timestamp"] = datetime.datetime.utcnow()
                self._is_stimulating = True
            case "stop_stimulation":
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationStatusUpdateFailedError("stop_stimulation")
                    prev_command_info["hardware_test_message"] = "Command failed"  # pragma: no cover
                self._is_stimulating = False
            case ("start_firmware_update" | "send_firmware_data" | "end_of_firmware_update") as command:
                if self._firmware_update_manager is None:
                    raise NotImplementedError("_firmware_update_manager should never be None here")
                await self._firmware_update_manager.update(command, response_data)

        await self._to_monitor_queue.put(prev_command_info)

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
                {"command": "stim_status_update", "wells_done_stimulating": wells_done_stimulating}
            )

    async def _process_status_beacon(self, packet_payload: bytes) -> None:
        status_codes_dict = convert_status_code_bytes_to_dict(
            packet_payload[:SERIAL_COMM_STATUS_CODE_LENGTH_BYTES]
        )
        await self._process_status_codes(status_codes_dict, "Status Beacon")

    async def _process_status_codes(self, status_codes_dict: dict[str, int], comm_type: str) -> None:
        # placing this here so that handshake responses also set the event
        self._status_beacon_received_event.set()

        status_codes_msg = f"{comm_type} received from instrument. Status Codes: {status_codes_dict}"
        if any(status_codes_dict.values()):
            await self._send_data_packet(SerialCommPacketTypes.ERROR_ACK)
            raise InstrumentFirmwareError(status_codes_msg)
        logger.debug(status_codes_msg)


FirmwareUpdateItems = tuple[int, bytes, dict[str, Any]]


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
            raise FirmwareUpdateCommandFailedError(error_msg)

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
        data = await self.reader.read(size)
        logger.debug(f"RECV: {data}")  # type: ignore
        return data

    async def write_async(self, data: bytearray | bytes | memoryview) -> None:
        logger.debug(f"SEND: {data}")  # type: ignore
        self.writer.write(data)
        await self.writer.drain()
