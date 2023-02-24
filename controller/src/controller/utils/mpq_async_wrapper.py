# -*- coding: utf-8 -*-
import asyncio
from multiprocessing import Queue as MPQueue

from ..constants import MPQUEUE_POLL_PERIOD


class MPQueueAsyncWrapper:
    def __init__(self, mpq: MPQueue) -> None:
        self.mpq = mpq

    async def get(self):
        while True:
            try:
                return self.mpq.get_nowait()
            except MPQueue.Empty:
                asyncio.sleep(MPQUEUE_POLL_PERIOD)

    def put_nowait(self, item):
        self.mpq.put_nowait(item)

    async def drain(self):
        pass  # TODO
