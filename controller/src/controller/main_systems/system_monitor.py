# -*- coding: utf-8 -*-
"""Handling communication between subsystems and server."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from controller.constants import CURRENT_SOFTWARE_VERSION
from controller.constants import StimulatorCircuitStatuses
from controller.constants import SystemStatuses
from controller.utils.state_management import ReadOnlyDict
from controller.utils.state_management import SystemStateManager
from pulse3D.constants import MAIN_FIRMWARE_VERSION_UUID
from pulse3D.constants import MANTARRAY_SERIAL_NUMBER_UUID as INSTRUMENT_SERIAL_NUMBER_UUID

from ..utils.generic import compare_semver
from ..utils.generic import wait_tasks_clean


logger = logging.getLogger(__name__)


class SystemMonitor:
    """TODO."""

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

    async def _handle_system_state_update(self) -> None:
        update_details = await self._system_state_manager.previous_update_queue.get()

        await self._handle_system_status_transition()

        if True:  # TODO check if an update needs to be pushed by looking at values in update_details
            await self._push_status_update(update_details)

    async def _handle_system_status_transition(self) -> None:
        system_state = self._system_state_manager.data

        new_system_status: SystemStatuses | None = None

        # TODO can probably clean this up even more
        match system_state["system_status"]:
            case SystemStatuses.SERVER_INITIALIZING_STATE:
                # Tanner (3/15/23): this state just instantly transitions right now, probably not needed anymore
                new_system_status = SystemStatuses.SERVER_READY_STATE
            case SystemStatuses.SERVER_READY_STATE:
                # Tanner (3/15/23): this state just instantly transitions right now, probably not needed anymore
                new_system_status = SystemStatuses.INSTRUMENT_INITIALIZING_STATE
            case SystemStatuses.INSTRUMENT_INITIALIZING_STATE:
                if "in_simulation_mode" not in system_state or "instrument_metadata" not in system_state:
                    pass  # need to wait for these values before proceeding with state transition
                elif system_state["latest_software_version"] is not None:
                    new_system_status = SystemStatuses.CHECKING_FOR_UPDATES_STATE
                    # send command to instrument comm process to check for firmware updates
                    instrument_metadata = system_state["instrument_metadata"]
                    await self._queues["to"]["instrument_comm"].put(
                        {
                            "communication_type": "firmware_update",
                            "command": "check_versions",
                            "serial_number": instrument_metadata[INSTRUMENT_SERIAL_NUMBER_UUID],
                            "main_fw_version": instrument_metadata[MAIN_FIRMWARE_VERSION_UUID],
                        }
                    )
            case SystemStatuses.CHECKING_FOR_UPDATES_STATE:
                pass  # TODO set some value in the system state that indicates whether or not an update is needed
                # TODO switch to either SystemStatuses.IDLE_READY_STATE or SystemStatuses.UPDATES_NEEDED_STATE
            case SystemStatuses.IDLE_READY_STATE:
                pass  # Tanner (3/15/23): there is currently no way to transition out of this state
            case SystemStatuses.UPDATES_NEEDED_STATE:
                if system_state.get("firmware_update_accepted"):
                    if system_state["user_creds"]:
                        new_system_status = SystemStatuses.DOWNLOADING_UPDATES_STATE
                        await self._queues["to"]["instrument_comm"].put(
                            {
                                "communication_type": "firmware_update",
                                "command": "download_firmware_updates",
                                "main": system_state["firmware_updates_needed"]["main"],
                                "channel": system_state["firmware_updates_needed"]["channel"],
                                "customer_id": system_state["user_creds"]["customer_id"],
                                "username": system_state["user_creds"]["user_name"],
                                "password": system_state["user_creds"]["user_password"],
                            }
                        )
                    else:
                        await self._queues["to"]["server"].put(
                            {"communication_type": "prompt_user_input", "input_type": "user_creds"}
                        )

        if new_system_status:
            await self._system_state_manager.update({"system_status": new_system_status})

    async def _push_status_update(self, update_details: ReadOnlyDict) -> None:
        pass  # TODO

    # COMM HANDLERS

    async def _handle_comm_from_server(self) -> None:
        while True:
            communication = await self._queues["from"]["server"].get()

            logger.info(f"Comm from Server: {communication}")

            # TODO remove this when done testing
            if communication == "err":  # type: ignore
                raise Exception("raising from monitor")
            await self._queues["to"]["server"].put({"echoing from monitor": communication})

            system_state_updates = {}

            match communication:
                case {"command": "update_user_settings", **new_settings}:
                    # Tanner (3/16/23): this assumes that either all or none of these values will be sent
                    if new_user_creds := {
                        key: value
                        for key in ("customer_id", "user_name", "user_password")
                        if (value := new_settings.pop(key))
                    }:
                        system_state_updates["user_creds"] = new_user_creds
                    # all remaining settings fall under config settings
                    if new_settings:
                        # TODO figure out if this sends every setting or just the ones that changed
                        system_state_updates["config_settings"] = new_settings
                case {"command": "set_latest_software_version", "version": version}:
                    system_state_updates["latest_software_version"] = version
                    # send message to FE if indicating if an update is available
                    try:
                        software_update_available = compare_semver(version, CURRENT_SOFTWARE_VERSION)
                    except ValueError:
                        software_update_available = False
                    await self._queues["to"]["server"].put(
                        {
                            "communication_type": "sw_update",
                            "software_update_available": software_update_available,
                        }
                    )
                case {"command": "set_firmware_update_confirmation", "update_accepted": update_accepted}:
                    system_state_updates["firmware_update_accepted"] = update_accepted
                case {"command": "set_stim_status", "status": status}:
                    await self._queues["to"]["instrument_comm"].put(
                        {"command": "start_stimulation" if status else "stop_stimulation"}
                    )
                case {"command": "set_stim_protocols", "stim_info": stim_info}:
                    system_state_updates["stimulation_info"] = stim_info
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
        pass  # TODO

        # TODO Tanner (10/25/21): refactor this into smaller methods
        # communication = await self._queues["from"]["instrument_comm"].get()

        # communication_type = communication["communication_type"]
        # command = communication.get("command")

        # # Tanner (1/20/21): items in communication dict are used after these log messages are generated, so need to create a copy of the dict when redacting info
        # if "instrument_nickname" in communication:
        #     comm_copy = copy.deepcopy(communication)
        #     comm_copy["instrument_nickname"] = get_redacted_string(len(comm_copy["instrument_nickname"]))
        #     comm_str = str(comm_copy)
        # elif communication_type == "metadata_comm":
        #     comm_copy = copy.deepcopy(communication)
        #     comm_copy["metadata"][INSTRUMENT_NICKNAME_UUID] = get_redacted_string(
        #         len(comm_copy["metadata"][INSTRUMENT_NICKNAME_UUID])
        #     )
        #     comm_str = str(comm_copy)
        # elif communication_type == "stimulation" and command == "start_stim_checks":
        #     comm_copy = copy.deepcopy(communication)
        #     for sub_dict_name in ("stimulator_circuit_statuses", "adc_readings"):
        #         sub_dict = comm_copy[sub_dict_name]
        #         for well_idx in sorted(sub_dict):
        #             well_name = GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx)
        #             sub_dict[well_name] = sub_dict.pop(well_idx)
        #     comm_str = str(comm_copy)
        # else:
        #     comm_str = str(communication)
        # # Tanner (1/11/21): Unsure why the back slashes are duplicated when converting the communication dict to string. Using replace here to remove the duplication, not sure if there is a better way to solve or avoid this problem
        # logger.info(f"Communication from the Instrument Controller: {comm_str}".replace(r"\\", "\\"))
        # # TODO rename "instrument comm" stuff to "instrument controller"

        # if communication_type == "acquisition_manager":
        #     if command == "start_managed_acquisition":
        #         self._system_state["utc_timestamps_of_beginning_of_data_acquisition"] = [
        #             communication["timestamp"]
        #         ]
        #         self._handle_data_stream_task = asyncio.create_task(self.handle_outgoing_data_stream())
        #         # TODO schedule handle_outgoing_data_stream task
        #     elif command == "stop_managed_acquisition":
        #         if not communication.get("is_calibration_recording", False):
        #             self._system_state["system_status"] = CALIBRATED_STATE
        #             self._handle_data_stream_task.cancel()
        #             await self._handle_data_stream_task
        #     else:
        #         raise NotImplementedError(  # TODO make a single generic error for all these. Also have code cov ignore it
        #             f"Unrecognized acquisition_manager command from Instrument Comm: {command}"
        #         )
        # elif communication_type == "stimulation":
        #     if command == "start_stimulation":
        #         stim_running_list = [False] * 24
        #         protocol_assignments = self._system_state["stimulation_info"]["protocol_assignments"]
        #         for well_name, assignment in protocol_assignments.items():
        #             if not assignment:
        #                 continue
        #             well_idx = GENERIC_24_WELL_DEFINITION.get_well_index_from_well_name(well_name)
        #             stim_running_list[well_idx] = True
        #         self._system_state["stimulation_running"] = stim_running_list
        #     elif command == "stop_stimulation":
        #         self._system_state["stimulation_running"] = [False] * 24
        #     elif command == "status_update":
        #         # ignore stim status updates if stim was already stopped manually
        #         for well_idx in communication["wells_done_stimulating"]:
        #             self._system_state["stimulation_running"][well_idx] = False
        #     elif command == "start_stim_checks":
        #         key = "stimulator_circuit_statuses"
        #         stimulator_circuit_statuses = communication[key]
        #         self._system_state[key] = stimulator_circuit_statuses
        #         self._queue_websocket_message(
        #             {"data_type": key, "data_json": json.dumps(stimulator_circuit_statuses)}
        #         )
        # elif communication_type == "board_connection_status_change":
        #     board_idx = communication["board_index"]
        #     self._system_state["in_simulation_mode"] = not communication[
        #         "is_connected"
        #     ]  # TODO change the name of this
        # elif communication_type == "barcode_comm":
        #     barcode = communication["barcode"]
        #     if "barcodes" not in self._system_state:
        #         self._system_state["barcodes"] = dict()

        #     # TODO remove all multi-board support
        #     board_idx = communication["board_idx"]
        #     barcode_type = "stim_barcode" if barcode.startswith("MS") else "plate_barcode"
        #     if board_idx not in self._system_state["barcodes"]:
        #         self._system_state["barcodes"][board_idx] = dict()
        #     elif self._system_state["barcodes"][board_idx].get(barcode_type) == barcode:
        #         return

        #     barcode_entry = {barcode_type: barcode}
        #     self._system_state["barcodes"][board_idx].update(barcode_entry)
        #     # send message to FE
        #     barcode_update_message = {"communication_type": "barcode_update", "new_barcode": barcode_entry}
        #     self._queue_websocket_message(barcode_update_message)
        # elif communication_type == "metadata_comm":
        #     board_idx = communication["board_index"]
        #     # remove keys that aren't UUIDs as these don't need to be stored. They are only included in the comm so that the values are logged
        #     for key in list(communication["metadata"].keys()):
        #         if not isinstance(key, uuid.UUID):  # type: ignore # queue is defined containing dicts with str keys, but sometimes has UUIDs
        #             communication["metadata"].pop(key)
        #     self._system_state["instrument_metadata"] = {board_idx: communication["metadata"]}
        # elif communication_type == "firmware_update":
        #     if command == "check_versions":
        #         if "error" in communication:
        #             self._system_state["system_status"] = CALIBRATION_NEEDED_STATE
        #         else:
        #             required_sw_for_fw = communication["latest_versions"]["sw"]
        #             latest_main_fw = communication["latest_versions"]["main-fw"]
        #             latest_channel_fw = communication["latest_versions"]["channel-fw"]
        #             min_sw_version_unavailable = _compare_semver(
        #                 required_sw_for_fw, self._system_state["latest_software_version"]
        #             )
        #             main_fw_update_needed = _compare_semver(
        #                 latest_main_fw,
        #                 self._system_state["instrument_metadata"][board_idx][MAIN_FIRMWARE_VERSION_UUID],
        #             )
        #             channel_fw_update_needed = _compare_semver(
        #                 latest_channel_fw,
        #                 self._system_state["instrument_metadata"][board_idx][CHANNEL_FIRMWARE_VERSION_UUID],
        #             )
        #             if (main_fw_update_needed or channel_fw_update_needed) and not min_sw_version_unavailable:
        #                 self._system_state["firmware_updates_needed"] = {
        #                     "main": latest_main_fw if main_fw_update_needed else None,
        #                     "channel": latest_channel_fw if channel_fw_update_needed else None,
        #                 }
        #                 self._system_state["system_status"] = SystemStatuses.UPDATES_NEEDED_STATE
        #                 self._queue_websocket_message(
        #                     {
        #                         "data_type": "fw_update",
        #                         "data_json": json.dumps(
        #                             {
        #                                 "firmware_update_available": True,
        #                                 "channel_fw_update": channel_fw_update_needed,
        #                             }
        #                         ),
        #                     }
        #                 )
        #             else:
        #                 # if no updates found, enable auto install of SW update and switch to calibration needed state
        #                 self._send_enable_sw_auto_install_message()
        #                 self._system_state["system_status"] = CALIBRATION_NEEDED_STATE
        #     elif command == "download_firmware_updates":
        #         if "error" in communication:
        #             self._system_state["system_status"] = SystemStatuses.UPDATE_ERROR_STATE
        #         else:
        #             self._system_state["system_status"] = SystemStatuses.INSTALLING_UPDATES_STATE
        #             # Tanner (1/13/22): send both firmware update commands at once, and make sure channel is sent first. If both are sent, the second will be ignored until the first install completes
        #             for firmware_type in ("channel", "main"):
        #                 new_version = self._system_state["firmware_updates_needed"][firmware_type]
        #                 if new_version is not None:
        #                     self._queues["to"]["instrument_comm"].put_nowait(
        #                         {
        #                             "communication_type": "firmware_update",
        #                             "command": "start_firmware_update",
        #                             "firmware_type": firmware_type,
        #                         }
        #                     )
        #     elif command == "update_completed":
        #         firmware_type = communication["firmware_type"]
        #         self._system_state["firmware_updates_needed"][firmware_type] = None
        #         if all(val is None for val in self._system_state["firmware_updates_needed"].values()):
        #             self._send_enable_sw_auto_install_message()
        #             self._system_state["system_status"] = SystemStatuses.UPDATES_COMPLETE_STATE

    async def _handle_comm_from_cloud_comm(self) -> None:
        pass  # TODO

    # ###############

    # def _send_enable_sw_auto_install_message(self) -> None:
    #     self._queue_websocket_message(
    #         {"data_type": "sw_update", "data_json": json.dumps({"allow_software_update": True})}
    #     )
