# -*- coding: utf-8 -*-
"""Misc utility functions."""
from __future__ import annotations
import asyncio
import logging

import re
import traceback
from typing import Optional

logger = logging.getLogger(__name__)


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


async def wait_tasks_clean(tasks, return_when=asyncio.FIRST_COMPLETED):
    done = set()
    pending = set()
    try:
        done, pending = await asyncio.wait(tasks, return_when=return_when)
    finally:
        await clean_up_tasks(done, pending)


async def clean_up_tasks(done, pending):
    for task in done:
        if not task.cancelled() and (exc := task.exception()):
            logger.error("".join(traceback.format_exception(exc)))
    for task in pending:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
