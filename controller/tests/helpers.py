# -*- coding: utf-8 -*-
import math
from random import choice
from random import randint

from controller.constants import GENERIC_24_WELL_DEFINITION
from controller.constants import MICRO_TO_BASE_CONVERSION
from controller.constants import MICROS_PER_MILLI
from controller.constants import NUM_WELLS
from controller.constants import SERIAL_COMM_MAX_TIMESTAMP_VALUE
from controller.constants import STIM_MAX_DUTY_CYCLE_DURATION_MICROSECONDS
from controller.constants import STIM_MAX_DUTY_CYCLE_PERCENTAGE
from controller.constants import STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS
from controller.constants import STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS
from controller.constants import STIM_PULSE_BYTES_LEN
from controller.constants import VALID_STIMULATION_TYPES
from controller.utils.serial_comm import convert_subprotocol_pulse_bytes_to_dict
from controller.utils.serial_comm import SUBPROTOCOL_BIPHASIC_ONLY_COMPONENTS
from controller.utils.stimulation import get_pulse_duty_cycle_dur_us
from immutabledict import immutabledict

TEST_SERIAL_NUMBER = "MA2023001000"
TEST_PLATE_BARCODE = "ML22001000-2"
TEST_STIM_BARCODE = "MS22001000-2"
TEST_EVENT_INFO = immutabledict(
    {
        "prev_main_status_update_timestamp": 1,
        "prev_channel_status_update_timestamp": 2,
        "start_of_prev_mag_data_stream_timestamp": 3,
        "start_of_prev_stim_timestamp": 4,
        "prev_handshake_received_timestamp": 5,
        "prev_system_going_dormant_timestamp": 6,
        "mag_data_stream_active": False,
        "stim_active": False,
        "pc_connection_status": 1,
        "prev_barcode_scanned": TEST_PLATE_BARCODE,
    }
)
TEST_INITIAL_MAGNET_FINDING_PARAMS = immutabledict({"X": 0, "Y": 2, "Z": -5, "REMN": 1200})

MAX_POSTPHASE_INTERVAL_DUR_MICROSECONDS = 2**32 - 1  # max uint32 value

# Tanner (/17/23): arbitrarily deciding to use 10ms as the min pulse duration
MIN_PULSE_DUR_MICROSECONDS = 10 * MICROS_PER_MILLI
MAX_PULSE_DUR_MICROSECONDS = (
    STIM_MAX_DUTY_CYCLE_DURATION_MICROSECONDS + MAX_POSTPHASE_INTERVAL_DUR_MICROSECONDS
)


def random_semver():
    return f"{randint(0,1000)}.{randint(0,1000)}.{randint(0,1000)}"


def random_bool():
    return choice([True, False])


def random_well_idx():
    return randint(0, NUM_WELLS - 1)


def random_serial_comm_timestamp():
    return randint(0, SERIAL_COMM_MAX_TIMESTAMP_VALUE)


def random_stim_type():
    return choice(list(VALID_STIMULATION_TYPES))


def get_random_subprotocol(*, allow_loop=False, total_subprotocol_dur_us=None):
    subprotocol_fns = [get_random_stim_delay, get_random_stim_pulse]

    if allow_loop:
        if total_subprotocol_dur_us is not None:
            raise ValueError("Cannot supply total_subprotocol_dur_us if allowing loops")
        subprotocol_fns.append(get_random_stim_loop)

        subprotocol = choice(subprotocol_fns)()
    else:
        subprotocol = choice(subprotocol_fns)(total_subprotocol_dur_us=total_subprotocol_dur_us)

    return subprotocol


def get_random_stim_delay(total_subprotocol_dur_us=None):
    duration_us = total_subprotocol_dur_us
    if duration_us is None:
        # make sure this is a whole number of ms
        duration_ms = randint(
            STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS // MICROS_PER_MILLI,
            STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS // MICROS_PER_MILLI,
        )
        # convert to µs
        duration_us = duration_ms * MICROS_PER_MILLI
    elif not (
        STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS < duration_us < STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS
        or duration_us % MICROS_PER_MILLI != 0
    ):
        raise ValueError(f"Invalid delay duration: {duration_us}")
    return {"type": "delay", "duration": duration_us}


