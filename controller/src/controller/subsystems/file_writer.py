# -*- coding: utf-8 -*-
import asyncio
from collections import deque
from collections import namedtuple
import datetime
import json
import logging
import os
import tempfile
from typing import Any
import uuid

import h5py
from nptyping import NDArray
import numpy as np
from pulse3D.constants import DATETIME_STR_FORMAT as METADATA_DATETIME_STR_FORMAT
from pulse3D.constants import IS_CALIBRATION_FILE_UUID
from pulse3D.constants import METADATA_UUID_DESCRIPTIONS
from pulse3D.constants import NOT_APPLICABLE_H5_METADATA
from pulse3D.constants import PLATE_BARCODE_UUID
from pulse3D.constants import START_RECORDING_TIME_INDEX_UUID
from pulse3D.constants import STIMULATION_PROTOCOL_UUID
from pulse3D.constants import STIMULATION_READINGS
from pulse3D.constants import TIME_INDICES
from pulse3D.constants import TIME_OFFSETS
from pulse3D.constants import TISSUE_SENSOR_READINGS
from pulse3D.constants import UTC_BEGINNING_DATA_ACQUISTION_UUID
from pulse3D.constants import UTC_BEGINNING_RECORDING_UUID
from pulse3D.plate_recording import MantarrayH5FileCreator

from ..constants import CURRENT_RECORDING_FILE_VERSION
from ..constants import FILE_WRITER_BUFFER_SIZE_MILLISECONDS
from ..constants import NUM_MAG_DATA_CHANNELS_PER_WELL
from ..constants import NUM_MAG_SENSORS_PER_WELL
from ..constants import NUM_WELLS
from ..utils.aio import wait_tasks_clean
from ..utils.generic import handle_system_error


logger = logging.getLogger(__name__)

RecordingBounds = namedtuple("RecordingBounds", ["start", "stop"])

# TODO move these to pulse3D
UTC_BEGINNING_CALIBRATION_UUID = uuid.UUID("b0995a2e-8f1d-41d7-b369-54ec06656683")
CALIBRATION_TIME_INDICES = f"calibration_{TIME_INDICES}"
CALIBRATION_TIME_OFFSETS = f"calibration_{TIME_OFFSETS}"
CALIBRATION_TISSUE_SENSOR_READINGS = f"calibration_{TISSUE_SENSOR_READINGS}"
STIMULATION_READINGS_TEMPLATE = f"{STIMULATION_READINGS}_{{protocol_idx}}"


ERROR_MSG = "IN FILE WRITER"

# Tanner (5/17/21): Not sure what this value represents, should add comment if/when it is determined
MAX_DATA_LEN = 100 * 3600 * 12


def _get_earliest_required_stim_idx(
    stim_timepoints: NDArray[(1, Any), int], earliest_mag_time_idx: int
) -> int:
    return max(np.argmax(stim_timepoints > earliest_mag_time_idx) - 1, 0)  # type: ignore


