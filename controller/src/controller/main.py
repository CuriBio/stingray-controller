# -*- coding: utf-8 -*-
"""Instrument Controller."""


import argparse
import asyncio
import hashlib
import logging
import os
import platform
import socket
import sys
from typing import Any
import uuid

from stdlib_utils import is_port_in_use

from .constants import COMPILED_EXE_BUILD_TIMESTAMP
from .constants import CURRENT_SOFTWARE_VERSION
from .constants import DEFAULT_SERVER_PORT_NUMBER
from .constants import SERVER_BOOT_UP_TIMEOUT_SECONDS
from .constants import SOFTWARE_RELEASE_CHANNEL
from .constants import SystemStatuses
from .constants import VALID_CONFIG_SETTINGS
from .exceptions import LocalServerPortAlreadyInUseError
from .main_systems.server import Server
from .main_systems.system_monitor import SystemMonitor
from .subsystems.cloud_comm import CloudComm
from .subsystems.instrument_comm import InstrumentComm
from .utils.aio import wait_tasks_clean
from .utils.logging import configure_logging
from .utils.logging import redact_sensitive_info_from_path
from .utils.state_management import SystemStateManager


logger = logging.getLogger(__name__)

ERROR_MSG = "IN MAIN"


async def main(command_line_args: list[str]) -> None:
    """Parse command line arguments and run."""

    try:
        parsed_args = _parse_cmd_line_args(command_line_args)

        log_level = logging.DEBUG if parsed_args["log_level_debug"] else logging.INFO
        if parsed_args["base_directory"] is not None and parsed_args["log_directory"] is not None:
            path_to_log_folder = os.path.join(parsed_args["base_directory"], parsed_args["log_directory"])
        else:
            path_to_log_folder = None
        configure_logging(
            path_to_log_folder=path_to_log_folder, log_file_prefix="stingray_log", log_level=log_level
        )

        logger.info(f"Stingray Controller v{CURRENT_SOFTWARE_VERSION} started")
        logger.info(f"Build timestamp/version: {COMPILED_EXE_BUILD_TIMESTAMP}")
        logger.info(f"Release Channel: {SOFTWARE_RELEASE_CHANNEL}")

        log_file_id = uuid.uuid4()
        logger.info(f"Log ID: {log_file_id}")

        _log_cmd_line_args(parsed_args)
        _log_system_info()

        logger.info(f"Using server port number: {DEFAULT_SERVER_PORT_NUMBER}")

        if is_port_in_use(DEFAULT_SERVER_PORT_NUMBER):
            raise LocalServerPortAlreadyInUseError(DEFAULT_SERVER_PORT_NUMBER)

        # TODO wrap all this in a function?

        system_state_manager = SystemStateManager()
        await system_state_manager.update(initialize_system_state(parsed_args, log_file_id))

        queues = create_system_queues()

        # create subsystems
        system_monitor = SystemMonitor(system_state_manager, queues)
        server = Server(
            system_state_manager.get_read_only_copy, queues["to"]["server"], queues["from"]["server"]
        )
        instrument_comm_subsystem = InstrumentComm(
            queues["to"]["instrument_comm"], queues["from"]["instrument_comm"]
        )
        cloud_comm_subsystem = CloudComm(
            queues["to"]["cloud_comm"], queues["from"]["cloud_comm"], **_get_user_config_settings(parsed_args)
        )

        # future for subsystems to set if they experience an error. The server will report the error in the future to the UI
        system_error_future: asyncio.Future[tuple[int, dict[str, str]]] = asyncio.Future()

        # make sure that WS server boots up before starting other subsystems. This ensures that errors can be reported to the UI
        logger.info("Booting up server before other subsystems")

        server_running_event = asyncio.Event()
        tasks = {asyncio.create_task(server.run(system_error_future, server_running_event))}

        try:
            await asyncio.wait_for(server_running_event.wait(), SERVER_BOOT_UP_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            for task in tasks:
                task.cancel()
            logger.error(f"Server failed to boot up before {SERVER_BOOT_UP_TIMEOUT_SECONDS} second timeout")
        else:
            logger.info("Creating remaining subsystems")
            tasks |= {
                # TODO might be cleaner to pass in a call back to handle errors instead of the future itself
                asyncio.create_task(system_monitor.run(system_error_future)),
                asyncio.create_task(instrument_comm_subsystem.run(system_error_future)),
                asyncio.create_task(cloud_comm_subsystem.run(system_error_future)),
            }
        finally:
            await wait_tasks_clean(tasks)

    except BaseException:
        logger.exception(ERROR_MSG)

    finally:
        logger.info("Program exiting")


# TODO consider moving this to a different file
def create_system_queues() -> dict[str, Any]:
    return {
        direction: {subsystem: asyncio.Queue() for subsystem in ("server", "instrument_comm", "cloud_comm")}
        for direction in ("to", "from")
    }


def _parse_cmd_line_args(command_line_args: list[str]) -> dict[str, Any]:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level-debug",
        action="store_true",
        help="sets the loggers to be more verbose and log DEBUG level pieces of information",
    )
    parser.add_argument(
        "--base-directory",
        type=str,
        help="allow manual setting of the directory in which files should be saved",
    )
    parser.add_argument(
        "--log-directory",
        type=str,
        help="allow manual setting of the sub-directory in which the log file should be created",
    )
    parser.add_argument(
        "--expected-software-version",
        type=str,
        help="used to make sure python exe and electron exe are the same version",
    )
    parser.add_argument(
        "--skip-software-version-verification",
        action="store_true",
        help="override any supplied expected software version and disable the check",
    )
    return vars(parser.parse_args(command_line_args))


