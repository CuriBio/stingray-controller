# -*- coding: utf-8 -*-


import asyncio
import copy
import logging
import os
import tempfile
from typing import Any
from typing import Coroutine
import zipfile

from controller.utils.logging import get_redacted_string
import httpx
from httpx import Response
from semver import VersionInfo

from ..constants import AuthCreds
from ..constants import AuthTokens
from ..constants import CLOUD_API_ENDPOINT
from ..constants import CLOUD_PULSE3D_ENDPOINT
from ..constants import ConfigSettings
from ..constants import CURRENT_SOFTWARE_VERSION
from ..exceptions import FirmwareAndSoftwareNotCompatibleError
from ..exceptions import FirmwareDownloadError
from ..exceptions import LoginFailedError
from ..exceptions import RefreshFailedError
from ..exceptions import RequestFailedError
from ..utils.aio import clean_up_tasks
from ..utils.aio import wait_tasks_clean
from ..utils.files import check_for_local_firmware_versions
from ..utils.files import get_file_md5
from ..utils.generic import handle_system_error


logger = logging.getLogger(__name__)

ERROR_MSG = "IN CLOUD COMM"


def _get_tokens(response_json: dict[str, Any]) -> AuthTokens:
    return AuthTokens(access=response_json["access"]["token"], refresh=response_json["refresh"]["token"])


def _load_fw_files(command: dict[str, Any]) -> dict[str, bytes]:
    fw_update_dir_path = command["fw_update_dir_path"]

    subtask_res = {}

    for fw_type in ("main", "channel"):
        if version := command[fw_type]:
            with open(os.path.join(fw_update_dir_path, f"{fw_type}-{version}.bin"), "rb") as fw_file:
                subtask_res[f"{fw_type}_firmware_contents"] = fw_file.read()

    return subtask_res


