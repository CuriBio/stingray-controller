# -*- coding: utf-8 -*-
import asyncio
import copy
import functools
import json
import logging
import os
from typing import Any
from typing import Awaitable
from typing import Callable
import urllib.parse

from pulse3D.constants import NOT_APPLICABLE_H5_METADATA
from semver import VersionInfo
import websockets
from websockets import serve
from websockets.server import WebSocketServerProtocol

from ..constants import DEFAULT_SERVER_PORT_NUMBER
from ..constants import GENERIC_24_WELL_DEFINITION
from ..constants import NUM_WELLS
from ..constants import RECORDINGS_SUBDIR
from ..constants import StimulationStates
from ..constants import StimulatorCircuitStatuses
from ..constants import SystemStatuses
from ..constants import VALID_CREDENTIAL_TYPES
from ..constants import VALID_STIMULATION_TYPES
from ..exceptions import WebsocketCommandError
from ..exceptions import WebsocketCommandNoOpException
from ..utils.aio import clean_up_tasks
from ..utils.aio import wait_tasks_clean
from ..utils.generic import handle_system_error
from ..utils.logging import get_redacted_string
from ..utils.state_management import ReadOnlyDict
from ..utils.stimulation import validate_stim_subprotocol
from ..utils.validation import check_barcode_for_errors

logger = logging.getLogger(__name__)

