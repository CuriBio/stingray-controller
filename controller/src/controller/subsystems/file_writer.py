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
import numpy as np
from pulse3D.constants import DATETIME_STR_FORMAT as METADATA_DATETIME_STR_FORMAT
from pulse3D.constants import IS_CALIBRATION_FILE_UUID
from pulse3D.constants import METADATA_UUID_DESCRIPTIONS
from pulse3D.constants import NOT_APPLICABLE_H5_METADATA
from pulse3D.constants import PLATE_BARCODE_UUID
from pulse3D.constants import START_RECORDING_TIME_INDEX_UUID
from pulse3D.constants import STIMULATION_PROTOCOL_UUID
from pulse3D.constants import TIME_INDICES
from pulse3D.constants import TIME_OFFSETS
from pulse3D.constants import TISSUE_SENSOR_READINGS
from pulse3D.constants import UTC_BEGINNING_DATA_ACQUISTION_UUID
from pulse3D.constants import UTC_BEGINNING_RECORDING_UUID
from pulse3D.plate_recording import MantarrayH5FileCreator

from ..constants import CURRENT_RECORDING_FILE_VERSION
from ..constants import NUM_MAG_DATA_CHANNELS_PER_WELL
from ..constants import NUM_MAG_SENSORS_PER_WELL
from ..constants import NUM_WELLS
from ..utils.aio import wait_tasks_clean
from ..utils.generic import handle_system_error


# TODO move these to pulse3D
UTC_BEGINNING_CALIBRATION_UUID = uuid.UUID("b0995a2e-8f1d-41d7-b369-54ec06656683")
CALIBRATION_TIME_INDICES = "calibration_time_indices"
CALIBRATION_TIME_OFFSETS = "calibration_time_offsets"
CALIBRATION_TISSUE_SENSOR_READINGS = "calibration_tissue_sensor_readings"


logger = logging.getLogger(__name__)

ERROR_MSG = "IN FILE WRITER"


