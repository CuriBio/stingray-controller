# -*- coding: utf-8 -*-
import asyncio
import copy
import json
import logging
from typing import Any
from typing import Awaitable
from typing import Callable

import websockets
from websockets import serve
from websockets.server import WebSocketServerProtocol

from ..constants import DEFAULT_SERVER_PORT_NUMBER
from ..constants import SYSTEM_STATUS_UUIDS
from ..utils.generic import wait_tasks_clean

logger = logging.getLogger(__name__)


# ------------- TODOs -------------
# - start adding in process monitor
#    - send msgs back and forth
#    - handle server initiated shutdown gracefully
#    - handle pm initiated shutdown gracefully
#    - more ?
# try out https://stackoverflow.com/questions/43418779/how-do-you-mark-a-group-of-python-methods-for-later-use-can-these-decorators to set up message handlers


def mark_handler(fn: Callable[..., Any]) -> Callable[..., Any]:
    fn._is_handler = True  # type: ignore
    return fn


def register_handlers(cls: Any) -> Any:
    cls._handlers = {
        ("_".join(fn_name.split("_")[1:])): fn
        for fn_name in dir(cls)
        if getattr(fn := getattr(cls, fn_name), "_is_handler", False)
    }
    return cls


@register_handlers
class Server:
    def __init__(
        self,
        system_state: dict[str, Any],
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        self._connected = False
        self._serve_task: asyncio.Task[None] | None = None

        self._system_state = system_state

        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue

        self.fe_initiated_shutdown = False

        # set by class decorator
        self._handlers: dict[str, Callable[[Any], Awaitable[dict[str, Any] | None]]]

    def get_system_state_copy(self) -> dict[str, Any]:
        return copy.deepcopy(self._system_state)

    # monitor_test,err

    async def run(self) -> None:
        logger.info("Starting WS Server")

        # self._exit_code = asyncio.Future()  # set this future to exit the server

        ws_server = await serve(self._run, "localhost", DEFAULT_SERVER_PORT_NUMBER)
        self._serve_task = asyncio.create_task(ws_server.serve_forever())
        try:
            await self._serve_task
        except asyncio.CancelledError:
            ws_server.close()
            await ws_server.wait_closed()
            raise
        finally:
            logger.info("WS server shut down")

    async def _run(self, websocket: WebSocketServerProtocol) -> None:
        if not self._serve_task:
            raise NotImplementedError("_serve_task must be not be None here")

        if self._connected:
            logger.exception("ERROR - SECOND CONNECTION MADE")
            # TODO figure out a good way to handle this
            # self._exit_code.set_result(1)
            return

        self._connected = True
        logger.info("CONNECTED")

        await self._handle_comm(websocket)

        self._connected = False
        logger.info("DISCONNECTED")

        self._serve_task.cancel()

    async def _handle_comm(self, websocket: WebSocketServerProtocol) -> None:
        producer = asyncio.create_task(self._producer(websocket))
        consumer = asyncio.create_task(self._consumer(websocket))
        await wait_tasks_clean({producer, consumer})

    async def _producer(self, websocket: WebSocketServerProtocol) -> None:
        while True:
            msg = await self._from_monitor_queue.get()

            # TODO
            # if msg["communication_type"] == "shutdown":
            #     break

            await websocket.send(json.dumps(msg))

    async def _consumer(self, websocket: WebSocketServerProtocol) -> None:
        while not self.fe_initiated_shutdown:
            try:
                msg = json.loads(await websocket.recv())
            except websockets.ConnectionClosed:
                break

            self._log_incoming_message(msg)

            command = msg.pop("command")

            handler_res = await self._handlers[command](self, **msg)

            res = {
                "communication_type": "command_response",
                "command": command,
            }

            if handler_res:
                res.update(handler_res)
                await websocket.send(json.dumps(res))

    def _log_incoming_message(self, msg: dict[str, Any]) -> None:
        # TODO
        # if "instrument_nickname" in msg:
        #     # Tanner (1/20/21): items in communication dict are used after this log message is generated, so need to create a copy of the dict when redacting info
        #     comm_copy = copy.deepcopy(msg)
        #     comm_copy["instrument_nickname"] = get_redacted_string(len(comm_copy["instrument_nickname"]))
        #     comm_str = str(comm_copy)
        # elif communication_type == "update_user_settings":
        #     comm_copy = copy.deepcopy(communication)
        #     comm_copy["content"]["user_password"] = get_redacted_string(4)
        #     comm_str = str(comm_copy)
        # elif communication_type == "mag_finding_analysis":
        #     comm_copy = copy.deepcopy(communication)
        #     comm_copy["recordings"] = [
        #         redact_sensitive_info_from_path(recording_path) for recording_path in comm_copy["recordings"]
        #     ]
        #     comm_str = str(comm_copy)
        # else:
        #     comm_str = str(communication)
        logger.info(f"Comm from UI: {msg}")  # TODO

    @mark_handler
    async def _test(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"test msg": msg}

    @mark_handler
    async def _monitor_test(self, msg: dict[str, Any]) -> None:
        await self._to_monitor_queue.put(msg)

    @mark_handler
    async def _shutdown(self) -> dict[str, Any]:
        self.fe_initiated_shutdown = True
        return {"msg": "beginning_shutdown"}

    @mark_handler
    async def _err(self) -> None:
        raise Exception()

    @mark_handler
    async def _get_system_status(self) -> dict[str, Any]:
        """Get the system status and other information.

        in_simulationMode is only accurate if ui_status_code is '009301eb-625c-4dc4-9e92-1a4d0762465f'

        instrument_serial_number and instrument_nickname are only accurate if ui_status_code is '8e24ef4d-2353-4e9d-aa32-4346126e73e3'
        """
        # TODO probably want to move this out and handle differently
        # shared_values_dict = _get_values_from_process_monitor()
        # current_software_version = get_current_software_version()
        # expected_software_version = server.system_state.get("expected_software_version", current_software_version)
        # if expected_software_version != current_software_version:
        #     return {
        #         "error": f"Versions of Electron and Flask EXEs do not match. Expected: {expected_software_version}"
        #     }

        # TODO
        system_state = self.get_system_state_copy()

        return {
            "ui_status_code": str(SYSTEM_STATUS_UUIDS[system_state["system_status"]]),
            "is_stimulating": _is_stimulating_on_any_well(system_state),
            # Tanner (7/1/20): this route may be called before process_monitor adds the following values to shared_values_dict, so default values are needed
            "in_simulationMode": system_state.get("in_simulationMode", False),
            "instrument_serial_number": system_state.get("instrument_serial_number", ""),
            "instrument_nickname": system_state.get("instrument_nickname", ""),
        }


# TODO
def _is_stimulating_on_any_well(system_state: dict[str, Any]) -> bool:
    return any(system_state["stimulation_running"])
