# -*- coding: utf-8 -*-


import asyncio
from collections import namedtuple
import logging
from typing import Any
from typing import Coroutine

import httpx
from httpx import Response
from semver import VersionInfo

from ..constants import CLOUD_API_ENDPOINT
from ..exceptions import FirmwareAndSoftwareNotCompatibleError
from ..exceptions import LoginFailedError
from ..exceptions import RefreshFailedError
from ..exceptions import RequestFailedError
from ..utils.aio import clean_up_tasks
from ..utils.aio import wait_tasks_clean
from ..utils.generic import handle_system_error


logger = logging.getLogger(__name__)

ERROR_MSG = "IN CLOUD COMM"


AuthTokens = namedtuple("AuthTokens", ["access", "refresh"])
AuthCreds = namedtuple("AuthCreds", ["customer_id", "username", "password"])


def _get_tokens(response_json: dict[str, Any]) -> AuthTokens:
    return AuthTokens(access=response_json["access"]["token"], refresh=response_json["refresh"]["token"])


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

        self._creds: AuthCreds | None = None
        self._tokens: AuthTokens | None = None

        self._client: httpx.AsyncClient | None = None

    # ONE-SHOT TASKS

    async def run(self, system_error_future: asyncio.Future[int]) -> None:
        # TODO ADD MORE LOGGING
        logger.info("Starting CloudComm")

        try:
            with httpx.AsyncClient() as self._client:
                tasks = {
                    asyncio.create_task(self._manage_subtasks()),
                    # TODO add other tasks?
                }
                exc = await wait_tasks_clean(tasks, error_msg=ERROR_MSG)
                if exc:
                    handle_system_error(exc, system_error_future)
        except asyncio.CancelledError:
            logger.info("CloudComm cancelled")
            await self._attempt_to_upload_log_files_to_s3()
            raise
        finally:
            self._client = None
            logger.info("CloudComm shut down")

    async def _get_comm_from_monitor(self) -> dict[str, Any]:
        return await self._from_monitor_queue.get()

    async def _attempt_to_upload_log_files_to_s3(self) -> None:
        pass  # TODO

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
                except Exception as e:
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
                    await self._to_monitor_queue.put({"command": task_name[1:], **res})

    # SUBTASKS

    async def _login(self, command: dict[str, str]) -> dict[str, str]:
        subtask_res = {}
        try:
            await self._get_cloud_api_tokens(**command)
        except LoginFailedError:
            subtask_res["error"] = "Invalid credentials"
        except httpx.ConnectError:
            subtask_res["error"] = "No internet connection"
        # TODO also handle NetworkError?

        return subtask_res

    async def _check_versions(self, command: dict[str, str]) -> dict[str, str]:
        check_sw_response = await self._request(
            "get",
            f"https://{CLOUD_API_ENDPOINT}/mantarray/software-range/{command['main_fw_version']}",
            error_message="Error checking software/firmware compatibility",
        )
        range = check_sw_response.json()

        # TODO move this to constants.py
        EQUIVALENT_MA_CONTROLLER_VERSION = "1.1.0"
        if not (range["min_sw"] <= VersionInfo.parse(EQUIVALENT_MA_CONTROLLER_VERSION) <= range["max_sw"]):
            raise FirmwareAndSoftwareNotCompatibleError(range["max_sw"])

        get_versions_response = await self._request(
            "get",
            f"https://{CLOUD_API_ENDPOINT}/mantarray/versions/{command['serial_number']}",
            error_message="Error getting latest firmware versions",
        )
        return {"latest_versions": get_versions_response.json()["latest_versions"]}

    async def download_firmware_updates(
        self, main_fw_version: str | None, channel_fw_version: str | None
    ) -> dict[str, bytes]:
        if self._tokens is None:
            raise NotImplementedError("self._tokens should never be None here")

        if not main_fw_version and not channel_fw_version:
            raise NotImplementedError("No firmware types specified")

        presigned_urls = {}

        # get presigned download URL(s)
        for version, fw_type in ((main_fw_version, "main"), (channel_fw_version, "channel")):
            if version:
                download_details = await self._request(
                    "get",
                    f"https://{CLOUD_API_ENDPOINT}/mantarray/firmware/{fw_type}/{version}",
                    headers={"Authorization": f"Bearer {self._tokens.access}"},
                    error_message=f"Error getting presigned URL for {fw_type} firmware",
                )
                presigned_urls[fw_type] = download_details.json()["presigned_url"]

        subtask_res = {}

        # download firmware file(s)
        for fw_type, presigned_url in presigned_urls.items():
            download_response = await self._request(
                "get", presigned_url, error_message=f"Error during download of {fw_type} firmware"
            )
            subtask_res[f"{fw_type}_firmware_contents"] = download_response.content

        return subtask_res

    # HELPERS

    async def _sub_task_wrapper(self, coro: Coroutine[Any, Any, dict[str, str]]) -> dict[str, str]:
        try:
            return await coro
        except RequestFailedError as e:
            e_repr = repr(e)
            logger.error(e_repr)
            return {"error": e_repr}
        except httpx.ConnectError as e:
            return {"error": repr(e)}

    async def _get_cloud_api_tokens(self, customer_id: str, user_name: str, user_password: str) -> None:
        if self._client is None:
            raise NotImplementedError("self._client should never be None here")

        res = await self._client.post(
            f"https://{CLOUD_API_ENDPOINT}/users/login",
            json={
                "customer_id": customer_id,
                "username": user_name,
                "password": user_password,
                "service": "pulse3d",
            },
        )

        if res.status_code != 200:
            raise LoginFailedError(res.status_code)

        self._tokens = _get_tokens(res.json()["tokens"])
        self._creds = AuthCreds(customer_id=customer_id, username=user_name, password=user_password)

    async def _refresh_cloud_api_tokens(self) -> None:
        """Use refresh token to get new set of auth tokens."""
        if self._client is None:
            raise NotImplementedError("self._client should never be None here")
        if self._tokens is None:
            raise NotImplementedError("self._tokens should never be None here")

        # TODO check service worker to see how refresh mutex is handled

        res = await self._client.post(
            f"https://{CLOUD_API_ENDPOINT}/users/refresh",
            headers={"Authorization": f"Bearer {self._tokens.refresh}"},
        )
        if res.status_code != 201:
            raise RefreshFailedError(res.status_code)

        self._tokens = _get_tokens(res.json()["tokens"])

    async def _request_with_refresh(self, method: str, url: str, **kwargs: dict[str, Any]) -> Response:
        """Make request, refresh once if needed, and try request once more."""
        if self._client is None:
            raise NotImplementedError("self._client should never be None here")

        response = await self._client.request(method, url, **kwargs)
        # if auth token expired then request will return 401 code
        if response.status_code == 401:
            # get new tokens and try request once more
            self.tokens = self._refresh_cloud_api_tokens()
            response = await self._client.request(method, url, **kwargs)
            # TODO try logging in again if this also fails

        return response

    async def _request(self, method: str, url: str, error_message: str, **kwargs: dict[str, Any]) -> Response:
        res = await self._request_with_refresh(method, url, **kwargs)

        if not (200 <= res.status_code < 300):
            try:
                message = await res.json()["message"]
            except Exception:
                message = res.reason_phrase
            raise RequestFailedError(f"{error_message}. Status code: {res.status_code}, Reason: {message}")

        return res