def get_random_stim_pulse(*, pulse_type=None, total_subprotocol_dur_us=None, freq=None, num_cycles=None):
    # validate or randomize pulse type
    if pulse_type is not None:
        if pulse_type not in ("monophasic", "biphasic"):
            raise ValueError(f"Invalid pulse type: {pulse_type}")
        is_biphasic = pulse_type == "biphasic"
    else:
        is_biphasic = random_bool()
        pulse_type = "biphasic" if is_biphasic else "monophasic"

    # validate any params with provided values individually
    if total_subprotocol_dur_us is not None:
        if total_subprotocol_dur_us < STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS:
            raise ValueError(
                f"total_subprotocol_dur_us: {total_subprotocol_dur_us} must be >= {STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS}"
            )
        if total_subprotocol_dur_us > STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS:
            raise ValueError(
                f"total_subprotocol_dur_us: {total_subprotocol_dur_us} must be <= {STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS}"
            )
    if num_cycles is not None:
        if num_cycles <= 0:
            raise ValueError("num_cycles must be > 0")
        if not isinstance(num_cycles, int):
            raise ValueError("num_cycles must be an integer")
    if freq is not None and not (0 < freq < 100):
        raise ValueError("freq must be > 0 and < 100")

    # don't allow all 3 params to be given at once since the 3rd can be implied from the other 2
    if total_subprotocol_dur_us and num_cycles and freq:
        raise ValueError("Can only provide 2/3 of total_subprotocol_dur_us, num_cycles, and freq at a time")

    # validate params together and gerenate random values for those not given
    if total_subprotocol_dur_us is not None:
        if num_cycles:
            # calculate and validate pulse dur
            pulse_dur_us = total_subprotocol_dur_us / num_cycles
            if not pulse_dur_us.is_integer():
                raise ValueError(
                    f"total_subprotocol_dur_us: {total_subprotocol_dur_us} and num_cycles: {num_cycles} are"
                    f" incompatible, they create a non-int pulse duration: {pulse_dur_us}"
                )
            pulse_dur_us = int(pulse_dur_us)
            if not (MIN_PULSE_DUR_MICROSECONDS <= pulse_dur_us <= MAX_PULSE_DUR_MICROSECONDS):
                raise ValueError(
                    f"total_subprotocol_dur_us: {total_subprotocol_dur_us} and num_cycles: {num_cycles} are"
                    f" incompatible, they create a pulse duration: {pulse_dur_us} µs which is not in the"
                    f" range [{MIN_PULSE_DUR_MICROSECONDS}, {MAX_PULSE_DUR_MICROSECONDS}]"
                )
        elif freq:
            # calculate and validate num cycles
            pulse_dur_us = MICRO_TO_BASE_CONVERSION // freq
            num_cycles = total_subprotocol_dur_us / pulse_dur_us
            if not num_cycles.is_integer():
                raise ValueError(
                    f"total_subprotocol_dur_us: {total_subprotocol_dur_us} and freq: {freq} are incompatible,"
                    f" they create a non-int number of cycles: {num_cycles}"
                )
            num_cycles = int(num_cycles)
        else:
            # create random pulse dur and num cycles

            def is_valid_pulse_dur(dur_us):
                return (
                    total_subprotocol_dur_us % dur_us == 0
                    and MIN_PULSE_DUR_MICROSECONDS < dur_us < MAX_PULSE_DUR_MICROSECONDS
                )

            num_cycles, pulse_dur_us = choice(
                [
                    (n, dur_us)
                    for n in range(1, int(total_subprotocol_dur_us**0.5) + 1)
                    if is_valid_pulse_dur(dur_us := total_subprotocol_dur_us // n)
                ]
            )
    elif num_cycles:
        if freq:
            # calculate pulse dur, calculate and validate total_subprotocol_dur_us
            pulse_dur_us = MICRO_TO_BASE_CONVERSION // freq
            total_subprotocol_dur_us = num_cycles * pulse_dur_us
            if not (
                STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS
                < total_subprotocol_dur_us
                < STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS
            ):
                raise ValueError(
                    f"num_cycles: {num_cycles} and freq: {freq} are incompatible, they create a"
                    f" total_subprotocol_dur_us: {total_subprotocol_dur_us} which is not in the range"
                    f" [{STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS}, {STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS}]"
                )
        else:
            # calculate random pulse dur
            max_pulse_dur = min(
                math.floor(STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS / num_cycles),
                MAX_PULSE_DUR_MICROSECONDS,
            )
            min_pulse_dur = max(
                math.ceil(STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS / num_cycles), MIN_PULSE_DUR_MICROSECONDS
            )
            pulse_dur_us = randint(min_pulse_dur, max_pulse_dur)
    else:
        if freq:
            pulse_dur_us = MICRO_TO_BASE_CONVERSION // freq
        else:
            # create random pulse dur
            pulse_dur_us = randint(MIN_PULSE_DUR_MICROSECONDS, MAX_PULSE_DUR_MICROSECONDS)
        # create random num cycles
        num_cycles = _get_rand_num_cycles_from_pulse_dur(pulse_dur_us)

    # set up randomizer for duty cycle components
    all_pulse_components = {"phase_one_duration", "phase_one_charge", "postphase_interval"}
    if is_biphasic:
        all_pulse_components |= SUBPROTOCOL_BIPHASIC_ONLY_COMPONENTS

    charge_components = {comp for comp in all_pulse_components if "charge" in comp}
    duty_cycle_dur_comps = all_pulse_components - charge_components - {"postphase_interval"}

    min_dur_per_duty_cycle_comp = max(
        1,
        (pulse_dur_us - MAX_POSTPHASE_INTERVAL_DUR_MICROSECONDS) // len(duty_cycle_dur_comps),
    )
    max_dur_per_duty_cycle_comp = min(
        math.floor(pulse_dur_us * STIM_MAX_DUTY_CYCLE_PERCENTAGE), STIM_MAX_DUTY_CYCLE_DURATION_MICROSECONDS
    ) // len(duty_cycle_dur_comps)

    def _rand_dur_for_duty_cycle_comp():
        return randint(min_dur_per_duty_cycle_comp, max_dur_per_duty_cycle_comp)

    # create pulse dict
    pulse = {"type": pulse_type, "num_cycles": num_cycles}
    # add duration components
    pulse.update({comp: _rand_dur_for_duty_cycle_comp() for comp in duty_cycle_dur_comps})
    pulse["postphase_interval"] = pulse_dur_us - get_pulse_duty_cycle_dur_us(pulse)
    # add charge components
    pulse.update({comp: randint(1, 100) * 10 for comp in charge_components})

    return pulse


def _get_rand_num_cycles_from_pulse_dur(pulse_dur_us):
    max_num_cycles = math.floor(STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS / pulse_dur_us)
    # make sure there is at least 1 cycle
    min_num_cycles = max(1, math.floor(STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS / pulse_dur_us))
    num_cycles = randint(min_num_cycles, max_num_cycles)
    return num_cycles


def get_random_monophasic_pulse(**kwargs):
    return get_random_stim_pulse(pulse_type="monophasic", **kwargs)


def get_random_biphasic_pulse(**kwargs):
    return get_random_stim_pulse(pulse_type="biphasic", **kwargs)


def get_random_stim_loop():
    raise NotImplementedError("TODO")


def get_random_stim_info():
    protocol_ids = (None, "A", "B", "C", "D")
    stim_info = {
        "protocols": [
            {
                "protocol_id": pid,
                "stimulation_type": random_stim_type(),
                "run_until_stopped": choice([True, False]),
                "subprotocols": [
                    {
                        "type": "loop",
                        "num_iterations": 1,
                        "subprotocols": [
                            choice(
                                [
                                    get_random_stim_pulse(),
                                    get_random_stim_delay(50 * MICRO_TO_BASE_CONVERSION),
                                ]
                            )
                            for _ in range(randint(1, 2))
                        ],
                    },
                ],
            }
            for pid in protocol_ids[1:]
        ],
        "protocol_assignments": {
            GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx): choice(protocol_ids)
            for well_idx in range(24)
        },
    }

    if all(protocol_id is None for protocol_id in stim_info["protocol_assignments"].values()):
        # make sure at least one well has a protocol assigned
        stim_info["protocol_assignments"]["A1"] = "A"
    elif all(protocol_id is not None for protocol_id in stim_info["protocol_assignments"].values()):
        # make sure at least one well does not have a protocol assigned
        stim_info["protocol_assignments"]["A1"] = None

    return stim_info


