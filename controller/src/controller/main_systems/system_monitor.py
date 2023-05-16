# -*- coding: utf-8 -*-
"""Handling communication between subsystems and server."""


import asyncio
import logging
import os
from typing import Any

from pulse3D.constants import CHANNEL_FIRMWARE_VERSION_UUID
from pulse3D.constants import MAIN_FIRMWARE_VERSION_UUID
from pulse3D.constants import MANTARRAY_SERIAL_NUMBER_UUID as INSTRUMENT_SERIAL_NUMBER_UUID

from ..constants import CURRENT_SOFTWARE_VERSION
from ..constants import FW_UPDATE_SUBDIR
from ..constants import StimulationStates
from ..constants import StimulatorCircuitStatuses
from ..constants import SystemStatuses
from ..utils.aio import wait_tasks_clean
from ..utils.generic import handle_system_error
from ..utils.generic import semver_gt
from ..utils.state_management import ReadOnlyDict
from ..utils.state_management import SystemStateManager
from ..utils.stimulation import chunk_protocols_in_stim_info


logger = logging.getLogger(__name__)

ERROR_MSG = "IN SYSTEM MONITOR"


class SystemMonitor:
    """Manages the state of the system and delegates tasks to subsystems."""

    def __init__(
        self,
        system_state_manager: SystemStateManager,
        queues: dict[str, dict[str, asyncio.Queue[dict[str, Any]]]],
    ) -> None:
        self._system_state_manager = system_state_manager
        self._queues = queues

    async def run(self, system_error_future: asyncio.Future[int]) -> None:
        logger.info("Starting SystemMonitor")

        tasks = {
            asyncio.create_task(self._handle_comm_from_server()),
            asyncio.create_task(self._handle_comm_from_instrument_comm()),
            asyncio.create_task(self._handle_comm_from_cloud_comm()),
            asyncio.create_task(self._handle_system_state_updates()),
        }
        try:
            await wait_tasks_clean(tasks, error_msg=ERROR_MSG)
        except asyncio.CancelledError:
            logger.info("SystemMonitor cancelled")
            raise
        except BaseException as e:
            logger.exception(ERROR_MSG)
            handle_system_error(e, system_error_future)
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

        Most system status updates can be driven by just one message from another subsystem, however these
        updates require either multiple or specific values in the state to be present, that often come from
        different subsystems.
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
                        "fw_update_dir_path": os.path.join(system_state["base_directory"], FW_UPDATE_SUBDIR),
                        "serial_number": instrument_metadata[INSTRUMENT_SERIAL_NUMBER_UUID],
                        "main_fw_version": instrument_metadata[MAIN_FIRMWARE_VERSION_UUID],
                    }
                )
            case SystemStatuses.UPDATES_NEEDED_STATE if system_state["firmware_updates_accepted"]:
                if not system_state["firmware_updates_require_download"] or system_state["is_user_logged_in"]:
                    new_system_status = SystemStatuses.DOWNLOADING_UPDATES_STATE

                    fw_update_dir_path = (
                        None
                        if system_state["firmware_updates_require_download"]
                        else os.path.join(system_state["base_directory"], FW_UPDATE_SUBDIR)
                    )

                    await self._queues["to"]["cloud_comm"].put(
                        {
                            "command": "download_firmware_updates",
                            "main": system_state["main_firmware_update"],
                            "channel": system_state["channel_firmware_update"],
                            "fw_update_dir_path": fw_update_dir_path,
                        }
                    )
                else:
                    logger.info("Login required to download firmware update(s)")
                    await self._queues["to"]["server"].put(
                        {"communication_type": "user_input_needed", "input_type": "user_creds"}
                    )
            case SystemStatuses.UPDATES_NEEDED_STATE if system_state["firmware_updates_accepted"] is False:
                # firmware_updates_accepted value will be None before a user has made a decision, so need to explicitly check that it is False
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
        status_update_details = {
            status_name: new_system_status
            for status_name in ("system_status", "stimulation_protocol_statuses", "in_simulation_mode")
            if (new_system_status := update_details.get(status_name))
        }
        if not status_update_details:
            return

        logger.info(f"System status update: {status_update_details}")

        # starting/stopping states should be logged, but don't need to be sent to the UI, so remove them
        try:
            new_stim_statuses = status_update_details.pop("stimulation_protocol_statuses")
        except KeyError:
            pass
        else:
            if not (
                # if either of these are present then assume stim will either start or stop on every well soon so wait for that to happen before sending an update
                StimulationStates.STARTING in new_stim_statuses
                or StimulationStates.STOPPING in new_stim_statuses
            ):
                status_update_details["stimulation_protocols_running"] = [
                    stim_status == StimulationStates.RUNNING for stim_status in new_stim_statuses
                ]

        # this will happen if the only update was starting/stopping stim, in which case nothing needs to be sent to the UI
        if not status_update_details:
            return

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

            system_state = self._system_state_manager.data

            system_state_updates: dict[str, Any] = {}

            match communication:
                case {"command": "login"}:
                    await self._queues["to"]["cloud_comm"].put(communication)
                case {"command": "set_latest_software_version", "version": version}:
                    system_state_updates["latest_software_version"] = version
                    # send message to FE if indicating if an update is available
                    try:
                        software_update_available = semver_gt(version, CURRENT_SOFTWARE_VERSION)
                    except ValueError:
                        # CURRENT_SOFTWARE_VERSION will not be a valid semver in dev mode
                        software_update_available = False
                    await self._queues["to"]["server"].put(
                        {
                            "communication_type": "sw_update",
                            "software_update_available": software_update_available,
                        }
                    )
                case {"command": "set_firmware_update_confirmation", "update_accepted": update_accepted}:
                    action = "accepted" if update_accepted else "declined"
                    logger.info(f"User {action} firmware update(s)")
                    system_state_updates["firmware_updates_accepted"] = update_accepted
                case {"command": "set_stim_status", "running": status}:
                    num_protocols = len(system_state["stim_info"]["protocols"])
                    if status:
                        command = "start_stimulation"
                        stim_status_updates = [StimulationStates.STARTING] * num_protocols
                    else:
                        command = "stop_stimulation"
                        stim_status_updates = [
                            StimulationStates.STOPPING
                            if current_status in (StimulationStates.STARTING, StimulationStates.RUNNING)
                            else current_status
                            for current_status in system_state["stimulation_protocol_statuses"]
                        ]
                    system_state_updates["stimulation_protocol_statuses"] = stim_status_updates
                    await self._queues["to"]["instrument_comm"].put({"command": command})
                case {"command": "set_stim_protocols", "stim_info": stim_info}:
                    system_state_updates["stim_info"] = stim_info
                    chunked_stim_info, *_ = chunk_protocols_in_stim_info(stim_info)
                    await self._queues["to"]["instrument_comm"].put(
                        {**communication, "stim_info": chunked_stim_info}
                    )
                case {"command": "start_stim_checks", "well_indices": well_indices}:
                    system_state_updates["stimulator_circuit_statuses"] = {
                        well_idx: StimulatorCircuitStatuses.CALCULATING.name.lower()
                        for well_idx in well_indices
                    }
                    await self._queues["to"]["instrument_comm"].put(communication)
                case invalid_comm:
                    raise NotImplementedError(f"Invalid communication from Server: {invalid_comm}")

            if system_state_updates:
                await self._system_state_manager.update(system_state_updates)

            if e := communication.get("command_processed_event"):
                e.set()

    async def _handle_comm_from_instrument_comm(self) -> None:
        while True:
            communication = await self._queues["from"]["instrument_comm"].get()

            system_state = self._system_state_manager.data

            system_state_updates: dict[str, Any] = {}

            match communication:
                case {"command": "set_stim_protocols"}:
                    pass  # nothing to do here
                case {"command": "start_stimulation"}:
                    system_state_updates["stimulation_protocol_statuses"] = [StimulationStates.RUNNING] * len(
                        system_state["stim_info"]["protocols"]
                    )
                case {"command": "stop_stimulation"}:
                    pass  # Tanner (3/31/23): let the stim status updates handle setting all the running statuses back to False
                case {"command": "stim_status_update", "protocols_completed": protocols_completed}:
                    system_state_updates["stimulation_protocol_statuses"] = list(
                        system_state["stimulation_protocol_statuses"]
                    )
                    for protocol_idx in protocols_completed:
                        system_state_updates["stimulation_protocol_statuses"][
                            protocol_idx
                        ] = StimulationStates.INACTIVE
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
                        await self._queues["to"]["server"].put(
                            {
                                "communication_type": "barcode_update",
                                "barcode_type": barcode_type,
                                "new_barcode": barcode,
                            }
                        )
                case {"command": "get_metadata", **metadata}:
                    system_state_updates["instrument_metadata"] = metadata
                case {"command": "firmware_update_complete", "firmware_type": firmware_type}:
                    key = f"{firmware_type}_firmware_update"
                    fw_version = system_state[key]
                    # also delete the local files if necessary
                    if not system_state["firmware_updates_require_download"]:
                        fw_file_path = os.path.join(
                            system_state["base_directory"],
                            FW_UPDATE_SUBDIR,
                            f"{firmware_type}-{fw_version}.bin",
                        )
                        os.remove(fw_file_path)
                    system_state_updates[key] = None
                case invalid_comm:
                    raise NotImplementedError(f"Invalid communication from InstrumentComm: {invalid_comm}")

            if system_state_updates:
                await self._system_state_manager.update(system_state_updates)

    async def _handle_comm_from_cloud_comm(self) -> None:
        # TODO could make try making these first 4 boiler plates lines reusable somehow
        while True:
            communication = await self._queues["from"]["cloud_comm"].get()

            system_state = self._system_state_manager.data

            system_state_updates: dict[str, Any] = {}

            match communication:
                case {"command": "login"}:
                    # TODO figure out what to do if one user is logged in and then there is a failed attempt to login as a different user
                    success = not communication.get("error")
                    system_state_updates["is_user_logged_in"] = success
                    await self._queues["to"]["server"].put(
                        {"communication_type": "login_result", "success": success}
                    )
                case {"command": "check_versions", "error": _}:
                    # error will be logged by cloud comm
                    system_state_updates["system_status"] = SystemStatuses.IDLE_READY_STATE
                case {"command": "check_versions"}:
                    system_state_updates["firmware_updates_require_download"] = communication["download"]

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
                        logger.info("Firmware update(s) found")

                        system_state_updates["system_status"] = SystemStatuses.UPDATES_NEEDED_STATE
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
                        logger.info("No firmware updates found")
                        system_state_updates["system_status"] = SystemStatuses.IDLE_READY_STATE
                        # since no updates available, also enable auto install of SW update
                        await self._send_enable_sw_auto_install_message()
                case {"command": "download_firmware_updates"}:
                    system_state_updates["system_status"] = SystemStatuses.INSTALLING_UPDATES_STATE
                    # Tanner (1/13/22): send both firmware update commands at once, and make sure channel is sent first.
                    # If both are sent, the second will be ignored by instrument comm until the first install completes
                    for firmware_type in ("channel", "main"):
                        if (version := system_state[f"{firmware_type}_firmware_update"]) is not None:
                            self._queues["to"]["instrument_comm"].put_nowait(
                                {
                                    "command": "start_firmware_update",
                                    "firmware_type": firmware_type,
                                    "file_contents": communication[f"{firmware_type}_firmware_contents"],
                                    "version": version,
                                }
                            )
                case invalid_comm:
                    raise NotImplementedError(f"Invalid communication from CloudComm: {invalid_comm}")

            if system_state_updates:
                await self._system_state_manager.update(system_state_updates)

    # HELPERS

    async def _send_enable_sw_auto_install_message(self) -> None:
        await self._queues["to"]["server"].put(
            {"communication_type": "sw_update", "allow_software_update": True}
        )
