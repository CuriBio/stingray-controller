# -*- coding: utf-8 -*-
"""Utility functions for Serial Communication."""


import datetime
import math
import struct
from typing import Any
from typing import Union
from uuid import UUID
from zlib import crc32

from controller.exceptions import InstrumentInvalidMetadataError
from immutabledict import immutabledict
import numpy as np
from pulse3D.constants import BOOT_FLAGS_UUID
from pulse3D.constants import BOOTUP_COUNTER_UUID
from pulse3D.constants import CHANNEL_FIRMWARE_VERSION_UUID
from pulse3D.constants import INITIAL_MAGNET_FINDING_PARAMS_UUID
from pulse3D.constants import MAIN_FIRMWARE_VERSION_UUID
from pulse3D.constants import MANTARRAY_NICKNAME_UUID
from pulse3D.constants import MANTARRAY_SERIAL_NUMBER_UUID
from pulse3D.constants import PCB_SERIAL_NUMBER_UUID
from pulse3D.constants import TAMPER_FLAG_UUID
from pulse3D.constants import TOTAL_WORKING_HOURS_UUID

from ..constants import GENERIC_24_WELL_DEFINITION
from ..constants import MICROS_PER_MILLI
from ..constants import NUM_WELLS
from ..constants import PROTOCOL_STATUS_BYTES_LEN
from ..constants import SERIAL_COMM_CHECKSUM_LENGTH_BYTES
from ..constants import SERIAL_COMM_MAGIC_WORD_BYTES
from ..constants import SERIAL_COMM_MODULE_ID_TO_WELL_IDX
from ..constants import SERIAL_COMM_OKAY_CODE
from ..constants import SERIAL_COMM_PACKET_REMAINDER_SIZE_LENGTH_BYTES
from ..constants import SERIAL_COMM_STATUS_CODE_LENGTH_BYTES
from ..constants import SERIAL_COMM_TIMESTAMP_EPOCH
from ..constants import SERIAL_COMM_TIMESTAMP_LENGTH_BYTES
from ..constants import SERIAL_COMM_WELL_IDX_TO_MODULE_ID
from ..constants import STIM_MODULE_ID_TO_WELL_IDX
from ..constants import STIM_OPEN_CIRCUIT_THRESHOLD_OHMS
from ..constants import STIM_PULSE_BYTES_LEN
from ..constants import STIM_SHORT_CIRCUIT_THRESHOLD_OHMS
from ..constants import STIM_WELL_IDX_TO_MODULE_ID
from ..constants import StimProtocolStatuses
from ..constants import StimulationStates
from ..constants import StimulatorCircuitStatuses

# Tanner (3/18/21): If/When additional cython is needed to improve serial communication, this file may be worth investigating


METADATA_TYPES: immutabledict[UUID, str] = immutabledict(
    {
        MAIN_FIRMWARE_VERSION_UUID: str,
        CHANNEL_FIRMWARE_VERSION_UUID: str,
        MANTARRAY_NICKNAME_UUID: str,
        MANTARRAY_SERIAL_NUMBER_UUID: str,
        TOTAL_WORKING_HOURS_UUID: int,
        TAMPER_FLAG_UUID: int,
        BOOTUP_COUNTER_UUID: int,
        PCB_SERIAL_NUMBER_UUID: str,
        BOOT_FLAGS_UUID: int,
    }
)

METADATA_TAGS_FOR_LOGGING = immutabledict(
    {
        BOOT_FLAGS_UUID: "Boot flags",
        MANTARRAY_NICKNAME_UUID: "Instrument nickname",
        MANTARRAY_SERIAL_NUMBER_UUID: "Serial Number",
        MAIN_FIRMWARE_VERSION_UUID: "Main micro firmware version",
        CHANNEL_FIRMWARE_VERSION_UUID: "Channel micro firmware version",
        INITIAL_MAGNET_FINDING_PARAMS_UUID: "Initial magnet position estimate",
    }
)

