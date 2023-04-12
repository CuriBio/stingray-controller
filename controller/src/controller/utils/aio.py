# -*- coding: utf-8 -*-
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


GenericTask = asyncio.Task[Any]


CLEANUP_ERROR_MSG = "IN TASK CLEANUP"


async def wait_tasks_clean(
    tasks: set[GenericTask], return_when: str = asyncio.FIRST_COMPLETED, error_msg: str = CLEANUP_ERROR_MSG
) -> None:
    if not tasks:
        return None

    try:
        await asyncio.wait(tasks, return_when=return_when)
    finally:
        exc = await clean_up_tasks(tasks, error_msg)
        if exc:
            raise exc


async def clean_up_tasks(tasks: set[GenericTask], error_msg: str = CLEANUP_ERROR_MSG) -> BaseException | None:
    # Tanner (3/31/23): assuming there will only be one exception per set of tasks
    exc = None

    for task in tasks:
        logger.debug(f"cleaning up task {task}")
        if not task.done():
            task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass
        except BaseException as e:
            # TODO use an exception group here?
            if exc is None:
                # catch the first exception raised and return to caller. Assume that if it needs to be logged, it will be logged by caller
                exc = e
            else:
                # if there are other exceptions, log them here since only the first exception found will be returned
                logger.exception(error_msg)  # type: ignore  # mypy thinks this is unreachable for some reason

    return exc
