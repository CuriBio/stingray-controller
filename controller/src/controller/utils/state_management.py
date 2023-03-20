# -*- coding: utf-8 -*-
import asyncio
import collections
from typing import Any
from typing import Iterator


class ReadOnlyDict(collections.abc.Mapping):  # type: ignore  # Tanner (3/16/23): not sure how to add the type here
    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        item = self._data[key]

        if isinstance(item, dict):
            return ReadOnlyDict(item)
        if isinstance(item, (list, set)):
            # Tanner (3/15/23): for now, not worrying about making items inside sequences immutable, just want to make the sequence itself immutable
            return tuple(item)

        return item

    def __iter__(self) -> Iterator[Any]:
        # Tanner (3/16/23): abc requires this function to be implemented, but it's not necessary right now
        raise NotImplementedError()

    def __len__(self) -> int:
        return len(self._data)

    def __str__(self) -> str:  # pragma: no cover
        return str(self._data)


class SystemStateManager:
    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

        self.previous_update_queue: asyncio.Queue[ReadOnlyDict] = asyncio.Queue()

    def __str__(self) -> str:  # pragma: no cover
        return str(self._data)

    @property
    def data(self) -> ReadOnlyDict:
        return ReadOnlyDict(self._data)

    async def update(self, new_values: dict[str, Any]) -> None:
        await self.previous_update_queue.put(ReadOnlyDict(new_values))

        # TODO make sure this updates the inner dicts correctly
        self._data.update(new_values)

    def get_read_only_copy(self) -> ReadOnlyDict:
        # Tanner (3/15/23): this may not be necessary, but assuming for now that the data property won't
        # update, so creating this method that returns the data property to gaurantee that the most up to
        # date values can be accessed
        return self.data