SUBPROTOCOL_BIPHASIC_ONLY_COMPONENTS = frozenset(
    ["interphase_interval", "phase_two_duration", "phase_two_charge"]
)


def convert_module_id_to_well_name(module_id: int, use_stim_mapping: bool = False) -> str:
    mapping = STIM_MODULE_ID_TO_WELL_IDX if use_stim_mapping else SERIAL_COMM_MODULE_ID_TO_WELL_IDX
    well_name: str = GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(mapping[module_id])
    return well_name


def convert_well_name_to_module_id(well_name: str, use_stim_mapping: bool = False) -> int:
    mapping = STIM_WELL_IDX_TO_MODULE_ID if use_stim_mapping else SERIAL_COMM_WELL_IDX_TO_MODULE_ID
    module_id: int = mapping[GENERIC_24_WELL_DEFINITION.get_well_index_from_well_name(well_name)]
    return module_id


def _get_checksum_bytes(packet: bytes) -> bytes:
    return crc32(packet).to_bytes(SERIAL_COMM_CHECKSUM_LENGTH_BYTES, byteorder="little")


def create_data_packet(timestamp: int, packet_type: int, packet_payload: bytes = bytes(0)) -> bytes:
    """Create a data packet to send to the PC."""
    packet_base = convert_to_timestamp_bytes(timestamp) + bytes([packet_type])
    packet_remainder_size = len(packet_base) + len(packet_payload) + SERIAL_COMM_CHECKSUM_LENGTH_BYTES

    data_packet = SERIAL_COMM_MAGIC_WORD_BYTES
    data_packet += packet_remainder_size.to_bytes(
        SERIAL_COMM_PACKET_REMAINDER_SIZE_LENGTH_BYTES, byteorder="little"
    )
    data_packet += packet_base
    data_packet += packet_payload
    data_packet += _get_checksum_bytes(data_packet)
    return data_packet


def validate_checksum(comm_from_pc: bytes) -> bool:
    expected_checksum = crc32(comm_from_pc[:-SERIAL_COMM_CHECKSUM_LENGTH_BYTES])
    actual_checksum = int.from_bytes(comm_from_pc[-SERIAL_COMM_CHECKSUM_LENGTH_BYTES:], byteorder="little")
    return actual_checksum == expected_checksum


def parse_instrument_event_info(event_info: bytes) -> dict[str, Any]:
    return {
        "prev_main_status_update_timestamp": int.from_bytes(event_info[:8], byteorder="little"),
        "prev_channel_status_update_timestamp": int.from_bytes(event_info[8:16], byteorder="little"),
        "start_of_prev_mag_data_stream_timestamp": int.from_bytes(event_info[16:24], byteorder="little"),
        "start_of_prev_stim_timestamp": int.from_bytes(event_info[24:32], byteorder="little"),
        "prev_handshake_received_timestamp": int.from_bytes(event_info[32:40], byteorder="little"),
        "prev_system_going_dormant_timestamp": int.from_bytes(event_info[40:48], byteorder="little"),
        "mag_data_stream_active": bool(event_info[48]),
        "stim_active": bool(event_info[49]),
        "pc_connection_status": event_info[50],
        "prev_barcode_scanned": _parse_prev_barcode_scanned(event_info[51:63]),
    }


def _parse_prev_barcode_scanned(barcode_bytes: bytes) -> str:
    try:
        return barcode_bytes.decode("ascii")
    except UnicodeDecodeError:
        return "N/A"


def convert_instrument_event_info_to_bytes(event_info: dict[str, Any]) -> bytes:
    return (  # type: ignore
        event_info["prev_main_status_update_timestamp"].to_bytes(8, byteorder="little")
        + event_info["prev_channel_status_update_timestamp"].to_bytes(8, byteorder="little")
        + event_info["start_of_prev_mag_data_stream_timestamp"].to_bytes(8, byteorder="little")
        + event_info["start_of_prev_stim_timestamp"].to_bytes(8, byteorder="little")
        + event_info["prev_handshake_received_timestamp"].to_bytes(8, byteorder="little")
        + event_info["prev_system_going_dormant_timestamp"].to_bytes(8, byteorder="little")
        + bytes(
            [event_info[key] for key in ("mag_data_stream_active", "stim_active", "pc_connection_status")]
        )
        + bytes(event_info["prev_barcode_scanned"], encoding="ascii")
    )


