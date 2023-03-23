# -*- coding: utf-8 -*-
"""Handling communication between subsystems and server."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from pulse3D.constants import CHANNEL_FIRMWARE_VERSION_UUID
from pulse3D.constants import MAIN_FIRMWARE_VERSION_UUID
from pulse3D.constants import MANTARRAY_SERIAL_NUMBER_UUID as INSTRUMENT_SERIAL_NUMBER_UUID

from ..constants import CURRENT_SOFTWARE_VERSION
from ..constants import GENERIC_24_WELL_DEFINITION
from ..constants import NUM_WELLS
from ..constants import StimulatorCircuitStatuses
from ..constants import SystemStatuses
from ..utils.generic import semver_gt
from ..utils.generic import wait_tasks_clean
from ..utils.state_management import ReadOnlyDict
from ..utils.state_management import SystemStateManager


logger = logging.getLogger(__name__)


# TODO ADD LOGGING
class SystemMonitor:
    """Manages the state of the system and delegates tasks to subsystems."""

    def __init__(
        self,
        system_state_manager: SystemStateManager,
        queues: dict[str, dict[str, asyncio.Queue[dict[str, Any]]]],
    ) -> None:
        self._system_state_manager = system_state_manager
        self._queues = queues

    async def run(self) -> None:
        logger.info("Starting SystemMonitor")

        tasks = {
            asyncio.create_task(self._handle_comm_from_server()),
            asyncio.create_task(self._handle_comm_from_instrument_comm()),
            asyncio.create_task(self._handle_comm_from_cloud_comm()),
            asyncio.create_task(self._handle_system_state_updates()),
        }
        try:
            await wait_tasks_clean(tasks)
        except asyncio.CancelledError:
            logger.info("SystemMonitor cancelled")
            # TODO ?
            raise
        finally:
            logger.info("SystemMonitor shut down")

    # STATE HANDLING

    async def _handle_system_state_updates(self) -> None:
        while True:
            update_details = await self._system_state_manager.previous_update_queue.get()
            await self._update_system_status_special_cases()
            await self._push_system_status_update(update_details)

    async def _update_system_status_special_cases(self) -> None:
        """Update system status in special cases.

        Most system status updates can be driven by just one message
        from another subsystem, however these updates require either
        multiple or specific values in the state to be present, that
        often come from different subsystems.
        """
        system_state = self._system_state_manager.data

        new_system_status: SystemStatuses | None = None

        match system_state["system_status"]:
            case SystemStatuses.SERVER_INITIALIZING_STATE:
                # TODO Tanner (3/15/23): this state just instantly transitions right now, probably not needed anymore
                new_system_status = SystemStatuses.SERVER_READY_STATE
            case SystemStatuses.SERVER_READY_STATE:
                # TODO Tanner (3/15/23): this state just instantly transitions right now, probably not needed anymore
                new_system_status = SystemStatuses.SYSTEM_INITIALIZING_STATE
            case SystemStatuses.SYSTEM_INITIALIZING_STATE if (
                # need to wait in SYSTEM_INITIALIZING_STATE until UI connects (indicated by
                # latest_software_version being set) and instrument completes booting up (indicated by
                # instrument_metadata being set)
                system_state["instrument_metadata"]
                and system_state["latest_software_version"]
            ):
                new_system_status = SystemStatuses.CHECKING_FOR_UPDATES_STATE
                instrument_metadata = system_state["instrument_metadata"]
                # send command to cloud comm process to check for latest firmware versions
                await self._queues["to"]["cloud_comm"].put(
                    {
                        "command": "check_versions",
                        "serial_number": instrument_metadata[INSTRUMENT_SERIAL_NUMBER_UUID],
                        "main_fw_version": instrument_metadata[MAIN_FIRMWARE_VERSION_UUID],
                    }
                )
            case SystemStatuses.UPDATES_NEEDED_STATE if system_state["firmware_update_accepted"]:
                if system_state["is_user_logged_in"]:
                    new_system_status = SystemStatuses.DOWNLOADING_UPDATES_STATE
                    await self._queues["to"]["cloud_comm"].put(
                        {
                            "command": "download_firmware_updates",
                            "main": system_state["main_firmware_update"],
                            "channel": system_state["channel_firmware_update"],
                        }
                    )
                else:
                    await self._queues["to"]["server"].put(
                        {"communication_type": "user_input_needed", "input_type": "user_creds"}
                    )
            case SystemStatuses.UPDATES_NEEDED_STATE:
                new_system_status = SystemStatuses.IDLE_READY_STATE
            case SystemStatuses.INSTALLING_UPDATES_STATE:
                # these two values get reset to None after their respective installs complete
                if (
                    system_state["main_firmware_update"] is None
                    and system_state["channel_firmware_update"] is None
                ):
                    new_system_status = SystemStatuses.UPDATES_COMPLETE_STATE
                    await self._send_enable_sw_auto_install_message()

        if new_system_status:
            system_status_dict = {"system_status": new_system_status}
            await self._system_state_manager.update(system_status_dict)

    async def _push_system_status_update(self, update_details: ReadOnlyDict) -> None:
        status_update_details = {}
        if (new_system_status := update_details.get("system_status")) is not None:
            status_update_details["system_status"] = new_system_status
        if (stim_running_updates := update_details.get("stimulation_running")) is not None:
            status_update_details["is_stimulating"] = any(stim_running_updates)
        if (in_simulation_mode := update_details.get("in_simulation_mode")) is not None:
            status_update_details["in_simulation_mode"] = in_simulation_mode

        if status_update_details:
            logger.info(f"System status update: {status_update_details}")
            # want to have system_status logged as an enum, so afterwards need to convert it to a string so it can be json serialized later
            if system_status := status_update_details.get("system_status"):
                status_update_details["system_status"] = str(system_status.value)

            await self._queues["to"]["server"].put(
                {"communication_type": "status_update", **status_update_details}
            )

    # COMM HANDLERS

    async def _handle_comm_from_server(self) -> None:
        while True:
            communication = await self._queues["from"]["server"].get()

            system_state_updates: dict[str, Any] = {}

            match communication:
                case {"command": "update_user_settings", **new_settings}:
                    # Tanner (3/16/23): this assumes that either all or none of these values will be sent
                    if new_user_creds := {
                        key: value
                        for key in ("customer_id", "user_name", "user_password")
                        if (value := new_settings.pop(key))
                    }:
                        await self._queues["to"]["cloud_comm"].put(
                            {"command": "login", "user_creds": new_user_creds}
                        )
                    # all remaining settings fall under config settings
                    if new_settings:
                        # TODO figure out if this sends every setting all together or just the ones that changed
                        system_state_updates["config_settings"] = new_settings
                case {"command": "set_latest_software_version", "version": version}:
                    system_state_updates["latest_software_version"] = version
                    # send message to FE if indicating if an update is available
                    try:
                        software_update_available = semver_gt(version, CURRENT_SOFTWARE_VERSION)
                    except ValueError:
                        software_update_available = False
                    await self._queues["to"]["server"].put(
                        {
                            "communication_type": "sw_update",
                            "software_update_available": software_update_available,
                        }
                    )
                case {"command": "set_firmware_update_confirmation", "update_accepted": update_accepted}:
                    system_state_updates["system_status"] = (
                        SystemStatuses.DOWNLOADING_UPDATES_STATE
                        if update_accepted
                        else SystemStatuses.IDLE_READY_STATE
                    )
                case {"command": "set_stim_status", "status": status}:
                    await self._queues["to"]["instrument_comm"].put(
                        {"command": "start_stimulation" if status else "stop_stimulation"}
                    )
                case {"command": "set_stim_protocols", "stim_info": stim_info}:
                    system_state_updates["stim_info"] = stim_info
                    await self._queues["to"]["instrument_comm"].put(communication)
                case {"command": "start_stim_checks", "well_indices": well_indices}:
                    system_state_updates["stimulator_circuit_statuses"] = {
                        well_idx: StimulatorCircuitStatuses.CALCULATING.name.lower()
                        for well_idx in well_indices
                    }
                    await self._queues["to"]["instrument_comm"].put(communication)
                case invalid_comm:
                    raise NotImplementedError(f"Invalid communication from server: {invalid_comm}")

            if system_state_updates:
                await self._system_state_manager.update(system_state_updates)

    async def _handle_comm_from_instrument_comm(self) -> None:
        while True:
            communication = await self._queues["from"]["instrument_comm"].get()

            system_state = self._system_state_manager.data

            system_state_updates: dict[str, Any] = {}

            # TODO for all these comm handlers, raise error for unrecognized comm. Do this in subsystems as well
            match communication:
                case {"command": "start_stimulation"}:
                    stim_running_list = [False] * NUM_WELLS
                    protocol_assignments = system_state["stim_info"]["protocol_assignments"]
                    for well_name, assignment in protocol_assignments.items():
                        if not assignment:
                            continue
                        well_idx = GENERIC_24_WELL_DEFINITION.get_well_index_from_well_name(well_name)
                        stim_running_list[well_idx] = True
                    system_state_updates["stimulation_running"] = stim_running_list
                case {"command": "stop_stimulation"}:
                    system_state_updates["stimulation_running"] = [False] * NUM_WELLS
                case {"command": "stim_status_update", "wells_done_stimulating": wells_done_stimulating}:
                    system_state_updates["stimulation_running"] = list(system_state["stimulation_running"])
                    for well_idx in wells_done_stimulating:
                        system_state_updates["stimulation_running"][well_idx] = False
                case {
                    "command": "start_stim_checks",
                    "stimulator_circuit_statuses": stimulator_circuit_statuses,
                }:
                    update = {"stimulator_circuit_statuses": stimulator_circuit_statuses}
                    system_state_updates.update(update)
                    await self._queues["to"]["server"].put(
                        {"communication_type": "stimulator_circuit_statuses", **update}
                    )
                case {"command": "get_board_connection_status", "in_simulation_mode": in_simulation_mode}:
                    system_state_updates["in_simulation_mode"] = in_simulation_mode
                case {"command": "get_barcode", "barcode": barcode}:
                    barcode_type = "stim_barcode" if barcode.startswith("MS") else "plate_barcode"
                    # if barcode didn't change, then no need to create an update
                    if system_state[barcode_type] != barcode:
                        system_state_updates[barcode_type] = barcode
                        # send message to FE
                        barcode_update_message = {
                            "communication_type": "barcode_update",
                            "new_barcode": barcode,
                        }
                        await self._queues["to"]["server"].put(barcode_update_message)
                case {"command": "get_metadata", **metadata}:
                    system_state_updates["instrument_metadata"] = metadata
                case {"command": "firmware_update_completed", "firmware_type": firmware_type}:
                    system_state_updates[f"{firmware_type}_firmware_update"] = None

            if system_state_updates:
                await self._system_state_manager.update(system_state_updates)

    async def _handle_comm_from_cloud_comm(self) -> None:
        # TODO could make try making these first 4 boiler plates lines reusable somehow
        while True:
            communication = await self._queues["from"]["cloud_comm"].get()

            system_state = self._system_state_manager.data

            system_state_updates: dict[str, Any] = {}

            match communication:
                case {"command": "check_versions", "error": _}:
                    system_state_updates["system_status"] = SystemStatuses.IDLE_READY_STATE
                case {"command": "check_versions"}:
                    required_sw_for_fw = communication["latest_versions"]["sw"]
                    latest_main_fw = communication["latest_versions"]["main-fw"]
                    latest_channel_fw = communication["latest_versions"]["channel-fw"]

                    min_sw_version_available = not semver_gt(
                        required_sw_for_fw, system_state["latest_software_version"]
                    )
                    main_fw_update_needed = semver_gt(
                        latest_main_fw,
                        system_state["instrument_metadata"][MAIN_FIRMWARE_VERSION_UUID],
                    )
                    channel_fw_update_needed = semver_gt(
                        latest_channel_fw,
                        system_state["instrument_metadata"][CHANNEL_FIRMWARE_VERSION_UUID],
                    )

                    # FW updates are only available if the required SW can be downloaded
                    if (main_fw_update_needed or channel_fw_update_needed) and min_sw_version_available:
                        system_state_updates["fsystem_status"] = SystemStatuses.UPDATES_NEEDED_STATE
                        system_state_updates["main_firmware_update"] = (
                            latest_main_fw if main_fw_update_needed else None
                        )
                        system_state_updates["channel_firmware_update"] = (
                            latest_channel_fw if channel_fw_update_needed else None
                        )
                        # let UI know the details of the update since they take different amounts of time
                        await self._queues["to"]["server"].put(
                            {
                                "communication_type": "firmware_update_available",
                                "channel_fw_update": channel_fw_update_needed,
                            }
                        )
                    else:
                        system_state_updates["system_status"] = SystemStatuses.IDLE_READY_STATE
                        # since no updates available, also enable auto install of SW update
                        await self._send_enable_sw_auto_install_message()
                case {"error": _}:
                    system_state_updates["system_status"] = SystemStatuses.UPDATE_ERROR_STATE
                case {"command": "download_firmware_updates"}:
                    system_state_updates["system_status"] = SystemStatuses.INSTALLING_UPDATES_STATE
                    # Tanner (1/13/22): send both firmware update commands at once, and make sure channel is sent first.
                    # If both are sent, the second will be ignored by instrument comm until the first install completes
                    for firmware_type in ("channel", "main"):
                        if system_state[f"{firmware_type}_firmware_update"] is not None:
                            self._queues["to"]["instrument_comm"].put_nowait(
                                {
                                    "command": "start_firmware_update",
                                    "firmware_type": firmware_type,
                                    "file_contents": " TODO",
                                }
                            )

            if system_state_updates:
                await self._system_state_manager.update(system_state_updates)

    # HELPERS

    async def _send_enable_sw_auto_install_message(self) -> None:
        await self._queues["to"]["server"].put(
            {"communication_type": "sw_update", "allow_software_update": True}
        )