class CloudComm:
    """Subsystem that manages communication with cloud services."""

    def __init__(
        self,
        from_monitor_queue: asyncio.Queue[dict[str, Any]],
        to_monitor_queue: asyncio.Queue[dict[str, Any]],
        **config_settings: dict[str, Any],
    ) -> None:
        # comm queues
        self._from_monitor_queue = from_monitor_queue
        self._to_monitor_queue = to_monitor_queue

        # TODO figure out if there is a better way to define this default value for auto_upload_on_completion,
        # or if it should also become a command line arg
        self._config = ConfigSettings(**config_settings, auto_upload_on_completion=True)

        self._creds: AuthCreds | None = None
        self._tokens: AuthTokens | None = None

        self._client: httpx.AsyncClient | None = None

    # ONE-SHOT TASKS

    async def run(self, system_error_future: asyncio.Future[int]) -> None:
        # TODO ADD MORE LOGGING
        logger.info("Starting CloudComm")

        try:
            self._client = httpx.AsyncClient()
            tasks = {
                asyncio.create_task(self._manage_subtasks()),
                # TODO add other tasks?
            }
            await wait_tasks_clean(tasks, error_msg=ERROR_MSG)
        except asyncio.CancelledError:
            logger.info("CloudComm cancelled")
            raise
        except BaseException as e:
            logger.exception(ERROR_MSG)
            handle_system_error(e, system_error_future)
        finally:
            # TODO consider making this a public function and calling in main after this is shut down
            await self._attempt_to_upload_log_files_to_s3()
            self._client = None
            logger.info("CloudComm shut down")

    async def _get_comm_from_monitor(self) -> dict[str, Any]:
        return await self._from_monitor_queue.get()

    async def _attempt_to_upload_log_files_to_s3(self) -> None:
        if not self._creds:
            logger.info("No user logged in, skipping upload of log files.")
            return
        if not self._config.auto_upload_on_completion:
            logger.info("Auto-upload is not turned on, skipping upload of log files.")
            return

        if not self._config.log_directory:
            logger.info("Skipping upload of log files to s3 because no log files were created")
            return

        logger.info("Attempting upload of log files to s3")

        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # TODO put a timeout on this
                await self._upload_to_s3(
                    self._config.log_directory, upload_type="log", dir_for_zipping=tmp_dir
                )
        except BaseException:
            logger.exception("Failed to upload log files to s3")
        else:
            logger.info("Successfully uploaded session logs to s3")

    # INFINITE TASKS

    async def _manage_subtasks(self) -> None:
        main_task_name = self._get_comm_from_monitor.__name__

        pending = {asyncio.create_task(self._get_comm_from_monitor(), name=main_task_name)}

        while True:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                task_name = task.get_name()
                try:
                    res = task.result()
                except BaseException as e:
                    # TODO make sure this works as expected. Also see if asyncio.CancelledError needs to be handled differently
                    await clean_up_tasks(pending)
                    raise e

                if task_name == main_task_name:
                    comm_from_monitor = res
                    try:
                        subtask_fn = getattr(self, f"_{comm_from_monitor['command']}")
                    except AttributeError as e:
                        raise NotImplementedError(
                            f"CloudComm received invalid comm from SystemMonitor: {comm_from_monitor}"
                        ) from e

                    # remove this before sending command
                    comm_from_monitor.pop("command")
                    wrapped_subtask = self._sub_task_wrapper(subtask_fn(comm_from_monitor))

                    pending |= {
                        asyncio.create_task(self._get_comm_from_monitor(), name=main_task_name),
                        asyncio.create_task(wrapped_subtask, name=subtask_fn.__name__),
                    }
                else:
                    command = task_name[1:]
                    # TODO make a general dict redaction function and make sure to call it before logging in all subsystems
                    self._log_sub_task_result(command, res)
                    await self._to_monitor_queue.put({"command": command, **res})

    # SUBTASKS

    async def _login(self, command: dict[str, str]) -> dict[str, str]:
        subtask_res = {}
        try:
            await self._get_cloud_api_tokens(**command)
        except LoginFailedError:
            subtask_res["error"] = "Invalid credentials"
        except httpx.ConnectError:
            subtask_res["error"] = "No internet connection"
        else:
            username = self._creds.username  # type: ignore  # mypy doesn't realize this will never be None here
            logger.info(f"User '{username}' successfully logged in")
        # TODO also handle NetworkError?

        return subtask_res

    # TODO make sure entire FW update process (including InstrumentComm portion) has sufficient logging
    async def _check_versions(self, command: dict[str, str]) -> dict[str, Any]:
        try:
            if local_firmware_versions := check_for_local_firmware_versions(command["fw_update_dir_path"]):
                return local_firmware_versions
        except Exception:  # nosec B110
            # catch all errors here to avoid user error preventing the next checks
            pass

        check_sw_response = await self._request(
            "get",
            f"https://{CLOUD_API_ENDPOINT}/mantarray/software-range/{command['main_fw_version']}",
            auth_required=False,
            error_message="Error checking software/firmware compatibility",
        )
        range = check_sw_response.json()

        try:
            sw_version_semver = VersionInfo.parse(CURRENT_SOFTWARE_VERSION)
        except ValueError:
            pass  # CURRENT_SOFTWARE_VERSION will not be a valid semver in dev mode
        else:
            if not (range["min_sting_sw"] <= sw_version_semver <= range["max_sting_sw"]):
                raise FirmwareAndSoftwareNotCompatibleError(range["max_sting_sw"])

        get_versions_response = await self._request(
            "get",
            f"https://{CLOUD_API_ENDPOINT}/mantarray/versions/{command['serial_number']}",
            auth_required=False,
            error_message="Error getting latest firmware versions",
        )
        return {"latest_versions": get_versions_response.json()["latest_versions"], "download": True}

    async def _download_firmware_updates(self, command: dict[str, str]) -> dict[str, bytes]:
        try:
            if command["fw_update_dir_path"]:
                return _load_fw_files(command)

            presigned_urls = {}

            # get presigned download URL(s)
            for fw_type in ("main", "channel"):
                if version := command[fw_type]:
                    download_details = await self._request(
                        "get",
                        f"https://{CLOUD_API_ENDPOINT}/mantarray/firmware/{fw_type}/{version}",
                        auth_required=True,
                        error_message=f"Error getting presigned URL for {fw_type} firmware download",
                    )
                    presigned_urls[fw_type] = download_details.json()["presigned_url"]

            if not presigned_urls:
                raise NotImplementedError("No firmware types specified")

            subtask_res = {}

            # download firmware file(s)
            for fw_type, presigned_url in presigned_urls.items():
                download_response = await self._request(
                    "get",
                    presigned_url,
                    auth_required=False,
                    error_message=f"Error during download of {fw_type} firmware",
                )
                subtask_res[f"{fw_type}_firmware_contents"] = download_response.content
        except BaseException as e:
            # TODO see if asyncio.CancelledError needs to be handled differently?
            raise FirmwareDownloadError() from e

        return subtask_res

    # HELPERS

    def _log_sub_task_result(self, command: str, result: dict[str, Any]) -> None:
        result = copy.copy(result)

        for key in result:
            if "content" in key:
                result[key] = get_redacted_string(4)

        logger.info(f"Result of '{command}' command: {result}")

    async def _sub_task_wrapper(self, coro: Coroutine[Any, Any, dict[str, str]]) -> dict[str, str]:
        try:
            return await coro
        except (RequestFailedError, httpx.ConnectError) as e:
            return {"error": repr(e)}

    async def _get_cloud_api_tokens(self, customer_id: str, username: str, password: str) -> None:
        if self._client is None:
            raise NotImplementedError("self._client should never be None here")

        res = await self._client.post(
            f"https://{CLOUD_API_ENDPOINT}/users/login",
            json={
                "customer_id": customer_id,
                "username": username,
                "password": password,
                "service": "pulse3d",
                "client_type": f"stingray:{CURRENT_SOFTWARE_VERSION}",
            },
        )

        if res.status_code != 200:
            raise LoginFailedError(res.status_code)

        self._tokens = _get_tokens(res.json()["tokens"])
        self._creds = AuthCreds(customer_id=customer_id, username=username, password=password)

    async def _refresh_cloud_api_tokens(self) -> None:
        """Use refresh token to get new set of auth tokens."""
        if self._client is None:
            raise NotImplementedError("self._client should never be None here")
        if self._tokens is None:
            raise NotImplementedError("self._tokens should never be None here")

        res = await self._client.post(
            f"https://{CLOUD_API_ENDPOINT}/users/refresh",
            headers={"Authorization": f"Bearer {self._tokens.refresh}"},
        )
        if res.status_code != 201:
            raise RefreshFailedError(res.status_code)

        self._tokens = _get_tokens(res.json()["tokens"])

    async def _request_with_refresh(
        self, method: str, url: str, **request_kwargs: dict[str, Any]
    ) -> Response:
        """Make request, refresh once if needed, and try request once more.

        This is primarily for use inside _request.
        """
        if self._client is None:
            raise NotImplementedError("self._client should never be None here")

        res = await self._client.request(method, url, **request_kwargs)
        # if auth token expired then request will return 401 code
        if res.status_code == 401:
            # TODO check service worker to see how refresh mutex is handled

            # get new tokens and try request once more
            # TODO try logging in again if this also fails
            self.tokens = self._refresh_cloud_api_tokens()

            res = await self._client.request(method, url, **request_kwargs)

        return res

    async def _request(
        self,
        method: str,
        url: str,
        *,
        auth_required: bool,
        error_message: str,
        **request_kwargs: dict[str, Any],
    ) -> Response:
        """Make a request.

        This is the primary function that should be used to handle requests.
        """
        if auth_required:
            if self._tokens is None:
                raise NotImplementedError("self._tokens should never be None here")
            request_kwargs["headers"] = {"Authorization": f"Bearer {self._tokens.access}"}

        res = await self._request_with_refresh(method, url, **request_kwargs)

        if not (200 <= res.status_code < 300):
            try:
                message = await res.json()["message"]
            except Exception:
                message = res.reason_phrase
            raise RequestFailedError(f"{error_message}. Status code: {res.status_code}, Reason: {message}")

        return res

    # TODO make an enum for upload types
    async def _upload_to_s3(
        self, path_: str, *, upload_type: str, dir_for_zipping: str | None = None
    ) -> None:
        # TODO break this into smaller functions
        if os.path.isdir(path_):
            if not dir_for_zipping:
                raise NotImplementedError("a dir to store the zipped file must be given if path_ is a folder")

            uploaded_file_name = f"{os.path.basename(path_)}.zip"
            path_to_upload_file = os.path.join(dir_for_zipping, uploaded_file_name)

            # Tanner (4/10/23): assuming that the folder only contains files. Can change this if needed
            with zipfile.ZipFile(path_to_upload_file, "w") as zf:
                for file_name in os.listdir(path_):
                    zf.write(os.path.join(path_, file_name), file_name)
        elif os.path.isfile(path_):
            uploaded_file_name = os.path.basename(path_)
            path_to_upload_file = path_
        else:
            raise NotImplementedError("given path does not exist")

        # upload file
        file_md5 = get_file_md5(path_to_upload_file)

        route = "uploads" if upload_type == "recording" else "logs"
        upload_details_res = await self._request(
            "post",
            f"https://{CLOUD_PULSE3D_ENDPOINT}/{route}",
            json={"filename": uploaded_file_name, "md5s": file_md5, "upload_type": "pulse3d"},
            auth_required=True,
            error_message="Error getting presigned URL for file upload",
        )
        upload_details = upload_details_res.json()

        with open(path_to_upload_file, "rb") as file_handle:
            await self._request(
                "post",
                upload_details["params"]["url"],
                data=upload_details["params"]["fields"],
                files={"file": (uploaded_file_name, file_handle)},
                auth_required=False,
                error_message="Error uploading file to s3 through presigned URL",
            )
