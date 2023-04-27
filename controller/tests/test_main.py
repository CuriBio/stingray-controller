# -*- coding: utf-8 -*-
import hashlib
import logging
import os
import platform
from random import choice
import socket
import sys

from controller import main
from controller.constants import COMPILED_EXE_BUILD_TIMESTAMP
from controller.constants import CURRENT_SOFTWARE_VERSION
from controller.constants import DEFAULT_SERVER_PORT_NUMBER
from controller.constants import SOFTWARE_RELEASE_CHANNEL
from controller.constants import SystemStatuses
from controller.main_systems.server import Server
from controller.main_systems.system_monitor import SystemMonitor
from controller.subsystems import instrument_comm
from controller.subsystems.cloud_comm import CloudComm
from controller.subsystems.instrument_comm import InstrumentComm
from controller.utils.logging import redact_sensitive_info_from_path
import pytest


# TODO consider patching __init__ of all subsystems instead
@pytest.fixture(scope="function", name="patch_ic_event", autouse=True)
def fixture__patch_ic_event(mocker):
    # InstrumentComm.__init__ creates an asyncio.Event, so mock it there so this doesn't happen
    mocker.patch.object(instrument_comm.asyncio, "Event")


@pytest.fixture(scope="function", name="patch_run_tasks")
def fixture__patch_run_tasks(mocker):
    def server_run_se(server, system_error_future, server_running_event):
        server_running_event.set()

    mocks = {
        "system_monitor": mocker.patch.object(main.SystemMonitor, "run", autospec=True),
        "server": mocker.patch.object(main.Server, "run", autospec=True, side_effect=server_run_se),
        "instrument_comm": mocker.patch.object(main.InstrumentComm, "run", autospec=True),
        "cloud_comm": mocker.patch.object(main.CloudComm, "run", autospec=True),
    }
    yield mocks


@pytest.mark.asyncio
@pytest.mark.parametrize("use_debug_logging", [True, False])
@pytest.mark.parametrize("base_directory", [None, os.path.join("Users", "Username", "AppData")])
@pytest.mark.parametrize("log_directory", [None, "some/dir"])
async def test_main__configures_logging_correctly(
    use_debug_logging, base_directory, log_directory, patch_run_tasks, mocker
):
    mocked_configure_logging = mocker.patch.object(main, "configure_logging", autospec=True)

    cmd_line_args = []
    if use_debug_logging:
        cmd_line_args.append("--log-level-debug")
    if log_directory:
        cmd_line_args.append(f"--log-directory={log_directory}")
    if base_directory:
        cmd_line_args.append(f"--base-directory={base_directory}")

    await main.main(cmd_line_args)

    if base_directory and log_directory:
        expected_path_to_log_folder = os.path.join(base_directory, log_directory)
    else:
        expected_path_to_log_folder = None

    expected_log_level = logging.DEBUG if use_debug_logging else logging.INFO
    mocked_configure_logging.assert_called_once_with(
        path_to_log_folder=expected_path_to_log_folder,
        log_file_prefix="stingray_log",
        log_level=expected_log_level,
    )


@pytest.mark.asyncio
async def test_main__initial_bootup_logging(patch_run_tasks, mocker):
    spied_info = mocker.spy(main.logger, "info")
    spied_uuid4 = mocker.spy(main.uuid, "uuid4")

    await main.main([])

    for bootup_msg in (
        f"Stingray Controller v{CURRENT_SOFTWARE_VERSION} started",
        f"Build timestamp/version: {COMPILED_EXE_BUILD_TIMESTAMP}",
        f"Release Channel: {SOFTWARE_RELEASE_CHANNEL}",
        f"Log ID: {spied_uuid4.spy_return}",
    ):
        spied_info.assert_any_call(bootup_msg)


