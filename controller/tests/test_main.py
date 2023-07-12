# -*- coding: utf-8 -*-
from asyncio import create_task
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
from controller.utils.logging import redact_sensitive_info_from_path
import pytest


@pytest.fixture(scope="function", name="patch_subsystem_inits", autouse=True)
def fixture__patch_subsystem_inits(mocker):
    mocks = {
        "system_monitor": mocker.patch.object(
            main.SystemMonitor, "__init__", autospec=True, return_value=None
        ),
        "server": mocker.patch.object(main.Server, "__init__", autospec=True, return_value=None),
        "instrument_comm": mocker.patch.object(
            main.InstrumentComm, "__init__", autospec=True, return_value=None
        ),
        "cloud_comm": mocker.patch.object(main.CloudComm, "__init__", autospec=True, return_value=None),
    }
    yield mocks


@pytest.fixture(scope="function", name="patch_run_tasks", autouse=True)
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
async def test_main__configures_logging_correctly(use_debug_logging, base_directory, log_directory, mocker):
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
async def test_main__initial_bootup_logging(mocker):
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
async def test_main__logs_command_line_args(log_directory, mocker):
    # mock to avoid looking for non-existent dir
    mocker.patch.object(main, "configure_logging", autospec=True)

    spied_info = mocker.spy(main.logger, "info")

    rand_arg = choice(["--log-level-debug", "--expected-software-version=1.2.3"])

    cmd_line_args = [rand_arg, f"--base-directory={os.path.join('Users', 'some-user', 'some-other-dir')}"]
    if log_directory:
        cmd_line_args.append(f"--log-directory={log_directory}")

    await main.main(cmd_line_args)

    expected_cmd_line_arg_dict = {}
    for arg in sorted(cmd_line_args):
        arg_name, *arg_values = arg.split("=")
        arg_name = arg_name[2:].replace("-", "_")
        if "directory" in arg_name:
            arg_value = redact_sensitive_info_from_path(arg_values[0])
        else:
            arg_value = arg_values[0] if arg_values else True
        expected_cmd_line_arg_dict[arg_name] = arg_value

    spied_info.assert_any_call(f"Command Line Args: {expected_cmd_line_arg_dict}".replace(r"\\", "\\"))


@pytest.mark.asyncio
async def test_main__logs_system_info(mocker):
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
async def test_main__logs_error_if_port_already_in_use(mocker):
    spied_info = mocker.spy(main.logger, "info")
    spied_exception = mocker.spy(main.logger, "exception")

    mocker.patch.object(main, "is_port_in_use", autospec=True, return_value=True)

    await main.main([])

    spied_info.assert_any_call(f"Using server port number: {DEFAULT_SERVER_PORT_NUMBER}")
    spied_exception.assert_called_once_with(main.ERROR_MSG)


