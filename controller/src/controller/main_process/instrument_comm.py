# -*- coding: utf-8 -*-
import asyncio
from collections import defaultdict
from collections import deque
import datetime
import logging
from typing import Any

from aioserial import AioSerial
from controller.utils.serial_comm import convert_status_code_bytes_to_dict
from controller.utils.serial_comm import convert_stimulator_check_bytes_to_dict
from controller.utils.serial_comm import create_data_packet
from controller.utils.serial_comm import get_serial_comm_timestamp
from controller.utils.serial_comm import parse_metadata_bytes
import serial
import serial.tools.list_ports as list_ports

from ..constants import SERIAL_COMM_BARCODE_FOUND_PACKET_TYPE
from ..constants import SERIAL_COMM_BAUD_RATE
from ..constants import SERIAL_COMM_BEGIN_FIRMWARE_UPDATE_PACKET_TYPE
from ..constants import SERIAL_COMM_CHECKSUM_FAILURE_PACKET_TYPE
from ..constants import SERIAL_COMM_END_FIRMWARE_UPDATE_PACKET_TYPE
from ..constants import SERIAL_COMM_ERROR_ACK_PACKET_TYPE
from ..constants import SERIAL_COMM_FIRMWARE_UPDATE_PACKET_TYPE
from ..constants import SERIAL_COMM_GET_METADATA_PACKET_TYPE
from ..constants import SERIAL_COMM_GOING_DORMANT_PACKET_TYPE
from ..constants import SERIAL_COMM_HANDSHAKE_PACKET_TYPE
from ..constants import SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS
from ..constants import SERIAL_COMM_MAGIC_WORD_BYTES
from ..constants import SERIAL_COMM_MAGNETOMETER_DATA_PACKET_TYPE
from ..constants import SERIAL_COMM_MAX_FULL_PACKET_LENGTH_BYTES
from ..constants import SERIAL_COMM_PACKET_METADATA_LENGTH_BYTES
from ..constants import SERIAL_COMM_REBOOT_PACKET_TYPE
from ..constants import SERIAL_COMM_REGISTRATION_TIMEOUT_SECONDS
from ..constants import SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS
from ..constants import SERIAL_COMM_SET_NICKNAME_PACKET_TYPE
from ..constants import SERIAL_COMM_SET_SAMPLING_PERIOD_PACKET_TYPE
from ..constants import SERIAL_COMM_SET_STIM_PROTOCOL_PACKET_TYPE
from ..constants import SERIAL_COMM_START_DATA_STREAMING_PACKET_TYPE
from ..constants import SERIAL_COMM_START_STIM_PACKET_TYPE
from ..constants import SERIAL_COMM_STATUS_BEACON_PACKET_TYPE
from ..constants import SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS
from ..constants import SERIAL_COMM_STATUS_BEACON_TIMEOUT_SECONDS
from ..constants import SERIAL_COMM_STATUS_CODE_LENGTH_BYTES
from ..constants import SERIAL_COMM_STIM_IMPEDANCE_CHECK_PACKET_TYPE
from ..constants import SERIAL_COMM_STIM_STATUS_PACKET_TYPE
from ..constants import SERIAL_COMM_STOP_DATA_STREAMING_PACKET_TYPE
from ..constants import SERIAL_COMM_STOP_STIM_PACKET_TYPE
from ..constants import STIM_COMPLETE_SUBPROTOCOL_IDX
from ..constants import STIM_MODULE_ID_TO_WELL_IDX
from ..constants import StimulatorCircuitStatuses
from ..constants import STM_VID
from ..exceptions import FirmwareGoingDormantError
from ..exceptions import FirmwareUpdateCommandFailedError
from ..exceptions import InstrumentDataStreamingAlreadyStartedError
from ..exceptions import InstrumentDataStreamingAlreadyStoppedError
from ..exceptions import InstrumentFirmwareError
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
from ..utils.data_parsing_cy import parse_stim_data
from ..utils.data_parsing_cy import sort_serial_packets


logger = logging.getLogger(__name__)


