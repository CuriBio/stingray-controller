# -*- coding: utf-8 -*-


import asyncio
import logging
from typing import Any

from ..utils.aio import wait_tasks_clean
from ..utils.generic import handle_system_error


logger = logging.getLogger(__name__)

ERROR_MSG = "IN CLOUD COMM"


class CloudComm:
    """Subsystem that manages communication with cloud services."""

    def __init__(
        self,
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
    ) -> None:
        # comm queues
        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue

        self._customer_id: str | None = None
        self._user_name: str | None = None
        self._user_password: str | None = None

        self._access_token: str | None = None
        self._refresh_token: str | None = None

    # ONE-SHOT TASKS

    async def run(self, system_error_future: asyncio.Future[int]) -> None:
        # TODO ADD MORE LOGGING
        try:
            tasks = {
                asyncio.create_task(self._manage_subtasks()),
                # TODO add other tasks
            }
            exc = await wait_tasks_clean(tasks, error_msg=ERROR_MSG)
            if exc:
                handle_system_error(exc, system_error_future)
        except asyncio.CancelledError:
            logger.info("CloudComm cancelled")
            # TODO await self._attempt_to_upload_log_files_to_s3()
            raise
        finally:
            logger.info("CloudComm shut down")

    async def _get_comm_from_monitor(self) -> dict[str, Any]:
        return await self._from_monitor_queue.get()

    # INFINITE TASKS

    async def _manage_subtasks(self) -> None:
        main_task_name = self._get_comm_from_monitor.__name__

        pending = {asyncio.create_task(self._get_comm_from_monitor(), name=main_task_name)}

        while True:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                res = task.result()
                task_name = task.get_name()
                if task_name == main_task_name:
                    subtask_fn = getattr(self, f"_{res['command']}")
                    pending |= {
                        asyncio.create_task(self._get_comm_from_monitor(), name=main_task_name),
                        asyncio.create_task(subtask_fn(), name=subtask_fn.__name__),
                    }
                else:
                    await self._to_monitor_queue.put({"command": task_name[1:], **res})

    # SUBTASKS

    async def _check_versions(self) -> dict[str, str]:
        # TODO
        return {"error": "some error"}

    # async def _download_firmware_updates(self):
    #     pass  # TODO

    # HELPERS

    # async def _call_route(self):
    #     pass  # TODO


# def call_firmware_download_route(url: str, error_message: str, **kwargs: Any) -> Response:
#     try:
#         response = requests.get(url, **kwargs)
#     except ConnectionError as e:
#         raise FirmwareDownloadError(f"{error_message}") from e

#     if response.status_code != 200:
#         try:
#             message = response.json()["message"]
#         except Exception:
#             message = response.reason
#         raise FirmwareDownloadError(
#             f"{error_message}. Status code: {response.status_code}, Reason: {message}"
#         )

#     return response


# def verify_software_firmware_compatibility(main_fw_version: str) -> None:
#     check_sw_response = call_firmware_download_route(
#         f"https://{CLOUD_API_ENDPOINT}/mantarray/software-range/{main_fw_version}",
#         error_message="Error checking software/firmware compatibility",
#     )
#     range = check_sw_response.json()

#     if not (range["min_sw"] <= VersionInfo.parse(CURRENT_SOFTWARE_VERSION) <= range["max_sw"]):
#         raise FirmwareAndSoftwareNotCompatibleError(range["max_sw"])


# def get_latest_firmware_versions(result_dict: Dict[str, Dict[str, str]], serial_number: str) -> None:
#     get_versions_response = call_firmware_download_route(
#         f"https://{CLOUD_API_ENDPOINT}/mantarray/versions/{serial_number}",
#         error_message="Error getting latest firmware versions",
#     )
#     result_dict["latest_versions"] = get_versions_response.json()["latest_versions"]


# def check_versions(result_dict: Dict[str, Dict[str, str]], serial_number: str, main_fw_version: str) -> None:
#     verify_software_firmware_compatibility(main_fw_version)
#     get_latest_firmware_versions(result_dict, serial_number)


# def download_firmware_updates(
#     result_dict: Dict[str, Any],
#     main_fw_version: Optional[str],
#     channel_fw_version: Optional[str],
#     customer_id: str,
#     username: str,
#     password: str,
# ) -> None:
#     if not main_fw_version and not channel_fw_version:
#         raise FirmwareDownloadError("No firmware types specified")

#     # get access token
#     access_token = get_cloud_api_tokens(customer_id, username, password).access

#     # get presigned download URL(s)
#     presigned_urls: Dict[str, Optional[str]] = {"main": None, "channel": None}
#     for version, fw_type in ((main_fw_version, "main"), (channel_fw_version, "channel")):
#         if version:
#             download_details = call_firmware_download_route(
#                 f"https://{CLOUD_API_ENDPOINT}/mantarray/firmware/{fw_type}/{version}",
#                 headers={"Authorization": f"Bearer {access_token}"},
#                 error_message=f"Error getting presigned URL for {fw_type} firmware",
#             )
#             presigned_urls[fw_type] = download_details.json()["presigned_url"]

#     # download firmware file(s)
#     for fw_type, presigned_url in presigned_urls.items():
#         if presigned_url:
#             download_response = call_firmware_download_route(
#                 presigned_url, error_message=f"Error during download of {fw_type} firmware"
#             )
#             result_dict[fw_type] = download_response.content
