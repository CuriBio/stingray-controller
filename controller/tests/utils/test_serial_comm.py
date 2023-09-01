# -*- coding: utf-8 -*-
import copy
import datetime
from random import choice
from random import randint
from zlib import crc32

from controller.constants import GENERIC_24_WELL_DEFINITION
from controller.constants import NUM_WELLS
from controller.constants import SERIAL_COMM_PACKET_BASE_LENGTH_BYTES
from controller.constants import SERIAL_COMM_STATUS_CODE_LENGTH_BYTES
from controller.constants import STIM_OPEN_CIRCUIT_THRESHOLD_OHMS
from controller.constants import STIM_SHORT_CIRCUIT_THRESHOLD_OHMS
from controller.constants import StimProtocolStatuses
from controller.constants import StimulationStates
from controller.constants import StimulatorCircuitStatuses
from controller.utils import serial_comm
from controller.utils.serial_comm import convert_adc_readings_to_circuit_status
from controller.utils.serial_comm import convert_adc_readings_to_impedance
from controller.utils.serial_comm import convert_instrument_event_info_to_bytes
from controller.utils.serial_comm import convert_status_code_bytes_to_dict
from controller.utils.serial_comm import convert_stim_bytes_to_dict
from controller.utils.serial_comm import convert_stim_dict_to_bytes
from controller.utils.serial_comm import convert_subprotocol_node_dict_to_bytes
from controller.utils.serial_comm import convert_subprotocol_pulse_bytes_to_dict
from controller.utils.serial_comm import convert_subprotocol_pulse_dict_to_bytes
from controller.utils.serial_comm import convert_well_name_to_module_id
from controller.utils.serial_comm import create_data_packet
from controller.utils.serial_comm import get_serial_comm_timestamp
from controller.utils.serial_comm import parse_end_offline_mode_bytes
from controller.utils.serial_comm import parse_instrument_event_info
from controller.utils.serial_comm import parse_metadata_bytes
from controller.utils.serial_comm import SERIAL_COMM_CHECKSUM_LENGTH_BYTES
from controller.utils.serial_comm import SERIAL_COMM_MAGIC_WORD_BYTES
from controller.utils.serial_comm import SERIAL_COMM_TIMESTAMP_EPOCH
from controller.utils.serial_comm import SERIAL_COMM_TIMESTAMP_LENGTH_BYTES
from controller.utils.serial_comm import validate_checksum
from freezegun import freeze_time
import numpy as np
from pulse3D.constants import BOOT_FLAGS_UUID
from pulse3D.constants import CHANNEL_FIRMWARE_VERSION_UUID
from pulse3D.constants import INITIAL_MAGNET_FINDING_PARAMS_UUID
from pulse3D.constants import MAIN_FIRMWARE_VERSION_UUID
from pulse3D.constants import MANTARRAY_NICKNAME_UUID
from pulse3D.constants import MANTARRAY_SERIAL_NUMBER_UUID
import pytest

from ..helpers import assert_subprotocol_node_bytes_are_expected
from ..helpers import assert_subprotocol_pulse_bytes_are_expected
from ..helpers import get_generic_protocols
from ..helpers import get_random_biphasic_pulse
from ..helpers import get_random_monophasic_pulse
from ..helpers import get_random_protocol_status
from ..helpers import get_random_stim_delay
from ..helpers import get_random_stim_pulse
from ..helpers import get_random_subprotocol
from ..helpers import random_bool
from ..helpers import random_timestamp
from ..helpers import TEST_EVENT_INFO
from ..helpers import TEST_INITIAL_MAGNET_FINDING_PARAMS
from ..helpers import TEST_SERIAL_NUMBER


def test_create_data_packet__creates_data_packet_bytes_correctly():
    test_timestamp = 100
    test_packet_type = 1
    test_data = bytes([1, 5, 3])
    test_packet_remainder_size = (
        SERIAL_COMM_PACKET_BASE_LENGTH_BYTES + len(test_data) + SERIAL_COMM_CHECKSUM_LENGTH_BYTES
    )

    expected_data_packet_bytes = SERIAL_COMM_MAGIC_WORD_BYTES
    expected_data_packet_bytes += test_packet_remainder_size.to_bytes(2, byteorder="little")
    expected_data_packet_bytes += test_timestamp.to_bytes(
        SERIAL_COMM_TIMESTAMP_LENGTH_BYTES, byteorder="little"
    )
    expected_data_packet_bytes += bytes([test_packet_type])
    expected_data_packet_bytes += test_data
    expected_data_packet_bytes += crc32(expected_data_packet_bytes).to_bytes(
        SERIAL_COMM_CHECKSUM_LENGTH_BYTES, byteorder="little"
    )

    actual = create_data_packet(test_timestamp, test_packet_type, test_data)
    assert actual == expected_data_packet_bytes


