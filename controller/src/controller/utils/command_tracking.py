# -*- coding: utf-8 -*-
import asyncio
from collections import defaultdict
from collections import deque
from typing import Any

from ..constants import SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS


class _Command:
    def __init__(self, info: dict[str, Any], timeout_info: asyncio.Future[dict[str, Any]]) -> None:
        self.info = info

        self._timeout_info = timeout_info
        self._timer = asyncio.create_task(self._start_timer())

    async def _start_timer(self) -> None:
        try:
            await asyncio.sleep(SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS)
        except asyncio.CancelledError:
            return
        else:
            if not self._timeout_info.done() and not self._timeout_info.cancelled():
                self._timeout_info.set_result(self.info)

    async def complete(self) -> None:
        self._timer.cancel()
        await self._timer
        # TODO is this necessary?
        # try:
        #     await self._timer
        # except asyncio.CancelledError:
        #     pass


class CommandTracker:
    def __init__(self) -> None:
        self._command_mapping: dict[int, deque[_Command]] = defaultdict(deque)

        self._timeout_info: asyncio.Future[dict[str, Any]] = asyncio.Future()

    async def add(self, packet_type: int, command_info: dict[str, Any]) -> None:
        self._command_mapping[packet_type].append(_Command(command_info, self._timeout_info))
        # make sure the command's timer task begins
        await asyncio.sleep(0)

    async def pop(self, packet_type: int) -> dict[str, Any]:
        commands_for_packet_type = self._command_mapping[packet_type]

        try:
            command = commands_for_packet_type.popleft()
        except IndexError as e:
            raise ValueError(f"No commands of packet type: {packet_type}") from e

        await command.complete()

        return command.info

    async def wait_for_expired_command(self) -> dict[str, Any]:
        try:
            return await self._timeout_info
        except asyncio.CancelledError:
            raise
        finally:
            pass  # TODO complete all commands?

    # def __bool__(self) -> bool:
    #     return bool(self._command_mapping)