def _log_cmd_line_args(parsed_args: dict[str, Any]) -> None:
    # Tanner (2/27/23): make a copy so that the original dict is not modified. Sorting just to make testing easier
    parsed_args_copy = {
        arg_name: arg_value for arg_name, arg_value in sorted(parsed_args.items()) if arg_value
    }

    for arg_name in ("base_directory", "log_directory"):
        if arg_val := parsed_args_copy.get(arg_name):
            parsed_args_copy[arg_name] = redact_sensitive_info_from_path(arg_val)
    # Tanner (1/14/21): Unsure why the back slashes are duplicated when converting the dict to string. Using replace here to remove the duplication, not sure if there is a better way to solve or avoid this problem
    logger.info(f"Command Line Args: {parsed_args_copy}".replace(r"\\", "\\"))


def initialize_system_state(parsed_args: dict[str, Any], log_file_id: uuid.UUID) -> dict[str, Any]:
    base_directory = (
        parsed_args["base_directory"] if parsed_args["base_directory"] is not None else os.getcwd()
    )

    system_state = {
        # main
        "system_status": SystemStatuses.SERVER_INITIALIZING_STATE,
        "in_simulation_mode": False,
        "stimulation_protocol_statuses": [],  # TODO consider renaming this stimulation_protocol_states
        # updating
        "main_firmware_update": None,
        "channel_firmware_update": None,
        "latest_software_version": None,
        "firmware_updates_accepted": None,
        "firmware_updates_require_download": None,
        "is_user_logged_in": False,
        # instrument
        "instrument_metadata": {},
        "stim_info": {},
        "stimulator_circuit_statuses": {},
        "stim_barcode": None,
        "plate_barcode": None,
        # misc
        "base_directory": base_directory,
        "log_file_id": log_file_id,
    }

    if expected_software_version := parsed_args["expected_software_version"]:
        system_state["expected_software_version"] = expected_software_version

    return system_state


def _log_system_info() -> None:
    uname = platform.uname()
    uname_sys = getattr(uname, "system")
    uname_release = getattr(uname, "release")
    uname_version = getattr(uname, "version")

    computer_name_hash = hashlib.sha512(socket.gethostname().encode(encoding="UTF-8")).hexdigest()

    for msg in (
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
        logger.info(msg)


def _get_user_config_settings(parsed_args: dict[str, Any]) -> dict[str, Any]:
    return {key: val for key, val in parsed_args.items() if key in VALID_CONFIG_SETTINGS}