COMMAND_PACKET_TYPES = frozenset(
    [
        SERIAL_COMM_REBOOT_PACKET_TYPE,
        SERIAL_COMM_SET_STIM_PROTOCOL_PACKET_TYPE,
        SERIAL_COMM_START_STIM_PACKET_TYPE,
        SERIAL_COMM_STOP_STIM_PACKET_TYPE,
        SERIAL_COMM_STIM_IMPEDANCE_CHECK_PACKET_TYPE,
        SERIAL_COMM_SET_SAMPLING_PERIOD_PACKET_TYPE,
        SERIAL_COMM_START_DATA_STREAMING_PACKET_TYPE,
        SERIAL_COMM_STOP_DATA_STREAMING_PACKET_TYPE,
        SERIAL_COMM_GET_METADATA_PACKET_TYPE,
        SERIAL_COMM_SET_NICKNAME_PACKET_TYPE,
        SERIAL_COMM_BEGIN_FIRMWARE_UPDATE_PACKET_TYPE,
        SERIAL_COMM_FIRMWARE_UPDATE_PACKET_TYPE,
        SERIAL_COMM_END_FIRMWARE_UPDATE_PACKET_TYPE,
    ]
)


class InstrumentComm:
    """TODO."""

    def __init__(
        self,
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        # comm queues
        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue
        # instrument
        self._instrument: AioSerial | None = None
        self._serial_packet_cache = bytes(0)
        # instrument status
        self._hardware_test_mode = False  # TODO
        self._status_beacon_received = asyncio.Event()
        self._wells_actively_stimulating: set[int] = set()

        self._command_tracker = CommandTracker()
        # self._tasks = set()

    # TASKS

    async def run(self) -> None:
        await self._create_connection_to_instrument()

        # start running these tasks in the background
        tasks = {
            asyncio.create_task(self._handle_comm_from_monitor()),
            asyncio.create_task(self._handle_handshake()),
        }
        # register magic word before starting any other tasks
        await self._register_magic_word()

        tasks.add(asyncio.create_task(self._handle_command_tracking()))
        tasks.add(asyncio.create_task(self._handle_beacon_tracking()))
        tasks.add(asyncio.create_task(self._handle_data_stream()))

        # TODO ?
        # self._check_reboot_status()
        # self._check_firmware_update_status()
        # self._check_worker_thread()

        # TODO error handling, finish when first complete, etc.
        await asyncio.wait(tasks)

    async def _create_connection_to_instrument(self) -> None:
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

        if not self._instrument:
            raise NotImplementedError("TODO")
            # create simulator as no serial connection could be made
            # creating_sim_msg = "No instrument detected. Creating simulator."
            # simulator = MantarrayMcSimulator(Queue(), Queue(), Queue(), Queue(), num_wells=self._num_wells)
            # return simulator, creating_sim_msg

        await self._to_monitor_queue.put(
            {
                "communication_type": "instrument_connection_made",
                "in_simulation_mode": not isinstance(self._instrument, AioSerial),
            }
        )

    async def _handle_comm_from_monitor(self) -> None:
        pass  # TODO

    async def _handle_handshake(self) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        while True:
            await self._send_data_packet(SERIAL_COMM_HANDSHAKE_PACKET_TYPE)
            await asyncio.sleep(SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS)

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
            # TODO figure out what happens if a different exception type gets raised in search_for_magic_word
        except asyncio.TimeoutError:
            # if this point is reach it's most likely that at some point no additional bytes were being read
            raise SerialCommPacketRegistrationReadEmptyError()

        # put the magic word bytes into the cache so the next data packet can be read properly
        self._serial_packet_cache = SERIAL_COMM_MAGIC_WORD_BYTES

    async def _handle_beacon_tracking(self) -> None:
        while True:
            try:
                await asyncio.wait_for(
                    self._status_beacon_received.wait(), SERIAL_COMM_STATUS_BEACON_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                # TODO handle self._is_waiting_for_reboot, self._is_updating_firmware, self._is_setting_nickname
                raise SerialCommStatusBeaconTimeoutError()

            self._status_beacon_received.clear()

    async def _handle_command_tracking(self) -> None:
        expired_command = await self._command_tracker.wait_for_command_timeout()
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

    # UTILITIES

    async def _send_data_packet(self, packet_type: int, data_to_send: bytes = bytes(0)) -> None:
        if not self._instrument:
            raise NotImplementedError("_instrument should never be None here")

        data_packet = create_data_packet(get_serial_comm_timestamp(), packet_type, data_to_send)
        await self._instrument.write_async(data_packet)

    async def _process_comm_from_instrument(self, packet_type: int, packet_payload: bytes) -> None:
        if packet_type == SERIAL_COMM_CHECKSUM_FAILURE_PACKET_TYPE:
            returned_packet = SERIAL_COMM_MAGIC_WORD_BYTES + packet_payload
            raise SerialCommIncorrectChecksumFromPCError(returned_packet)

        if packet_type == SERIAL_COMM_STATUS_BEACON_PACKET_TYPE:
            # TODO
            await self._process_status_beacon(packet_payload)
        elif packet_type == SERIAL_COMM_HANDSHAKE_PACKET_TYPE:
            status_codes_dict = convert_status_code_bytes_to_dict(packet_payload)
            # TODO
            await self._process_status_codes(status_codes_dict, "Handshake Response")
        elif packet_type == SERIAL_COMM_MAGNETOMETER_DATA_PACKET_TYPE:
            raise NotImplementedError(
                "Should never receive magnetometer data packets when not streaming data"
            )
        elif packet_type == SERIAL_COMM_GOING_DORMANT_PACKET_TYPE:
            going_dormant_reason = packet_payload[0]
            raise FirmwareGoingDormantError(going_dormant_reason)
        elif packet_type in COMMAND_PACKET_TYPES:
            # TODO
            try:
                prev_command = await self._command_tracker.pop(packet_type)
            except ValueError:
                raise SerialCommUntrackedCommandResponseError(
                    f"Packet Type ID: {packet_type}, Packet Body: {str(packet_payload)}"
                )

            response_data = packet_payload
            if prev_command["command"] == "get_metadata":
                prev_command["metadata"] = parse_metadata_bytes(response_data)
            # elif prev_command["command"] == "reboot":
            #     prev_command["message"] = "Instrument beginning reboot"
            #     # TODO self._time_of_reboot_start = perf_counter()
            elif prev_command["command"] == "start_stim_checks":
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
            elif prev_command["command"] == "set_protocols":
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationProtocolUpdateFailedError()
                    prev_command["hardware_test_message"] = "Command failed"  # pragma: no cover
                # remove stim info so it is not logged again
                prev_command.pop("stim_info")
            elif prev_command["command"] == "start_stimulation":
                # Tanner (10/25/21): if needed, can save _base_global_time_of_data_stream here
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationStatusUpdateFailedError("start_stimulation")
                    prev_command["hardware_test_message"] = "Command failed"  # pragma: no cover
                prev_command["timestamp"] = datetime.datetime.utcnow()
                self._is_stimulating = True  # TODO
            elif prev_command["command"] == "stop_stimulation":
                if response_data[0]:
                    if not self._hardware_test_mode:
                        raise StimulationStatusUpdateFailedError("stop_stimulation")
                    prev_command["hardware_test_message"] = "Command failed"  # pragma: no cover
                self._is_stimulating = False
            # elif prev_command["command"] in (
            #     "start_firmware_update",
            #     "send_firmware_data",
            #     "end_of_firmware_update",
            # ):
            #     if response_data[0]:
            #         error_msg = prev_command["command"]
            #         if error_msg == "send_firmware_data":
            #             error_msg += f", packet index: {self._firmware_packet_idx}"
            #         raise FirmwareUpdateCommandFailedError(error_msg)
            #     if prev_command["command"] == "end_of_firmware_update":
            #         # Tanner (11/16/21): reset here instead of with the other firmware update values so that the error message above can include the packet index
            #         self._firmware_packet_idx = None
            #         self._time_of_firmware_update_start = perf_counter()
            #     else:
            #         if prev_command["command"] == "send_firmware_data":
            #             if self._firmware_packet_idx is None:  # making mypy happy
            #                 raise NotImplementedError("_firmware_file_contents should never be None here")
            #             self._firmware_packet_idx += 1
            #         self._handle_firmware_update()

            await self._to_monitor_queue.put(prev_command)
        elif packet_type == SERIAL_COMM_STIM_STATUS_PACKET_TYPE:
            raise NotImplementedError("Should never receive stim status packets when not stimulating")
        # elif packet_type in (
        #     SERIAL_COMM_CF_UPDATE_COMPLETE_PACKET_TYPE,
        #     SERIAL_COMM_MF_UPDATE_COMPLETE_PACKET_TYPE,
        # ):
        #     self._to_monitor_queue.put(
        #         {
        #             "communication_type": "firmware_update",
        #             "command": "update_completed",
        #             "firmware_type": self._firmware_update_type,
        #         }
        #     )
        #     self._firmware_update_type = ""
        #     self._is_updating_firmware = False
        #     self._time_of_firmware_update_start = None
        #     # set up values for reboot
        #     self._is_waiting_for_reboot = True
        #     self._time_of_reboot_start = perf_counter()
        elif packet_type == SERIAL_COMM_BARCODE_FOUND_PACKET_TYPE:
            barcode = packet_payload.decode("ascii")
            barcode_comm = {
                "communication_type": "barcode_comm",
                "barcode": barcode,
                # TODO ? "valid": check_barcode_is_valid(barcode, True),
            }
            await self._to_monitor_queue.put(barcode_comm)
        else:
            raise UnrecognizedSerialCommPacketTypeError(f"Packet Type ID: {packet_type} is not defined")

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
        # TODO make this all a stand alone task, wait for an event
        # if status_codes_dict["main_status"] == SERIAL_COMM_OKAY_CODE and self._auto_get_metadata:
        #     await self._send_data_packet(SERIAL_COMM_GET_METADATA_PACKET_TYPE)
        #     self._add_command_to_track(  # TODO
        #         SERIAL_COMM_GET_METADATA_PACKET_TYPE,
        #         {"communication_type": "metadata_comm", "command": "get_metadata"},
        #     )

    async def _process_status_codes(self, status_codes_dict: dict[str, int], comm_type: str) -> None:
        # TODO
        # if (
        #     self._time_of_reboot_start is not None
        # ):  # Tanner (4/1/21): want to check that reboot has actually started before considering a status beacon to mean that reboot has completed. It is possible (and has happened in unit tests) where a beacon is received in between sending the reboot command and the instrument actually beginning to reboot
        #     self._is_waiting_for_reboot = False
        #     self._time_of_reboot_start = None
        #     self._to_monitor_queue.put(
        #         {
        #             "communication_type": "to_instrument",
        #             "command": "reboot",
        #             "message": "Instrument completed reboot",
        #         }
        #     )
        self._status_beacon_received.set()

        status_codes_msg = f"{comm_type} received from instrument. Status Codes: {status_codes_dict}"
        if any(status_codes_dict.values()):
            await self._send_data_packet(SERIAL_COMM_ERROR_ACK_PACKET_TYPE)
            raise InstrumentFirmwareError(status_codes_msg)
        logger.debug(status_codes_msg)


class Command:
    def __init__(self, info: dict[str, Any], timeout_info: asyncio.Future[dict[str, Any]]) -> None:
        self.info = info

        self._timeout_info = timeout_info
        self._timer = asyncio.create_task(self._start_timer())

    async def _start_timer(self) -> None:
        try:
            await asyncio.sleep(SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS)
        except asyncio.CancelledError:
            return
        else:
            if not self._timeout_info.done() and not self._timeout_info.cancelled():
                self._timeout_info.set_result(self.info)

    async def complete(self) -> None:
        self._timer.cancel()
        await self._timer


class CommandTracker:
    def __init__(self) -> None:
        self._command_mapping: dict[int, deque[Command]] = defaultdict(deque)

        self._timeout_info: asyncio.Future[dict[str, Any]] = asyncio.Future()

    async def wait_for_command_timeout(self) -> dict[str, Any]:
        try:
            return await self._timeout_info
        except asyncio.CancelledError:
            # TODO complete all commands
            raise

    def add(self, packet_type: int, command_info: dict[str, Any]) -> None:
        self._command_mapping[packet_type].append(Command(command_info, self._timeout_info))

    async def pop(self, packet_type: int) -> dict[str, Any]:
        try:
            commands_for_packet_type = self._command_mapping[packet_type]
        except KeyError as e:
            raise ValueError(f"No commands of packet type: {packet_type}") from e

        command = commands_for_packet_type.popleft()
        await command.complete()

        # remove this packet type from the dict if the deque is now empty
        if not self._command_mapping[packet_type]:
            self._command_mapping.pop(packet_type)

        return command.info

    # def __bool__(self) -> bool:
    #     return bool(self._command_mapping)
