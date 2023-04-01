# -*- coding: utf-8 -*-
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


GenericTask = asyncio.Task[Any]


CLEANUP_ERROR_MSG = "IN TASK CLEANUP"


async def wait_tasks_clean(
    tasks: set[GenericTask], return_when: str = asyncio.FIRST_COMPLETED, error_msg: str = CLEANUP_ERROR_MSG
) -> Exception | None:
    if not tasks:
        return None

    try:
        await asyncio.wait(tasks, return_when=return_when)
    finally:
        return await clean_up_tasks(tasks, error_msg)


async def clean_up_tasks(tasks: set[GenericTask], error_msg: str = CLEANUP_ERROR_MSG) -> Exception | None:
    # Tanner (3/31/23): assuming there will only be one exception per set of tasks
    exc = None

    for task in tasks:
        if not task.done():
            task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass
        except Exception as e:
            if not exc:
                exc = e
            logger.exception(error_msg)

    return exc
