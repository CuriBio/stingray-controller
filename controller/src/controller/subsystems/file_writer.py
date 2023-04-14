# -*- coding: utf-8 -*-
import asyncio
import datetime
import json
import logging
import os
import tempfile
from typing import Any
import uuid

import h5py
from pulse3D.constants import DATETIME_STR_FORMAT as METADATA_DATETIME_STR_FORMAT
from pulse3D.constants import IS_CALIBRATION_FILE_UUID
from pulse3D.constants import METADATA_UUID_DESCRIPTIONS
from pulse3D.constants import NOT_APPLICABLE_H5_METADATA
from pulse3D.constants import PLATE_BARCODE_UUID
from pulse3D.constants import STIMULATION_PROTOCOL_UUID
from pulse3D.constants import STIMULATION_READINGS
from pulse3D.constants import TIME_INDICES
from pulse3D.constants import TIME_OFFSETS
from pulse3D.constants import TISSUE_SENSOR_READINGS
from pulse3D.constants import UTC_BEGINNING_DATA_ACQUISTION_UUID
from pulse3D.constants import UTC_BEGINNING_RECORDING_UUID
from pulse3D.plate_recording import MantarrayH5FileCreator

from ..constants import CURRENT_RECORDING_FILE_VERSION
from ..constants import NUM_MAG_DATA_CHANNELS_PER_WELL
from ..constants import NUM_MAG_SENSORS_PER_WELL
from ..utils.aio import wait_tasks_clean
from ..utils.generic import handle_system_error


# TODO move these to pulse3D
UTC_BEGINNING_CALIBRATION_UUID = uuid.UUID("b0995a2e-8f1d-41d7-b369-54ec06656683")
CALIBRATION_TIME_INDICES = "calibration_time_indices"
CALIBRATION_TIME_OFFSETS = "calibration_time_offsets"
CALIBRATION_TISSUE_SENSOR_READINGS = "calibration_tissue_sensor_readings"


logger = logging.getLogger(__name__)

ERROR_MSG = "IN FILE WRITER"


class FileWriter:
    """Subsystem that manages writing data to file."""

    def __init__(
        self,
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
        data_queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        # comm queues
        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue
        # data queue
        self._data_queue = data_queue

        self._calibration_tmp_dir: tempfile.TemporaryDirectory | None = None

        self._recordings_directory: str | None = None
        self._current_recording_name: str | None = None
        self._current_recording_path: str | None = None
        self._current_calibration_path: str | None = None

        self._current_recording_file: MantarrayH5FileCreator | None = None

        self._start_data_stream_timestamp_utc: datetime.datetime | None = None
        self._stim_info: dict[str, Any] | None = None

    # ONE-SHOT TASKS

    async def run(self, system_error_future: asyncio.Future[int]) -> None:
        logger.info("Starting FileWriter")

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
            self._calibration_tmp_dir.cleanup()
            logger.info("FileWriter shut down")

    # INFINITE TASKS

    async def _handle_comm_from_monitor(self) -> None:
        while True:
            comm_from_monitor = await self._from_monitor_queue.get()

            match comm_from_monitor:
                case {"command": "start_recording"}:
                    await self._start_recording(comm_from_monitor)
                case {"command": "stop_recording"}:
                    pass  # TODO: self._stop_recording()
                case {"command": "update_recording_name"}:
                    pass  # TODO: self._update_recording_name()

    async def _handle_incoming_data(self) -> None:
        while True:
            data_packet = await self._data_queue.get()
            # TODO

    # COMMAND HANDLERS

    async def _start_recording(self, start_recording_command: dict[str, Any]) -> None:
        self._is_recording = True

        metadata = start_recording_command["metadata"]
        recording_start_timestamp_str = metadata[UTC_BEGINNING_RECORDING_UUID].strftime("%Y_%m_%d__%H_%M_%S")

        self._is_recording_calibration = metadata[IS_CALIBRATION_FILE_UUID]

        if self._is_recording_calibration:
            self._current_recording_name = f"Calibration__{recording_start_timestamp_str}"
            self._current_recording_path = os.path.join(
                self._calibration_tmp_dir.name, self._current_recording_name
            )
            # remove old calibration file if one exists
            if self._current_calibration_path and os.path.isfile(self._current_calibration_path):
                os.remove(self._current_calibration_path)
            # set new calibration file path
            self._current_calibration_path = self._current_recording_path
        else:
            self._current_recording_name = f"{metadata[PLATE_BARCODE_UUID]}__{recording_start_timestamp_str}"
            self._current_recording_path = os.path.join(
                self._recordings_directory, self._current_recording_name
            )

        await self._create_recording_file(metadata)

        if not self._is_recording_calibration:
            await self._add_calibration_data_to_recording()
            await self._add_protocols_to_recording_files()
            await self._record_data_from_buffers()

    # HELPERS

    async def _create_recording_file(self, metadata_for_file: dict[uuid.UUID, Any]) -> None:
        self._current_recording_file = MantarrayH5FileCreator(
            self._current_recording_path, file_format_version=CURRENT_RECORDING_FILE_VERSION
        )

        # TODO set this value when start_data_stream command is received
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
        # stim data
        self._current_recording_file.create_dataset(
            STIMULATION_READINGS, (2, 0), maxshape=(2, max_data_len), dtype="int64", chunks=True
        )
        # magnetometer data (tissue)
        self._current_recording_file.create_dataset(
            TISSUE_SENSOR_READINGS,
            (NUM_MAG_DATA_CHANNELS_PER_WELL, 0),
            maxshape=(NUM_MAG_DATA_CHANNELS_PER_WELL, max_data_len),
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
        pass  # TODO
        # for data_packet in self._mag_data_buffers:
        #     self._handle_recording_of_mag_data_packet(data_packet)
        # for well_idx, well_buffers in self._stim_data_buffers.items():
        #     if well_buffers[0]:
        #         self._handle_recording_of_stim_statuses(well_idx, np.array(well_buffers))