@pytest.mark.asyncio
@pytest.mark.parametrize("log_directory", [None, "some/dir"])
async def test_main__logs_command_line_args(log_directory, patch_run_tasks, mocker):
    # mock to avoid looking for non-existent dir
    mocker.patch.object(main, "configure_logging", autospec=True)

    spied_info = mocker.spy(main.logger, "info")

    rand_arg = choice(
        ["--log-level-debug", "--skip-software-version-verification", "--expected-software-version=1.2.3"]
    )

    cmd_line_args = [rand_arg]
    if log_directory:
        cmd_line_args.append(f"--log-directory={log_directory}")

    await main.main(cmd_line_args)

    expected_cmd_line_arg_dict = {}
    for arg in sorted(cmd_line_args):
        arg_name, *arg_values = arg.split("=")
        arg_name = arg_name[2:].replace("-", "_")
        if arg_name == "log_directory":
            arg_value = redact_sensitive_info_from_path(arg_values[0])
        else:
            arg_value = arg_values[0] if arg_values else True
        expected_cmd_line_arg_dict[arg_name] = arg_value

    spied_info.assert_any_call(f"Command Line Args: {expected_cmd_line_arg_dict}".replace(r"\\", "\\"))


@pytest.mark.asyncio
async def test_main__logs_system_info(patch_run_tasks, mocker):
    spied_info = mocker.spy(main.logger, "info")

    await main.main([])

    uname = platform.uname()
    uname_sys = getattr(uname, "system")
    uname_release = getattr(uname, "release")
    uname_version = getattr(uname, "version")

    computer_name_hash = hashlib.sha512(socket.gethostname().encode(encoding="UTF-8")).hexdigest()

    for system_info_msg in (
        f"System: {uname_sys}",
        f"Release: {uname_release}",
        f"Version: {uname_version}",
        f"Machine: {getattr(uname, 'machine')}",
        f"Processor: {getattr(uname, 'processor')}",
        f"Win 32 Ver: {platform.win32_ver()}",
        f"Platform: {platform.platform()}",
        f"Architecture: {platform.architecture()}",
        f"Interpreter is 64-bits: {sys.maxsize > 2**32}",
        f"System Alias: {platform.system_alias(uname_sys, uname_release, uname_version)}",
        f"SHA512 digest of Computer Name {computer_name_hash}",
    ):
        spied_info.assert_any_call(system_info_msg)


@pytest.mark.asyncio
async def test_main__logs_error_if_port_already_in_use(patch_run_tasks, mocker):
    spied_info = mocker.spy(main.logger, "info")
    spied_exception = mocker.spy(main.logger, "exception")

    mocker.patch.object(main, "is_port_in_use", autospec=True, return_value=True)

    await main.main([])

    spied_info.assert_any_call(f"Using server port number: {DEFAULT_SERVER_PORT_NUMBER}")
    spied_exception.assert_called_once_with(main.ERROR_MSG)


@pytest.mark.asyncio
async def test_main__handles_errors_correctly(patch_run_tasks, mocker):
    spied_info = mocker.spy(main.logger, "info")
    spied_exception = mocker.spy(main.logger, "exception")

    expected_err = Exception("test msg")

    # picking arbitrary function to raise error
    mocker.patch.object(main, "configure_logging", autospec=True, side_effect=expected_err)

    await main.main([])

    spied_exception.assert_called_once_with(main.ERROR_MSG)
    # Tanner (2/27/23): using assert_called_with since to make the assertion on the final call to this method
    spied_info.assert_called_with("Program exiting")


@pytest.mark.asyncio
@pytest.mark.parametrize("base_directory", [None, os.path.join("Users", "Username", "AppData")])
@pytest.mark.parametrize("log_directory", [None, "logs_in_here"])
@pytest.mark.parametrize("expected_software_version", [None, "1.2.3"])
@pytest.mark.parametrize("skip_software_version_verification", [True, False])
async def test_main__initializes_system_state_correctly(
    base_directory,
    log_directory,
    expected_software_version,
    skip_software_version_verification,
    patch_run_tasks,
    mocker,
):
    spied_uuid4 = mocker.spy(main.uuid, "uuid4")
    mocked_getcwd = mocker.patch.object(main.os, "getcwd", autospec=True)
    # mock to avoid looking for non-existent dir
    mocker.patch.object(main, "configure_logging", autospec=True)

    spied_init_state = mocker.spy(main, "_initialize_system_state")

    cmd_line_args = []
    if base_directory:
        cmd_line_args.append(f"--base-directory={base_directory}")
    if log_directory:
        cmd_line_args.append(f"--log-directory={log_directory}")
    if expected_software_version:
        cmd_line_args.append(f"--expected-software-version={expected_software_version}")
    if skip_software_version_verification:
        cmd_line_args.append("--skip-software-version-verification")

    await main.main(cmd_line_args)

    expected_system_state = {
        "system_status": SystemStatuses.SERVER_INITIALIZING_STATE,
        "in_simulation_mode": False,
        "stimulation_protocols_running": [],
        "main_firmware_update": None,
        "channel_firmware_update": None,
        "latest_software_version": None,
        "firmware_updates_accepted": None,
        "firmware_updates_require_download": None,
        "is_user_logged_in": False,
        "instrument_metadata": {},
        "stim_info": {},
        "stimulator_circuit_statuses": {},
        "stim_barcode": None,
        "plate_barcode": None,
        "base_directory": base_directory if base_directory else mocked_getcwd.return_value,
        "log_file_id": spied_uuid4.spy_return,
    }

    if expected_software_version and not skip_software_version_verification:
        expected_system_state["expected_software_version"] = expected_software_version

    assert spied_init_state.spy_return == expected_system_state