def assert_subprotocol_pulse_bytes_are_expected(actual, expected, include_idx=False, err_msg=None):
    if len(expected) != STIM_PULSE_BYTES_LEN:
        raise ValueError(f"'expected' has incorrect len: {len(expected)}, should be: {STIM_PULSE_BYTES_LEN}")

    assert len(actual) == STIM_PULSE_BYTES_LEN, "Incorrect number of bytes"

    actual_dict = convert_subprotocol_pulse_bytes_to_dict(actual)
    expected_dict = convert_subprotocol_pulse_bytes_to_dict(expected)

    if err_msg:
        assert actual_dict == expected_dict, err_msg
    else:
        assert actual_dict == expected_dict


def assert_subprotocol_node_bytes_are_expected(actual, expected):
    assert len(actual) == len(expected), "Incorrect number of bytes"

    assert actual[0] == expected[0], "Incorrect stim node type"

    is_loop = bool(expected[0])

    if is_loop:
        assert actual[1] == expected[1], "Incorrect num stim nodes"

        actual_num_iterations = int.from_bytes(actual[2:6], byteorder="little")
        expected_num_iterations = int.from_bytes(expected[2:6], byteorder="little")
        assert actual_num_iterations == expected_num_iterations, "Incorrect number of iterations"

        # this will only work with single level loops right now
        num_subprotocols = len(expected[6:]) // STIM_PULSE_BYTES_LEN
        for subprotocol_idx in range(num_subprotocols):
            start_idx = 6 + (subprotocol_idx * (STIM_PULSE_BYTES_LEN + 1))
            stop_idx = start_idx + STIM_PULSE_BYTES_LEN

            assert actual[start_idx - 1] == expected[start_idx - 1], "Invalid subprotocol idx"
            assert_subprotocol_pulse_bytes_are_expected(
                actual[start_idx:stop_idx],
                expected[start_idx:stop_idx],
                err_msg=f"subprotocol_idx: {subprotocol_idx}",
            )
    else:
        assert actual[1] == expected[1], "Invalid subprotocol idx"
        assert_subprotocol_pulse_bytes_are_expected(actual[2:], expected[2:])


def compare_exceptions(e1, e2):
    # from https://stackoverflow.com/questions/15844131/comparing-exception-objects-in-python
    return type(e1) is type(e2) and e1.args == e2.args
