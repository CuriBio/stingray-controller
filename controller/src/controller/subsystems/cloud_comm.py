# -*- coding: utf-8 -*-
# TODO move these to a new subsystem that communicates with cloud
# elif communication_type == "firmware_update":
# if comm_from_monitor["command"] == "check_versions":
#     # set up worker thread
#     self._fw_update_thread_dict = {
#         "communication_type": "firmware_update",
#         "command": comm_from_monitor["command"],
#         "latest_versions": {},
#     }
#     self._fw_update_worker_thread = ErrorCatchingThread(
#         target=check_versions,
#         args=(
#             self._fw_update_thread_dict,
#             comm_from_monitor["serial_number"],
#             comm_from_monitor["main_fw_version"],
#         ),
#         use_error_repr=False,
#     )
#     self._fw_update_worker_thread.start()
# elif comm_from_monitor["command"] == "download_firmware_updates":
#     if not comm_from_monitor["main"] and not comm_from_monitor["channel"]:
#         raise InvalidCommandFromMainError(
#             "Cannot download firmware files if neither firmware type needs an update"
#         )
#     # set up worker thread
#     self._fw_update_thread_dict = {
#         "communication_type": "firmware_update",
#         "command": comm_from_monitor["command"],
#         "main": None,
#         "channel": None,
#     }
#     self._fw_update_worker_thread = ErrorCatchingThread(
#         target=download_firmware_updates,
#         args=(
#             self._fw_update_thread_dict,
#             comm_from_monitor["main"],
#             comm_from_monitor["channel"],
#             comm_from_monitor["customer_id"],
#             comm_from_monitor["username"],
#             comm_from_monitor["password"],
#         ),
#     )
#     self._fw_update_worker_thread.start()
