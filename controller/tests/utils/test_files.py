# -*- coding: utf-8 -*-
import logging

from controller.utils.files import check_for_local_firmware_versions
from controller.utils.files import NO_UPDATE_FW_VERSION
import pytest

from ..helpers import create_fw_files


def test_check_for_local_firmware_versions__returns_none_if_dir_does_not_exist(tmp_path):
    assert check_for_local_firmware_versions(str(tmp_path / "does_not_exist")) is None


def test_check_for_local_firmware_versions__returns_none_if_dir_is_empty(tmp_path):
    assert check_for_local_firmware_versions(str(tmp_path)) is None


def test_check_for_local_firmware_versions__returns_versions_of_both_fw_types(tmp_path):
    create_fw_files(tmp_path, ["main-1.2.3.bin", "channel-4.5.6.bin"])

    assert check_for_local_firmware_versions(str(tmp_path)) == {
        "latest_versions": {"main_fw": "1.2.3", "channel_fw": "4.5.6"},
        "download": False,
    }


@pytest.mark.parametrize(
    "file_name,expected_versions",
    [
        ("main-1.2.3.bin", {"main_fw": "1.2.3", "channel_fw": NO_UPDATE_FW_VERSION}),
        ("channel-4.5.6.bin", {"main_fw": NO_UPDATE_FW_VERSION, "channel_fw": "4.5.6"}),
    ],
)
def test_check_for_local_firmware_versions__uses_no_update_version_for_missing_fw_type(
    tmp_path, file_name, expected_versions
):
    create_fw_files(tmp_path, [file_name])

    assert check_for_local_firmware_versions(str(tmp_path)) == {
        "latest_versions": expected_versions,
        "download": False,
    }


@pytest.mark.parametrize(
    "file_name",
    [
        "main-1.2.3.txt",  # wrong extension
        "main-1.2.3",  # no extension
        "main_1.2.3.bin",  # wrong separator
        "main-1.2.bin",  # not a semver
        "main-1.2.3-rc.bin",  # extra dash
        "other-1.2.3.bin",  # invalid fw type
        "main.bin",  # no version
        "notes.txt",  # unrelated file
    ],
)
def test_check_for_local_firmware_versions__ignores_files_with_invalid_names(tmp_path, file_name, caplog):
    create_fw_files(tmp_path, [file_name])

    with caplog.at_level(logging.WARNING):
        assert check_for_local_firmware_versions(str(tmp_path)) is None

    if file_name.endswith(".bin"):
        assert any(file_name in record.message for record in caplog.records)


def test_check_for_local_firmware_versions__ignores_invalid_files_alongside_valid_files(tmp_path):
    create_fw_files(tmp_path, ["main-1.2.3.bin", "notes.txt", "bad-name.bin"])

    assert check_for_local_firmware_versions(str(tmp_path)) == {
        "latest_versions": {"main_fw": "1.2.3", "channel_fw": NO_UPDATE_FW_VERSION},
        "download": False,
    }
