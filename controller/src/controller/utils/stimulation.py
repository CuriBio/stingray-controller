# -*- coding: utf-8 -*-
"""Utility functions for stimulation."""

import copy
from typing import Any

from ..constants import STIM_MAX_CHUNKED_SUBPROTOCOL_DUR_MICROSECONDS
from ..constants import STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS

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


def chunk_protocols_in_stim_info(
    stim_info: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, dict[int, int]], dict[str, tuple[int, ...]]]:
    # copying so the original dict passed in does not get modified
    chunked_stim_info = copy.deepcopy(stim_info)

    subprotocol_idx_mappings = {}
    max_subprotocol_idx_counts = {}

    for protocol in chunked_stim_info["protocols"]:
        curr_chunked_idx = 0

        chunked_idx_to_original_idx = {}
        original_idx_counts = []
        new_subprotocols = []

        for original_idx, subprotocol in enumerate(protocol["subprotocols"]):
            original_idx_count = 0

            for chunk in chunk_subprotocol(subprotocol):
                if not chunk:
                    continue

                chunked_idx_to_original_idx[curr_chunked_idx] = original_idx
                # for loop chunk, need to count the num iterations, leftover chunk is always 1
                original_idx_count += chunk.get("num_iterations", 1)
                new_subprotocols.append(chunk)

                curr_chunked_idx += 1

            original_idx_counts.append(original_idx_count)

        # FW requires top level to be a single loop
        protocol["subprotocols"] = [{"type": "loop", "num_iterations": 1, "subprotocols": new_subprotocols}]

        protocol_id = protocol["protocol_id"]
        subprotocol_idx_mappings[protocol_id] = chunked_idx_to_original_idx
        max_subprotocol_idx_counts[protocol_id] = tuple(original_idx_counts)

    return chunked_stim_info, subprotocol_idx_mappings, max_subprotocol_idx_counts
