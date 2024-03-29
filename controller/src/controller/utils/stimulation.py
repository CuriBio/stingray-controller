# -*- coding: utf-8 -*-
"""Utility functions for stimulation."""

import copy
from typing import Any

from ..constants import STIM_MAX_ABSOLUTE_CURRENT_MICROAMPS
from ..constants import STIM_MAX_ABSOLUTE_VOLTAGE_MILLIVOLTS
from ..constants import STIM_MAX_CHUNKED_SUBPROTOCOL_DUR_MICROSECONDS
from ..constants import STIM_MAX_DUTY_CYCLE_DURATION_MICROSECONDS
from ..constants import STIM_MAX_DUTY_CYCLE_PERCENTAGE
from ..constants import STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS
from ..constants import STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS
from ..constants import VALID_SUBPROTOCOL_TYPES
from ..exceptions import WebsocketCommandError


SUBPROTOCOL_DUTY_CYCLE_DUR_COMPONENTS = frozenset(
    ["phase_one_duration", "interphase_interval", "phase_two_duration"]
)


def get_pulse_duty_cycle_dur_us(subprotocol: dict[str, str | int]) -> int:
    return sum(subprotocol.get(comp, 0) for comp in SUBPROTOCOL_DUTY_CYCLE_DUR_COMPONENTS)  # type: ignore


def get_pulse_dur_us(subprotocol: dict[str, str | int]) -> int:
    return get_pulse_duty_cycle_dur_us(subprotocol) + subprotocol["postphase_interval"]  # type: ignore


def get_subprotocol_dur_us(subprotocol: dict[str, str | int]) -> int:
    duration = (
        subprotocol["duration"]
        if subprotocol["type"] == "delay"
        else get_pulse_dur_us(subprotocol) * subprotocol["num_cycles"]
    )
    return duration  # type: ignore


def chunk_subprotocol(
    original_subprotocol: dict[str, Any]
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    # copy so the original subprotocol dict isn't modified
    original_subprotocol = copy.deepcopy(original_subprotocol)
    original_subprotocol_dur_us = get_subprotocol_dur_us(original_subprotocol)

    if (
        original_subprotocol["type"] == "delay"
        or original_subprotocol_dur_us <= STIM_MAX_CHUNKED_SUBPROTOCOL_DUR_MICROSECONDS
    ):
        return None, original_subprotocol

    original_num_cycles = original_subprotocol["num_cycles"]

    pulse_dur_us = get_pulse_dur_us(original_subprotocol)
    max_num_cycles_in_loop = STIM_MAX_CHUNKED_SUBPROTOCOL_DUR_MICROSECONDS // pulse_dur_us
    looped_subprotocol = {**original_subprotocol, "num_cycles": max_num_cycles_in_loop}
    num_loop_iterations = original_subprotocol_dur_us // get_subprotocol_dur_us(looped_subprotocol)  # type: ignore

    loop_chunk = {"type": "loop", "num_iterations": num_loop_iterations, "subprotocols": [looped_subprotocol]}

    leftover_chunk = None

    if num_leftover_cycles := original_num_cycles - (looped_subprotocol["num_cycles"] * num_loop_iterations):
        leftover_chunk = {**original_subprotocol, "num_cycles": num_leftover_cycles}

        if get_subprotocol_dur_us(leftover_chunk) < STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS:
            # if there is only 1 loop iteration, then just return the original subprotocol
            if loop_chunk["num_iterations"] == 1:
                return None, original_subprotocol
            # otherwise, combine leftover chunk with the final loop iteration
            leftover_chunk["num_cycles"] += looped_subprotocol["num_cycles"]
            loop_chunk["num_iterations"] -= 1  # type: ignore

    return loop_chunk, leftover_chunk


def chunk_stim_nodes(
    original_stim_nodes: list[dict[str, Any]], curr_original_idx: int = 0, curr_chunked_idx: int = 0
) -> tuple[list[dict[str, Any]], dict[int, int], list[int], int, int]:
    new_stim_nodes = []

    chunked_idx_to_original_idx = {}
    original_idx_counts = []

    for stim_node in original_stim_nodes:
        if stim_node["type"] == "loop":
            inner_nodes, inner_mapping, inner_counts, curr_original_idx, curr_chunked_idx = chunk_stim_nodes(
                stim_node["subprotocols"], curr_original_idx, curr_chunked_idx
            )
            new_stim_nodes.append({**stim_node, "subprotocols": inner_nodes})
            chunked_idx_to_original_idx.update(inner_mapping)
            original_idx_counts.extend(inner_counts)
        else:
            original_idx_count = 0

            for chunk in chunk_subprotocol(stim_node):
                if not chunk:
                    continue

                chunked_idx_to_original_idx[curr_chunked_idx] = curr_original_idx
                # for loop chunk, need to count the num iterations, leftover chunk is always 1
                original_idx_count += chunk.get("num_iterations", 1)
                new_stim_nodes.append(chunk)

                curr_chunked_idx += 1

            original_idx_counts.append(original_idx_count)

            curr_original_idx += 1

    return (
        new_stim_nodes,
        chunked_idx_to_original_idx,
        original_idx_counts,
        curr_original_idx,
        curr_chunked_idx,
    )


def chunk_protocols_in_stim_info(
    stim_info: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, dict[int, int]], dict[str, tuple[int, ...]]]:
    # copying so the original dict passed in does not get modified
    chunked_stim_info = copy.deepcopy(stim_info)

    subprotocol_idx_mappings = {}
    max_subprotocol_idx_counts = {}

    for protocol in chunked_stim_info["protocols"]:
        new_subprotocols, chunked_idx_to_original_idx, original_idx_counts, *_ = chunk_stim_nodes(
            protocol["subprotocols"]
        )

        # FW requires top level to be a single loop
        protocol["subprotocols"] = [{"type": "loop", "num_iterations": 1, "subprotocols": new_subprotocols}]

        protocol_id = protocol["protocol_id"]
        subprotocol_idx_mappings[protocol_id] = chunked_idx_to_original_idx
        max_subprotocol_idx_counts[protocol_id] = tuple(original_idx_counts)

    return chunked_stim_info, subprotocol_idx_mappings, max_subprotocol_idx_counts


