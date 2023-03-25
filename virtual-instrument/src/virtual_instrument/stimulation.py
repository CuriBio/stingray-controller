# -*- coding: utf-8 -*-
"""Utility functions for stimulation."""

import copy
from typing import Any


class StimulationProtocolManager:
    def __init__(
        self, subprotocols: list[dict[str, Any]], num_iterations: int | None = None, start_idx: int = 0
    ) -> None:
        if num_iterations is not None and num_iterations < 1:  # pragma: no cover
            raise ValueError("num_iterations must be >= 1")

        self._subprotocols = copy.deepcopy(subprotocols)
        self._num_iterations = num_iterations
        self._start_idx = start_idx

        self._subprotocol_idx: int
        self._node_idx: int
        self._num_iterations_remaining: int | None
        self._loop: StimulationProtocolManager | None
        self._reset()

    def _reset(self) -> None:
        self._reset_idxs(hard_reset=True)
        # reset the number of iteratioms remaining if a limit was given
        if self._num_iterations:
            self._num_iterations_remaining = self._num_iterations - 1
        else:
            self._num_iterations_remaining = None
        self._loop = None

    def complete(self) -> bool:
        # if not on the final node or still have more iterations, then not complete
        if self._node_idx < len(self._subprotocols) - 1 or self._num_iterations_remaining:
            return False
        # if on the final node but a loop is present, need to check if the loop is complete
        if self._loop:
            return self._loop.complete()
        # if on the final node and no loop is present, then the protocol is complete
        return True

    def current(self) -> dict[str, Any]:
        # if there is a loop, the current subprotocol must be retrieved from it the current node at this level is a loop
        if self._loop:
            return self._loop.current()
        # otherwise, return the current node stored at this level since it is not a loop
        return self._subprotocols[self._node_idx]

    # TODO update this now that the subprotocol idx is included in the subprotocol?
    def idx(self) -> int:
        # if there is a loop, the current idx must be retrieved from it as it is invalid at this level
        if self._loop:
            return self._loop.idx()
        # otherwise, return the current idx stored at this level
        return self._subprotocol_idx

    def advance(self) -> dict[str, Any]:
        # if there is a loop, advance to the next subprotocol node within the loop first
        if self._loop:
            try:
                return self._loop.advance()
            except StopIteration:
                # the loop completed, so update the subprotocol idx at this level and then clear the loop
                self._subprotocol_idx = self._loop.idx()
                self._loop = None

        # advance to the next subprotocol node at this level
        self._increment_idxs(1)
        if self._node_idx >= len(self._subprotocols):
            if self._num_iterations_remaining is not None:
                if self._num_iterations_remaining <= 0:
                    self._increment_idxs(-1)
                    raise StopIteration
                self._num_iterations_remaining -= 1
            self._reset_idxs(hard_reset=False)

        subprotocol = self.current()

        # if the next subprotocol node is a loop, setup the loop and advance through it
        if subprotocol["type"] == "loop":
            self._loop = StimulationProtocolManager(
                subprotocol["subprotocols"], subprotocol["num_iterations"], self.idx()
            )
            return self._loop.advance()
        # otherwise, return this subprotocol
        return subprotocol

    def _increment_idxs(self, amount: int) -> None:
        self._node_idx += amount
        self._subprotocol_idx += amount

    def _reset_idxs(self, hard_reset: bool) -> None:
        self._subprotocol_idx = self._start_idx - int(hard_reset)
        self._node_idx = 0 - int(hard_reset)