ERROR_MSG = "IN SERVER"


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
        self, system_error_future: asyncio.Future[int], server_running_event: asyncio.Event
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
        self, websocket: WebSocketServerProtocol, system_error_future: asyncio.Future[int]
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

    async def _report_system_error(self, system_error_future: asyncio.Future[int]) -> None:
        if not system_error_future.done():
            logger.info("No errors to report to UI")
            return

        error_code = system_error_future.result()

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
            msg = {"communication_type": "error", "error_code": error_code}
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
                logger.error("Failed to read message from UI")
                return

            self._log_incoming_message(msg)

            command = msg["command"]
            try:
                # TODO try using pydantic to define message schema + some other message schema generator (nano message, ask Jason)
                handler = self._handlers[command]
            except KeyError as e:
                raise WebsocketCommandError(f"Unrecognized command from UI: {command}") from e

            try:
                await handler(self, msg)
            except WebsocketCommandNoOpException:
                logger.error(f"Command {command} resulted in a no-op")
            except WebsocketCommandError as e:
                e.add_note(f"Command {command} failed")
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
        required_keys = set(VALID_CREDENTIAL_TYPES) | {"command"}
        provided_keys = set(comm)
        if missing_keys := required_keys - provided_keys:
            raise WebsocketCommandError(f"Missing cred type(s): {missing_keys}")
        if invalid_keys := provided_keys - required_keys:
            raise WebsocketCommandError(f"Invalid cred type(s) given: {invalid_keys}")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_latest_software_version(self, comm: dict[str, str]) -> None:
        """Set the latest available software version."""

        try:
            version = comm["version"]
            # check if version is a valid semantic version string. ValueError will be raised if not
            VersionInfo.parse(version)
        except KeyError:
            raise WebsocketCommandError("Command missing 'version' value")
        except ValueError:
            raise WebsocketCommandError(f"Invalid semver: {version}")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_firmware_update_confirmation(self, comm: dict[str, Any]) -> None:
        """Confirm whether or not the user wants to proceed with the FW update."""
        if not isinstance(update_accepted := comm["update_accepted"], bool):
            raise WebsocketCommandError(f"Invalid value for update_accepted: {update_accepted}")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _start_calibration(self, comm: dict[str, Any]) -> None:
        """Begin magnetometer calibration recording."""
        system_state = self._get_system_state_ro()

        if system_state["system_status"] == SystemStatuses.CALIBRATING:
            raise WebsocketCommandNoOpException()

        if system_state["system_status"] not in (
            valid_states := (SystemStatuses.CALIBRATION_NEEDED, SystemStatuses.IDLE_READY)
        ):
            raise WebsocketCommandError(f"Cannot calibrate unless in {valid_states}")
        if _are_stimulator_checks_running(system_state):
            raise WebsocketCommandError("Cannot calibrate while stimulator checks are running")
        if _are_any_stim_protocols_running(system_state):
            raise WebsocketCommandError("Cannot calibrate while stimulation is running")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _start_data_stream(self, comm: dict[str, Any]) -> None:
        """Start magnetometer data stream."""
        system_state = self._get_system_state_ro()
        system_status = system_state["system_status"]

        if _is_data_streaming(system_state):
            raise WebsocketCommandNoOpException()
        if system_status != SystemStatuses.IDLE_READY:
            raise WebsocketCommandError(
                f"Cannot start data stream unless in in {SystemStatuses.IDLE_READY.name}"
            )
        if _are_stimulator_checks_running(system_state):
            raise WebsocketCommandError("Cannot start data stream while stimulator checks are running")

        try:
            plate_barcode = comm["plate_barcode"]
        except KeyError:
            raise WebsocketCommandError("Command missing 'plate_barcode' value")
        if not plate_barcode:
            raise WebsocketCommandError("Cannot start data stream without a plate barcode present")
        if error_message := check_barcode_for_errors(plate_barcode, "plate_barcode"):
            raise WebsocketCommandError(f"Plate {error_message}")

        # TODO import MANTARRAY_SERIAL_NUMBER_UUID as INSTRUMENT_SERIAL_NUMBER_UUID in all files. Same for nickname constant
        if not all(system_state["instrument_metadata"].values()):  # TODO test this
            # TODO make a custom error + code for this and move this handling to instrument_comm so it's handled right after getting metadata
            raise WebsocketCommandError("Instrument metadata is incomplete")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _stop_data_stream(self, comm: dict[str, Any]) -> None:
        """Stop magnetometer data stream."""
        system_state = self._get_system_state_ro()
        system_status = system_state["system_status"]

        # TODO add no-op handling

        if system_status not in (SystemStatuses.BUFFERING, SystemStatuses.LIVE_VIEW_ACTIVE):
            raise WebsocketCommandError(f"Cannot stop data stream while in {system_status.name}")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _start_recording(self, comm: dict[str, Any]) -> None:
        """Start writing data stream to file."""
        # TODO make sure all required params are always sent from UI
        system_state = self._get_system_state_ro()

        # TODO make sure this route can only be called in the correct state

        if _is_recording(system_state):
            raise WebsocketCommandNoOpException()

        if not isinstance((start_timepoint := comm.get("start_timepoint")), int):
            raise WebsocketCommandError(f"Invalid value for 'start_timepoint': {start_timepoint}")

        barcodes_to_validate = ["plate_barcode"]
        if _are_any_stim_protocols_running(system_state):
            barcodes_to_validate.append("stim_barcode")
        else:
            comm["stim_barcode"] = NOT_APPLICABLE_H5_METADATA
        # check that all required params are given before validating
        for barcode_type in barcodes_to_validate:
            try:
                barcode = comm[barcode_type]
            except KeyError:
                raise WebsocketCommandError(f"Command missing '{barcode_type}' value")
            else:
                if error_message := check_barcode_for_errors(barcode, barcode_type):
                    barcode_label = barcode_type.split("_")[0].title()
                    raise WebsocketCommandError(f"{barcode_label} {error_message}")

        if comm["platemap"] is not None:
            comm["platemap"] = json.loads(urllib.parse.unquote_plus(comm["platemap"]))

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _stop_recording(self, comm: dict[str, Any]) -> None:
        """Stop writing data stream to file and close the file."""
        system_state = self._get_system_state_ro()

        if not _is_recording(system_state):
            raise WebsocketCommandNoOpException()

        if not isinstance((stop_timepoint := comm.get("stop_timepoint")), int):
            raise WebsocketCommandError(f"Invalid value for 'stop_timepoint': {stop_timepoint}")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _update_recording_name(self, comm: dict[str, Any]) -> None:
        """Update the name of the most recent recording."""
        system_state = self._get_system_state_ro()

        comm["new_name"] = comm["new_name"].strip()

        if _recording_exists(system_state, comm["new_name"]) and not comm["replace_existing"]:
            # immediately sending message back to UI since there is no reason to have SystemMonitor handle doing this
            await self._from_monitor_queue.put(
                {"communication_type": "update_recording_name", "name_updated": False}
            )
        else:
            await self._to_monitor_queue.put(comm)

    # TODO make a new route for handling the recording snapshot?

    # TODO consider changing this to "set_stim_info"
    @mark_handler
    async def _set_stim_protocols(self, comm: dict[str, Any]) -> None:
        """Set stimulation protocols in program memory and send to instrument."""

        try:
            if not comm["stim_barcode"]:
                raise WebsocketCommandError("Cannot set stim protocols without a stim barcode present")
        except KeyError:
            raise WebsocketCommandError("Command missing 'stim_barcode' value")

        system_state = self._get_system_state_ro()
        system_status = system_state["system_status"]

        if _are_any_stim_protocols_running(system_state):
            raise WebsocketCommandError("Cannot set stim protocols while stimulation is running")
        if system_status != SystemStatuses.IDLE_READY:
            raise WebsocketCommandError(f"Cannot set stim protocols while in {system_status.name}")

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

        system_state = self._get_system_state_ro()

        if _are_stimulator_checks_running(system_state):
            raise WebsocketCommandNoOpException()

        if system_state["system_status"] != SystemStatuses.IDLE_READY:
            raise WebsocketCommandError(f"Cannot start stim check unless in {SystemStatuses.IDLE_READY.name}")
        if _are_any_stim_protocols_running(system_state):
            raise WebsocketCommandError("Cannot perform stimulator checks while stimulation is running")

        try:
            if not comm["well_indices"]:
                raise WebsocketCommandError("No well indices given")
        except KeyError:
            raise WebsocketCommandError("Request body missing 'well_indices'")

        # check if barcodes were manually entered and match
        for barcode_type in ("plate_barcode", "stim_barcode"):
            try:
                barcode = comm[barcode_type]
            except KeyError:
                raise WebsocketCommandError(f"Command missing '{barcode_type}' value")

            comm[f"{barcode_type}_is_from_scanner"] = barcode == system_state[barcode_type]

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_stim_status(self, comm: dict[str, Any]) -> None:
        """Start or stop stimulation on the instrument."""

        try:
            stim_status = comm["running"]
        except KeyError:
            raise WebsocketCommandError("Command missing 'running' value")

        for barcode_type in ("plate_barcode", "stim_barcode"):
            try:
                if not comm[barcode_type] and stim_status:
                    raise WebsocketCommandError(f"Cannot start stimulation without a {barcode_type} present")
            except KeyError:
                raise WebsocketCommandError(f"Command missing '{barcode_type}' value")

        system_state = self._get_system_state_ro()

        if stim_status is _are_any_stim_protocols_running(system_state):
            raise WebsocketCommandNoOpException()

        if not system_state["stim_info"]:
            raise WebsocketCommandError("Protocols have not been set")

        if stim_status:
            if (system_status := system_state["system_status"]) != SystemStatuses.IDLE_READY:
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


# HELPERS


def _is_data_streaming(system_state: ReadOnlyDict) -> bool:
    return system_state["system_status"] in (
        SystemStatuses.BUFFERING,
        SystemStatuses.LIVE_VIEW_ACTIVE,
        SystemStatuses.RECORDING,
    )


def _is_recording(system_state: ReadOnlyDict) -> bool:
    return system_state["system_status"] == SystemStatuses.RECORDING  # type: ignore  # mypy doesn't understand that this is a bool


def _recording_exists(system_state, recording_name):
    recording_dir = os.path.join(system_state["base_directory"], RECORDINGS_SUBDIR)
    os.path.exists(os.path.join(recording_dir, recording_name))


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