def parse_metadata_bytes(metadata_bytes: bytes) -> dict[Any, Any]:
    """Parse bytes containing metadata and return as Dict."""
    return {
        BOOT_FLAGS_UUID: metadata_bytes[0],
        MANTARRAY_NICKNAME_UUID: metadata_bytes[1:14].decode("utf-8"),
        MANTARRAY_SERIAL_NUMBER_UUID: metadata_bytes[14:26].decode("ascii"),
        MAIN_FIRMWARE_VERSION_UUID: convert_semver_bytes_to_str(metadata_bytes[26:29]),
        CHANNEL_FIRMWARE_VERSION_UUID: convert_semver_bytes_to_str(metadata_bytes[29:32]),
        "status_codes_prior_to_reboot": convert_status_code_bytes_to_dict(metadata_bytes[32:58]),
        INITIAL_MAGNET_FINDING_PARAMS_UUID: {
            "X": int.from_bytes(metadata_bytes[58:59], byteorder="little", signed=True),
            "Y": int.from_bytes(metadata_bytes[59:60], byteorder="little", signed=True),
            "Z": int.from_bytes(metadata_bytes[60:61], byteorder="little", signed=True),
            "REMN": int.from_bytes(metadata_bytes[61:63], byteorder="little", signed=True),
        },
        "is_stingray": bool(metadata_bytes[63]),
        **parse_instrument_event_info(metadata_bytes[64:]),
    }


def convert_metadata_to_bytes(metadata_dict: dict[UUID | str, Any]) -> bytes:
    metadata_bytes = (
        bytes([metadata_dict[BOOT_FLAGS_UUID]])
        + bytes(metadata_dict[MANTARRAY_NICKNAME_UUID], encoding="utf-8")
        + bytes(metadata_dict[MANTARRAY_SERIAL_NUMBER_UUID], encoding="ascii")
        + convert_semver_str_to_bytes(metadata_dict[MAIN_FIRMWARE_VERSION_UUID])
        + convert_semver_str_to_bytes(metadata_dict[CHANNEL_FIRMWARE_VERSION_UUID])
        # this function is only used in the simulator, so always send default status code
        + bytes([SERIAL_COMM_OKAY_CODE] * (NUM_WELLS + 2))
        + metadata_dict[INITIAL_MAGNET_FINDING_PARAMS_UUID]["X"].to_bytes(1, byteorder="little", signed=True)
        + metadata_dict[INITIAL_MAGNET_FINDING_PARAMS_UUID]["Y"].to_bytes(1, byteorder="little", signed=True)
        + metadata_dict[INITIAL_MAGNET_FINDING_PARAMS_UUID]["Z"].to_bytes(1, byteorder="little", signed=True)
        + metadata_dict[INITIAL_MAGNET_FINDING_PARAMS_UUID]["REMN"].to_bytes(
            2, byteorder="little", signed=True
        )
        + bytes([metadata_dict["is_stingray"]])
        + convert_instrument_event_info_to_bytes(metadata_dict)  # type: ignore
    )
    # append empty bytes so the result length is always a multiple of 32
    metadata_bytes += bytes(math.ceil(len(metadata_bytes) / 32) * 32 - len(metadata_bytes))
    return metadata_bytes  # type: ignore


def validate_instrument_metadata(metadata_dict: dict[UUID | str, Any]) -> None:
    for key in (MANTARRAY_SERIAL_NUMBER_UUID, MANTARRAY_NICKNAME_UUID):
        if all(ch == "\x00" for ch in metadata_dict[key]):
            raise InstrumentInvalidMetadataError(METADATA_TAGS_FOR_LOGGING[key])
    for key in (MAIN_FIRMWARE_VERSION_UUID, CHANNEL_FIRMWARE_VERSION_UUID):
        if metadata_dict[key] == "0.0.0":
            raise InstrumentInvalidMetadataError(METADATA_TAGS_FOR_LOGGING[key])
    # TODO validate metadata_dict[INITIAL_MAGNET_FINDING_PARAMS_UUID]