def test_validate_checksum__returns_true_when_checksum_is_correct():
    test_bytes = bytes([1, 2, 3, 4, 5])
    test_bytes += crc32(test_bytes).to_bytes(SERIAL_COMM_CHECKSUM_LENGTH_BYTES, byteorder="little")
    assert validate_checksum(test_bytes) is True


def test_validate_checksum__returns_false_when_checksum_is_incorrect():
    test_bytes = bytes([1, 2, 3, 4, 5])
    test_bytes += (crc32(test_bytes) - 1).to_bytes(SERIAL_COMM_CHECKSUM_LENGTH_BYTES, byteorder="little")
    assert validate_checksum(test_bytes) is False


def test_parse_metadata_bytes__returns_expected_value():
    test_status_codes = list(range(SERIAL_COMM_STATUS_CODE_LENGTH_BYTES))

    is_stingray = random_bool()

    metadata_bytes = (
        bytes([0b10101010])  # boot flags
        + bytes("マンタレ1", encoding="utf-8")  # nickname
        + bytes(TEST_SERIAL_NUMBER, encoding="ascii")
        + bytes([0, 1, 2])  # main FW version
        + bytes([255, 255, 255])  # channel FW version
        + bytes(test_status_codes)
        + TEST_INITIAL_MAGNET_FINDING_PARAMS["X"].to_bytes(1, byteorder="little", signed=True)
        + TEST_INITIAL_MAGNET_FINDING_PARAMS["Y"].to_bytes(1, byteorder="little", signed=True)
        + TEST_INITIAL_MAGNET_FINDING_PARAMS["Z"].to_bytes(1, byteorder="little", signed=True)
        + TEST_INITIAL_MAGNET_FINDING_PARAMS["REMN"].to_bytes(2, byteorder="little", signed=True)
        + bytes([is_stingray])
        + convert_instrument_event_info_to_bytes(TEST_EVENT_INFO)
    )

    # TODO make sure the bytes are the correct length?

    assert parse_metadata_bytes(metadata_bytes) == {
        BOOT_FLAGS_UUID: 0b10101010,
        MANTARRAY_SERIAL_NUMBER_UUID: TEST_SERIAL_NUMBER,
        MANTARRAY_NICKNAME_UUID: "マンタレ1",
        MAIN_FIRMWARE_VERSION_UUID: "0.1.2",
        CHANNEL_FIRMWARE_VERSION_UUID: "255.255.255",
        "status_codes_prior_to_reboot": convert_status_code_bytes_to_dict(bytes(test_status_codes)),
        INITIAL_MAGNET_FINDING_PARAMS_UUID: TEST_INITIAL_MAGNET_FINDING_PARAMS,
        "is_stingray": is_stingray,
        **TEST_EVENT_INFO,
    }


def test_parse_instrument_event_info__parses_default_metadata_values_without_error():
    event_info_len = 64
    test_bytes = bytes([0xFF] * event_info_len)
    actual = parse_instrument_event_info(test_bytes)
    assert actual["prev_barcode_scanned"] == "N/A"


@freeze_time("2021-04-07 13:14:07.234987")
def test_get_serial_comm_timestamp__returns_microseconds_since_2021_01_01():
    expected_usecs = (
        datetime.datetime.now(tz=datetime.timezone.utc) - SERIAL_COMM_TIMESTAMP_EPOCH
    ) // datetime.timedelta(microseconds=1)
    actual = get_serial_comm_timestamp()
    assert actual == expected_usecs


@pytest.mark.parametrize(
    "test_adc8,test_adc9,expected_impedance",
    [(0, 0, 61.08021), (0, 2039, 21375.4744533), (0, 2049, -192709.2700799), (1113, 0, 9.9680762)],
)
def test_convert_adc_readings_to_impedance__returns_expected_values(test_adc8, test_adc9, expected_impedance):
    actual_impedance = convert_adc_readings_to_impedance(test_adc8, test_adc9)
    np.testing.assert_almost_equal(actual_impedance, expected_impedance)


