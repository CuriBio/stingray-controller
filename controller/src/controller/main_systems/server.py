# -*- coding: utf-8 -*-
import asyncio
import copy
import functools
import json
import logging
from typing import Any
from typing import Awaitable
from typing import Callable

from semver import VersionInfo
import websockets
from websockets import serve
from websockets.server import WebSocketServerProtocol

from ..constants import DEFAULT_SERVER_PORT_NUMBER
from ..constants import GENERIC_24_WELL_DEFINITION
from ..constants import NUM_WELLS
from ..constants import StimulationStates
from ..constants import StimulatorCircuitStatuses
from ..constants import SystemStatuses
from ..constants import VALID_CREDENTIAL_TYPES
from ..constants import VALID_STIMULATION_TYPES
from ..exceptions import WebsocketCommandError
from ..utils.aio import clean_up_tasks
from ..utils.aio import wait_tasks_clean
from ..utils.generic import handle_system_error
from ..utils.logging import get_redacted_string
from ..utils.state_management import ReadOnlyDict
from ..utils.stimulation import validate_stim_subprotocol

logger = logging.getLogger(__name__)

ERROR_MSG = "IN SERVER"

COMMANDS_ALLOWED_IN_OFFLINE_MODE = ("set_offline_state", "shutdown")


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
    # set by class decorator
    _handlers: dict[str, Callable[["Server", dict[str, Any]], Awaitable[dict[str, Any] | None]]]

    def __init__(
        self,
        get_system_state_ro: Callable[..., ReadOnlyDict],
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        self._serve_task: asyncio.Task[None] | None = None
        # this is only used in _report_system_error
        self._websocket: WebSocketServerProtocol | None = None

        # TODO consider just passing in the read only version of the dict instead
        self._get_system_state_ro = get_system_state_ro

        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue

        self._ui_connection_made = asyncio.Event()
        self.user_initiated_shutdown = False

    async def run(
        self,
        system_error_future: asyncio.Future[tuple[int, dict[str, str]]],
        server_running_event: asyncio.Event,
    ) -> None:
        logger.info("Starting Server")

        _run = functools.partial(self._run, system_error_future=system_error_future)

        ws_server = await serve(_run, "localhost", DEFAULT_SERVER_PORT_NUMBER)
        self._serve_task = asyncio.create_task(ws_server.serve_forever())
        logger.info("WS Server running")

        server_running_event.set()

        try:
            await asyncio.shield(self._serve_task)
        except asyncio.CancelledError:
            # if _serve_task is cancelled, assume the error has already been reported
            if not self._serve_task.cancelled():
                logger.info("Server cancelled")
                await self._report_system_error(system_error_future)

            ws_server.close()
            await ws_server.wait_closed()

            raise
        except BaseException:
            # Tanner (4/10/23): don't expected this to be reached, but logging just in case
            logger.exception(ERROR_MSG)
        finally:
            await clean_up_tasks({self._serve_task}, ERROR_MSG)
            logger.info("Server shut down")

    async def _run(
        self,
        websocket: WebSocketServerProtocol,
        system_error_future: asyncio.Future[tuple[int, dict[str, str]]],
    ) -> None:
        if not self._serve_task:
            raise NotImplementedError("_serve_task must be not be None here")

        if self._websocket:
            logger.error("SECOND CONNECTION MADE")
            # TODO figure out a good way to handle this
            return

        self._ui_connection_made.set()
        self._websocket = websocket
        logger.info("UI has connected")

        try:
            await self._handle_comm(websocket)
        except asyncio.CancelledError:
            pass
        except BaseException as e:
            logger.exception(ERROR_MSG)
            handle_system_error(e, system_error_future)
            await self._report_system_error(system_error_future)

        self._serve_task.cancel()

    async def _report_system_error(
        self, system_error_future: asyncio.Future[tuple[int, dict[str, str]]]
    ) -> None:
        if not system_error_future.done():
            logger.info("No errors to report to UI")
            return

        # TODO use a dataclass for this instead of a tuple
        error_code, extra_info = system_error_future.result()

        logger.info(f"Attempting to report system error code {error_code} to UI")

        if not self._ui_connection_made.is_set():
            # if the error occured before the UI even connected, wait a little for it to connect
            wait_time = 3
            try:
                logger.info(f"Waiting up to {wait_time} seconds for UI to connect")
                await asyncio.wait_for(self._ui_connection_made.wait(), wait_time)
            except asyncio.TimeoutError:
                logger.error("UI never connected")
                return

        if self._websocket:
            logger.info(f"Sending system error code {error_code} to UI")
            msg = {"communication_type": "error", "error_code": error_code, **extra_info}
            try:
                await self._websocket.send(json.dumps(msg))
            except BaseException:
                logger.exception("Failed to send error message to UI")
        else:
            logger.error("UI has already disconnected, cannot send error message")

    async def _handle_comm(self, websocket: WebSocketServerProtocol) -> None:
        producer = asyncio.create_task(self._producer(websocket))
        consumer = asyncio.create_task(self._consumer(websocket))
        await wait_tasks_clean({producer, consumer}, error_msg=ERROR_MSG)

    async def _producer(self, websocket: WebSocketServerProtocol) -> None:
        while True:
            msg = json.dumps(await self._from_monitor_queue.get())
            try:
                await websocket.send(msg)
            except websockets.ConnectionClosed:
                logger.error(f"Failed to send message to UI: {msg}")
                return

    async def _consumer(self, websocket: WebSocketServerProtocol) -> None:
        while not self.user_initiated_shutdown:
            try:
                msg = json.loads(await websocket.recv())
            except websockets.ConnectionClosed:
                return

            self._log_incoming_message(msg)

            command = msg["command"]

            if (
                _is_in_offline_mode(self._get_system_state_ro())
                and command not in COMMANDS_ALLOWED_IN_OFFLINE_MODE
            ):
                logger.info(f"Ignoring online-only command '{command}'")
                continue

            try:
                # TODO try using pydantic to define message schema + some other message schema generator (nano message, ask Jason)
                handler = self._handlers[command]
            except KeyError as e:
                raise WebsocketCommandError(f"Unrecognized command from UI: {command}") from e

            # TODO make sure the error handling works here
            try:
                await handler(self, msg)
            except WebsocketCommandError as e:
                logger.error(f"Command {command} failed with error: {e.args[0]}")
                raise

    def _log_incoming_message(self, msg: dict[str, Any]) -> None:
        if msg["command"] == "login":
            comm_copy = copy.deepcopy(msg)
            comm_copy["password"] = get_redacted_string(4)
            comm_str = str(comm_copy)
        else:
            comm_str = str(msg)
        logger.info(f"Comm from UI: {comm_str}")

    # MESSAGE HANDLERS

    @mark_handler
    async def _shutdown(self, *args: Any) -> None:
        """Shutdown the controller."""
        logger.info("User initiated shutdown")
        self.user_initiated_shutdown = True

    @mark_handler
    async def _login(self, comm: dict[str, str]) -> None:
        """Update the customer/user settings."""
        for cred_type in comm:
            if cred_type not in VALID_CREDENTIAL_TYPES | {"command"}:
                raise WebsocketCommandError(f"Invalid cred type given: {cred_type}")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_latest_software_version(self, comm: dict[str, str]) -> None:
        """Set the latest available software version."""
        try:
            version = comm["version"]
            # check if version is a valid semantic version string. ValueError will be raised if not
            VersionInfo.parse(version)
        except KeyError:
            raise WebsocketCommandError("Version not specified")
        except ValueError:
            raise WebsocketCommandError(f"Invalid version string: {version}")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_firmware_update_confirmation(self, comm: dict[str, Any]) -> None:
        """Confirm whether or not the user wants to proceed with the FW update."""
        if not isinstance(update_accepted := comm["update_accepted"], bool):
            raise WebsocketCommandError(f"Invalid value for update_accepted: {update_accepted}")

        await self._to_monitor_queue.put(comm)

    # TODO consider changing this to "set_stim_info"
    @mark_handler
    async def _set_stim_protocols(self, comm: dict[str, Any]) -> None:
        """Set stimulation protocols in program memory and send to instrument."""
        # TODO make sure the UI includes a stim barcode in this msg

        system_state = self._get_system_state_ro()
        system_status = system_state["system_status"]

        if _are_any_stim_protocols_running(system_state):
            raise WebsocketCommandError("Cannot change protocols while stimulation is running")
        if system_status != SystemStatuses.IDLE_READY_STATE:
            raise WebsocketCommandError(f"Cannot change protocols while in {system_status.name}")

        stim_info = comm["stim_info"]

        protocol_list = stim_info["protocols"]
        # make sure at least one protocol is given
        if not protocol_list:
            raise WebsocketCommandError("Protocol list empty")

        # validate protocols
        given_protocol_ids = set()
        for protocol in protocol_list:
            # make sure protocol ID is unique
            protocol_id = protocol["protocol_id"]
            if protocol_id in given_protocol_ids:
                raise WebsocketCommandError(f"Multiple protocols given with ID: {protocol_id}")
            given_protocol_ids.add(protocol_id)

            # validate stim type
            stim_type = protocol["stimulation_type"]
            if stim_type not in VALID_STIMULATION_TYPES:
                raise WebsocketCommandError(f"Protocol {protocol_id}, Invalid stimulation type: {stim_type}")

            # validate subprotocol dictionaries
            try:
                for idx, subprotocol in enumerate(protocol["subprotocols"]):
                    validate_stim_subprotocol(subprotocol, stim_type, protocol_id, idx)
            except WebsocketCommandError:
                raise

        protocol_assignments_dict = stim_info["protocol_assignments"]
        # make sure protocol assignments are not missing any wells and do not contain any invalid wells
        all_well_names = set(
            GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx)
            for well_idx in range(NUM_WELLS)
        )
        given_well_names = set(protocol_assignments_dict.keys())
        if missing_wells := all_well_names - given_well_names:
            raise WebsocketCommandError(f"Protocol assignments missing wells: {missing_wells}")
        if invalid_wells := given_well_names - all_well_names:
            raise WebsocketCommandError(f"Protocol assignments contain invalid wells: {invalid_wells}")
        # make sure all protocol IDs are valid and that no protocols are unassigned
        assigned_ids = set(pid for pid in protocol_assignments_dict.values() if pid)
        if missing_protocol_ids := given_protocol_ids - assigned_ids:
            raise WebsocketCommandError(f"Protocol assignments missing protocol IDs: {missing_protocol_ids}")
        if invalid_protocol_ids := assigned_ids - given_protocol_ids:
            raise WebsocketCommandError(
                f"Protocol assignments contain invalid protocol IDs: {invalid_protocol_ids}"
            )

        comm["command_processed_event"] = asyncio.Event()
        await self._to_monitor_queue.put(comm)

        await comm["command_processed_event"].wait()

    @mark_handler
    async def _start_stim_checks(self, comm: dict[str, Any]) -> None:
        """Start the stimulator impedence checks on the instrument."""
        # TODO make sure the UI includes a stim barcode in this msg

        system_state = self._get_system_state_ro()

        if _are_stimulator_checks_running(system_state):
            return  # nothing to do here

        if system_state["system_status"] != SystemStatuses.IDLE_READY_STATE:
            raise WebsocketCommandError(
                f"Cannot start stim check unless in {SystemStatuses.IDLE_READY_STATE.name}"
            )
        if _are_any_stim_protocols_running(system_state):
            raise WebsocketCommandError("Cannot perform stimulator checks while stimulation is running")

        try:
            if not comm["well_indices"]:
                raise WebsocketCommandError("No well indices given")
        except KeyError:
            raise WebsocketCommandError("Request body missing 'well_indices'")

        # TODO figure out if the well idxs are still strings
        comm["well_indices"] = [int(idx) for idx in comm["well_indices"]]

        # check if barcodes were manually entered and match
        for barcode_type in ("plate_barcode", "stim_barcode"):
            barcode = comm.get(barcode_type)
            comm[f"{barcode_type}_is_from_scanner"] = barcode == system_state[barcode_type]

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_stim_status(self, comm: dict[str, Any]) -> None:
        """Start or stop stimulation on the instrument."""
        # TODO make sure the UI includes a stim barcode in this msg

        try:
            stim_status = comm["running"]
        except KeyError:
            raise WebsocketCommandError("Missing 'running' parameter")

        system_state = self._get_system_state_ro()

        if stim_status is _are_any_stim_protocols_running(system_state):
            return  # nothing to do here

        if not system_state["stim_info"]:
            raise WebsocketCommandError("Protocols have not been set")

        if stim_status:
            if (system_status := system_state["system_status"]) != SystemStatuses.IDLE_READY_STATE:
                raise WebsocketCommandError(f"Cannot start stimulation while in {system_status.name}")
            if not _are_initial_stimulator_checks_complete(system_state):
                raise WebsocketCommandError(
                    "Cannot start stimulation before initial stimulator circuit checks complete"
                )
            if _are_stimulator_checks_running(system_state):
                raise WebsocketCommandError(
                    "Cannot start stimulation while running stimulator circuit checks"
                )
            if _are_any_stimulator_circuits_short(system_state):
                raise WebsocketCommandError("Cannot start stimulation when a stimulator has a short circuit")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_offline_state(self, comm: dict[str, Any]) -> None:
        """Initiate or terminate system offline mode."""
        system_state = self._get_system_state_ro()

        incoming_offline_state = comm["offline_state"]

        if incoming_offline_state is _is_in_offline_mode(system_state):
            return  # nothing to do here
        if not _are_any_stim_protocols_running(system_state) and incoming_offline_state:
            raise WebsocketCommandError("Can only enter offline state if stimulation is active")

        comm = {"command": "init_offline_mode" if incoming_offline_state else "end_offline_mode"}
        await self._to_monitor_queue.put(comm)


# HELPERS


def _is_in_offline_mode(system_state: ReadOnlyDict) -> bool:
    system_status = system_state["system_status"]
    return system_status == SystemStatuses.OFFLINE_STATE  # type: ignore  # for some reason mypy thinks the type here is Any


def _are_any_stim_protocols_running(system_state: ReadOnlyDict) -> bool:
    stim_statuses = system_state["stimulation_protocol_statuses"]
    return any(status in (StimulationStates.STARTING, StimulationStates.RUNNING) for status in stim_statuses)


def _are_stimulator_checks_running(system_state: ReadOnlyDict) -> bool:
    return any(
        status == StimulatorCircuitStatuses.CALCULATING.name.lower()
        for status in system_state["stimulator_circuit_statuses"].values()
    )


def _are_initial_stimulator_checks_complete(system_state: ReadOnlyDict) -> bool:
    return bool(system_state["stimulator_circuit_statuses"])


def _are_any_stimulator_circuits_short(system_state: ReadOnlyDict) -> bool:
    return any(
        status == StimulatorCircuitStatuses.SHORT.name.lower()
        for status in system_state["stimulator_circuit_statuses"].values()
    )