def convert_semver_bytes_to_str(semver_bytes: bytes) -> str:
    return f"{semver_bytes[0]}.{semver_bytes[1]}.{semver_bytes[2]}"


def convert_semver_str_to_bytes(semver_str: str) -> bytes:
    return bytes([int(num) for num in semver_str.split(".")])


def convert_status_code_bytes_to_dict(status_code_bytes: bytes) -> dict[str, int]:
    if len(status_code_bytes) != SERIAL_COMM_STATUS_CODE_LENGTH_BYTES:
        raise ValueError(
            f"Status code bytes must have len of {SERIAL_COMM_STATUS_CODE_LENGTH_BYTES}, {len(status_code_bytes)} bytes given: {str(status_code_bytes)}"
        )
    status_code_labels = (
        "main_status",
        "index_of_thread_with_error",
        *[f"module_{i}_status" for i in range(NUM_WELLS)],
    )
    return {label: status_code_bytes[i] for i, label in enumerate(status_code_labels)}


def convert_to_timestamp_bytes(timestamp: int) -> bytes:
    return timestamp.to_bytes(SERIAL_COMM_TIMESTAMP_LENGTH_BYTES, byteorder="little")


def get_serial_comm_timestamp() -> int:
    # Tanner (4/7/21): This method should not be used in the simulator. It has its own way of determining the timestamp to send in order to behave more accurately like the real Mantarray instrument
    return (
        datetime.datetime.now(tz=datetime.timezone.utc) - SERIAL_COMM_TIMESTAMP_EPOCH
    ) // datetime.timedelta(microseconds=1)