class FileWriter:
    """Subsystem that manages writing data to file."""

    def __init__(
        self,
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
        data_queue: asyncio.Queue[dict[str, Any]],
        recordings_directory: str,
    ) -> None:
        # comm queues
        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue
        # data queue
        self._data_queue = data_queue

        self._recordings_directory = recordings_directory
        self._calibration_tmp_dir: tempfile.TemporaryDirectory | None = None  # type: ignore [type-arg]

        self._current_calibration_path: str | None = None
        self._current_recording_name: str | None = None
        self._current_recording_file: MantarrayH5FileCreator | None = None

        self._recording_time_idx_bounds = RecordingBounds(None, None)

        self._is_calibration_recording = False

        self._stim_info: dict[str, Any] | None = None
        self._start_data_stream_timestamp_utc: datetime.datetime | None = None
        self._end_of_mag_stream_reached = False
        self._end_of_stim_stream_reached = False

        self._mag_data_buffer: deque[dict[str, Any]] = deque()
        self._stim_data_buffers: dict[int, NDArray[(2, Any), int]] = dict()

    # PROPERTIES

    @property
    def _is_recording(self) -> bool:
        return self._recording_time_idx_bounds.start is not None

    @property
    def _current_recording_path(self) -> str | None:
        if not self._calibration_tmp_dir:
            raise NotImplementedError("self._calibration_tmp_dir should never be None here")

        if not self._current_recording_name:
            return None

        recording_dir = (
            self._calibration_tmp_dir.name if self._is_calibration_recording else self._recordings_directory
        )
        return os.path.join(recording_dir, self._current_recording_name)

    @property
    def _num_stim_protocols(self) -> int:
        if not self._stim_info:
            return 0
        return len(self._stim_info["protocols"])

    # ONE-SHOT TASKS

    async def run(self, system_error_future: asyncio.Future[int]) -> None:
        logger.info("Starting FileWriter")

        # TODO asyncio.shield functions that edit files? Need to make sure edits are done fully, i.e. add either all datasets during file creation or none of them

        try:
            self._calibration_tmp_dir = tempfile.TemporaryDirectory()

            tasks = {
                asyncio.create_task(self._handle_comm_from_monitor()),
                asyncio.create_task(self._handle_incoming_data()),
            }
            await wait_tasks_clean(tasks, error_msg=ERROR_MSG)
        except asyncio.CancelledError:
            logger.info("FileWriter cancelled")
            raise
        except BaseException as e:
            logger.exception(ERROR_MSG)
            handle_system_error(e, system_error_future)
        finally:
            if self._current_recording_file:
                await self._handle_file_close()
            if self._calibration_tmp_dir:
                self._calibration_tmp_dir.cleanup()
            logger.info("FileWriter shut down")

    # INFINITE TASKS

    async def _handle_comm_from_monitor(self) -> None:
        while True:
            comm_from_monitor = await self._from_monitor_queue.get()

            match comm_from_monitor:
                case {"command": "start_data_stream"}:
                    self._start_data_stream_timestamp_utc = datetime.datetime.utcnow()
                case {"command": "stop_data_stream"}:
                    self._start_data_stream_timestamp_utc = None
                    if self._current_recording_file:
                        await self._handle_file_close()
                case {"command": "start_recording"}:
                    await self._start_recording(comm_from_monitor)
                case {"command": "stop_recording"}:
                    await self._stop_recording(comm_from_monitor)
                case {"command": "update_recording_name"}:
                    await self._update_recording_name(comm_from_monitor)
                case {"command": "set_stim_protocols", "stim_info": stim_info}:
                    self._stim_info = stim_info
                    await self._reset_stim_data_buffers()
                    if self._is_recording:
                        await self._create_stim_datasets()

            if comm_from_monitor["command"] != "stop_recording":
                await self._to_monitor_queue.put(comm_from_monitor)

    async def _handle_incoming_data(self) -> None:
        while True:
            data_packet = await self._data_queue.get()

            match data_packet["data_type"]:
                case "magnetometer":
                    await self._process_mag_data_packet(data_packet)
                case "stimulation":
                    await self._process_stim_data_packet(data_packet)
                case invalid_data_type:
                    raise NotImplementedError(
                        f"Invalid data type from Instrument Comm Process: {invalid_data_type}"
                    )

    # COMMAND HANDLERS

    async def _start_recording(self, command: dict[str, Any]) -> None:
        metadata = command["metadata"]

        self._recording_time_idx_bounds._replace(start=metadata[START_RECORDING_TIME_INDEX_UUID])
        self._is_calibration_recording = metadata[IS_CALIBRATION_FILE_UUID]

        if self._is_calibration_recording:
            recording_prefix = "Calibration"
            # remove old calibration file if one exists
            if self._current_calibration_path and os.path.isfile(self._current_calibration_path):
                os.remove(self._current_calibration_path)
            # set new calibration file path
            self._current_calibration_path = self._current_recording_path
        else:
            recording_prefix = str(metadata[PLATE_BARCODE_UUID])

        recording_start_timestamp_str = metadata[UTC_BEGINNING_RECORDING_UUID].strftime("%Y_%m_%d__%H_%M_%S")
        self._current_recording_name = f"{recording_prefix}__{recording_start_timestamp_str}"

        await self._create_recording_file(metadata)

        if not self._is_calibration_recording:
            await self._add_calibration_data_to_recording()
            await self._add_protocols_to_recording_files()
            await self._record_data_from_buffers()

    async def _stop_recording(self, command: dict[str, Any]) -> None:
        if not self._current_recording_file:
            raise NotImplementedError("self._current_recording_file should never be None here")

        # if the final timpeoint need is not present, then there's nothing else to do yet
        if self._current_recording_file[TIME_INDICES][-1] < command["stop_timepoint"]:
            self._recording_time_idx_bounds._replace(stop=command["stop_timepoint"])
            return

        # if the final timepoint needed is already present, then clear the recording bounds as the recording can be completed without another data packet
        self._recording_time_idx_bounds._replace(start=None)
        self._recording_time_idx_bounds._replace(stop=None)

        upper_magnetometer_data_bound = np.argmax(
            self._current_recording_file[TIME_INDICES] > command["stop_timepoint"]
        )

        # trim off magnetometer data after stop recording timepoint
        for mag_data_type in (TIME_INDICES, TIME_OFFSETS, TISSUE_SENSOR_READINGS):
            current_recorded_data = self._current_recording_file[mag_data_type]
            current_recorded_data.resize([*current_recorded_data.shape[:-1], upper_magnetometer_data_bound])

        # trim off stim data after stop recording timepoint
        for protocol_idx in range(self._num_stim_protocols):
            current_recorded_data = self._current_recording_file[
                STIMULATION_READINGS_TEMPLATE.format(protocol_idx)
            ]
            if current_recorded_data[0, -1] <= command["stop_timepoint"]:
                continue
            upper_stim_data_bound = np.argmax(current_recorded_data[0] > command["stop_timepoint"])
            current_recorded_data.resize([*current_recorded_data.shape[:-1], upper_stim_data_bound])

        await self._handle_file_close()

    async def _update_recording_name(self, command: dict[str, str]) -> None:
        if not self._current_recording_path:
            raise NotImplementedError("self._current_recording_path should never be None here")
        if not self._current_recording_name:
            raise NotImplementedError("self._current_recording_name should never be None here")

        new_recording_path = self._current_recording_path.replace(
            self._current_recording_name, command["new_name"]
        )
        os.rename(self._current_recording_path, new_recording_path)
        self._current_recording_name = command["new_name"]

    # DATA HANDLERS

    async def _process_mag_data_packet(self, data_packet: dict[str, Any]) -> None:
        if data_packet["is_first_packet_of_stream"]:
            self._end_of_mag_stream_reached = False
            self._mag_data_buffer.clear()
        if not self._end_of_mag_stream_reached:
            self._mag_data_buffer.append(data_packet)
            await self._update_data_buffers()

        if self._is_recording:
            await self._handle_recording_of_mag_data_packet(data_packet)

    async def _process_stim_data_packet(self, data_packet: dict[str, Any]) -> None:
        if data_packet["is_first_packet_of_stream"]:
            self._end_of_stim_stream_reached = False
            await self._reset_stim_data_buffers()
        if not self._end_of_stim_stream_reached:
            await self._append_to_stim_data_buffers(data_packet["protocol_statuses"])

        if self._is_recording:
            await self._handle_recording_of_stim_statuses(data_packet["protocol_statuses"])

    # HELPERS

    async def _create_recording_file(self, metadata_for_file: dict[uuid.UUID, Any]) -> None:
        if not self._start_data_stream_timestamp_utc:
            raise NotImplementedError("self._start_data_stream_timestamp_utc should never be None here")

        self._current_recording_file = MantarrayH5FileCreator(
            self._current_recording_path, file_format_version=CURRENT_RECORDING_FILE_VERSION
        )

        metadata_for_file[
            UTC_BEGINNING_DATA_ACQUISTION_UUID
        ] = self._start_data_stream_timestamp_utc.strftime(METADATA_DATETIME_STR_FORMAT)

        for this_attr_name, this_attr_value in metadata_for_file.items():
            # apply custom formatting to UTC datetime value
            if (
                METADATA_UUID_DESCRIPTIONS[this_attr_name].startswith("UTC Timestamp")
                and this_attr_value != NOT_APPLICABLE_H5_METADATA
            ):
                this_attr_value = this_attr_value.strftime(METADATA_DATETIME_STR_FORMAT)

            # UUIDs must be stored as strings
            this_attr_name = str(this_attr_name)  # type: ignore
            if isinstance(this_attr_value, uuid.UUID):
                this_attr_value = str(this_attr_value)

            self._current_recording_file.attrs[this_attr_name] = this_attr_value

        # converting to a string since json does not like UUIDs
        self._current_recording_file.attrs["Metadata UUID Descriptions"] = str(METADATA_UUID_DESCRIPTIONS)

        # sampling time values
        self._current_recording_file.create_dataset(
            TIME_INDICES, (0,), maxshape=(MAX_DATA_LEN,), dtype="uint64", chunks=True
        )
        # sampling time offset
        self._current_recording_file.create_dataset(
            TIME_OFFSETS,
            (NUM_MAG_SENSORS_PER_WELL, 0),
            maxshape=(NUM_MAG_SENSORS_PER_WELL, MAX_DATA_LEN),
            dtype="uint16",
            chunks=True,
        )
        # magnetometer data (tissue)
        self._current_recording_file.create_dataset(
            TISSUE_SENSOR_READINGS,
            (NUM_WELLS, NUM_MAG_DATA_CHANNELS_PER_WELL, 0),
            maxshape=(NUM_WELLS, NUM_MAG_DATA_CHANNELS_PER_WELL, MAX_DATA_LEN),
            dtype="uint16",
            chunks=True,
        )
        # stim data
        if self._stim_info:
            await self._create_stim_datasets()

        self._current_recording_file.swmr_mode = True

    async def _create_stim_datasets(self) -> None:
        if not self._current_recording_file:
            raise NotImplementedError("self._current_recording_file should never be None here")

        for protocol_idx in range(self._num_stim_protocols):
            self._current_recording_file.create_dataset(
                STIMULATION_READINGS_TEMPLATE.format(protocol_idx),
                (2, 0),
                maxshape=(2, MAX_DATA_LEN),
                dtype="int64",
                chunks=True,
            )

    async def _add_calibration_data_to_recording(self) -> None:
        if not self._current_recording_file:
            raise NotImplementedError("self._current_recording_file should never be None here")
        if not self._current_calibration_path:
            raise NotImplementedError("self._current_calibration_path should never be None here")

        with h5py.File(self._current_calibration_path, "r") as calibration_file:
            self._current_recording_file.attrs[UTC_BEGINNING_CALIBRATION_UUID] = calibration_file.attrs[
                UTC_BEGINNING_RECORDING_UUID
            ]

            for new_label, original_label in {
                CALIBRATION_TIME_INDICES: TIME_INDICES,
                CALIBRATION_TIME_OFFSETS: TIME_OFFSETS,
                CALIBRATION_TISSUE_SENSOR_READINGS: TISSUE_SENSOR_READINGS,
            }.items():
                self._current_recording_file.create_dataset(
                    new_label, data=calibration_file[original_label], chunks=True
                )

    async def _add_protocols_to_recording_files(self) -> None:
        if not self._current_recording_file:
            raise NotImplementedError("self._current_recording_file should never be None here")
        if not self._stim_info:
            raise NotImplementedError("self._stim_info should never be None here")

        self._current_recording_file.attrs[str(STIMULATION_PROTOCOL_UUID)] = json.dumps(self._stim_info)

    async def _record_data_from_buffers(self) -> None:
        for data_packet in self._mag_data_buffer:
            await self._handle_recording_of_mag_data_packet(data_packet)
        await self._handle_recording_of_stim_statuses(self._stim_data_buffers)

    async def _handle_recording_of_mag_data_packet(self, data_packet: dict[str, Any]) -> None:
        if self._recording_time_idx_bounds.start is None:  # check needed for mypy to be happy
            raise NotImplementedError("_recording_time_idx_bounds.start should never be None here")

        time_indices = data_packet[TIME_INDICES]

        if time_indices[-1] < self._recording_time_idx_bounds.start:
            # if final data point is less than the recording start time, then there's nothing else to do
            return

        upper_time_bound = (
            self._recording_time_idx_bounds.stop
            if self._recording_time_idx_bounds.stop is not None
            else np.inf
        )

        # if the final timepoint needed is present, then clear the recording bounds as the recording will be complete after this packet
        if time_indices[-1] >= upper_time_bound:
            self._recording_time_idx_bounds._replace(start=None)
            self._recording_time_idx_bounds._replace(stop=None)

        data_window = (self._recording_time_idx_bounds.start <= time_indices) & (
            time_indices <= upper_time_bound
        )

        for data_type in (TIME_INDICES, TIME_OFFSETS, TISSUE_SENSOR_READINGS):
            await self._update_dataset(data_packet[data_type][data_window], data_type)

        if self._recording_time_idx_bounds.stop is None:
            await self._handle_file_close()

    async def _handle_recording_of_stim_statuses(
        self, protocol_statuses: dict[int, NDArray[(2, Any), int]]
    ) -> None:
        if self._recording_time_idx_bounds.start is None:  # check needed for mypy to be happy
            raise NotImplementedError("_recording_time_idx_bounds.start should never be None here")

        for protocol_idx, new_stim_statuses in protocol_statuses.items():
            earliest_required_idx = _get_earliest_required_stim_idx(
                new_stim_statuses[0], self._recording_time_idx_bounds.start
            )

            upper_idx_bound = None
            if (
                self._recording_time_idx_bounds.stop is not None
                and new_stim_statuses[0, -1] > self._recording_time_idx_bounds.stop
            ):
                upper_idx_bound = np.argmax(new_stim_statuses[0] > self._recording_time_idx_bounds.stop)

            await self._update_dataset(
                new_stim_statuses[:, earliest_required_idx:upper_idx_bound],
                STIMULATION_READINGS_TEMPLATE.format(protocol_idx),
            )

    async def _handle_file_close(self) -> None:
        if not self._current_recording_file:
            raise NotImplementedError("self._current_recording_file should never be None here")
        if not self._current_recording_path:
            raise NotImplementedError("self._current_recording_path should never be None here")

        self._current_recording_file.close()

        msg_to_main = {"command": "stop_recording"}

        # after h5 close, reopen them and attempt to read. If not possible then add file to list
        try:
            with h5py.File(self._current_recording_path, "r"):
                pass  # if file opens, then there is no corruption
        except Exception:
            # TODO does a different message need to be sent if this is a calibration recording?
            msg_to_main["corrupted_file"] = self._current_recording_path

        # TODO does a different message need to be sent if this is a calibration recording?
        await self._to_monitor_queue.put(msg_to_main)

    async def _update_dataset(self, new_data: NDArray, dataset: str) -> None:
        if not self._current_recording_file:
            raise NotImplementedError("self._current_recording_file should never be None here")

        current_recorded_data = self._current_recording_file[dataset]
        previous_recorded_data_len = current_recorded_data.shape[-1]
        current_recorded_data.resize(
            [*current_recorded_data.shape[:-1], previous_recorded_data_len + new_data.shape[-1]]
        )
        current_recorded_data[..., previous_recorded_data_len:] = new_data

    async def _update_data_buffers(self) -> None:
        """Remove old data packets if necessary"""
        curr_buffer_memory_size = (
            self._mag_data_buffer[-1]["time_indices"][0] - self._mag_data_buffer[0]["time_indices"][0]
        )
        if curr_buffer_memory_size <= FILE_WRITER_BUFFER_SIZE_MILLISECONDS:
            return

        # buffer has grown too large, so need to remove the earliest magnetomer data packet
        self._mag_data_buffer.popleft()

        # since a magnetometer data packet was removed, also check to see if the earliest stim data packet
        # is now unnecessary
        earliest_buffered_mag_time_idx = self._mag_data_buffer[0]["time_indices"][0]

        for protocol_idx in range(self._num_stim_protocols):
            buffered_stim_statuses = self._stim_data_buffers[protocol_idx]
            earliest_required_stim_idx = _get_earliest_required_stim_idx(
                buffered_stim_statuses[0], earliest_buffered_mag_time_idx
            )
            self._stim_data_buffers[protocol_idx] = buffered_stim_statuses[:, earliest_required_stim_idx:]

    async def _reset_stim_data_buffers(self) -> None:
        self._stim_data_buffers = {
            protocol_idx: np.empty((2, 0)) for protocol_idx in range(self._num_stim_protocols)
        }

    async def _append_to_stim_data_buffers(
        self, protocol_statuses: dict[int, NDArray[(2, Any), int]]
    ) -> None:
        for protocol_idx in range(self._num_stim_protocols):
            if (status_arr := protocol_statuses.get(protocol_idx)) is not None:
                self._stim_data_buffers[protocol_idx] = np.concatenate(
                    self._stim_data_buffers[protocol_idx], status_arr
                )
