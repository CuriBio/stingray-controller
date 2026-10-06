# -*- coding: utf-8 -*-
import asyncio
import os

from controller.exceptions import FirmwareDownloadError
from controller.subsystems import cloud_comm
from controller.subsystems.cloud_comm import CloudComm
from controller.utils.files import NO_UPDATE_FW_VERSION
import pytest

from ..helpers import create_fw_files


@pytest.fixture(scope="function", name="test_cloud_comm_obj")
def fixture__test_cloud_comm_obj():
    cc = CloudComm(asyncio.Queue(), asyncio.Queue(), log_directory=None)
    yield cc


@pytest.mark.asyncio
async def test_CloudComm__check_versions__returns_local_firmware_versions_if_present(
    test_cloud_comm_obj, tmp_path
):
    create_fw_files(tmp_path, ["main-1.2.3.bin", "channel-4.5.6.bin"])

    assert await test_cloud_comm_obj._check_versions({"fw_update_dir_path": str(tmp_path)}) == {
        "latest_versions": {"main_fw": "1.2.3", "channel_fw": "4.5.6"},
        "download": False,
    }


@pytest.mark.asyncio
async def test_CloudComm__check_versions__returns_no_update_versions_if_no_local_files_present(
    test_cloud_comm_obj, tmp_path
):
    assert await test_cloud_comm_obj._check_versions({"fw_update_dir_path": str(tmp_path)}) == {
        "latest_versions": {"main_fw": NO_UPDATE_FW_VERSION, "channel_fw": NO_UPDATE_FW_VERSION},
        "download": False,
    }


@pytest.mark.asyncio
async def test_CloudComm__check_versions__returns_no_update_versions_if_error_occurs_checking_local_files(
    test_cloud_comm_obj, tmp_path, mocker
):
    mocker.patch.object(
        cloud_comm, "check_for_local_firmware_versions", autospec=True, side_effect=PermissionError()
    )

    assert await test_cloud_comm_obj._check_versions({"fw_update_dir_path": str(tmp_path)}) == {
        "latest_versions": {"main_fw": NO_UPDATE_FW_VERSION, "channel_fw": NO_UPDATE_FW_VERSION},
        "download": False,
    }


@pytest.mark.asyncio
async def test_CloudComm__check_versions__never_makes_cloud_requests(test_cloud_comm_obj, tmp_path, mocker):
    spied_request = mocker.spy(test_cloud_comm_obj, "_request")

    await test_cloud_comm_obj._check_versions({"fw_update_dir_path": str(tmp_path)})

    spied_request.assert_not_called()


@pytest.mark.asyncio
async def test_CloudComm__download_firmware_updates__loads_contents_of_requested_local_files(
    test_cloud_comm_obj, tmp_path
):
    create_fw_files(tmp_path, {"main-1.0.0.bin": b"main fw", "channel-1.0.0.bin": b"channel fw"})

    assert await test_cloud_comm_obj._download_firmware_updates(
        {"fw_update_dir_path": str(tmp_path), "main": "1.0.0", "channel": "1.0.0"}
    ) == {"main_firmware_contents": b"main fw", "channel_firmware_contents": b"channel fw"}

    # only the requested FW type should be loaded
    assert await test_cloud_comm_obj._download_firmware_updates(
        {"fw_update_dir_path": str(tmp_path), "main": "1.0.0", "channel": None}
    ) == {"main_firmware_contents": b"main fw"}


@pytest.mark.asyncio
async def test_CloudComm__download_firmware_updates__raises_error_if_local_file_missing(
    test_cloud_comm_obj, tmp_path
):
    assert not os.path.exists(tmp_path / "main-1.0.0.bin")

    with pytest.raises(FirmwareDownloadError):
        await test_cloud_comm_obj._download_firmware_updates(
            {"fw_update_dir_path": str(tmp_path), "main": "1.0.0", "channel": None}
        )


@pytest.mark.asyncio
async def test_CloudComm__download_firmware_updates__raises_error_if_no_dir_path_given(
    test_cloud_comm_obj,
):
    with pytest.raises(NotImplementedError):
        await test_cloud_comm_obj._download_firmware_updates(
            {"fw_update_dir_path": None, "main": "1.0.0", "channel": None}
        )