@pytest.mark.parametrize(
    "test_impedance,expected_status",
    [
        (STIM_OPEN_CIRCUIT_THRESHOLD_OHMS + 1, StimulatorCircuitStatuses.OPEN),
        (STIM_OPEN_CIRCUIT_THRESHOLD_OHMS, StimulatorCircuitStatuses.OPEN),
        (STIM_OPEN_CIRCUIT_THRESHOLD_OHMS - 1, StimulatorCircuitStatuses.MEDIA),
        (STIM_SHORT_CIRCUIT_THRESHOLD_OHMS + 1, StimulatorCircuitStatuses.MEDIA),
        (STIM_SHORT_CIRCUIT_THRESHOLD_OHMS, StimulatorCircuitStatuses.SHORT),
        (STIM_SHORT_CIRCUIT_THRESHOLD_OHMS - 1, StimulatorCircuitStatuses.SHORT),
        (0, StimulatorCircuitStatuses.SHORT),
        (-1, StimulatorCircuitStatuses.ERROR),
    ],
)
def test_convert_adc_readings_to_circuit_status__returns_correct_values(
    test_impedance, expected_status, mocker
):
    mocked_to_impedance = mocker.patch.object(
        serial_comm, "convert_adc_readings_to_impedance", autospec=True, return_value=test_impedance
    )
    # mocking convert_adc_readings_to_impedance so these values don't actually matter
    test_adc8 = randint(0, 0xFFFF)
    test_adc9 = randint(0, 0xFFFF)

    assert convert_adc_readings_to_circuit_status(test_adc8, test_adc9) == expected_status

    mocked_to_impedance.assert_called_once_with(test_adc8, test_adc9)


@pytest.mark.parametrize(
    "test_len", [SERIAL_COMM_STATUS_CODE_LENGTH_BYTES - 1, SERIAL_COMM_STATUS_CODE_LENGTH_BYTES + 1]
)
def test_convert_status_code_bytes_to_dict__raises_error_if_given_value_does_not_expected_length_exactly(
    test_len,
):
    test_bytes = bytes([randint(0, 255) for _ in range(test_len)])
    with pytest.raises(ValueError) as exc_info:
        convert_status_code_bytes_to_dict(test_bytes)
    assert (
        str(exc_info.value)
        == f"Status code bytes must have len of {SERIAL_COMM_STATUS_CODE_LENGTH_BYTES}, {test_len} bytes given: {test_bytes}"
    )


def test_convert_subprotocol_pulse_dict_to_bytes__returns_expected_bytes__for_voltage_controlled_monophasic_pulse():
    test_subprotocol_dict = {
        "type": "monophasic",
        "phase_one_duration": 0x654321,
        "phase_one_charge": 0x333,
        "postphase_interval": 0x3BA,
        "num_cycles": 0xFF,
    }
    # fmt: off
    expected_bytes = bytes(
        [
            0x21, 0x43, 0x65, 0,  # phase_one_duration
            0x33, 3,  # phase_one_charge
            0, 0, 0, 0,  # interphase_interval (always 0 for monophasic)
            0, 0,  # interphase_interval amplitude (always 0)
            0, 0, 0, 0,  # phase_two_duration (always 0 for monophasic)
            0, 0,  # phase_two_charge (always 0 for monophasic)
            0xBA, 3, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0xFF, 0, 0, 0,  # num_cycles
            0,  # is_null_subprotocol
        ]
    )
    # fmt: on
    actual = convert_subprotocol_pulse_dict_to_bytes(test_subprotocol_dict, is_voltage=True)
    assert_subprotocol_pulse_bytes_are_expected(actual, expected_bytes)


def test_convert_subprotocol_pulse_dict_to_bytes__returns_expected_bytes__for_current_controlled_monophasic_pulse():
    test_subprotocol_dict = {
        "type": "monophasic",
        "phase_one_duration": 0x111,
        "phase_one_charge": 50,
        "postphase_interval": 0x6BF,
        "num_cycles": 0x12000034,
    }
    # fmt: off
    expected_bytes = bytes(
        [
            0x11, 1, 0, 0,  # phase_one_duration
            0x05, 0,  # phase_one_charge  # Tanner (11/15/22): this currently gets divided by 10
            0, 0, 0, 0,  # interphase_interval (always 0 for monophasic)
            0, 0,  # interphase_interval amplitude (always 0)
            0, 0, 0, 0,  # phase_two_duration (always 0 for monophasic)
            0, 0,  # phase_two_charge (always 0 for monophasic)
            0xBF, 6, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0x34, 0, 0, 0x12,  # num_cycles
            0,  # is_null_subprotocol
        ]
    )
    # fmt: on
    actual = convert_subprotocol_pulse_dict_to_bytes(test_subprotocol_dict)
    assert_subprotocol_pulse_bytes_are_expected(actual, expected_bytes)


