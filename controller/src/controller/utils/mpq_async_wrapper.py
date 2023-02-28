# -*- coding: utf-8 -*-
import asyncio
from multiprocessing import Queue as MPQueue
import queue
from typing import Any

from ..constants import MPQUEUE_POLL_PERIOD


class MPQueueAsyncWrapper:
    def __init__(self, mpq: MPQueue[dict[str, Any]]) -> None:
        self.mpq = mpq

    async def get(self) -> dict[str, Any]:
        while True:
            try:
                return self.mpq.get_nowait()
            except queue.Empty:
                await asyncio.sleep(MPQUEUE_POLL_PERIOD)

    def put_nowait(self, item: dict[str, Any]) -> None:
        self.mpq.put_nowait(item)

    async def drain(self) -> list[dict[str, Any]]:  # type: ignore
        pass  # TODO
