# -*- coding: utf-8 -*-
"""Mantarray Microcontroller Simulator."""


import csv
import logging
from multiprocessing import Queue
import os
import random
import socket
import struct
from time import perf_counter
from time import perf_counter_ns
from typing import Any
from uuid import UUID
from zlib import crc32

from controller.constants import GOING_DORMANT_HANDSHAKE_TIMEOUT_CODE
from controller.constants import MAX_MC_REBOOT_DURATION_SECONDS
from controller.constants import MICRO_TO_BASE_CONVERSION
from controller.constants import MICROS_PER_MILLIS
from controller.constants import SERIAL_COMM_CHECKSUM_LENGTH_BYTES
from controller.constants import SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS
from controller.constants import SERIAL_COMM_HANDSHAKE_TIMEOUT_SECONDS
from controller.constants import SERIAL_COMM_MAGIC_WORD_BYTES
from controller.constants import SERIAL_COMM_MAX_PAYLOAD_LENGTH_BYTES
from controller.constants import SERIAL_COMM_MODULE_ID_TO_WELL_IDX
from controller.constants import SERIAL_COMM_NICKNAME_BYTES_LENGTH
from controller.constants import SERIAL_COMM_NUM_ALLOWED_MISSED_HANDSHAKES
from controller.constants import SERIAL_COMM_OKAY_CODE
from controller.constants import SERIAL_COMM_PACKET_TYPE_INDEX
from controller.constants import SERIAL_COMM_PAYLOAD_INDEX
from controller.constants import SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS
from controller.constants import SERIAL_COMM_TIME_INDEX_LENGTH_BYTES
from controller.constants import SERIAL_COMM_TIME_OFFSET_LENGTH_BYTES
from controller.constants import SerialCommPacketTypes
from controller.constants import STIM_COMPLETE_SUBPROTOCOL_IDX
from controller.constants import StimProtocolStatuses
from controller.utils.serial_comm import convert_adc_readings_to_circuit_status
from controller.utils.serial_comm import convert_metadata_to_bytes
from controller.utils.serial_comm import convert_stim_bytes_to_dict
from controller.utils.serial_comm import create_data_packet
from controller.utils.serial_comm import is_null_subprotocol
from controller.utils.serial_comm import validate_checksum
from controller.utils.stimulation import get_subprotocol_dur_us
from immutabledict import immutabledict
from nptyping import NDArray
import numpy as np
from pulse3D.constants import BOOT_FLAGS_UUID
from pulse3D.constants import CHANNEL_FIRMWARE_VERSION_UUID
from pulse3D.constants import INITIAL_MAGNET_FINDING_PARAMS_UUID
from pulse3D.constants import MAIN_FIRMWARE_VERSION_UUID
from pulse3D.constants import MANTARRAY_NICKNAME_UUID
from pulse3D.constants import MANTARRAY_SERIAL_NUMBER_UUID
from scipy import interpolate
from stdlib_utils import get_current_file_abs_directory
from stdlib_utils import InfiniteProcess
from stdlib_utils import resource_path

from .constants import DEFAULT_SAMPLING_PERIOD
from .constants import MICROSECONDS_PER_CENTIMILLISECOND
from .constants import SERIAL_COMM_NUM_CHANNELS_PER_SENSOR
from .constants import SERIAL_COMM_NUM_SENSORS_PER_WELL
from .exceptions import SerialCommInvalidSamplingPeriodError
from .exceptions import SerialCommTooManyMissedHandshakesError
from .exceptions import UnrecognizedSerialCommPacketTypeError
from .stimulation import StimulationProtocolManager


MAGIC_WORD_LEN = len(SERIAL_COMM_MAGIC_WORD_BYTES)
AVERAGE_MC_REBOOT_DURATION_SECONDS = MAX_MC_REBOOT_DURATION_SECONDS / 2


def _perf_counter_us() -> int:
    """Return perf_counter value as microseconds."""
    return perf_counter_ns() // 10**3


def _get_secs_since_read_start(start: float) -> float:
    return perf_counter() - start


