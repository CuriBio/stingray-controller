# -*- coding: utf-8 -*-
"""Misc utility functions."""


import asyncio
import logging
import re
import traceback
from typing import Any
from typing import Optional

from semver import VersionInfo

from .. import exceptions
from ..constants import ErrorCodes

logger = logging.getLogger(__name__)


GenericTask = asyncio.Task[Any]


def redact_sensitive_info_from_path(file_path: Optional[str]) -> Optional[str]:
    """Scrubs username from file path to protect sensitive info."""
    if file_path is None:
        return None
    split_path = re.split(r"(Users\\)(.*)(\\AppData)", file_path)
    if len(split_path) != 5:
        return get_redacted_string(len(file_path))
    scrubbed_path = split_path[0] + split_path[1]
    scrubbed_path += get_redacted_string(len(split_path[2]))
    scrubbed_path += split_path[3] + split_path[4]
    return scrubbed_path


def get_redacted_string(length: int) -> str:
    return "*" * length


def semver_gt(version_a: str, version_b: str) -> bool:
    """Determine if Version A is greater than Version B."""
    return VersionInfo.parse(version_a) > VersionInfo.parse(version_b)  # type: ignore


# TODO move these to an async utils file


async def wait_tasks_clean(
    tasks: set[GenericTask], return_when: str = asyncio.FIRST_COMPLETED
) -> Exception | None:
    if not tasks:
        return None

    try:
        await asyncio.wait(tasks, return_when=return_when)
    finally:
        return await clean_up_tasks(tasks)


async def clean_up_tasks(tasks: set[GenericTask]) -> Exception | None:
    # Tanner (): assuming there will only be one exception per set of tasks
    exc = None

    for task in tasks:
        if task.done():
            if not task.cancelled() and (e := task.exception()):
                if not exc:
                    exc = e
                logger.error("".join(traceback.format_exception(e)))
        else:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    return exc  # type: ignore


def handle_system_error(exc: Exception, system_error_future: asyncio.Future[int]) -> None:
    if system_error_future.done():
        return

    logger.exception(f"############: {type(exc)}, {isinstance(exc, exceptions.NoInstrumentDetectedError)}")

    match type(exc):
        case exceptions.NoInstrumentDetectedError:
            error_code = ErrorCodes.INSTRUMENT_NOT_FOUND
        case exceptions.InstrumentConnectionCreationError:
            error_code = ErrorCodes.INSTRUMENT_CONNECTION_CREATION
        case exceptions.InstrumentConnectionLostError:
            error_code = ErrorCodes.INSTRUMENT_CONNECTION_LOST
        case exceptions.InstrumentBadDataError:
            error_code = ErrorCodes.INSTRUMENT_SENT_BAD_DATA
        case exceptions.InstrumentFirmwareError:
            error_code = ErrorCodes.INSTRUMENT_STATUS_CODE
        case exceptions.FirmwareAndSoftwareNotCompatibleError:
            error_code = ErrorCodes.INSTRUMENT_FW_INCOMPATIBLE_WITH_SW
        # case
        #     error_code = ErrorCodes.UI_SENT_BAD_DATA
        case _:
            error_code = ErrorCodes.UNSPECIFIED

    system_error_future.set_result(error_code)
