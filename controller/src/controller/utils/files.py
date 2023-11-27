# -*- coding: utf-8 -*-
import base64
import hashlib
import os
from typing import Any

from controller.constants import CURRENT_SOFTWARE_VERSION


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
    if not os.path.isdir(fw_update_dir_path):
        return None

    fw_versions = {}

    for fw_file_name in os.listdir(fw_update_dir_path):
        if "main" in fw_file_name or "channel" in fw_file_name:
            fw_type, version = os.path.splitext(fw_file_name)[0].split("-")
            fw_versions[f"{fw_type}_fw"] = version

    if not fw_versions:
        return None

    # A version must be returned for both FW types, so if a file for one isn't present just set it to 0.0.0 so no update will occur for it
    fw_versions = {"main_fw": "0.0.0", "channel_fw": "0.0.0", **fw_versions}

    # set software version to whatever the current version is to ensure that the FW updates run
    return {"latest_versions": {"sting_sw": CURRENT_SOFTWARE_VERSION, **fw_versions}, "download": False}
