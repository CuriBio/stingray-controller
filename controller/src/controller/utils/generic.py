# -*- coding: utf-8 -*-
"""Misc utility functions."""

import asyncio
import hashlib
import socket

from semver import VersionInfo

from ..constants import ErrorCodes
from ..exceptions import FirmwareAndSoftwareNotCompatibleError
from ..exceptions import InstrumentBadDataError
from ..exceptions import InstrumentConnectionCreationError
from ..exceptions import InstrumentConnectionLostError
from ..exceptions import InstrumentFirmwareError
from ..exceptions import NoInstrumentDetectedError
from ..exceptions import WebsocketCommandError


def get_hash_of_computer_name() -> str:
    return hashlib.sha512(socket.gethostname().encode(encoding="UTF-8")).hexdigest()


def semver_gt(version_a: str, version_b: str) -> bool:
    """Determine if Version A is greater than Version B."""
    return VersionInfo.parse(version_a) > VersionInfo.parse(version_b)  # type: ignore


def handle_system_error(exc: BaseException, system_error_future: asyncio.Future[int]) -> None:
    if system_error_future.done():
        return

    match exc:
        case NoInstrumentDetectedError():
            error_code = ErrorCodes.INSTRUMENT_NOT_FOUND
        case InstrumentConnectionCreationError():
            error_code = ErrorCodes.INSTRUMENT_CONNECTION_CREATION
        case InstrumentConnectionLostError():
            error_code = ErrorCodes.INSTRUMENT_CONNECTION_LOST
        case InstrumentBadDataError():
            error_code = ErrorCodes.INSTRUMENT_SENT_BAD_DATA
        case InstrumentFirmwareError():
            error_code = ErrorCodes.INSTRUMENT_STATUS_CODE
        case FirmwareAndSoftwareNotCompatibleError():
            error_code = ErrorCodes.INSTRUMENT_FW_INCOMPATIBLE_WITH_SW
        case WebsocketCommandError():
            error_code = ErrorCodes.UI_SENT_BAD_DATA
        case _:
            error_code = ErrorCodes.UNSPECIFIED

    system_error_future.set_result(error_code)