def _get_secs_since_last_handshake(last_time: float) -> float:
    return perf_counter() - last_time


def _get_secs_since_last_status_beacon(last_time: float) -> float:
    return perf_counter() - last_time


def _get_secs_since_reboot_command(command_time: float) -> float:
    return perf_counter() - command_time


def _get_secs_since_last_comm_from_controller(last_time: float) -> float:
    return perf_counter() - last_time


def _get_us_since_last_data_packet(last_time_us: int) -> int:
    return _perf_counter_us() - last_time_us


def _get_us_since_subprotocol_start(start_time_us: int) -> int:
    return _perf_counter_us() - start_time_us


class MantarrayMcSimulator(InfiniteProcess):
    """Simulate a running Instrument with Microcontroller.

    If a command from the Controller triggers an update to the status
    code, the updated status beacon will be sent after the command
    response
    """

    # values for V1 instrument as of 6/17/22
    initial_magnet_finding_params: immutabledict[str, int] = immutabledict(
        {"X": 0, "Y": 2, "Z": -5, "REMN": 1200},
    )

    default_mantarray_nickname = "Vrtl Stingray"
    default_mantarray_serial_number = "MA2023102001"
    default_main_firmware_version = "0.0.0"
    default_channel_firmware_version = "0.0.0"
    default_plate_barcode = "ML22001000-2"
    default_stim_barcode = "MS22001000-2"
    default_metadata_values: immutabledict[UUID, Any] = immutabledict(
        {
            BOOT_FLAGS_UUID: 0b00000000,
            MANTARRAY_SERIAL_NUMBER_UUID: default_mantarray_serial_number,
            MANTARRAY_NICKNAME_UUID: default_mantarray_nickname,
            MAIN_FIRMWARE_VERSION_UUID: default_main_firmware_version,
            CHANNEL_FIRMWARE_VERSION_UUID: default_channel_firmware_version,
            INITIAL_MAGNET_FINDING_PARAMS_UUID: initial_magnet_finding_params,
            "is_stingray": False,
        }
    )
    default_adc_reading = 0xFF00
    global_timer_offset_secs = 2.5  # TODO Tanner (11/17/21): figure out if this should be removed

    def __init__(
        self,
        conn: socket.socket,
        logging_level: int = logging.INFO,
        num_wells: int = 24,
    ) -> None:
        # InfiniteProcess values
        super().__init__(Queue(), logging_level=logging_level)
        # socket connections
        self.conn = conn
        # plate values
        self._num_wells = num_wells
        # simulator values (not set in _handle_boot_up_config)
        self._time_of_last_status_beacon_secs: float | None = None
        self._ready_to_send_barcode = False
        self._timepoint_of_last_data_packet_us: int | None = None
        self._time_index_us = 0
        self._is_first_data_stream = True
        self._simulated_data_index = 0
        self._simulated_data: NDArray[np.uint16] = np.array([], dtype=np.uint16)
        self._metadata_dict: dict[UUID, Any] = dict()
        self._reset_metadata_dict()
        # self._setup_data_interpolator()
        # simulator values (set in _handle_boot_up_config)
        self._time_of_last_handshake_secs: float | None = None
        self._time_of_last_comm_from_controller_secs: float | None = None
        self._reboot_again = False
        self._reboot_time_secs: float | None
        self._boot_up_time_secs: float | None = None
        self._status_codes: list[int]
        self._sampling_period_us: int
        self._adc_readings: list[tuple[int, int]]
        self._stim_info: dict[str, Any]
        # TODO move all the stim info below into StimulationProtocolManager?
        self._stim_running_statuses: list[bool] = []
        self._timepoints_of_subprotocols_start: list[int | None]
        self._stim_time_indices: list[int]
        self._stim_subprotocol_managers: list[StimulationProtocolManager]
        self._firmware_update_type: int | None = None
        self._firmware_update_idx: int | None = None
        self._firmware_update_bytes: bytes | None
        self._new_nickname: str | None = None
        self._handle_boot_up_config()

    def start(self) -> None:
        super().start()

    @property
    def _is_streaming_data(self) -> bool:
        return self._timepoint_of_last_data_packet_us is not None

    @_is_streaming_data.setter
    def _is_streaming_data(self, value: bool) -> None:
        if value:
            self._timepoint_of_last_data_packet_us = _perf_counter_us()
            self._simulated_data_index = 0
            self._time_index_us = self._get_global_timer()
            if self._sampling_period_us == 0:
                raise NotImplementedError("sampling period must be set before streaming data")
            self._simulated_data = self.get_interpolated_data(self._sampling_period_us)
        else:
            self._timepoint_of_last_data_packet_us = None

    @property
    def _is_stimulating(self) -> bool:
        return any(self._stim_running_statuses)

    @_is_stimulating.setter
    def _is_stimulating(self, value: bool) -> None:
        # do nothing if already set to given value
        if value is self._is_stimulating:
            return

        if value:
            start_timepoint = _perf_counter_us()
            self._timepoints_of_subprotocols_start = [start_timepoint] * len(self._stim_info["protocols"])
            start_time_index = self._get_global_timer()
            self._stim_time_indices = [start_time_index] * len(self._stim_info["protocols"])
            self._stim_subprotocol_managers = [
                StimulationProtocolManager(protocol["subprotocols"])
                for protocol in self._stim_info["protocols"]
            ]
            self._stim_running_statuses = [True] * len(self._stim_info["protocols"])
        else:
            self._timepoints_of_subprotocols_start = list()
            self._stim_time_indices = list()
            self._stim_subprotocol_managers = list()
            for protocol_idx in range(len(self._stim_info["protocols"])):
                self._stim_running_statuses[protocol_idx] = False

    def _setup_data_interpolator(self) -> None:
        """Set up the function to interpolate data.

        This function is necessary to handle different sampling periods.

        This function should only be called once.
        """
        relative_path = os.path.join("src", "simulated_data", "simulated_twitch.csv")
        absolute_path = os.path.normcase(
            os.path.join(get_current_file_abs_directory(), os.pardir, os.pardir, os.pardir)
        )
        file_path = resource_path(relative_path, base_path=absolute_path)
        with open(file_path, newline="") as csvfile:
            simulated_data_timepoints = next(csv.reader(csvfile, delimiter=","))
            simulated_data_values = next(csv.reader(csvfile, delimiter=","))
        self._interpolator = interpolate.interp1d(
            np.array(simulated_data_timepoints, dtype=np.uint64),
            simulated_data_values,
        )

    def _handle_boot_up_config(self, reboot: bool = False) -> None:
        self._time_of_last_handshake_secs = None
        self._time_of_last_comm_from_controller_secs = None
        self._reset_start_time()
        self._reboot_time_secs = None
        self._status_codes = [SERIAL_COMM_OKAY_CODE] * (self._num_wells + 2)
        self._sampling_period_us = DEFAULT_SAMPLING_PERIOD
        self._adc_readings = [(self.default_adc_reading, self.default_adc_reading)] * self._num_wells
        self._stim_info = {}
        self._is_stimulating = False
        self._firmware_update_idx = None
        self._firmware_update_bytes = None
        if reboot:
            if self._firmware_update_type is not None:
                packet_type = (
                    SerialCommPacketTypes.CF_UPDATE_COMPLETE
                    if self._firmware_update_type
                    else SerialCommPacketTypes.MF_UPDATE_COMPLETE
                )
                self._send_data_packet(
                    packet_type,
                    bytes([0, 0, 0]),  # TODO make this the new firmware version
                )
            elif self._new_nickname is not None:
                self._send_data_packet(
                    SerialCommPacketTypes.SET_NICKNAME,
                    # TODO should send timestamp here
                )
                self._metadata_dict[MANTARRAY_NICKNAME_UUID] = self._new_nickname
                self._new_nickname = None
            # only set boot up time automatically after a reboot
            self._boot_up_time_secs = perf_counter()
            # after reboot, if not rebooting again, send status beacon to signal that reboot has completed
            if not self._reboot_again:
                self._send_status_beacon(truncate=False)
        self._firmware_update_type = None

    def _reset_metadata_dict(self) -> None:
        self._metadata_dict = dict(self.default_metadata_values)

    def get_interpolated_data(self, sampling_period_us: int) -> NDArray[np.uint16]:
        """Return one second (one twitch) of interpolated data."""
        data_indices = np.arange(0, MICRO_TO_BASE_CONVERSION, sampling_period_us)
        return self._interpolator(data_indices).astype(np.uint16)

    def is_rebooting(self) -> bool:
        return self._reboot_time_secs is not None

    def _get_absolute_timer(self) -> int:
        absolute_time: int = self.get_cms_since_init() * MICROSECONDS_PER_CENTIMILLISECOND
        return absolute_time

    def _get_global_timer(self) -> int:
        return self._get_absolute_timer() + int(self.global_timer_offset_secs * MICRO_TO_BASE_CONVERSION)

    def _get_timestamp(self) -> int:
        return self._get_absolute_timer()

    def _send_data_packet(
        self,
        packet_type: int,
        data_to_send: bytes = bytes(0),
        truncate: bool = False,
    ) -> None:
        timestamp = self._get_timestamp()
        data_packet = create_data_packet(timestamp, packet_type, data_to_send)
        if truncate:
            trunc_index = random.randint(  # nosec B311 # Tanner (2/4/21): Bandit blacklisted this pseudo-random generator for cryptographic security reasons that do not apply to the desktop app.
                0, len(data_packet) - 1
            )
            data_packet = data_packet[trunc_index:]
        print("SEND:", packet_type)  # allow-print

        self.conn.sendall(data_packet)

    def _commands_for_each_run_iteration(self) -> None:
        """Ordered actions to perform each iteration.

        1. Handle any test communication. This must be done first since test comm may cause the simulator to enter a certain state or send a data packet. Test communication should also be processed regardless of the internal state of the simulator.
        2. Check if rebooting. The simulator should not be responsive to any commands from the Controller while it is rebooting.
        3. Handle communication from the Controller.
        4. Send a status beacon if enough time has passed since the previous one was sent.
        5. If streaming is on, check to see how many data packets are ready to be sent and send them if necessary.
        6. If stimulating, send any stimulation data packets that need to be sent.
        7. Check if the handshake from the Controller is overdue. This should be done after checking for data sent from the Controller since the next packet might be a handshake.
        8. Check if the barcode is ready to send. This is currently the lowest priority.
        """
        if self.is_rebooting():  # Tanner (1/24/22): currently checks if self._reboot_time_secs is not None
            secs_since_reboot = _get_secs_since_reboot_command(self._reboot_time_secs)  # type: ignore
            # if secs_since_reboot is less than the reboot duration, simulator is still in the 'reboot' phase. Commands from Controller will be ignored and status beacons will not be sent
            if (
                secs_since_reboot < AVERAGE_MC_REBOOT_DURATION_SECONDS
            ):  # Tanner (3/31/21): rebooting should be much faster than the maximum allowed time for rebooting, so arbitrarily picking a simulated reboot duration
                return
            self._handle_boot_up_config(reboot=True)
            if self._reboot_again:
                self._reboot_time_secs = perf_counter()
            self._reboot_again = False
        self._handle_comm_from_controller()
        self._handle_status_beacon()
        if self._is_streaming_data:
            self._handle_magnetometer_data_packet()
        if self._is_stimulating:
            self._handle_stimulation_packets()
        self._check_handshake()
        self._handle_barcode()

    def _handle_comm_from_controller(self) -> None:
        try:
            magic_word = self.conn.recv(8)
        except BlockingIOError:
            self._check_handshake_timeout()
            return

        if magic_word != SERIAL_COMM_MAGIC_WORD_BYTES:
            raise Exception(f"Incorrect magic word from controller: {list(magic_word)}")

        packet_remainder_size_bytes = self.conn.recv(2)
        comm_from_controller = (
            magic_word
            + packet_remainder_size_bytes
            + self.conn.recv(int.from_bytes(packet_remainder_size_bytes, "little"))
        )

        self._time_of_last_comm_from_controller_secs = perf_counter()

        # validate checksum before handling the communication
        checksum_is_valid = validate_checksum(comm_from_controller)
        if not checksum_is_valid:
            # remove magic word before returning message to Controller
            trimmed_comm_from_controller = comm_from_controller[MAGIC_WORD_LEN:]
            self._send_data_packet(SerialCommPacketTypes.CHECKSUM_FAILURE, trimmed_comm_from_controller)
            return
        self._process_main_module_command(comm_from_controller)

    def _check_handshake_timeout(self) -> None:
        if self._time_of_last_comm_from_controller_secs is None:
            return
        secs_since_last_comm_from_controller = _get_secs_since_last_comm_from_controller(
            self._time_of_last_comm_from_controller_secs
        )
        if secs_since_last_comm_from_controller >= SERIAL_COMM_HANDSHAKE_TIMEOUT_SECONDS:
            self._time_of_last_comm_from_controller_secs = None
            # Tanner (3/23/22): real board will also stop stimulation and magnetometer data streaming here, but adding this to the simulator is not entirely necessary as there is no risk to leaving these processes on
            self._send_data_packet(
                SerialCommPacketTypes.GOING_DORMANT, bytes([GOING_DORMANT_HANDSHAKE_TIMEOUT_CODE])
            )

    def _process_main_module_command(self, comm_from_controller: bytes) -> None:
        # Tanner (11/15/21): many branches needed here to handle all types of communication. Could try refactoring int smaller methods for similar packet types
        send_response = True

        response_body = bytes(0)

        packet_type = comm_from_controller[SERIAL_COMM_PACKET_TYPE_INDEX]
        print("RECV:", packet_type)  # allow-print
        if packet_type == SerialCommPacketTypes.REBOOT:
            self._reboot_time_secs = perf_counter()
        elif packet_type == SerialCommPacketTypes.HANDSHAKE:
            self._time_of_last_handshake_secs = perf_counter()
            response_body += bytes(self._status_codes)
        elif packet_type == SerialCommPacketTypes.SET_STIM_PROTOCOL:
            # command fails if > 24 unique protocols given, the length of the array of protocol IDs != 24, or if > 50 subprotocols are in a single protocol
            stim_info_dict = convert_stim_bytes_to_dict(
                comm_from_controller[SERIAL_COMM_PAYLOAD_INDEX:-SERIAL_COMM_CHECKSUM_LENGTH_BYTES]
            )
            # TODO handle too many subprotocols?
            command_failed = self._is_stimulating or len(stim_info_dict["protocols"]) > self._num_wells
            if not command_failed:
                self._stim_info = stim_info_dict
            response_body += bytes([command_failed])
        elif packet_type == SerialCommPacketTypes.START_STIM:
            # command fails if protocols are not set or if stimulation is already running
            command_failed = "protocol_assignments" not in self._stim_info or self._is_stimulating
            response_body += bytes([command_failed])
            if not command_failed:
                self._is_stimulating = True
        elif packet_type == SerialCommPacketTypes.STOP_STIM:
            # command fails only if stimulation is not currently running
            command_failed = not self._is_stimulating
            response_body += bytes([command_failed])
            if not command_failed:
                self._handle_manual_stim_stop()
                self._is_stimulating = False
        elif packet_type == SerialCommPacketTypes.STIM_IMPEDANCE_CHECK:
            # Tanner (4/8/22): currently assuming that stim checks will take a negligible amount of time
            for module_readings in self._adc_readings:
                status = convert_adc_readings_to_circuit_status(*module_readings)
                response_body += struct.pack("<HHB", *module_readings, status)
        elif packet_type == SerialCommPacketTypes.SET_SAMPLING_PERIOD:
            response_body += self._update_sampling_period(comm_from_controller)
        elif packet_type == SerialCommPacketTypes.START_DATA_STREAMING:
            is_data_already_streaming = self._is_streaming_data
            response_body += bytes([is_data_already_streaming])
            self._is_streaming_data = True
            if not is_data_already_streaming:
                response_body += self._time_index_us.to_bytes(8, byteorder="little")
        elif packet_type == SerialCommPacketTypes.STOP_DATA_STREAMING:
            response_body += bytes([not self._is_streaming_data])
            if self._is_streaming_data and self._is_first_data_stream:
                self._is_first_data_stream = False
            self._is_streaming_data = False
        elif packet_type == SerialCommPacketTypes.GET_METADATA:
            response_body += convert_metadata_to_bytes(self._metadata_dict)
            # wait until this command is received and then start sending barcodes
            self._ready_to_send_barcode = True
        elif packet_type == SerialCommPacketTypes.SET_NICKNAME:
            send_response = False
            start_idx = SERIAL_COMM_PAYLOAD_INDEX
            nickname_bytes = comm_from_controller[start_idx : start_idx + SERIAL_COMM_NICKNAME_BYTES_LENGTH]
            self._new_nickname = nickname_bytes.decode("utf-8")
            self._reboot_time_secs = perf_counter()
            self._reboot_again = True
        elif packet_type == SerialCommPacketTypes.BEGIN_FIRMWARE_UPDATE:
            firmware_type = comm_from_controller[SERIAL_COMM_PAYLOAD_INDEX]
            command_failed = firmware_type not in (0, 1) or self._firmware_update_type is not None
            # TODO store new FW version and number of bytes in FW
            self._firmware_update_idx = 0
            self._firmware_update_type = firmware_type
            self._firmware_update_bytes = bytes(0)
            response_body += bytes([command_failed])
        elif packet_type == SerialCommPacketTypes.FIRMWARE_UPDATE:
            if self._firmware_update_bytes is None:
                # Tanner (11/10/21): currently unsure how real board would handle receiving this packet before the previous two firmware packet types
                raise NotImplementedError("_firmware_update_bytes should never be None here")
            if self._firmware_update_idx is None:
                # Tanner (11/10/21): currently unsure how real board would handle receiving this packet before the previous two firmware packet types
                raise NotImplementedError("_firmware_update_idx should never be None here")
            packet_idx = comm_from_controller[SERIAL_COMM_PAYLOAD_INDEX]
            new_firmware_bytes = comm_from_controller[
                SERIAL_COMM_PAYLOAD_INDEX + 1 : -SERIAL_COMM_CHECKSUM_LENGTH_BYTES
            ]
            command_failed = (
                len(new_firmware_bytes) > SERIAL_COMM_MAX_PAYLOAD_LENGTH_BYTES - 1
                or packet_idx != self._firmware_update_idx
            )
            response_body += bytes([command_failed])
            self._firmware_update_bytes += new_firmware_bytes
            self._firmware_update_idx += 1
        elif packet_type == SerialCommPacketTypes.END_FIRMWARE_UPDATE:
            if self._firmware_update_type is None:
                # Tanner (11/10/21): currently unsure how real board would handle receiving this packet before the previous two firmware packet types
                raise NotImplementedError("_firmware_update_type should never be None here")
            if self._firmware_update_bytes is None:
                # Tanner (11/10/21): currently unsure how real board would handle receiving this packet before the previous two firmware packet types
                raise NotImplementedError("_firmware_update_bytes should never be None here")
            received_checksum = int.from_bytes(
                comm_from_controller[SERIAL_COMM_PAYLOAD_INDEX : SERIAL_COMM_PAYLOAD_INDEX + 4],
                byteorder="little",
            )
            calculated_checksum = crc32(self._firmware_update_bytes)
            checksum_failure = received_checksum != calculated_checksum
            response_body += bytes([checksum_failure])
            if not checksum_failure:
                self._reboot_time_secs = perf_counter()
                self._reboot_again = True
        elif packet_type == SerialCommPacketTypes.ERROR_ACK:  # pragma: no cover
            # Tanner (3/24/22): As of right now, simulator does not need to handle this message at all, so it is the responsibility of tests to prompt simulator to go through the rest of the error handling procedure
            pass
        else:
            raise UnrecognizedSerialCommPacketTypeError(f"Packet Type ID: {packet_type} is not defined")

        if send_response:
            self._send_data_packet(packet_type, response_body)

    def _update_sampling_period(self, comm_from_controller: bytes) -> bytes:
        update_status_byte = bytes([self._is_streaming_data])
        if self._is_streaming_data:
            # cannot change configuration while data is streaming, so return here
            return update_status_byte
        # check and set sampling period
        sampling_period = int.from_bytes(
            comm_from_controller[SERIAL_COMM_PAYLOAD_INDEX : SERIAL_COMM_PAYLOAD_INDEX + 2],
            byteorder="little",
        )
        if sampling_period % MICROS_PER_MILLIS != 0:
            raise SerialCommInvalidSamplingPeriodError(sampling_period)
        self._sampling_period_us = sampling_period
        return update_status_byte

    def _handle_status_beacon(self) -> None:
        if self._time_of_last_status_beacon_secs is None:
            self._send_status_beacon(truncate=self._time_of_last_handshake_secs is None)
            return
        seconds_elapsed = _get_secs_since_last_status_beacon(self._time_of_last_status_beacon_secs)
        if seconds_elapsed >= SERIAL_COMM_STATUS_BEACON_PERIOD_SECONDS:
            self._send_status_beacon(truncate=False)

    def _send_status_beacon(self, truncate: bool = False) -> None:
        self._time_of_last_status_beacon_secs = perf_counter()
        self._send_data_packet(SerialCommPacketTypes.STATUS_BEACON, bytes(self._status_codes), truncate)

    def _check_handshake(self) -> None:
        if self._time_of_last_handshake_secs is None:
            return
        time_of_last_handshake_secs = _get_secs_since_last_handshake(self._time_of_last_handshake_secs)
        if (
            time_of_last_handshake_secs
            >= SERIAL_COMM_HANDSHAKE_PERIOD_SECONDS * SERIAL_COMM_NUM_ALLOWED_MISSED_HANDSHAKES
        ):
            raise SerialCommTooManyMissedHandshakesError()

    def _handle_barcode(self) -> None:
        if self._ready_to_send_barcode:
            self._send_data_packet(
                SerialCommPacketTypes.BARCODE_FOUND, bytes(self.default_plate_barcode, encoding="ascii")
            )
            self._send_data_packet(
                SerialCommPacketTypes.BARCODE_FOUND, bytes(self.default_stim_barcode, encoding="ascii")
            )
            self._ready_to_send_barcode = False

    def _handle_manual_stim_stop(self) -> None:
        num_status_updates = 0
        status_update_bytes = bytes(0)
        stop_time_index = self._get_global_timer()
        for protocol_idx, is_stim_running in enumerate(self._stim_running_statuses):
            if not is_stim_running:
                continue

            num_status_updates += 1
            status_update_bytes += (
                bytes([protocol_idx])
                + stop_time_index.to_bytes(8, byteorder="little")
                + bytes([StimProtocolStatuses.FINISHED])
                + bytes([STIM_COMPLETE_SUBPROTOCOL_IDX])
            )
        self._send_data_packet(
            SerialCommPacketTypes.STIM_STATUS, bytes([num_status_updates]) + status_update_bytes
        )

    def _handle_magnetometer_data_packet(self) -> None:
        """Send the required number of data packets.

        Since this process iterates once per 10 ms, it is possible that
        more than one data packet must be sent.
        """
        if self._timepoint_of_last_data_packet_us is None:  # making mypy happy
            raise NotImplementedError("_timepoint_of_last_data_packet_us should never be None here")
        us_since_last_data_packet = _get_us_since_last_data_packet(self._timepoint_of_last_data_packet_us)
        num_packets_to_send = us_since_last_data_packet // self._sampling_period_us
        if num_packets_to_send < 1:
            return
        simulated_data_len = len(self._simulated_data)

        data_packet_bytes = bytes(0)
        for _ in range(num_packets_to_send):
            # not using _send_data_packet here because it is more efficient to send all packets at once
            data_packet_bytes += create_data_packet(
                self._get_timestamp(),
                SerialCommPacketTypes.MAGNETOMETER_DATA,
                self._create_magnetometer_data_payload(),
            )
            # increment values
            self._time_index_us += self._sampling_period_us
            self._simulated_data_index = (self._simulated_data_index + 1) % simulated_data_len
        # TODO self._output_queue.put_nowait(data_packet_bytes)
        # update timepoint
        self._timepoint_of_last_data_packet_us += num_packets_to_send * self._sampling_period_us

    def _create_magnetometer_data_payload(self) -> bytes:
        # add time index to data packet body
        magnetometer_data_payload = self._time_index_us.to_bytes(
            SERIAL_COMM_TIME_INDEX_LENGTH_BYTES, byteorder="little"
        )
        for module_id in range(self._num_wells):
            # add offset of 0 since this is simulated data
            time_offset = bytes(SERIAL_COMM_TIME_OFFSET_LENGTH_BYTES)
            # create data point value
            data_value = self._simulated_data[self._simulated_data_index] * np.uint16(
                SERIAL_COMM_MODULE_ID_TO_WELL_IDX[module_id] + 1
            )
            # add data points
            well_sensor_data = time_offset + (data_value.tobytes() * SERIAL_COMM_NUM_CHANNELS_PER_SENSOR)
            well_data = well_sensor_data * SERIAL_COMM_NUM_SENSORS_PER_WELL
            magnetometer_data_payload += well_data
        return magnetometer_data_payload

    def _handle_stimulation_packets(self) -> None:
        num_status_updates = 0
        packet_bytes = bytes(0)

        for protocol_idx, protocol in enumerate(self._stim_info["protocols"]):
            start_timepoint = self._timepoints_of_subprotocols_start[protocol_idx]
            if start_timepoint is None:
                continue

            subprotocol_manager = self._stim_subprotocol_managers[protocol_idx]

            if subprotocol_manager.idx() == -1:
                curr_subprotocol_duration_us = 0
            else:
                curr_subprotocol_duration_us = get_subprotocol_dur_us(subprotocol_manager.current())

            dur_since_subprotocol_start = _get_us_since_subprotocol_start(start_timepoint)
            while dur_since_subprotocol_start >= curr_subprotocol_duration_us:
                # update time index for subprotocol
                self._stim_time_indices[protocol_idx] += curr_subprotocol_duration_us
                # need to check if the protocol is complete before advancing to the next protocol
                protocol_complete = subprotocol_manager.complete()
                # move on to next subprotocol in this protocol
                curr_subprotocol = subprotocol_manager.advance()

                packet_bytes += bytes([protocol_idx])
                num_status_updates += 1  # increment for all statuses

                packet_bytes += self._stim_time_indices[protocol_idx].to_bytes(8, byteorder="little")

                if not protocol["run_until_stopped"] and protocol_complete:
                    # protocol stopping
                    packet_bytes += bytes([StimProtocolStatuses.FINISHED, STIM_COMPLETE_SUBPROTOCOL_IDX])
                    self._stim_running_statuses[protocol_idx] = False
                    self._timepoints_of_subprotocols_start[protocol_idx] = None
                    break
                else:
                    stim_status = (
                        StimProtocolStatuses.NULL
                        if is_null_subprotocol(curr_subprotocol)
                        else StimProtocolStatuses.ACTIVE
                    )
                    packet_bytes += bytes([stim_status, subprotocol_manager.idx()])

                    # update timepoints and durations for next iteration
                    self._timepoints_of_subprotocols_start[protocol_idx] += curr_subprotocol_duration_us  # type: ignore
                    dur_since_subprotocol_start -= curr_subprotocol_duration_us
                    curr_subprotocol_duration_us = get_subprotocol_dur_us(curr_subprotocol)

        if num_status_updates > 0:
            packet_bytes = bytes([num_status_updates]) + packet_bytes
            self._send_data_packet(SerialCommPacketTypes.STIM_STATUS, packet_bytes)

        # if all timepoints are None, stimulation has ended
        self._is_stimulating = any(self._timepoints_of_subprotocols_start)

    def _drain_all_queues(self) -> dict[str, Any]:
        return {}