def test_convert_subprotocol_pulse_dict_to_bytes__returns_expected_bytes__for_voltage_controlled_biphasic_pulse():
    test_subprotocol_dict = {
        "type": "biphasic",
        "phase_one_duration": 0x111,
        "phase_one_charge": 0x333,
        "interphase_interval": 0x555,
        "phase_two_duration": 0x777,
        "phase_two_charge": -1,
        "postphase_interval": 0x993,
        "num_cycles": 0x432100,
    }
    # fmt: off
    expected_bytes = bytes(
        [
            0x11, 1, 0, 0,  # phase_one_duration
            0x33, 3,  # phase_one_charge
            0x55, 5, 0, 0,  # interphase_interval
            0, 0,  # interphase_interval amplitude (always 0)
            0x77, 7, 0, 0,  # phase_two_duration
            0xFF, 0xFF,  # phase_two_charge
            0x93, 9, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0, 0x21, 0x43, 0,  # num_cycles
            0,  # is_null_subprotocol
        ]
    )
    # fmt: on
    actual = convert_subprotocol_pulse_dict_to_bytes(test_subprotocol_dict, is_voltage=True)
    assert_subprotocol_pulse_bytes_are_expected(actual, expected_bytes)


def test_convert_subprotocol_pulse_dict_to_bytes__returns_expected_bytes__for_current_controlled_biphasic_pulse():
    test_subprotocol_dict = {
        "type": "biphasic",
        "phase_one_duration": 0x111,
        "phase_one_charge": 50,
        "interphase_interval": 0x555,
        "phase_two_duration": 0x777,
        "phase_two_charge": -50,
        "postphase_interval": 0x993,
        "num_cycles": 0xFFFFFFFF,
    }
    # fmt: off
    expected_bytes = bytes(
        [
            0x11, 1, 0, 0,  # phase_one_duration
            0x05, 0,  # phase_one_charge  # Tanner (11/15/22): this currently gets divided by 10
            0x55, 5, 0, 0,  # interphase_interval
            0, 0,  # interphase_interval amplitude (always 0)
            0x77, 7, 0, 0,  # phase_two_duration
            0xFB, 0xFF,  # phase_two_charge  # Tanner (11/15/22): this currently gets divided by 10
            0x93, 9, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0xFF, 0xFF, 0xFF, 0xFF,  # num_cycles
            0,  # is_null_subprotocol
        ]
    )
    # fmt: on
    actual = convert_subprotocol_pulse_dict_to_bytes(test_subprotocol_dict)
    assert_subprotocol_pulse_bytes_are_expected(actual, expected_bytes)


def test_convert_subprotocol_pulse_dict_to_bytes__returns_expected_bytes__when_subprotocol_is_a_delay():
    test_subprotocol_dict = {"type": "delay", "duration": 123000}
    # fmt: off
    expected_bytes = bytes(
        [
            0, 0, 0, 0,  # phase_one_duration (value is ignored when converting delay)
            0, 0,  # phase_one_charge
            0, 0, 0, 0,  # interphase_interval
            0, 0,  # interphase_interval amplitude (always 0)
            0, 0, 0, 0,  # phase_two_duration
            0, 0,  # phase_two_charge
            0, 0, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0x7B, 0, 0, 0,  # duration_ms
            1,  # is_null_subprotocol
        ]
    )
    # fmt: on
    actual = convert_subprotocol_pulse_dict_to_bytes(test_subprotocol_dict)
    assert_subprotocol_pulse_bytes_are_expected(actual, expected_bytes)


def test_convert_subprotocol_pulse_bytes_to_dict__returns_expected_dict__for_voltage_controlled_monophasic_pulse():
    # fmt: off
    test_bytes = bytes(
        [
            0x99, 9, 0, 0,  # phase_one_duration
            0x77, 7,  # phase_one_charge
            0, 0, 0, 0,  # interphase_interval
            0, 0,  # interphase_interval amplitude (always 0)
            0, 0, 0, 0,  # phase_two_duration
            0, 0,  # phase_two_charge
            0x11, 1, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0x7, 0, 0, 0,  # num_cycles
            0,  # is_null_subprotocol
        ]
    )
    # fmt: on
    expected_subprotocol_dict = {
        "type": "monophasic",
        "phase_one_duration": 0x999,
        "phase_one_charge": 0x777,
        "postphase_interval": 0x111,
        "num_cycles": 0x7,
    }

    actual = convert_subprotocol_pulse_bytes_to_dict(test_bytes, is_voltage=True)
    assert actual == expected_subprotocol_dict


