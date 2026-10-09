# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
import os
from typing import Any

from semver import VersionInfo


logger = logging.getLogger(__name__)

FW_FILE_EXTENSION = ".bin"
FW_TYPES = frozenset(("main", "channel"))
# version used for a FW type when no update file is present for it, this ensures no update will occur for it
NO_UPDATE_FW_VERSION = "0.0.0"


def get_file_md5(file_path: str) -> str:
    """Generate md5 of zip file.

    Args:
        file_path: path to zip file.
    """
    with open(file_path, "rb") as file_to_read:
        contents = file_to_read.read()
        md5 = hashlib.md5(  # nosec B324 B303 # Tanner (2/4/21): Bandit blacklisted this hash function for cryptographic security reasons that do not apply to the desktop app.
            contents
        ).digest()
        md5s = base64.b64encode(md5).decode()

    return md5s


def check_for_local_firmware_versions(fw_update_dir_path: str) -> dict[str, Any] | None:
    """Check the given directory for firmware update files.

    Firmware files must be named '<main|channel>-<x.y.z>.bin'. Files that do not follow this naming scheme
    are ignored.

    Returns None if the directory does not exist or does not contain any valid firmware files.
    """
    if not os.path.isdir(fw_update_dir_path):
        return None

    fw_versions: dict[str, str] = {}

    for fw_file_name in sorted(os.listdir(fw_update_dir_path)):
        file_name_no_ext, ext = os.path.splitext(fw_file_name)
        if ext != FW_FILE_EXTENSION:
            continue

        try:
            fw_type, version = file_name_no_ext.split("-")
            if fw_type not in FW_TYPES:
                raise ValueError(f"Invalid firmware type: {fw_type}")
            VersionInfo.parse(version)
        except ValueError:
            logger.warning(
                f"Ignoring firmware file with invalid name '{fw_file_name}'. "
                "Expected format: <main|channel>-<x.y.z>.bin"
            )
            continue

        fw_type_key = f"{fw_type}_fw"
        if fw_type_key in fw_versions:
            logger.warning(
                f"Multiple {fw_type} firmware files found, using '{fw_file_name}' instead of "
                f"'{fw_type}-{fw_versions[fw_type_key]}{FW_FILE_EXTENSION}'"
            )

        fw_versions[fw_type_key] = version

    if not fw_versions:
        return None

    logger.info(f"Local firmware files found: {fw_versions}")

    # A version must be returned for both FW types, so if a file for one isn't present just set it to a
    # version that will never be considered an update
    fw_versions = {"main_fw": NO_UPDATE_FW_VERSION, "channel_fw": NO_UPDATE_FW_VERSION, **fw_versions}

    return {"latest_versions": fw_versions, "download": False}