def convert_stimulator_check_bytes_to_dict(stimulator_check_bytes: bytes) -> dict[str, list[int]]:
    stimulator_checks_as_ints = struct.unpack("<" + "HHB" * NUM_WELLS * 2, stimulator_check_bytes)
    # convert to lists of adc8, adc9, and status where the index of each list is the module id. Only creating an array here to reshape easily
    stimulator_checks_list = (
        np.array(stimulator_checks_as_ints, copy=False)
        .reshape((6, len(stimulator_checks_as_ints) // 6), order="F")
        .tolist()
    )
    stimulator_checks_dict = {
        key: stimulator_checks_list[i]
        for i, key in enumerate(["adc8_pos", "adc9_pos", "status_pos", "adc8_neg", "adc9_neg", "status_neg"])
    }
    return stimulator_checks_dict


def convert_adc_readings_to_circuit_status(adc8: int, adc9: int) -> int:
    impedance = convert_adc_readings_to_impedance(adc8, adc9)
    # Tanner (5/12/22): this section NOT based on the FW's actual calculation
    if impedance < 0:
        return StimulatorCircuitStatuses.ERROR
    if impedance <= STIM_SHORT_CIRCUIT_THRESHOLD_OHMS:
        return StimulatorCircuitStatuses.SHORT
    if impedance >= STIM_OPEN_CIRCUIT_THRESHOLD_OHMS:
        return StimulatorCircuitStatuses.OPEN
    return StimulatorCircuitStatuses.MEDIA


def convert_adc_readings_to_impedance(adc8: int, adc9: int) -> float:
    # Tanner (5/12/22): this calculation is the FW's actual calculation  # TODO consider making all these numbers constants
    adc8_volts = (adc8 / 4096.0) * 3.3
    adc9_volts = (adc9 / 4096.0) * 3.3
    well_plus = 5.7 * (adc8_volts - 1.65053)
    well_minus = 2 * adc9_volts - 3.3
    current = well_minus / 33
    voltage = well_plus - well_minus
    impedance = voltage / current
    return impedance


def is_null_subprotocol(subprotocol_dict: dict[str, Union[int, str]]) -> bool:
    return subprotocol_dict["type"] == "delay"


def convert_subprotocol_pulse_dict_to_bytes(
    subprotocol_dict: dict[str, Union[int, str]], is_voltage: bool = False
) -> bytes:
    conversion_factor = 1 if is_voltage else 10
    is_null = is_null_subprotocol(subprotocol_dict)

    # for mypy
    subprotocol_components: dict[str, int] = {k: v for k, v in subprotocol_dict.items() if isinstance(v, int)}

    if is_null:
        num_unused_bytes = 24
        subprotocol_bytes = bytes(num_unused_bytes) + (
            subprotocol_components["duration"] // MICROS_PER_MILLI
        ).to_bytes(4, byteorder="little")
    else:
        subprotocol_bytes = subprotocol_components["phase_one_duration"].to_bytes(4, byteorder="little") + (
            subprotocol_components["phase_one_charge"] // conversion_factor
        ).to_bytes(2, byteorder="little", signed=True)

        if subprotocol_dict["type"] == "monophasic":
            subprotocol_bytes += bytes(12)
        else:
            subprotocol_bytes += (
                subprotocol_components["interphase_interval"].to_bytes(4, byteorder="little")
                + bytes(2)  # interphase_interval amplitude (always 0)
                + subprotocol_components["phase_two_duration"].to_bytes(4, byteorder="little")
                + (subprotocol_components["phase_two_charge"] // conversion_factor).to_bytes(
                    2, byteorder="little", signed=True
                )
            )

        subprotocol_bytes += (
            subprotocol_components["postphase_interval"].to_bytes(4, byteorder="little")
            + bytes(2)  # postphase_interval amplitude (always 0)
            + subprotocol_components["num_cycles"].to_bytes(4, byteorder="little")
        )

    subprotocol_bytes += bytes([is_null])
    return subprotocol_bytes


def convert_subprotocol_pulse_bytes_to_dict(
    subprotocol_bytes: bytes, is_voltage: bool = False
) -> dict[str, Union[int, str]]:
    # duration_ms if subprotocols is a delay (null subprotocol), num_cycles o/w
    num_cycles_or_duration_ms = int.from_bytes(subprotocol_bytes[24:28], byteorder="little")
    # the final byte is a flag indicating whether or not this subprotocol is a delay
    if subprotocol_bytes[-1]:
        duration_us = num_cycles_or_duration_ms * MICROS_PER_MILLI
        return {"type": "delay", "duration": duration_us}

    conversion_factor = 1 if is_voltage else 10
    subprotocol_dict: dict[str, Union[int, str]] = {
        "type": "biphasic",  # assume biphasic to start
        "phase_one_duration": int.from_bytes(subprotocol_bytes[:4], byteorder="little"),
        "phase_one_charge": int.from_bytes(subprotocol_bytes[4:6], byteorder="little", signed=True)
        * conversion_factor,
        "interphase_interval": int.from_bytes(subprotocol_bytes[6:10], byteorder="little"),
        "phase_two_duration": int.from_bytes(subprotocol_bytes[12:16], byteorder="little"),
        "phase_two_charge": int.from_bytes(subprotocol_bytes[16:18], byteorder="little", signed=True)
        * conversion_factor,
        "postphase_interval": int.from_bytes(subprotocol_bytes[18:22], byteorder="little"),
    }

    if not any(subprotocol_dict[k] for k in SUBPROTOCOL_BIPHASIC_ONLY_COMPONENTS):
        subprotocol_dict["type"] = "monophasic"
        for k in SUBPROTOCOL_BIPHASIC_ONLY_COMPONENTS:
            subprotocol_dict.pop(k)

    num_cycles = num_cycles_or_duration_ms
    subprotocol_dict["num_cycles"] = num_cycles

    return subprotocol_dict


def convert_subprotocol_node_dict_to_bytes(
    subprotocol_node_dict: dict[str, Any], start_idx: int, is_voltage: bool = False
) -> tuple[bytes, int]:
    is_loop = subprotocol_node_dict["type"] == "loop"

    subprotocol_node_bytes = bytes([is_loop])

    curr_idx = start_idx
    if is_loop:
        subprotocol_node_bytes += bytes([len(subprotocol_node_dict["subprotocols"])])
        subprotocol_node_bytes += subprotocol_node_dict["num_iterations"].to_bytes(4, byteorder="little")
        for inner_subprotocol_node_dict in subprotocol_node_dict["subprotocols"]:
            new_bytes, curr_idx = convert_subprotocol_node_dict_to_bytes(
                inner_subprotocol_node_dict, curr_idx, is_voltage
            )
            subprotocol_node_bytes += new_bytes
    else:
        subprotocol_node_bytes += bytes([curr_idx])
        subprotocol_node_bytes += convert_subprotocol_pulse_dict_to_bytes(subprotocol_node_dict, is_voltage)
        curr_idx += 1

    return subprotocol_node_bytes, curr_idx


def _convert_subprotocol_node_bytes_to_dict(
    subprotocol_node_bytes: bytes, is_voltage: bool = False
) -> tuple[dict[str, Any], int]:
    is_loop = bool(subprotocol_node_bytes[0])

    if not is_loop:
        stop_idx = STIM_PULSE_BYTES_LEN + 2
        pulse_dict = convert_subprotocol_pulse_bytes_to_dict(subprotocol_node_bytes[2:stop_idx], is_voltage)
        return pulse_dict, stop_idx

    num_subprotocol_nodes = subprotocol_node_bytes[1]
    subprotocol_nodes = []  # type: ignore

    loop_dict = {
        "type": "loop",
        "num_iterations": int.from_bytes(subprotocol_node_bytes[2:6], byteorder="little"),
        "subprotocols": subprotocol_nodes,
    }

    curr_idx = 6
    for _ in range(num_subprotocol_nodes):
        subprotocol_node_dict, num_bytes_processed = _convert_subprotocol_node_bytes_to_dict(
            subprotocol_node_bytes[curr_idx:], is_voltage
        )
        subprotocol_nodes.append(subprotocol_node_dict)
        curr_idx += num_bytes_processed

    return loop_dict, curr_idx


def convert_stim_dict_to_bytes(stim_dict: dict[str, Any]) -> bytes:
    """Convert a stimulation info dictionary to bytes.

    Assumes the stimulation dictionary given does not have any issues.
    """
    # add bytes for protocol definitions
    stim_bytes = bytes([len(stim_dict["protocols"])])  # number of unique protocols
    for idx, protocol_dict in enumerate(stim_dict["protocols"]):
        is_voltage_controlled = protocol_dict["stimulation_type"] == "V"

        # data type is always 0 as of 12/23/22
        stim_bytes += bytes([is_voltage_controlled, protocol_dict["run_until_stopped"], 0])

        # TODO remove this since the top level should always be a loop

        curr_idx = 0
        for subprotocol_dict in protocol_dict["subprotocols"]:
            subprotocol_bytes, curr_idx = convert_subprotocol_node_dict_to_bytes(
                subprotocol_dict, curr_idx, is_voltage=is_voltage_controlled
            )
            stim_bytes += subprotocol_bytes

        module_ids_assigned = [
            convert_well_name_to_module_id(well_name, use_stim_mapping=True)
            for well_name, assigned_protocol_id in stim_dict["protocol_assignments"].items()
            if assigned_protocol_id == protocol_dict.get("protocol_id", idx)
        ]
        stim_bytes += bytes([len(module_ids_assigned)] + sorted(module_ids_assigned))

    return stim_bytes


def convert_stim_bytes_to_dict(stim_bytes: bytes) -> dict[str, Any]:
    """Convert a stimulation info bytes to dictionary."""
    stim_info_dict: dict[str, Any] = {
        "protocols": [],
        "protocol_assignments": {
            GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx): None
            for well_idx in range(NUM_WELLS)
        },
    }

    # convert protocol bytes
    num_protocols = stim_bytes[0]

    curr_byte_idx = 1
    for protocol_idx in range(num_protocols):
        is_voltage_controlled, run_until_stopped = stim_bytes[curr_byte_idx : curr_byte_idx + 2]
        # Tanner (1/17/23): data_type is not used at the moment, so skipping one extra byte
        curr_byte_idx += 2 + 1

        subprotocol_nodes, num_bytes_processed = _convert_subprotocol_node_bytes_to_dict(
            stim_bytes[curr_byte_idx:], bool(is_voltage_controlled)
        )
        curr_byte_idx += num_bytes_processed

        stim_info_dict["protocols"].append(
            {
                "stimulation_type": "V" if is_voltage_controlled else "C",
                "run_until_stopped": bool(run_until_stopped),
                "subprotocols": [subprotocol_nodes],
            }
        )

        num_wells_assigned = stim_bytes[curr_byte_idx]
        curr_byte_idx += 1

        stim_info_dict["protocol_assignments"].update(
            {
                convert_module_id_to_well_name(module_id, use_stim_mapping=True): protocol_idx
                for module_id in stim_bytes[curr_byte_idx : curr_byte_idx + num_wells_assigned]
            }
        )

        curr_byte_idx += num_wells_assigned

    return stim_info_dict


def parse_end_offline_mode_bytes(response_bytes: bytes) -> dict[str, Any]:
    """Parse bytes containing stimulation info and return as dict."""
    protocol_status_start_idx = 17
    protocol_status_stop_idx = protocol_status_start_idx + PROTOCOL_STATUS_BYTES_LEN * NUM_WELLS

    stim_dict = convert_stim_bytes_to_dict(response_bytes[protocol_status_stop_idx:])
    updated_stim_dict = format_stim_dict_with_ids(stim_dict)

    num_protocols = len(updated_stim_dict["protocols"])
    stimulation_protocol_statuses = parse_stim_offline_statuses(
        response_bytes[protocol_status_start_idx:protocol_status_stop_idx], num_protocols
    )

    return {
        "system_dormant_timestamp": int.from_bytes(response_bytes[:8], byteorder="little"),
        "stim_active": bool(response_bytes[8]),
        "last_stim_scheduled_start_timestamp": int.from_bytes(
            response_bytes[9:protocol_status_start_idx], byteorder="little"
        ),
        "stimulation_protocol_statuses": stimulation_protocol_statuses,
        "stim_info": updated_stim_dict,
    }


def parse_stim_offline_statuses(status_bytes: bytes, num_protocols: int) -> list[StimulationStates]:
    """Parse stimulator statuses bytes for active states."""
    stimulator_status_idx = 9

    status_bytes_to_parse = num_protocols * PROTOCOL_STATUS_BYTES_LEN
    return [
        _stim_status_to_state(status_bytes[status_idx])
        for status_idx in range(
            stimulator_status_idx, len(status_bytes[:status_bytes_to_parse]), PROTOCOL_STATUS_BYTES_LEN
        )
    ]


def _stim_status_to_state(status: int) -> StimulationStates:
    return (
        StimulationStates.RUNNING
        if status in (StimProtocolStatuses.ACTIVE, StimProtocolStatuses.NULL)
        else StimulationStates.INACTIVE
    )


# TODO consider just adding this into convert_stim_bytes_to_dict
def format_stim_dict_with_ids(stim_dict: dict[str, Any]) -> dict[str, Any]:
    """Add protocol IDs to stim dict from instrument after being offline."""
    for idx, _ in enumerate(stim_dict["protocols"]):
        protocol_id = chr(idx + ord("A"))
        stim_dict["protocols"][idx]["protocol_id"] = protocol_id

        stim_dict["protocol_assignments"] |= {
            well: protocol_id
            for well, assignment in stim_dict["protocol_assignments"].items()
            if assignment == idx
        }

    return stim_dict