def test_convert_subprotocol_pulse_bytes_to_dict__returns_expected_dict__for_current_controlled_monophasic_pulse():
    # fmt: off
    test_bytes = bytes(
        [
            0xBF, 6, 0, 0,  # phase_one_duration
            0x77, 7,  # phase_one_charge
            0, 0, 0, 0,  # interphase_interval
            0, 0,  # interphase_interval amplitude (always 0)
            0, 0, 0, 0,  # phase_two_duration
            0, 0,  # phase_two_charge
            0x11, 1, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0x12, 0, 0, 0x34,  # num_cycles
            0,  # is_null_subprotocol
        ]
    )
    # fmt: on
    expected_subprotocol_dict = {
        "type": "monophasic",
        "phase_one_duration": 0x6BF,
        "phase_one_charge": 0x777 * 10,
        "postphase_interval": 0x111,
        "num_cycles": 0x34000012,
    }

    actual = convert_subprotocol_pulse_bytes_to_dict(test_bytes)
    assert actual == expected_subprotocol_dict


def test_convert_subprotocol_pulse_bytes_to_dict__returns_expected_dict__for_voltage_controlled_biphasic_pulse():
    # fmt: off
    test_bytes = bytes(
        [
            0x93, 9, 0, 0,  # phase_one_duration
            0x77, 7,  # phase_one_charge
            0x55, 5, 0, 0,  # interphase_interval
            0, 0,  # interphase_interval amplitude (always 0)
            0x33, 3, 0, 0,  # phase_two_duration
            0xFF, 0xFF,  # phase_two_charge
            0x11, 1, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0, 0x80, 0, 0x80,  # num_cycles
            0,  # is_null_subprotocol
        ]
    )
    # fmt: on
    expected_subprotocol_dict = {
        "type": "biphasic",
        "phase_one_duration": 0x993,
        "phase_one_charge": 0x777,
        "interphase_interval": 0x555,
        "phase_two_duration": 0x333,
        "phase_two_charge": -1,
        "postphase_interval": 0x111,
        "num_cycles": 0x80008000,
    }

    actual = convert_subprotocol_pulse_bytes_to_dict(test_bytes, is_voltage=True)
    assert actual == expected_subprotocol_dict


def test_convert_subprotocol_pulse_bytes_to_dict__returns_expected_dict__for_current_controlled_biphasic_pulse():
    # fmt: off
    test_bytes = bytes(
        [
            0x93, 9, 0, 0,  # phase_one_duration
            0x77, 7,  # phase_one_charge
            0x55, 5, 0, 0,  # interphase_interval
            0, 0,  # interphase_interval amplitude (always 0)
            0x33, 3, 0, 0,  # phase_two_duration
            0xFF, 0xFF,  # phase_two_charge
            0x11, 1, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0x21, 3, 0, 0,  # num_cycles
            0,  # is_null_subprotocol
        ]
    )
    # fmt: on
    expected_subprotocol_dict = {
        "type": "biphasic",
        "phase_one_duration": 0x993,
        "phase_one_charge": 0x777 * 10,
        "interphase_interval": 0x555,
        "phase_two_duration": 0x333,
        "phase_two_charge": -1 * 10,
        "postphase_interval": 0x111,
        "num_cycles": 0x321,
    }

    actual = convert_subprotocol_pulse_bytes_to_dict(test_bytes)
    assert actual == expected_subprotocol_dict


def test_convert_subprotocol_pulse_bytes_to_dict__returns_expected_dict__when_subprotocol_is_a_delay():
    # fmt: off
    test_bytes = bytes(
        [
            0, 0, 0, 0,  # phase_one_duration
            0, 0,  # phase_one_charge
            0, 0, 0, 0,  # interphase_interval
            0, 0,  # interphase_interval amplitude (always 0)
            0, 0, 0, 0,  # phase_two_duration
            0, 0,  # phase_two_charge
            0, 0, 0, 0,  # postphase_interval
            0, 0,  # postphase_interval amplitude (always 0)
            0x41, 1, 0, 0,  # duration_ms
            1,  # is_null_subprotocol
        ]
    )
    # fmt: on
    expected_subprotocol_dict = {"type": "delay", "duration": 321000}

    actual = convert_subprotocol_pulse_bytes_to_dict(test_bytes)
    assert actual == expected_subprotocol_dict


@pytest.mark.parametrize(
    "test_pulse_fn", [get_random_biphasic_pulse, get_random_monophasic_pulse, get_random_stim_delay]
)
def test_convert_subprotocol_node_dict_to_bytes__returns_expected_bytes_and_idx__when_node_is_a_pulse(
    test_pulse_fn,
):
    test_pulse_dict = test_pulse_fn()
    test_idx = randint(0, 200)

    is_voltage = random_bool()

    expected_bytes = bytes([0])  # node_type
    expected_bytes += bytes([test_idx])
    expected_bytes += convert_subprotocol_pulse_dict_to_bytes(test_pulse_dict, is_voltage)

    actual_bytes, actual_idx = convert_subprotocol_node_dict_to_bytes(test_pulse_dict, test_idx, is_voltage)
    assert_subprotocol_node_bytes_are_expected(actual_bytes, expected_bytes)
    assert actual_idx == test_idx + 1