def _check_subprotocol_type(subprotocol: dict[str, Any], protocol_id: int, idx: int) -> Any:
    subprotocol["type"] = subprotocol_type = subprotocol["type"].lower()
    # validate subprotocol type
    if subprotocol_type not in VALID_SUBPROTOCOL_TYPES:
        raise WebsocketCommandError(
            f"Protocol {protocol_id}, Subprotocol {idx}, Invalid subprotocol type: {subprotocol_type}"
        )

    return subprotocol_type


def validate_stim_subprotocol(
    subprotocol: dict[str, Any], stim_type: str, protocol_id: int, idx: int
) -> None:
    subprotocol_type = _check_subprotocol_type(subprotocol, protocol_id, idx)

    if subprotocol_type == "loop":
        for nested_subprotocol in subprotocol["subprotocols"]:
            validate_stim_subprotocol(nested_subprotocol, stim_type, protocol_id, idx)
    else:
        # validate subprotocol components
        if subprotocol_type == "delay":
            # make sure this value is not a float
            subprotocol["duration"] = int(subprotocol["duration"])
            total_subprotocol_duration_us = subprotocol["duration"]
        else:  # monophasic and biphasic
            max_abs_charge = (
                STIM_MAX_ABSOLUTE_VOLTAGE_MILLIVOLTS
                if stim_type == "V"
                else STIM_MAX_ABSOLUTE_CURRENT_MICROAMPS
            )

            subprotocol_component_validators = {
                "phase_one_duration": lambda n: n > 0,
                "phase_one_charge": lambda n: abs(n) <= max_abs_charge,
                "postphase_interval": lambda n: n >= 0,
            }
            if subprotocol_type == "biphasic":
                subprotocol_component_validators.update(
                    {
                        "phase_two_duration": lambda n: n > 0,
                        "phase_two_charge": lambda n: abs(n) <= max_abs_charge,
                        "interphase_interval": lambda n: n >= 0,
                    }
                )
            for component_name, validator in subprotocol_component_validators.items():
                if not validator(component_value := subprotocol[component_name]):  # type: ignore
                    component_name = component_name.replace("_", " ")
                    raise WebsocketCommandError(
                        f"Protocol {protocol_id}, Subprotocol {idx}, Invalid {component_name}: {component_value}"
                    )

            duty_cycle_dur_us = get_pulse_duty_cycle_dur_us(subprotocol)

            # make sure duty cycle duration is not too long
            if duty_cycle_dur_us > STIM_MAX_DUTY_CYCLE_DURATION_MICROSECONDS:
                raise WebsocketCommandError(
                    f"Protocol {protocol_id}, Subprotocol {idx}, Duty cycle duration too long"
                )

            total_subprotocol_duration_us = (
                duty_cycle_dur_us + subprotocol["postphase_interval"]
            ) * subprotocol["num_cycles"]

            # make sure duty cycle percentage is not too high
            if duty_cycle_dur_us > get_pulse_dur_us(subprotocol) * STIM_MAX_DUTY_CYCLE_PERCENTAGE:
                raise WebsocketCommandError(
                    f"Protocol {protocol_id}, Subprotocol {idx}, Duty cycle exceeds {int(STIM_MAX_DUTY_CYCLE_PERCENTAGE * 100)}%"
                )

        # make sure subprotocol duration is within the acceptable limits
        if total_subprotocol_duration_us < STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS:
            raise WebsocketCommandError(
                f"Protocol {protocol_id}, Subprotocol {idx}, Subprotocol duration not long enough"
            )
        if total_subprotocol_duration_us > STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS:
            raise WebsocketCommandError(
                f"Protocol {protocol_id}, Subprotocol {idx}, Subprotocol duration too long"
            )
