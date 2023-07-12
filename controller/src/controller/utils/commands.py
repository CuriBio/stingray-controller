# -*- coding: utf-8 -*-
import datetime
import json
from typing import Any

from pulse3D.constants import BACKEND_LOG_UUID
from pulse3D.constants import BOOT_FLAGS_UUID
from pulse3D.constants import CHANNEL_FIRMWARE_VERSION_UUID
from pulse3D.constants import COMPUTER_NAME_HASH_UUID
from pulse3D.constants import CUSTOMER_ACCOUNT_ID_UUID
from pulse3D.constants import INITIAL_MAGNET_FINDING_PARAMS_UUID
from pulse3D.constants import IS_CALIBRATION_FILE_UUID
from pulse3D.constants import MAIN_FIRMWARE_VERSION_UUID
from pulse3D.constants import MANTARRAY_SERIAL_NUMBER_UUID
from pulse3D.constants import NOT_APPLICABLE_H5_METADATA
from pulse3D.constants import PLATE_BARCODE_IS_FROM_SCANNER_UUID
from pulse3D.constants import PLATE_BARCODE_UUID
from pulse3D.constants import PLATEMAP_LABEL_UUID
from pulse3D.constants import PLATEMAP_NAME_UUID
from pulse3D.constants import SOFTWARE_BUILD_NUMBER_UUID
from pulse3D.constants import SOFTWARE_RELEASE_VERSION_UUID
from pulse3D.constants import START_RECORDING_TIME_INDEX_UUID
from pulse3D.constants import STIM_BARCODE_IS_FROM_SCANNER_UUID
from pulse3D.constants import STIM_BARCODE_UUID
from pulse3D.constants import TISSUE_SAMPLING_PERIOD_UUID
from pulse3D.constants import TOTAL_WELL_COUNT_UUID
from pulse3D.constants import USER_ACCOUNT_ID_UUID
from pulse3D.constants import UTC_BEGINNING_RECORDING_UUID

from .generic import get_hash_of_computer_name
from .state_management import ReadOnlyDict
from ..constants import COMPILED_EXE_BUILD_TIMESTAMP
from ..constants import CURRENT_SOFTWARE_VERSION
from ..constants import DEFAULT_MAG_SAMPLING_PERIOD
from ..constants import NUM_WELLS


def create_start_recording_command(
    system_state: ReadOnlyDict,
    *,
    start_recording_time_index: int,
    barcodes: dict[str, str] | None = None,
    platemap_info: dict[str, Any] | None = None,
    is_calibration_recording: bool = False,
) -> dict[str, Any]:
    start_recording_timestamp_utc = datetime.datetime.utcnow()

    # barcodes
    if not barcodes:
        barcodes = {"plate_barcode": NOT_APPLICABLE_H5_METADATA, "stim_barcode": NOT_APPLICABLE_H5_METADATA}

    barcode_metadata = {}
    for barcode_type, barcode_uuid, barcode_match_uuid in (
        ("plate_barcode", PLATE_BARCODE_UUID, PLATE_BARCODE_IS_FROM_SCANNER_UUID),
        ("stim_barcode", STIM_BARCODE_UUID, STIM_BARCODE_IS_FROM_SCANNER_UUID),
    ):
        barcode = barcodes[barcode_type]
        barcode_metadata[barcode_uuid] = barcode
        barcode_metadata[barcode_match_uuid] = barcode == system_state[barcode_type]

    # platemap
    formatted_platemap_info = {
        "name": str(NOT_APPLICABLE_H5_METADATA),
        "labels": [str(NOT_APPLICABLE_H5_METADATA)] * 24,
    }
    if platemap_info:
        formatted_platemap_info["name"] = platemap_info["map_name"]
        for label_info in platemap_info["labels"]:
            for well_idx in label_info["wells"]:
                formatted_platemap_info["labels"][well_idx] = label_info["name"]  # type: ignore

    config_settings = system_state["config_settings"]
    instrument_metadata = system_state["instrument_metadata"]

    command: dict[str, Any] = {
        "communication_type": "recording",
        "command": "start_recording",
        "metadata": {
            # recording
            IS_CALIBRATION_FILE_UUID: is_calibration_recording,
            UTC_BEGINNING_RECORDING_UUID: start_recording_timestamp_utc,
        },
    }

    if not is_calibration_recording:
        command["metadata"] |= {
            # machine
            COMPUTER_NAME_HASH_UUID: get_hash_of_computer_name(),
            # software
            SOFTWARE_BUILD_NUMBER_UUID: COMPILED_EXE_BUILD_TIMESTAMP,
            SOFTWARE_RELEASE_VERSION_UUID: CURRENT_SOFTWARE_VERSION,
            # user
            CUSTOMER_ACCOUNT_ID_UUID: config_settings.get("customer_id", NOT_APPLICABLE_H5_METADATA),
            USER_ACCOUNT_ID_UUID: config_settings.get("username", NOT_APPLICABLE_H5_METADATA),
            # session
            BACKEND_LOG_UUID: system_state["log_file_id"],
            # recording
            START_RECORDING_TIME_INDEX_UUID: start_recording_time_index,
            # barcodes
            **barcode_metadata,
            # experiment/analysis
            PLATEMAP_NAME_UUID: formatted_platemap_info["name"],
            PLATEMAP_LABEL_UUID: formatted_platemap_info["labels"],
            TOTAL_WELL_COUNT_UUID: NUM_WELLS,
            # instrument
            MANTARRAY_SERIAL_NUMBER_UUID: instrument_metadata[MANTARRAY_SERIAL_NUMBER_UUID],
            MAIN_FIRMWARE_VERSION_UUID: instrument_metadata[MAIN_FIRMWARE_VERSION_UUID],
            CHANNEL_FIRMWARE_VERSION_UUID: instrument_metadata[CHANNEL_FIRMWARE_VERSION_UUID],
            TISSUE_SAMPLING_PERIOD_UUID: DEFAULT_MAG_SAMPLING_PERIOD,
            INITIAL_MAGNET_FINDING_PARAMS_UUID: json.dumps(
                dict(instrument_metadata[INITIAL_MAGNET_FINDING_PARAMS_UUID])
            ),
            BOOT_FLAGS_UUID: instrument_metadata[BOOT_FLAGS_UUID],
        }

    return command