def test_convert_subprotocol_node_dict_to_bytes__returns_expected_bytes__when_node_is_a_single_level_loop():
    is_voltage = random_bool()

    test_num_iterations = randint(1, 0xFFFFFFFF)

    test_num_subprotocol_pulses = randint(1, 3)
    test_subprotocol_pulses = [get_random_stim_pulse() for _ in range(test_num_subprotocol_pulses)]

    test_starting_idx = randint(0, 100)

    test_loop_dict = {
        "type": "loop",
        "num_iterations": test_num_iterations,
        "subprotocols": test_subprotocol_pulses,
    }
    actual, _ = convert_subprotocol_node_dict_to_bytes(test_loop_dict, test_starting_idx, is_voltage)

    expected_bytes = bytes([1])  # node_type
    expected_bytes += bytes([test_num_subprotocol_pulses])
    expected_bytes += test_num_iterations.to_bytes(4, byteorder="little")
    for subprotocol_idx, test_pulse_dict in enumerate(test_subprotocol_pulses):
        expected_bytes += bytes([0])  # node_type
        expected_bytes += bytes([test_starting_idx + subprotocol_idx])
        expected_bytes += convert_subprotocol_pulse_dict_to_bytes(test_pulse_dict, is_voltage)

    assert_subprotocol_node_bytes_are_expected(actual, expected_bytes)


def test_convert_subprotocol_node_dict_to_bytes__returns_expected_bytes__when_node_is_a_multi_level_loop():
    is_voltage = random_bool()

    test_num_iterations = [randint(1, 0xFFFFFFFF) for _ in range(4)]
    test_subprotocol_pulses = [get_random_stim_pulse() for _ in range(7)]
    test_num_subprotocol_nodes = [3, 2, 2, 3]

    test_starting_idx = randint(0, 100)

    test_num_iterations_iter = iter(test_num_iterations)
    test_subprotocol_pulses_iter = iter(test_subprotocol_pulses)
    test_subprotocol_idx_iter = iter(
        range(test_starting_idx, test_starting_idx + len(test_subprotocol_pulses))
    )

    test_loop_dict = {
        "type": "loop",
        "num_iterations": next(test_num_iterations_iter),
        "subprotocols": [
            next(test_subprotocol_pulses_iter),
            {
                "type": "loop",
                "num_iterations": next(test_num_iterations_iter),
                "subprotocols": [
                    {
                        "type": "loop",
                        "num_iterations": next(test_num_iterations_iter),
                        "subprotocols": [next(test_subprotocol_pulses_iter) for _ in range(2)],
                    },
                    {
                        "type": "loop",
                        "num_iterations": next(test_num_iterations_iter),
                        "subprotocols": [next(test_subprotocol_pulses_iter) for _ in range(3)],
                    },
                ],
            },
            next(test_subprotocol_pulses_iter),
        ],
    }
    actual, _ = convert_subprotocol_node_dict_to_bytes(test_loop_dict, test_starting_idx, is_voltage)

    test_num_iterations_iter = iter(test_num_iterations)
    test_subprotocol_pulses_iter = iter(test_subprotocol_pulses)
    test_num_subprotocol_nodes_iter = iter(test_num_subprotocol_nodes)

    # top level loop
    expected_bytes = bytes([1, next(test_num_subprotocol_nodes_iter)]) + next(
        test_num_iterations_iter
    ).to_bytes(4, byteorder="little")
    expected_bytes += bytes([0, next(test_subprotocol_idx_iter)]) + convert_subprotocol_pulse_dict_to_bytes(
        next(test_subprotocol_pulses_iter), is_voltage
    )
    # - level 1 loop
    expected_bytes += bytes([1, next(test_num_subprotocol_nodes_iter)]) + next(
        test_num_iterations_iter
    ).to_bytes(4, byteorder="little")
    # - - first level 2 loop
    expected_bytes += bytes([1, next(test_num_subprotocol_nodes_iter)]) + next(
        test_num_iterations_iter
    ).to_bytes(4, byteorder="little")
    for _ in range(2):
        expected_bytes += bytes(
            [0, next(test_subprotocol_idx_iter)]
        ) + convert_subprotocol_pulse_dict_to_bytes(next(test_subprotocol_pulses_iter), is_voltage)
    # - - second level 2 loop
    expected_bytes += bytes([1, next(test_num_subprotocol_nodes_iter)]) + next(
        test_num_iterations_iter
    ).to_bytes(4, byteorder="little")
    for _ in range(3):
        expected_bytes += bytes(
            [0, next(test_subprotocol_idx_iter)]
        ) + convert_subprotocol_pulse_dict_to_bytes(next(test_subprotocol_pulses_iter), is_voltage)
    # back to top level
    expected_bytes += bytes([0, next(test_subprotocol_idx_iter)]) + convert_subprotocol_pulse_dict_to_bytes(
        next(test_subprotocol_pulses_iter), is_voltage
    )

    assert actual == expected_bytes


