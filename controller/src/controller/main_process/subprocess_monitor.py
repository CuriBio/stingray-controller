# -*- coding: utf-8 -*-
"""Handling communication between subprocesses and main process."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..utils.generic import wait_tasks_clean

# TODO change these names

# from ..utils.generic import _compare_semver

logger = logging.getLogger(__name__)

# TODO fix all msgs going to the WS: remove "data_type" and "data_json"


class SubprocessMonitor:
    """TODO."""

    def __init__(
        self, system_state: dict[str, Any], queues: dict[str, dict[str, asyncio.Queue[dict[str, Any]]]]
    ) -> None:
        self._system_state = system_state
        self._queues = queues

    async def run(self) -> None:
        tasks = {asyncio.create_task(self._handle_comm_from_server())}
        await wait_tasks_clean(tasks)

    async def _handle_comm_from_server(self) -> None:
        while True:
            communication = await self._queues["from"]["server"].get()

            logger.info(f"Comm from Server: {communication}")

            if communication == "err":  # type: ignore
                raise Exception("raising from monitor")

            await self._queues["to"]["server"].put({"echoing from monitor": communication})

        # TODO
        # communication_type = communication["communication_type"]
        # if communication_type

        # TODO
        # if communication_type == "instrument_naming":
        #     command = communication["command"]
        #     if command == "set_instrument_nickname":
        #         if "instrument_nickname" not in self._system_state:
        #             self._system_state["instrument_nickname"] = dict()
        #         self._system_state["instrument_nickname"][0] = communication["instrument_nickname"]
        #     elif command == "set_instrument_serial_number":
        #         if "instrument_serial_number" not in self._system_state:
        #             self._system_state["instrument_serial_number"] = dict()
        #         self._system_state["instrument_serial_number"][0] = communication["instrument_serial_number"]
        #     else:
        #         raise TODOError(command)
        #     self._queues["to"]["instrument_comm"].put_nowait(communication)
        # elif communication_type == "shutdown":
        #     # TODO fix all this
        #     command = communication["command"]
        #     if command == "hard_stop":
        #         self._hard_stop_and_join_processes_and_log_leftovers(shutdown_server=False, error=False)
        #     elif command == "shutdown_server":
        #         self._process_manager.shutdown_server()
        #     else:
        #         raise NotImplementedError(f"Unrecognized shutdown command from Server: {command}")
        # elif communication_type == "update_user_settings":
        #     new_values = communication["content"]
        #     if new_recording_directory := new_values.get("recording_directory"):
        #         self._queues["to"]["file_writer"].put_nowait(
        #             {"command": "update_directory", "new_directory": new_recording_directory}
        #         )

        #         scrubbed_recordings_dir = redact_sensitive_info_from_path(new_recording_directory)
        #         logger.info(f"Using directory for recording files: {scrubbed_recordings_dir}")
        #     if "customer_id" in new_values:
        #         # TODO Tanner (5/5/22): should probably combine this with config_settings
        #         self._system_state["user_creds"] = {
        #             "customer_id": new_values["customer_id"],
        #             "user_name": new_values["user_name"],
        #             "user_password": new_values["user_password"],
        #         }
        #         self._queues["to"]["file_writer"].put_nowait(
        #             {"command": "update_user_settings", "config_settings": new_values}
        #         )
        #     self._system_state["config_settings"].update(new_values)
        # elif communication_type == "set_latest_software_version":
        #     self._system_state["latest_software_version"] = communication["version"]
        #     # send message to FE if an update is available
        #     try:
        #         softwareUpdateAvailable = _compare_semver(
        #             communication["version"], CURRENT_SOFTWARE_VERSION
        #         )
        #     except ValueError:
        #         softwareUpdateAvailable = False
        #     self._queue_websocket_message(
        #         {
        #             "data_type": "sw_update",
        #             "data_json": json.dumps({"softwareUpdateAvailable": softwareUpdateAvailable}),
        #         }
        #     )
        # elif communication_type == "firmware_update_confirmation":
        #     self._system_state["firmware_update_accepted"] = communication["update_accepted"]
        # elif communication_type == "stimulation":
        #     command = communication["command"]
        #     if command == "setStimStatus":
        #         self._queues["to"]["instrument_comm"].put_nowait(
        #             {
        #                 "communication_type": communication_type,
        #                 "command": "start_stimulation" if communication["status"] else "stopStimulation",
        #             }
        #         )
        #     elif command == "set_protocols":
        #         self._system_state["stimulation_info"] = communication["stim_info"]
        #         self._queues["to"]["instrument_comm"].put_nowait(communication)
        #         self._queues["to"]["file_writer"].put_nowait(communication)
        #     elif command == "start_stim_checks":
        #         self._system_state["stimulatorCircuitStatuses"] = {
        #             well_idx: StimulatorCircuitStatuses.CALCULATING.name.lower()
        #             for well_idx in communication["well_indices"]
        #         }
        #         self._queues["to"]["instrument_comm"].put_nowait(communication)
        #     else:
        #         # Tanner (8/9/21): could make this a custom error if needed
        #         raise NotImplementedError(f"Unrecognized stimulation command from Server: {command}")
        # elif communication_type == "calibration":
        #     # Tanner (12/10/21): run_calibration is currently the only calibration command
        #     self._system_state["system_status"] = CALIBRATING_STATE
        #     self._queues["to"]["instrument_comm"].put_nowait(dict(START_MANAGED_ACQUISITION_COMMUNICATION))

        #     system_state_copy = copy.deepcopy(self._system_state)  # type: ignore

        #     # Tanner (12/10/21): set this manually here since a start_managed_acquisition command response has not been received yet
        #     system_state_copy["utc_timestamps_of_beginning_of_data_acquisition"] = [
        #         datetime.datetime.utcnow()
        #     ]

        #     self._queues["to"]["file_writer"].put_nowait(
        #         _create_start_recording_command(system_state_copy, is_calibration_recording=True)
        #     )
        #     self._queues["to"]["file_writer"].put_nowait(
        #         {
        #             "communication_type": "recording",
        #             "command": "stop_recording",
        #             "timepoint_to_stop_recording_at": (
        #                 CALIBRATION_RECORDING_DUR_SECONDS * MICRO_TO_BASE_CONVERSION
        #             ),
        #             "is_calibration_recording": True,
        #         }
        #     )
        # elif communication_type == "recording":
        #     command = communication["command"]
        #     if command == "stop_recording":
        #         self._system_state["system_status"] = LIVE_VIEW_ACTIVE_STATE
        #     elif command == "start_recording":
        #         self._system_state["system_status"] = RECORDING_STATE
        #     elif command == "update_recording_name":
        #         pass
        #     else:
        #         raise TODOError(command)
        #     self._queues["to"]["file_writer"].put_nowait(communication)
        # elif communication_type == "acquisition_manager":
        #     command = communication["command"]
        #     if command == "start_managed_acquisition":
        #         self._system_state["system_status"] = BUFFERING_STATE
        #         self._queues["to"]["instrument_comm"].put_nowait(communication)
        #         self._queues["to"]["data_analyzer"].put_nowait(communication)
        #     elif command == "stop_managed_acquisition":
        #         # need to send stop command to the process the furthest downstream the data path first then move upstream
        #         self._queues["to"]["data_analyzer"].put_nowait(communication)
        #         self._queues["to"]["file_writer"].put_nowait(communication)
        #         self._queues["to"]["instrument_comm"].put_nowait(communication)
        #     else:
        #         raise TODOError(f"Invalid command: {command} for communication_type: {communication_type}")
        # elif communication_type == "mag_finding_analysis":
        #     # this comm type when coming from the server currently only has one possible command: "start_mag_analysis"
        #     self._queues["to"]["data_analyzer"].put_nowait(communication)
        # else:
        #     raise TODOError(f"Invalid communication_type: {communication_type}")

    # # TODO ?
    # def _report_fatal_error(self, the_err: Exception) -> None:
    #     stack_trace = get_formatted_stack_trace(the_err)
    #     logger.error(f"Error raised by {type(self).__name__}\n{stack_trace}")
    #     if self._process_manager.are_subprocess_start_ups_complete():
    #         self._hard_stop_and_join_processes_and_log_leftovers(shutdown_server=False)
    #     self._process_manager.shutdown_server()

    # # TODO loop all these, could maybe use a decorator for this
    # async def handle_comm_from_file_writer(self) -> None:
    #     communication = await self._queues["from"]["file_writer"].get()

    #     communication_type = communication["communication_type"]
    #     if communication_type == "update_upload_status":
    #         self._queue_websocket_message(communication["content"])
    #     elif communication_type == "file_finalized":
    #         if (
    #             self._system_state["system_status"] == CALIBRATING_STATE
    #             and communication.get("message") == "all_finals_finalized"
    #         ):
    #             self._system_state["system_status"] = CALIBRATED_STATE
    #             # need to send stop command to the process the furthest downstream the data path first then move upstream
    #             stop_comm = {**STOP_MANAGED_ACQUISITION_COMMUNICATION, "is_calibration_recording": True}
    #             self._queues["to"]["file_writer"].put_nowait(stop_comm)
    #             self._queues["to"]["instrument_comm"].put_nowait(stop_comm)
    #     elif communication_type == "corrupt_file_detected":
    #         corrupt_files = communication["corrupt_files"]
    #         self._queue_websocket_message(
    #             {
    #                 "data_type": "corrupt_files_alert",
    #                 "data_json": json.dumps({"corrupt_files_found": corrupt_files}),
    #             }
    #         )
    #     elif (
    #         communication_type == "mag_finding_analysis"
    #         and communication["command"] == "update_recording_name"
    #     ):
    #         self._queues["to"]["data_analyzer"].put_nowait(
    #             {
    #                 "communication_type": "mag_finding_analysis",
    #                 "command": "start_recording_snapshot",
    #                 "recording_path": communication["recording_path"],
    #             }
    #         )

    #     # Tanner (12/13/21): redact file/folder path after handling comm in case the actual file path is needed
    #     for sensitive_key in ("file_path", "file_folder", "recording_path"):
    #         if sensitive_value := communication.get(sensitive_key):
    #             communication[sensitive_key] = redact_sensitive_info_from_path(sensitive_value)
    #     # Tanner (1/11/21): Unsure why the back slashes are duplicated when converting the communication dict to string. Using replace here to remove the duplication, not sure if there is a better way to solve or avoid this problem
    #     logger.info(f"Communication from the File Writer: {communication}".replace(r"\\", "\\"))

    # async def handle_comm_from_data_analyzer(self) -> None:
    #     communication = await self._queues["from"]["data_analyzer"].get()

    #     communication_type = communication["communication_type"]

    #     if communication_type == "mag_analysis_complete":
    #         data_type = communication["content"]["data_type"]
    #         comm_copy = {
    #             "communication_type": "mag_analysis_complete",
    #             # make a shallow copy so all the data isn't copied
    #             "content": copy.copy(communication["content"]),
    #         }
    #         if data_type == "recording_snapshot_data":
    #             comm_copy["content"].pop("data_json")
    #         comm_str = str(comm_copy)
    #     else:
    #         comm_str = str(communication)
    #     logger.info(f"Communication from the Data Analyzer: {comm_str}")

    #     # TODO remove this msg from DA
    #     # if communication_type == "data_available":
    #     if communication_type == "mag_analysis_complete":
    #         self._queue_websocket_message(communication["content"])
    #     elif communication_type == "acquisition_manager":
    #         if communication["command"] == "stop_managed_acquisition":
    #             await self._queues["outgoing_data_stream"].drain()

    # async def handle_outgoing_data_stream(self) -> None:
    #     try:
    #         num_packets_available = 0

    #         while True:
    #             # TODO figure out how to interrupt this
    #             outgoing_data = await self._queues["outgoing_data_stream"].get()

    #             if self._system_state["system_status"] == BUFFERING_STATE:
    #                 num_packets_available += 1
    #                 if num_packets_available == 2:
    #                     self._system_state["system_status"] = LIVE_VIEW_ACTIVE_STATE

    #             self._queue_websocket_message(outgoing_data)
    #     except asyncio.CancelledError:
    #         return

    # async def handle_comm_from_instrument_comm(self) -> None:
    #     # TODO Tanner (10/25/21): refactor this into smaller methods
    #     communication = await self._queues["from"]["instrument_comm"].get()

    #     communication_type = communication["communication_type"]
    #     command = communication.get("command")

    #     # Tanner (1/20/21): items in communication dict are used after these log messages are generated, so need to create a copy of the dict when redacting info
    #     if "instrument_nickname" in communication:
    #         comm_copy = copy.deepcopy(communication)
    #         comm_copy["instrument_nickname"] = get_redacted_string(len(comm_copy["instrument_nickname"]))
    #         comm_str = str(comm_copy)
    #     elif communication_type == "metadata_comm":
    #         comm_copy = copy.deepcopy(communication)
    #         comm_copy["metadata"][INSTRUMENT_NICKNAME_UUID] = get_redacted_string(
    #             len(comm_copy["metadata"][INSTRUMENT_NICKNAME_UUID])
    #         )
    #         comm_str = str(comm_copy)
    #     elif communication_type == "stimulation" and command == "start_stim_checks":
    #         comm_copy = copy.deepcopy(communication)
    #         for sub_dict_name in ("stimulatorCircuitStatuses", "adc_readings"):
    #             sub_dict = comm_copy[sub_dict_name]
    #             for well_idx in sorted(sub_dict):
    #                 well_name = GENERIC_24_WELL_DEFINITION.get_well_name_from_well_index(well_idx)
    #                 sub_dict[well_name] = sub_dict.pop(well_idx)
    #         comm_str = str(comm_copy)
    #     else:
    #         comm_str = str(communication)
    #     # Tanner (1/11/21): Unsure why the back slashes are duplicated when converting the communication dict to string. Using replace here to remove the duplication, not sure if there is a better way to solve or avoid this problem
    #     logger.info(f"Communication from the Instrument Controller: {comm_str}".replace(r"\\", "\\"))
    #     # TODO rename "instrument comm" stuff to "instrument controller"

    #     if communication_type == "acquisition_manager":
    #         if command == "start_managed_acquisition":
    #             self._system_state["utc_timestamps_of_beginning_of_data_acquisition"] = [
    #                 communication["timestamp"]
    #             ]
    #             self._handle_data_stream_task = asyncio.create_task(self.handle_outgoing_data_stream())
    #             # TODO schedule handle_outgoing_data_stream task
    #         elif command == "stop_managed_acquisition":
    #             if not communication.get("is_calibration_recording", False):
    #                 self._system_state["system_status"] = CALIBRATED_STATE
    #                 self._handle_data_stream_task.cancel()
    #                 await self._handle_data_stream_task
    #         else:
    #             raise NotImplementedError(  # TODO make a single generic error for all these. Also have code cov ignore it
    #                 f"Unrecognized acquisition_manager command from Instrument Comm: {command}"
    #             )
    #     elif communication_type == "stimulation":
    #         if command == "start_stimulation":
    #             stim_running_list = [False] * 24
    #             protocolAssignments = self._system_state["stimulation_info"]["protocolAssignments"]
    #             for well_name, assignment in protocolAssignments.items():
    #                 if not assignment:
    #                     continue
    #                 well_idx = GENERIC_24_WELL_DEFINITION.get_well_index_from_well_name(well_name)
    #                 stim_running_list[well_idx] = True
    #             self._system_state["stimulation_running"] = stim_running_list
    #         elif command == "stopStimulation":
    #             self._system_state["stimulation_running"] = [False] * 24
    #         elif command == "status_update":
    #             # ignore stim status updates if stim was already stopped manually
    #             for well_idx in communication["wells_done_stimulating"]:
    #                 self._system_state["stimulation_running"][well_idx] = False
    #         elif command == "start_stim_checks":
    #             key = "stimulatorCircuitStatuses"
    #             stimulatorCircuitStatuses = communication[key]
    #             self._system_state[key] = stimulatorCircuitStatuses
    #             self._queue_websocket_message(
    #                 {"data_type": key, "data_json": json.dumps(stimulatorCircuitStatuses)}
    #             )
    #     elif communication_type == "board_connection_status_change":
    #         board_idx = communication["board_index"]
    #         self._system_state["in_simulationMode"] = not communication[
    #             "is_connected"
    #         ]  # TODO change the name of this
    #     elif communication_type == "barcode_comm":
    #         barcode = communication["barcode"]
    #         if "barcodes" not in self._system_state:
    #             self._system_state["barcodes"] = dict()

    #         # TODO remove all multi-board support
    #         board_idx = communication["board_idx"]
    #         barcode_type = "stim_barcode" if barcode.startswith("MS") else "plate_barcode"
    #         if board_idx not in self._system_state["barcodes"]:
    #             self._system_state["barcodes"][board_idx] = dict()
    #         elif self._system_state["barcodes"][board_idx].get(barcode_type) == barcode:
    #             return

    #         barcode_entry = {barcode_type: barcode}
    #         self._system_state["barcodes"][board_idx].update(barcode_entry)
    #         # send message to FE
    #         barcode_update_message = {"communication_type": "barcode_update", "new_barcode": barcode_entry}
    #         self._queue_websocket_message(barcode_update_message)
    #     elif communication_type == "metadata_comm":
    #         board_idx = communication["board_index"]
    #         # remove keys that aren't UUIDs as these don't need to be stored. They are only included in the comm so that the values are logged
    #         for key in list(communication["metadata"].keys()):
    #             if not isinstance(key, uuid.UUID):  # type: ignore # queue is defined containing dicts with str keys, but sometimes has UUIDs
    #                 communication["metadata"].pop(key)
    #         self._system_state["instrument_metadata"] = {board_idx: communication["metadata"]}
    #     elif communication_type == "firmware_update":
    #         if command == "check_versions":
    #             if "error" in communication:
    #                 self._system_state["system_status"] = CALIBRATION_NEEDED_STATE
    #             else:
    #                 required_sw_for_fw = communication["latest_versions"]["sw"]
    #                 latest_main_fw = communication["latest_versions"]["main-fw"]
    #                 latest_channel_fw = communication["latest_versions"]["channel-fw"]
    #                 min_sw_version_unavailable = _compare_semver(
    #                     required_sw_for_fw, self._system_state["latest_software_version"]
    #                 )
    #                 main_fw_update_needed = _compare_semver(
    #                     latest_main_fw,
    #                     self._system_state["instrument_metadata"][board_idx][MAIN_FIRMWARE_VERSION_UUID],
    #                 )
    #                 channel_fw_update_needed = _compare_semver(
    #                     latest_channel_fw,
    #                     self._system_state["instrument_metadata"][board_idx][CHANNEL_FIRMWARE_VERSION_UUID],
    #                 )
    #                 if (main_fw_update_needed or channel_fw_update_needed) and not min_sw_version_unavailable:
    #                     self._system_state["firmware_updates_needed"] = {
    #                         "main": latest_main_fw if main_fw_update_needed else None,
    #                         "channel": latest_channel_fw if channel_fw_update_needed else None,
    #                     }
    #                     self._system_state["system_status"] = UPDATES_NEEDED_STATE
    #                     self._queue_websocket_message(
    #                         {
    #                             "data_type": "fw_update",
    #                             "data_json": json.dumps(
    #                                 {
    #                                     "firmwareUpdateAvailable": True,
    #                                     "channel_fw_update": channel_fw_update_needed,
    #                                 }
    #                             ),
    #                         }
    #                     )
    #                 else:
    #                     # if no updates found, enable auto install of SW update and switch to calibration needed state
    #                     self._send_enable_sw_auto_install_message()
    #                     self._system_state["system_status"] = CALIBRATION_NEEDED_STATE
    #         elif command == "download_firmware_updates":
    #             if "error" in communication:
    #                 self._system_state["system_status"] = UPDATE_ERROR_STATE
    #             else:
    #                 self._system_state["system_status"] = INSTALLING_UPDATES_STATE
    #                 # Tanner (1/13/22): send both firmware update commands at once, and make sure channel is sent first. If both are sent, the second will be ignored until the first install completes
    #                 for firmware_type in ("channel", "main"):
    #                     new_version = self._system_state["firmware_updates_needed"][firmware_type]
    #                     if new_version is not None:
    #                         self._queues["to"]["instrument_comm"].put_nowait(
    #                             {
    #                                 "communication_type": "firmware_update",
    #                                 "command": "start_firmware_update",
    #                                 "firmware_type": firmware_type,
    #                             }
    #                         )
    #         elif command == "update_completed":
    #             firmware_type = communication["firmware_type"]
    #             self._system_state["firmware_updates_needed"][firmware_type] = None
    #             if all(val is None for val in self._system_state["firmware_updates_needed"].values()):
    #                 self._send_enable_sw_auto_install_message()
    #                 self._system_state["system_status"] = UPDATES_COMPLETE_STATE

    # async def check_for_error_in_subprocesses(self) -> None:
    #     coros = []

    #     # check for errors first
    #     for error_queue, sub_process in (
    #         (self._queues["error"]["instrument_comm"], self._process_manager.instrument_comm_process),
    #         (self._queues["error"]["file_writer"], self._process_manager.file_writer_process),
    #         (self._queues["error"]["data_analyzer"], self._process_manager.data_analyzer_process),
    #     ):

    #         async def foo():
    #             communication = await error_queue.get()
    #             return sub_process, communication

    #         coros.append(foo())

    #     done, _ = asyncio.wait(coros, return_when=asyncio.FIRST_COMPLETED)
    #     self._handle_error_in_subprocess(*done.pop().result())

    # ###############

    # def handle_system_start_up(self) -> None:
    #     board_idx = 0

    #     # make sure system status is up to date
    #     if self._system_state["system_status"] == SERVER_INITIALIZING_STATE:
    #         self._check_if_server_is_ready()
    #     elif self._system_state["system_status"] == SERVER_READY_STATE:
    #         self._system_state["system_status"] = INSTRUMENT_INITIALIZING_STATE
    #     elif self._system_state["system_status"] == INSTRUMENT_INITIALIZING_STATE:
    #         if (
    #             "in_simulationMode" not in self._system_state
    #             or "instrument_metadata" not in self._system_state
    #         ):
    #             pass  # need to wait for these values before proceeding with state transition
    #         elif self._system_state["in_simulationMode"]:
    #             self._system_state["system_status"] = CALIBRATION_NEEDED_STATE
    #         elif self._system_state["latest_software_version"] is not None:
    #             self._system_state["system_status"] = CHECKING_FOR_UPDATES_STATE
    #             # send command to instrument comm process to check for firmware updates
    #             instrument_metadata = self._system_state["instrument_metadata"][board_idx]
    #             to_instrument_comm_queue = self._process_manager.queue_container.to_instrument_comm(board_idx)
    #             to_instrument_comm_queue.put_nowait(
    #                 {
    #                     "communication_type": "firmware_update",
    #                     "command": "check_versions",
    #                     "serial_number": instrument_metadata[INSTRUMENT_SERIAL_NUMBER_UUID],
    #                     "main_fw_version": instrument_metadata[MAIN_FIRMWARE_VERSION_UUID],
    #                 }
    #             )
    #     elif self._system_state["system_status"] == UPDATES_NEEDED_STATE:
    #         if "firmware_update_accepted" not in self._system_state:
    #             pass  # need to wait for this value
    #         elif self._system_state["firmware_update_accepted"]:
    #             if "customer_id" in self._system_state.get("user_creds", {}):
    #                 self._start_firmware_update()
    #             else:
    #                 # Tanner (1/25/22): setting this value to empty dict to indicate that user input prompt has been sent
    #                 self._system_state["user_creds"] = {}
    #                 self._send_user_creds_prompt_message()
    #         else:
    #             self._system_state["system_status"] = CALIBRATION_NEEDED_STATE

    # def _check_if_server_is_ready(self) -> None:
    #     process_manager = self._process_manager
    #     if (
    #         process_manager.are_subprocess_start_ups_complete()
    #         and self._system_state["websocket_connection_made"]
    #     ):
    #         self._system_state["system_status"] = SERVER_READY_STATE

    # def _start_firmware_update(self) -> None:
    #     self._system_state["system_status"] = DOWNLOADING_UPDATES_STATE
    #     board_idx = 0
    #     to_instrument_comm_queue = self._process_manager.queue_container.to_instrument_comm(board_idx)
    #     to_instrument_comm_queue.put_nowait(
    #         {
    #             "communication_type": "firmware_update",
    #             "command": "download_firmware_updates",
    #             "main": self._system_state["firmware_updates_needed"]["main"],
    #             "channel": self._system_state["firmware_updates_needed"]["channel"],
    #             "customer_id": self._system_state["user_creds"]["customer_id"],
    #             "username": self._system_state["user_creds"]["user_name"],
    #             "password": self._system_state["user_creds"]["user_password"],
    #         }
    #     )

    # def TODO_____________(self):
    #     # TODO only need to check this during shutdown?
    #     # update status of subprocesses
    #     self._system_state["subprocesses_running"] = self._process_manager.get_subprocesses_running_status()

    # def _send_user_creds_prompt_message(self) -> None:
    #     self._queue_websocket_message(
    #         {"data_type": "prompt_user_input", "data_json": json.dumps({"input_type": "user_creds"})}
    #     )

    # def _send_enable_sw_auto_install_message(self) -> None:
    #     self._queue_websocket_message(
    #         {"data_type": "sw_update", "data_json": json.dumps({"allow_software_update": True})}
    #     )

    # def _queue_websocket_message(self, message_dict: Dict[str, Any]) -> None:
    #     # TODO
    #     data_to_websocket_queue = self._process_manager.queue_container.to_websocket
    #     data_to_websocket_queue.put_nowait(message_dict)

    # ########## !!! ##########

    # def _handle_error_in_subprocess(
    #     self,
    #     process: InfiniteProcess,
    #     error_communication: Tuple[Exception, str],
    # ) -> None:
    #     this_err, this_stack_trace = error_communication
    #     logger.error(f"Error raised by subprocess {process}\n{this_stack_trace}\n{this_err}")

    #     shutdown_server = True

    #     if process == self._process_manager.instrument_comm_process and isinstance(
    #         this_err, (InstrumentError, FirmwareAndSoftwareNotCompatibleError)
    #     ):
    #         if isinstance(this_err, InstrumentError):
    #             this_err_type_mro = type(this_err).mro()
    #             instrument_sub_error_class = this_err_type_mro[this_err_type_mro.index(InstrumentError) - 1]
    #             data = {"error_type": instrument_sub_error_class.__name__}
    #         else:
    #             data = {
    #                 "error_type": type(this_err).__name__,
    #                 "latest_compatible_sw_version": this_err.args[0],
    #             }
    #         self._queue_websocket_message({"data_type": "error", "data_json": json.dumps(data)})
    #     elif self._system_state["system_status"] in (
    #         DOWNLOADING_UPDATES_STATE,
    #         INSTALLING_UPDATES_STATE,
    #     ):
    #         self._system_state["system_status"] = UPDATE_ERROR_STATE
    #         shutdown_server = False

    #     self._hard_stop_and_join_processes_and_log_leftovers(shutdown_server=shutdown_server)

    # def _hard_stop_and_join_processes_and_log_leftovers(
    #     self, shutdown_server: bool = True, error: bool = True
    # ) -> None:
    #     process_items = self._process_manager.hard_stop_and_join_processes(shutdown_server=shutdown_server)
    #     msg = f"Remaining items in process queues: {process_items}".replace(r"\\", "\\")
    #     if error:
    #         logger.error(msg)
    #     else:
    #         logger.info(msg)

    # def soft_stop(self) -> None:
    #     self._process_manager.soft_stop_and_join_processes()

    # def _check_and_handle_websocket_to_main_queue(self) -> None:
    #     process_manager = self._process_manager
    #     to_main_queue = process_manager.queue_container.from_websocket
    #     try:
    #         communication = to_main_queue.get(timeout=MPQUEUE_POLL_PERIOD)
    #     except queue.Empty:
    #         return

    #     communication_type = communication["communication_type"]

    #     if communication_type == "connection_success":
    #         self._system_state["websocket_connection_made"] = True
    #     else:
    #         raise NotImplementedError(f"Unrecognized comm type from websocket: {communication_type}")
