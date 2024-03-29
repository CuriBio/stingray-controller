# -*- coding: utf-8 -*-
"""Misc utility functions."""

import asyncio

from semver import VersionInfo

from ..constants import ErrorCodes
from ..exceptions import ElectronControllerVersionMismatchError
from ..exceptions import FirmwareAndSoftwareNotCompatibleError
from ..exceptions import FirmwareDownloadError
from ..exceptions import FirmwareGoingDormantError
from ..exceptions import IncorrectInstrumentConnectedError
from ..exceptions import InstrumentBadDataError
from ..exceptions import InstrumentCommandAttemptError
from ..exceptions import InstrumentCommandResponseError
from ..exceptions import InstrumentConnectionCreationError
from ..exceptions import InstrumentConnectionLostError
from ..exceptions import InstrumentFirmwareError
from ..exceptions import InstrumentInvalidMetadataError
from ..exceptions import NoInstrumentDetectedError
from ..exceptions import WebsocketCommandError


def semver_gt(version_a: str, version_b: str) -> bool:
    """Determine if Version A is greater than Version B."""
    return VersionInfo.parse(version_a) > VersionInfo.parse(version_b)  # type: ignore


def handle_system_error(
    exc: BaseException, system_error_future: asyncio.Future[tuple[int, dict[str, str]]]
) -> None:
    if system_error_future.done():
        return

    extra_info = {}

    match exc:
        case NoInstrumentDetectedError():
            error_code = ErrorCodes.INSTRUMENT_NOT_FOUND
        case InstrumentConnectionCreationError():
            error_code = ErrorCodes.INSTRUMENT_CONNECTION_CREATION
        case InstrumentConnectionLostError():
            error_code = ErrorCodes.INSTRUMENT_CONNECTION_LOST
        case InstrumentFirmwareError():
            error_code = ErrorCodes.INSTRUMENT_STATUS_CODE
        case FirmwareAndSoftwareNotCompatibleError():
            error_code = ErrorCodes.INSTRUMENT_FW_INCOMPATIBLE_WITH_SW
            extra_info["latest_compatible_sw_version"] = exc.args[0]
        case IncorrectInstrumentConnectedError():
            error_code = ErrorCodes.INCORRECT_INSTRUMENT_TYPE
        case InstrumentInvalidMetadataError():
            error_code = ErrorCodes.INVALID_INSTRUMENT_METADATA
        case FirmwareDownloadError():
            error_code = ErrorCodes.FIRMWARE_DOWNLOAD_ERROR
        case InstrumentBadDataError():
            error_code = ErrorCodes.INSTRUMENT_SENT_BAD_DATA
        case FirmwareGoingDormantError():
            error_code = ErrorCodes.INSTRUMENT_INITIATED_DISCONNECTION
        case InstrumentCommandResponseError():
            error_code = ErrorCodes.INSTRUMENT_COMMAND_FAILED
        case InstrumentCommandAttemptError():
            error_code = ErrorCodes.INSTRUMENT_COMMAND_ATTEMPT
        case ElectronControllerVersionMismatchError():
            error_code = ErrorCodes.ELECTRON_CONTROLLER_VERSION_MISMATCH
            extra_info["expected_software_version"] = exc.args[0]
        case WebsocketCommandError():
            error_code = ErrorCodes.UI_SENT_BAD_DATA
        case _:
            error_code = ErrorCodes.UNSPECIFIED_CONTROLLER_ERROR

    system_error_future.set_result((error_code, extra_info))