@pytest.mark.parametrize(
    "protocols,assignments",
    [
        [get_generic_protocols(), {"D1": "A", "D2": "B"}],
        # format from firmware returning to online mode
        [get_generic_protocols(include_ids=False), {"D1": 0, "D2": 1}],
    ],
)
def test_convert_stim_dict_to_bytes__return_expected_bytes(protocols, assignments):
    protocol_assignments_dict = assignments
    protocol_assignments_dict.update(
        {
            well_name: None
            for well_idx in range(24)
            if (well_name := GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx))
            not in protocol_assignments_dict
        }
    )

    stim_info_dict = {"protocols": protocols, "protocol_assignments": protocol_assignments_dict}

    # Tanner (12/23/22): this test is also dependent on convert_subprotocol_node_dict_to_bytes working properly. If this test fails, make sure the tests for this func are passing first

    expected_bytes = (
        bytes([2])  # num unique protocols
        + bytes([0])  # control method
        + bytes([1])  # schedule mode
        + bytes([0])  # data type
        # bytes for protocol A
        + convert_subprotocol_node_dict_to_bytes(
            stim_info_dict["protocols"][0]["subprotocols"][0], 0, is_voltage=False
        )[0]
        + convert_subprotocol_node_dict_to_bytes(
            stim_info_dict["protocols"][0]["subprotocols"][1], 1, is_voltage=False
        )[0]
        + bytes([1])  # num wells that protocol A is assigned to
        + bytes(
            [convert_well_name_to_module_id(list(protocol_assignments_dict.keys())[0], use_stim_mapping=True)]
        )  # module ID(s) that protocol A is assigned to
        # bytes for protocol D
        + bytes([1])  # control method
        + bytes([0])  # schedule mode
        + bytes([0])  # data type
        + convert_subprotocol_node_dict_to_bytes(
            stim_info_dict["protocols"][1]["subprotocols"][0], 0, is_voltage=True
        )[0]
        + convert_subprotocol_node_dict_to_bytes(
            stim_info_dict["protocols"][1]["subprotocols"][1], 1, is_voltage=True
        )[0]
        + bytes([1])  # num wells that protocol D is assigned to
        + bytes(
            [convert_well_name_to_module_id(list(protocol_assignments_dict.keys())[1], use_stim_mapping=True)]
        )  # module ID(s) that protocol A is assigned to
    )

    actual = convert_stim_dict_to_bytes(stim_info_dict)
    assert actual == expected_bytes


def test_convert_stim_bytes_to_dict__can_correctly_recreate_stim_dict__except_for_protocol_ids():
    protocol_assignments_dict = {
        GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx): randint(0, 1)
        for well_idx in range(24)
    }
    # make sure at least one well is unassigned
    well_to_unassign = choice(["A", "B", "C", "D"]) + str(randint(1, 6))
    protocol_assignments_dict[well_to_unassign] = None

    # using numbers instead of letters here since the actual letter ID is lost and converted to a number when recreated
    original_stim_info_dict = {
        "protocols": [
            {
                "protocol_id": 0,
                "stimulation_type": "V",
                "run_until_stopped": False,
                "subprotocols": [
                    {
                        "type": "loop",
                        "num_iterations": randint(1, 10),
                        "subprotocols": [
                            *[get_random_subprotocol() for _ in range(randint(1, 3))],
                            {
                                "type": "loop",
                                "num_iterations": randint(1, 10),
                                "subprotocols": [get_random_subprotocol() for _ in range(randint(1, 3))],
                            },
                            get_random_biphasic_pulse(),
                        ],
                    }
                ],
            },
            {
                "protocol_id": 1,
                "stimulation_type": "C",
                "run_until_stopped": True,
                "subprotocols": [
                    {
                        "type": "loop",
                        "num_iterations": randint(1, 10),
                        "subprotocols": [get_random_subprotocol() for _ in range(randint(1, 3))],
                    }
                ],
            },
        ],
        "protocol_assignments": protocol_assignments_dict,
    }

    recreated_stim_info_dict = convert_stim_bytes_to_dict(
        convert_stim_dict_to_bytes(copy.deepcopy(original_stim_info_dict))
    )

    for protocol_idx, (recreated_protocol, original_protocol) in enumerate(
        zip(recreated_stim_info_dict["protocols"], original_stim_info_dict["protocols"])
    ):
        original_protocol.pop("protocol_id")  # this is not needed in the recreated dict
        assert recreated_protocol == original_protocol, f"Protocol {protocol_idx}"

    assert recreated_stim_info_dict["protocol_assignments"] == original_stim_info_dict["protocol_assignments"]