RecordingBounds = namedtuple("RecordingBounds", ["start", "stop"])


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
        self._calibration_tmp_dir: tempfile.TemporaryDirectory | None = None

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
        self._stim_data_buffers: dict[int, tuple[deque[int], deque[int]]] = dict()

    # PROPERTIES

    @property
    def _is_recording(self) -> bool:
        return self._recording_time_idx_bounds.start is not None

    @property
    def _current_recording_path(self) -> str | None:
        recording_dir = (
            self._calibration_tmp_dir.name if self._is_calibration_recording else self._recordings_directory
        )
        return os.path.join(recording_dir, self._current_recording_name)

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
                    self._stim_data_buffers = {
                        protocol_idx: deque() for protocol_idx in range(len(stim_info["protocols"]))
                    }

            # TODO send responses for all these commands except stop_recording

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
        # TODO handle setting this UTC_FIRST_TISSUE_DATA_POINT_UUID in create_start_recording_command
        metadata = command["metadata"]

        self._recording_time_idx_bounds.start = metadata[START_RECORDING_TIME_INDEX_UUID]
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
        # if the final timpeoint need is not present, then there's nothing else to do yet
        if self._current_recording_file[TIME_INDICES][-1] < command["stop_timepoint"]:
            self._recording_time_idx_bounds.stop = command["stop_timepoint"]
            return

        # TODO ? no further action needed if this is stopping a calibration recording
        # if self._is_calibration_recording:
        #     return

        # if the final timepoint needed is already present, then clear the recording bounds as the recording can be completed without another data packet
        self._recording_time_idx_bounds.start = None
        self._recording_time_idx_bounds.stop = None

        final_magnetometer_data_idx = np.argmax(
            self._current_recording_file[TIME_INDICES] > command["stop_timepoint"]
        )

        # trim off magnetometer data after stop recording timepoint
        for data_type in (TIME_INDICES, TIME_OFFSETS, TISSUE_SENSOR_READINGS):
            current_recorded_data = self._current_recording_file[data_type]
            current_recorded_data.resize([*current_recorded_data.shape[:-1], final_magnetometer_data_idx])

        # TODO
        # # find num points needed to remove from stimulation datasets
        # stimulation_dataset = get_stimulation_dataset_from_file(this_file)
        # try:
        #     num_indices_to_remove = next(
        #         i
        #         for i, time in enumerate(reversed(stimulation_dataset[0]))
        #         if time <= stop_recording_timepoint
        #     )
        # except StopIteration:
        #     num_indices_to_remove = 0
        # # trim off data after stop recording timepoint
        # dataset_shape = list(stimulation_dataset.shape)
        # dataset_shape[-1] -= num_indices_to_remove
        # stimulation_dataset.resize(dataset_shape)

        await self._handle_file_close()

    async def _update_recording_name(self, command: dict[str, str]) -> None:
        new_recording_path = self._current_recording_path.replace(
            self._current_recording_name, command["new_name"]
        )
        os.rename(self._current_recording_path, new_recording_path)
        self._current_recording_name = command["new_name"]

    # DATA HANDLERS

    async def _process_mag_data_packet(self, data_packet) -> None:
        if data_packet["is_first_packet_of_stream"]:
            self._end_of_mag_stream_reached = False
            self._mag_data_buffer.clear()
        if not self._end_of_mag_stream_reached:
            self._mag_data_buffer.append(data_packet)

        if self._is_recording:
            self._handle_recording_of_mag_data_packet(data_packet)

    async def _process_stim_data_packet(self, data_packet) -> None:
        # TODO
        if data_packet["is_first_packet_of_stream"]:
            self._end_of_stim_stream_reached = False
            self._clear_stim_data_buffers()  # TODO
            # TODO try to handle stim chunking entirely in InstrumentComm
            # self._reset_stim_idx_counters()  # TODO
        if not self._end_of_stim_stream_reached:
            self.append_to_stim_data_buffers(data_packet["protocol_statuses"])  # TODO
            # output_queue = self._board_queues[board_idx][1]
            # if reduced_well_statuses := self._reduce_subprotocol_chunks(stim_packet["well_statuses"]):
            #     output_queue.put_nowait({**stim_packet, "well_statuses": reduced_well_statuses})

        if self._is_recording:
            self._handle_recording_of_stim_statuses(data_packet["well_statuses"])

    # HELPERS

    async def _create_recording_file(self, metadata_for_file: dict[uuid.UUID, Any]) -> None:
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
            this_attr_name = str(this_attr_name)
            if isinstance(this_attr_value, uuid.UUID):
                this_attr_value = str(this_attr_value)

            self._current_recording_file.attrs[this_attr_name] = this_attr_value

        # converting to a string since json does not like UUIDs
        self._current_recording_file.attrs["Metadata UUID Descriptions"] = str(METADATA_UUID_DESCRIPTIONS)

        # Tanner (5/17/21): Not sure what this value represents, should make it a constant or add comment if/when it is determined
        max_data_len = 100 * 3600 * 12

        # sampling time values
        self._current_recording_file.create_dataset(
            TIME_INDICES, (0,), maxshape=(max_data_len,), dtype="uint64", chunks=True
        )
        # sampling time offset
        self._current_recording_file.create_dataset(
            TIME_OFFSETS,
            (NUM_MAG_SENSORS_PER_WELL, 0),
            maxshape=(NUM_MAG_SENSORS_PER_WELL, max_data_len),
            dtype="uint16",
            chunks=True,
        )
        # stim data  # TODO only do this if necessary. Also, only need to store statuses per protocol instead of per well
        # self._current_recording_file.create_dataset(
        #     STIMULATION_READINGS, (2, 0), maxshape=(2, max_data_len), dtype="int64", chunks=True
        # )
        # magnetometer data (tissue)
        self._current_recording_file.create_dataset(
            TISSUE_SENSOR_READINGS,
            (NUM_WELLS, NUM_MAG_DATA_CHANNELS_PER_WELL, 0),
            maxshape=(NUM_WELLS, NUM_MAG_DATA_CHANNELS_PER_WELL, max_data_len),
            dtype="uint16",
            chunks=True,
        )
        self._current_recording_file.swmr_mode = True

    async def _add_calibration_data_to_recording(self) -> None:
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
        self._current_recording_file.attrs[str(STIMULATION_PROTOCOL_UUID)] = json.dumps(self._stim_info)

    async def _record_data_from_buffers(self) -> None:
        for data_packet in self._mag_data_buffer:
            self._handle_recording_of_mag_data_packet(data_packet)
        for protocol_idx, protocol_buffers in self._stim_data_buffers.items():
            if protocol_buffers[0]:
                self._handle_recording_of_stim_statuses(protocol_idx, protocol_buffers)

    async def _handle_recording_of_mag_data_packet(self, data_packet) -> None:
        if self._recording_time_idx_bounds.start is None:  # check needed for mypy to be happy
            raise NotImplementedError("_recording_time_idx_bounds.start should never be None here")

        # TODO swap in H5 dataset labels here in other subsystems too
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
            self._recording_time_idx_bounds.start = None
            self._recording_time_idx_bounds.stop = None

        data_window = (self._recording_time_idx_bounds.start <= time_indices) & (
            time_indices <= upper_time_bound
        )

        # TODO make sure this loop works before deleting the commented out code below
        for data_type in (TIME_INDICES, TIME_OFFSETS, TISSUE_SENSOR_READINGS):
            current_recorded_data = self._current_recording_file[data_type]
            previous_recorded_data_len = current_recorded_data.shape[-1]
            new_data_to_record = data_packet[data_type][data_window]
            current_recorded_data.resize(
                [
                    *current_recorded_data.shape[:-1],
                    previous_recorded_data_len + new_data_to_record.shape[-1],
                ]
            )
            current_recorded_data[..., previous_recorded_data_len:] = new_data_to_record

        if self._recording_time_idx_bounds.stop is None:
            await self._handle_file_close()

        # # record new time indices
        # current_recorded_time_indices = self._current_recording_file[TIME_INDICES]
        # previous_time_idx_data_len = current_recorded_time_indices.shape[0]
        # new_time_indices_to_record = time_indices[data_window]
        # current_recorded_time_indices.resize(
        #     (previous_time_idx_data_len + new_time_indices_to_record.shape[0],)
        # )
        # current_recorded_time_indices[previous_time_idx_data_len:] = new_time_indices_to_record
        # # record new time offsets
        # current_recorded_time_offsets = self._current_recording_file[TIME_OFFSETS]
        # previous_time_offset_data_len = current_recorded_time_offsets.shape[1]
        # new_time_offsets_to_record = data_packet["time_offsets"][data_window]
        # current_recorded_time_offsets.resize(
        #     (
        #         current_recorded_time_offsets.shape[0],
        #         previous_time_offset_data_len + new_time_offsets_to_record.shape[1],
        #     )
        # )
        # current_recorded_time_offsets[:, previous_time_offset_data_len:] = new_time_offsets_to_record
        # # record new tissue data
        # current_recorded_tissue_data = self._current_recording_file[TISSUE_SENSOR_READINGS]
        # previous_tissue_data_data_len = current_recorded_tissue_data.shape[2]
        # new_tissue_data_to_record = data_packet["???"][data_window]
        # current_recorded_tissue_data.resize(
        #     (
        #         current_recorded_tissue_data.shape[0],
        #         current_recorded_tissue_data.shape[1],
        #         previous_tissue_data_data_len + new_tissue_data_to_record.shape[2],
        #     )
        # )
        # current_recorded_tissue_data[:, :, previous_tissue_data_data_len:] = new_tissue_data_to_record

    async def _handle_recording_of_stim_statuses(self, well_statuses) -> None:
        # TODO all of this needs to be refactored
        board_idx = 0
        if well_idx not in self._open_files[board_idx]:
            return

        well_name = GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx)
        assigned_protocol_id = self._stim_info["protocol_assignments"][well_name]

        stim_data_arr[1] = np.array(
            [
                self._convert_subprotocol_idx(assigned_protocol_id, chunked_subprotocol_idx)
                for chunked_subprotocol_idx in stim_data_arr[1]
            ]
        )

        this_start_recording_timestamps = self._start_recording_timestamps[board_idx]
        if this_start_recording_timestamps is None:  # check needed for mypy to be happy
            raise NotImplementedError("Something wrong in the code. This should never be none.")

        stop_recording_timestamp = self.get_stop_recording_timestamps()[board_idx]
        if stop_recording_timestamp is not None and stim_data_arr[0, 0] >= stop_recording_timestamp:
            return

        # remove unneeded status updates
        earliest_magnetometer_time_idx = this_start_recording_timestamps[1]
        earliest_valid_index = _find_earliest_valid_stim_status_index(
            stim_data_arr[0].tolist(), earliest_magnetometer_time_idx
        )
        stim_data_arr = stim_data_arr[:, earliest_valid_index:]
        # update dataset in h5 file
        this_well_file = self._open_files[board_idx][well_idx]
        stimulation_dataset = get_stimulation_dataset_from_file(this_well_file)
        previous_data_size = stimulation_dataset.shape[1]
        stimulation_dataset.resize((2, previous_data_size + stim_data_arr.shape[1]))
        stimulation_dataset[:, previous_data_size:] = stim_data_arr

    async def _handle_file_close(self):
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
