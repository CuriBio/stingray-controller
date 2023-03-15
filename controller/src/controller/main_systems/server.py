# -*- coding: utf-8 -*-
import asyncio
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
from ..constants import IDLE_READY_STATE
from ..constants import STIM_MAX_ABSOLUTE_CURRENT_MICROAMPS
from ..constants import STIM_MAX_ABSOLUTE_VOLTAGE_MILLIVOLTS
from ..constants import STIM_MAX_DUTY_CYCLE_DURATION_MICROSECONDS
from ..constants import STIM_MAX_DUTY_CYCLE_PERCENTAGE
from ..constants import STIM_MAX_SUBPROTOCOL_DURATION_MICROSECONDS
from ..constants import STIM_MIN_SUBPROTOCOL_DURATION_MICROSECONDS
from ..constants import StimulatorCircuitStatuses
from ..constants import VALID_CONFIG_SETTINGS
from ..constants import VALID_STIMULATION_TYPES
from ..constants import VALID_SUBPROTOCOL_TYPES
from ..exceptions import WebsocketCommandError
from ..utils.generic import wait_tasks_clean
from ..utils.stimulation import get_pulse_dur_us
from ..utils.stimulation import get_pulse_duty_cycle_dur_us

logger = logging.getLogger(__name__)


# ------------- TODOs -------------
# - start adding in process monitor
#    - send msgs back and forth
#    - handle server initiated shutdown gracefully
#    - handle pm initiated shutdown gracefully
#    - more ?


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
    _handlers: dict[str, Callable[[Any], Awaitable[dict[str, Any] | None]]]

    def __init__(
        self,
        get_system_state_copy: Callable[..., dict[str, Any]],
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        self._connected = False
        self._serve_task: asyncio.Task[None] | None = None

        self._get_system_state_copy: Callable[..., dict[str, Any]] = get_system_state_copy

        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue

        self.fe_initiated_shutdown = False

    async def run(self) -> None:
        logger.info("Starting Server")

        ws_server = await serve(self._run, "localhost", DEFAULT_SERVER_PORT_NUMBER)
        self._serve_task = asyncio.create_task(ws_server.serve_forever())
        try:
            await self._serve_task
        except asyncio.CancelledError:
            logger.info("Server cancelled")
            ws_server.close()
            await ws_server.wait_closed()
            raise
        finally:
            logger.info("Server shut down")

    async def _run(self, websocket: WebSocketServerProtocol) -> None:
        if not self._serve_task:
            raise NotImplementedError("_serve_task must be not be None here")

        if self._connected:
            logger.exception("ERROR - SECOND CONNECTION MADE")
            # TODO figure out a good way to handle this
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
            await websocket.send(json.dumps(msg))

    async def _consumer(self, websocket: WebSocketServerProtocol) -> None:
        while not self.fe_initiated_shutdown:
            try:
                msg = json.loads(await websocket.recv())
            except websockets.ConnectionClosed:
                break

            self._log_incoming_message(msg)

            command = msg["command"]

            # TODO handle KeyError here or make default method to handle unrecognized comm
            handler = self._handlers[command]

            try:
                handler_res = await handler(self, **msg)
            except WebsocketCommandError:
                # TODO
                error_res = {}  # type: ignore
                await websocket.send(json.dumps(error_res))
            else:
                if handler_res:
                    res = {"communication_type": "command_response", "command": command, **handler_res}
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

    # TEST MESSAGE HANDLERS

    @mark_handler
    async def _test(self, msg: dict[str, Any]) -> dict[str, Any]:
        return {"test msg": msg}

    @mark_handler
    async def _monitor_test(self, msg: dict[str, Any]) -> None:
        await self._to_monitor_queue.put(msg)

    @mark_handler
    async def _err(self) -> None:
        raise Exception()

    # MESSAGE HANDLERS

    @mark_handler
    async def _shutdown(self) -> dict[str, Any]:
        self.fe_initiated_shutdown = True
        # TODO remove this return when done testing
        return {"msg": "beginning_shutdown"}

    # TODO figure out if this is even needed anymore, can probably just push updates whenever part of the system status changes instead
    # @mark_handler
    # async def _get_system_status(self) -> dict[str, Any]:
    #     """Get the system status and other information.

    #     in_simulation_mode is only accurate if ui_status_code is '009301eb-625c-4dc4-9e92-1a4d0762465f'

    #     instrument_serial_number and instrument_nickname are only accurate if ui_status_code is '8e24ef4d-2353-4e9d-aa32-4346126e73e3'
    #     """
    #     # TODO probably want to move this out and handle differently
    #     # system_state = _get_values_from_process_monitor()
    #     # current_software_version = get_current_software_version()
    #     # expected_software_version = server.system_state.get("expected_software_version", current_software_version)
    #     # if expected_software_version != current_software_version:
    #     #     return {
    #     #         "error": f"Versions of Electron and Flask EXEs do not match. Expected: {expected_software_version}"
    #     #     }

    #     system_state = self._get_system_state_copy()

    #     return {
    #         "ui_status_code": str(SYSTEM_STATUS_UUIDS[system_state["system_status"]]),
    #         "is_stimulating": _is_stimulating_on_any_well(system_state),
    #         # TODO is this still true? Tanner (7/1/20): this route may be called before process_monitor adds the following values to system_state, so default values are needed
    #         "in_simulation_mode": system_state.get("in_simulation_mode", False),
    #         "instrument_serial_number": system_state.get("instrument_serial_number", ""),
    #         "instrument_nickname": system_state.get("instrument_nickname", ""),
    #     }

    @mark_handler
    async def _update_settings(self, comm: dict[str, str]) -> None:
        """Update the customer/user settings."""
        for setting in comm:
            if setting in ("communication_type", "command"):
                continue
            if setting not in VALID_CONFIG_SETTINGS:
                raise WebsocketCommandError(f"Invalid setting given: {setting}")

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
        """Confirm whether or not the user wants to proceed with the FW
        update."""
        if not isinstance(update_accepted := comm["update_accepted"], bool):
            raise WebsocketCommandError(f"Invalid value for update_accepted: {update_accepted}")

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_stim_protocols(self, comm: dict[str, Any]) -> None:
        """Set stimulation protocols in program memory and send to
        instrument."""
        system_status = self._get_system_state_copy()["system_status"]

        if _is_stimulating_on_any_well(system_status):
            raise WebsocketCommandError("Cannot change protocols while stimulation is running")
        if system_status != IDLE_READY_STATE:
            raise WebsocketCommandError(f"Cannot change protocols while {system_status}")

        protocol_list = comm["protocols"]
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
            for idx, subprotocol in enumerate(protocol["subprotocols"]):
                subprotocol["type"] = subprotocol["type"].lower()
                subprotocol_type = subprotocol["type"]
                # validate subprotocol type
                if subprotocol_type not in VALID_SUBPROTOCOL_TYPES:
                    raise WebsocketCommandError(
                        f"Protocol {protocol_id}, Subprotocol {idx}, Invalid subprotocol type: {subprotocol_type}"
                    )

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

        protocol_assignments_dict = comm["protocol_assignments"]
        # make sure protocol assignments are not missing any wells and do not contain any invalid wells
        all_well_names = set(
            GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx) for well_idx in range(24)
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

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _start_stim_checks(self, comm: dict[str, Any]) -> None:
        """Start the stimulator impedence checks on the instrument."""
        system_state = self._get_system_state_copy()
        if system_state["system_status"] != IDLE_READY_STATE:
            raise WebsocketCommandError(f"Cannot start stim check unless in {IDLE_READY_STATE} state")
        if _is_stimulating_on_any_well(system_state):
            raise WebsocketCommandError("Cannot perform stimulator checks while stimulation is running")
        if _are_stimulator_checks_running(system_state):
            raise WebsocketCommandError("Stimulator checks already running")

        try:
            if not comm["well_indices"]:
                raise WebsocketCommandError("400 No well indices given")
        except KeyError:
            raise WebsocketCommandError("400 Request body missing 'well_indices'")

        # TODO figure out if the well idxs are still strings
        comm["well_indices"] = [int(idx) for idx in comm["well_indices"]]

        await self._to_monitor_queue.put(comm)

    @mark_handler
    async def _set_stim_status(self, comm: dict[str, Any]) -> None:
        """Start or stop stimulation on the instrument."""
        try:
            stim_status = comm["running"]
        except KeyError:
            raise WebsocketCommandError("Missing 'running' parameter")

        system_state = self._get_system_state_copy()

        if system_state["stimulation_info"] is None:
            raise WebsocketCommandError("406 Protocols have not been set")

        if stim_status:
            if (system_status := system_state["system_status"]) != IDLE_READY_STATE:
                raise WebsocketCommandError(f"Cannot start stimulation while {system_status}")
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

        if stim_status is _is_stimulating_on_any_well(system_state):
            raise WebsocketCommandError("Stim status not updated")

        await self._to_monitor_queue.put(comm)


def _is_stimulating_on_any_well(system_state: dict[str, Any]) -> bool:
    return any(system_state["stimulation_running"])


def _are_stimulator_checks_running(system_state: dict[str, Any]) -> bool:
    return any(
        status == StimulatorCircuitStatuses.CALCULATING.name.lower()
        for status in system_state["stimulator_circuit_statuses"].values()
    )


def _are_initial_stimulator_checks_complete(system_state: dict[str, Any]) -> bool:
    return bool(system_state["stimulator_circuit_statuses"])


def _are_any_stimulator_circuits_short(system_state: dict[str, Any]) -> bool:
    return any(
        status == StimulatorCircuitStatuses.SHORT.name.lower()
        for status in system_state["stimulator_circuit_statuses"].values()
    )