def test_parse_end_offline_mode_bytes__correctly_recreates_stim_info(mocker):
    protocol_assignments_dict = {
        GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx): randint(0, 1)
        for well_idx in range(24)
    }

    # make sure at least one well is unassigned
    well_to_unassign = choice(["A", "B", "C", "D"]) + str(randint(1, 6))
    protocol_assignments_dict[well_to_unassign] = None

    original_stim_info_dict = {
        "protocols": [
            {
                "stimulation_type": "V",
                "run_until_stopped": False,
                "subprotocols": [
                    {
                        "type": "loop",
                        "num_iterations": randint(1, 10),
                        "subprotocols": [
                            *[get_random_subprotocol() for _ in range(randint(1, 3))],
                            {
                                "type": "loop",
                                "num_iterations": randint(1, 10),
                                "subprotocols": [get_random_subprotocol() for _ in range(randint(1, 3))],
                            },
                            get_random_biphasic_pulse(),
                        ],
                    }
                ],
            },
            {
                "stimulation_type": "C",
                "run_until_stopped": True,
                "subprotocols": [
                    {
                        "type": "loop",
                        "num_iterations": randint(1, 10),
                        "subprotocols": [get_random_subprotocol() for _ in range(randint(1, 3))],
                    }
                ],
            },
        ],
        "protocol_assignments": protocol_assignments_dict,
    }
    num_protocols = len(original_stim_info_dict["protocols"])

    # this value is not actually used right now
    test_is_stim_running = random_bool()

    test_dormant_timestamp = random_timestamp()
    test_stim_start_timestamp = random_timestamp()
    test_stim_bytes = convert_stim_dict_to_bytes(copy.deepcopy(original_stim_info_dict))

    # only stim status is parsed out of protocol status at the moment
    test_protocol_statuses = [
        choice([StimulationStates.RUNNING, StimulationStates.INACTIVE]) for _ in range(NUM_WELLS)
    ]
    test_protocol_statuses_bytes = bytes([])
    for test_protocol_status in test_protocol_statuses:
        possible_stim_statuses = (
            (StimProtocolStatuses.ACTIVE, StimProtocolStatuses.NULL)
            if test_protocol_status == StimulationStates.RUNNING
            else (StimProtocolStatuses.FINISHED, StimProtocolStatuses.ERROR)
        )
        test_stim_status = choice(possible_stim_statuses)
        test_protocol_statuses_bytes += get_random_protocol_status(stim_status=test_stim_status)

    test_bytes = (
        test_dormant_timestamp.to_bytes(8, byteorder="little")
        + bytes([test_is_stim_running])
        + test_stim_start_timestamp.to_bytes(8, byteorder="little")
        + test_protocol_statuses_bytes
        + test_stim_bytes
    )

    offline_stim_info_dict = parse_end_offline_mode_bytes(test_bytes)

    actual_stim_info = offline_stim_info_dict.pop("stim_info")

    assert offline_stim_info_dict == {
        "system_dormant_timestamp": test_dormant_timestamp,
        "stim_active": test_is_stim_running,
        "last_stim_scheduled_start_timestamp": test_stim_start_timestamp,
        "stimulation_protocol_statuses": test_protocol_statuses[:num_protocols],
    }

    # TODO should eventually split this test out and just assert that it the correct function was used on the correct bytes
    for protocol_idx, (recreated_protocol, original_protocol) in enumerate(
        zip(actual_stim_info["protocols"], original_stim_info_dict["protocols"])
    ):
        recreated_protocol.pop("protocol_id")  # this is not needed in the recreated dict
        assert recreated_protocol == original_protocol, f"Protocol {protocol_idx}"

    for recreated_assignment, original_assignment in zip(
        actual_stim_info["protocol_assignments"].values(),
        original_stim_info_dict["protocol_assignments"].values(),
    ):
        if recreated_assignment is not None:
            assert recreated_assignment == chr(original_assignment + ord("A"))
