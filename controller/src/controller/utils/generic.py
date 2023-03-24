# -*- coding: utf-8 -*-
"""Misc utility functions."""
from __future__ import annotations

import asyncio
import logging
import re
import traceback
from typing import Any
from typing import Optional

from semver import VersionInfo

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


async def wait_tasks_clean(tasks: set[GenericTask], return_when: str = asyncio.FIRST_COMPLETED) -> None:
    if not tasks:
        return

    try:
        await asyncio.wait(tasks, return_when=return_when)
    finally:
        await clean_up_tasks(tasks)


async def clean_up_tasks(tasks: set[GenericTask]) -> None:
    for task in tasks:
        if task.done():
            if not task.cancelled() and (exc := task.exception()):
                logger.error("".join(traceback.format_exception(exc)))
        else:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