@pytest.mark.asyncio
async def test_main__handles_errors_correctly(mocker):
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
async def test_main__initializes_system_state_correctly(
    base_directory,
    log_directory,
    expected_software_version,
    mocker,
):
    spied_uuid4 = mocker.spy(main.uuid, "uuid4")
    mocked_getcwd = mocker.patch.object(main.os, "getcwd", autospec=True)
    # mock to avoid looking for non-existent dir
    mocker.patch.object(main, "configure_logging", autospec=True)

    spied_init_state = mocker.spy(main, "initialize_system_state")

    cmd_line_args = []
    if base_directory:
        cmd_line_args.append(f"--base-directory={base_directory}")
    if log_directory:
        cmd_line_args.append(f"--log-directory={log_directory}")
    if expected_software_version:
        cmd_line_args.append(f"--expected-software-version={expected_software_version}")

    await main.main(cmd_line_args)

    expected_system_state = {
        "system_status": SystemStatuses.SERVER_INITIALIZING,
        "in_simulation_mode": False,
        "stimulation_protocol_statuses": [],
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

    if expected_software_version:
        expected_system_state["expected_software_version"] = expected_software_version

    assert spied_init_state.spy_return == expected_system_state


# TODO test state management


# TODO make sure to add all the run() assertions
@pytest.mark.asyncio
async def test_main__creates_SystemMonitor_and_runs_correctly(patch_run_tasks, patch_subsystem_inits, mocker):
    spied_ssm = mocker.spy(main, "SystemStateManager")
    spied_create_queues = mocker.spy(main, "create_system_comm_queues")

    await main.main([])

    patch_subsystem_inits["system_monitor"].assert_called_once_with(
        mocker.ANY, spied_ssm.spy_return, spied_create_queues.spy_return
    )


@pytest.mark.asyncio
async def test_main__creates_Server_and_runs_correctly(patch_run_tasks, patch_subsystem_inits, mocker):
    spied_ssm = mocker.spy(main, "SystemStateManager")
    spied_create_queues = mocker.spy(main, "create_system_comm_queues")

    await main.main([])

    expected_queues = spied_create_queues.spy_return

    patch_subsystem_inits["server"].assert_called_once_with(
        mocker.ANY,
        spied_ssm.spy_return.get_read_only_copy,
        expected_queues["to"]["server"],
        expected_queues["from"]["server"],
    )


@pytest.mark.asyncio
async def test_main__creates_InstrumentComm_and_runs_correctly(
    patch_run_tasks, patch_subsystem_inits, mocker
):
    spied_create_comm_queues = mocker.spy(main, "create_system_comm_queues")
    spied_create_data_queues = mocker.spy(main, "create_system_data_queues")

    await main.main([])

    expected_comm_queues = spied_create_comm_queues.spy_return
    expected_data_queues = spied_create_data_queues.spy_return

    patch_subsystem_inits["instrument_comm"].assert_called_once_with(
        mocker.ANY,
        expected_comm_queues["to"]["instrument_comm"],
        expected_comm_queues["from"]["instrument_comm"],
        expected_data_queues["main"],
        expected_data_queues["file_writer"],
    )


@pytest.mark.asyncio
async def test_main__creates_CloudComm_and_runs_correctly(patch_run_tasks, patch_subsystem_inits, mocker):
    spied_create_queues = mocker.spy(main, "create_system_comm_queues")
    spied_get_setting = mocker.spy(main, "_get_user_config_settings")

    await main.main([])

    expected_queues = spied_create_queues.spy_return

    patch_subsystem_inits["cloud_comm"].assert_called_once_with(
        mocker.ANY,
        expected_queues["to"]["cloud_comm"],
        expected_queues["from"]["cloud_comm"],
        **spied_get_setting.spy_return,
    )


@pytest.mark.asyncio
async def test_main__waits_for_server_to_start_before_running_other_subsystems(patch_run_tasks, mocker):
    mocked_aio_event = mocker.patch.object(main.asyncio, "Event", autospec=True)

    was_awaited = False

    def se(*args):
        try:
            mocked_aio_event.return_value.wait.assert_awaited_once_with()
        except AssertionError:
            pass
        else:
            nonlocal was_awaited
            was_awaited = True

    patch_run_tasks["system_monitor"].side_effect = se
    patch_run_tasks["instrument_comm"].side_effect = se
    patch_run_tasks["cloud_comm"].side_effect = se

    await main.main([])

    assert was_awaited, "Event not awaited before running other tasks"


@pytest.mark.asyncio
async def test_main__does_not_run_other_subsystem_if_server_never_starts_running(patch_run_tasks, mocker):
    # remove side effect so that the event is never sest
    patch_run_tasks["server"].side_effect = None
    # patch this value to speed up the test
    mocker.patch.object(main, "SERVER_BOOT_UP_TIMEOUT_SECONDS", 0)

    await main.main([])

    patch_run_tasks["system_monitor"].assert_not_called()
    patch_run_tasks["instrument_comm"].assert_not_called()
    patch_run_tasks["cloud_comm"].assert_not_called()


@pytest.mark.asyncio
async def test_main__runs_tasks_correctly(patch_run_tasks, mocker):
    expected_tasks = []

    def create_task_se(coro):
        task = create_task(coro)
        expected_tasks.append(task)
        return task

    mocker.patch.object(main.asyncio, "create_task", autospec=True, side_effect=create_task_se)

    await main.main([])

    patch_run_tasks["server"].assert_awaited_once()
    patch_run_tasks["system_monitor"].assert_awaited_once()
    patch_run_tasks["instrument_comm"].assert_awaited_once()
    patch_run_tasks["cloud_comm"].assert_awaited_once()