# TODO test state management


# TODO make sure to add all the run() assertions
@pytest.mark.asyncio
async def test_main__creates_SystemMonitor_and_runs_correctly(patch_run_tasks, mocker):
    spied_ssm = mocker.spy(main, "SystemStateManager")
    spied_create_queues = mocker.spy(main, "create_system_queues")

    spied_spm_init = mocker.spy(SystemMonitor, "__init__")

    await main.main([])

    spied_spm_init.assert_called_once_with(mocker.ANY, spied_ssm.spy_return, spied_create_queues.spy_return)


@pytest.mark.asyncio
async def test_main__creates_Server_and_runs_correctly(patch_run_tasks, mocker):
    spied_ssm = mocker.spy(main, "SystemStateManager")
    spied_create_queues = mocker.spy(main, "create_system_queues")

    spied_server_init = mocker.spy(Server, "__init__")

    await main.main([])

    expected_queues = spied_create_queues.spy_return

    spied_server_init.assert_called_once_with(
        mocker.ANY,
        spied_ssm.spy_return.get_read_only_copy,
        expected_queues["to"]["server"],
        expected_queues["from"]["server"],
    )


@pytest.mark.asyncio
async def test_main__creates_InstrumentComm_and_runs_correctly(patch_run_tasks, mocker):
    spied_create_queues = mocker.spy(main, "create_system_queues")

    spied_ic_init = mocker.spy(InstrumentComm, "__init__")

    await main.main([])

    expected_queues = spied_create_queues.spy_return

    spied_ic_init.assert_called_once_with(
        mocker.ANY, expected_queues["to"]["instrument_comm"], expected_queues["from"]["instrument_comm"]
    )


@pytest.mark.asyncio
async def test_main__creates_CloudComm_and_runs_correctly(patch_run_tasks, mocker):
    spied_create_queues = mocker.spy(main, "create_system_queues")
    spied_get_setting = mocker.spy(main, "_get_user_config_settings")

    spied_cc_init = mocker.spy(CloudComm, "__init__")

    await main.main([])

    expected_queues = spied_create_queues.spy_return

    spied_cc_init.assert_called_once_with(
        mocker.ANY,
        expected_queues["to"]["cloud_comm"],
        expected_queues["from"]["cloud_comm"],
        **spied_get_setting.spy_return,
    )


# TODO  Wait for WS server to start


@pytest.mark.asyncio
async def test_main__runs_tasks_correctly(mocker):
    mocked_server = mocker.patch.object(main, "Server")
    mocked_spm = mocker.patch.object(main, "SystemMonitor")
    mocked_ic = mocker.patch.object(main, "InstrumentComm")
    mocked_cc = mocker.patch.object(main, "CloudComm")

    expected_tasks = []

    def create_task_se(task):
        expected_tasks.append(task)
        return task

    mocked_create_task = mocker.patch.object(
        main.asyncio, "create_task", autospec=True, side_effect=create_task_se
    )

    # mock to speed up test
    mocker.patch.object(main.asyncio, "wait_for", autospec=True)

    mocked_wait_tasks_clean = mocker.patch.object(main, "wait_tasks_clean", autospec=True)

    await main.main([])

    mocked_create_task.assert_any_call(mocked_server().run())
    mocked_create_task.assert_any_call(mocked_spm().run())
    mocked_create_task.assert_any_call(mocked_ic().run())
    mocked_create_task.assert_any_call(mocked_cc().run())

    mocked_wait_tasks_clean.assert_called_once_with(set(expected_tasks))
