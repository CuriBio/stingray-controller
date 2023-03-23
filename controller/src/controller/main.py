# -*- coding: utf-8 -*-
"""Instrument Controller."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import platform
import socket
import sys
from typing import Any
import uuid

from stdlib_utils import configure_logging
from stdlib_utils import is_port_in_use

from .constants import COMPILED_EXE_BUILD_TIMESTAMP
from .constants import CURRENT_SOFTWARE_VERSION
from .constants import DEFAULT_SERVER_PORT_NUMBER
from .constants import NUM_WELLS
from .constants import SOFTWARE_RELEASE_CHANNEL
from .constants import SystemStatuses
from .exceptions import LocalServerPortAlreadyInUseError
from .main_systems.server import Server
from .main_systems.system_monitor import SystemMonitor
from .subsystems.cloud_comm import CloudComm
from .subsystems.instrument_comm import InstrumentComm
from .utils.generic import redact_sensitive_info_from_path
from .utils.generic import wait_tasks_clean
from .utils.state_management import SystemStateManager


logger = logging.getLogger(__name__)


async def main(command_line_args: list[str]) -> None:
    """Parse command line arguments and run."""
    # if object_access_for_testing is None:
    #     object_access_for_testing = dict()

    try:
        parsed_args = _parse_cmd_line_args(command_line_args)
        log_level = logging.DEBUG if parsed_args["log_level_debug"] else logging.INFO
        configure_logging(
            path_to_log_folder=parsed_args["log_file_dir"],
            log_file_prefix="stingray_log",
            log_level=log_level,
        )

        logger.info(f"Stingray Controller v{CURRENT_SOFTWARE_VERSION} started")
        logger.info(f"Build timestamp/version: {COMPILED_EXE_BUILD_TIMESTAMP}")
        logger.info(f"Release Channel: {SOFTWARE_RELEASE_CHANNEL}")

        log_file_id = uuid.uuid4()
        logger.info(f"Log ID: {log_file_id}")

        _log_cmd_line_args(parsed_args)
        _log_system_info()

        # if parsed_args.test:
        #     logger.info(f"Successfully opened and closed application v{CURRENT_SOFTWARE_VERSION}")
        #     return

        logger.info(f"Using server port number: {DEFAULT_SERVER_PORT_NUMBER}")

        if is_port_in_use(DEFAULT_SERVER_PORT_NUMBER):
            raise LocalServerPortAlreadyInUseError(DEFAULT_SERVER_PORT_NUMBER)

        # TODO move this into SystemMonitor?
        # logger.info("Spawning subsystems")

        # TODO wrap all this in a function?

        system_state_manager = SystemStateManager()
        await system_state_manager.update(_initialize_system_state(parsed_args, log_file_id))

        queues = create_system_queues()

        system_monitor = SystemMonitor(system_state_manager, queues)
        server = Server(
            system_state_manager.get_read_only_copy, queues["to"]["server"], queues["from"]["server"]
        )

        instrument_comm_subsystem = InstrumentComm(
            queues["to"]["instrument_comm"], queues["from"]["instrument_comm"]
        )

        cloud_comm_subsystem = CloudComm(queues["to"]["cloud_comm"], queues["from"]["cloud_comm"])

        tasks = {
            asyncio.create_task(system_monitor.run()),
            asyncio.create_task(server.run()),
            asyncio.create_task(instrument_comm_subsystem.run()),
            asyncio.create_task(cloud_comm_subsystem.run()),
        }

        # TODO make sure that errors in subprocesses get raised all the way up to the top here
        # TODO have server send a "shutting down" or "error" msg or something when it gets cancelled
        await wait_tasks_clean(tasks)

    except Exception as e:
        logger.error(f"ERROR IN MAIN: {repr(e)}")
        # TODO raise error here ?

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
    # parser.add_argument(
    #     "--test",
    #     action="store_true",
    #     help="simple test to run after building executable to confirm libraries are linked/imported correctly",
    # )
    parser.add_argument(
        "--log-level-debug",
        action="store_true",
        help="sets the loggers to be more verbose and log DEBUG level pieces of information",
    )
    parser.add_argument(
        "--log-file-dir",
        type=str,
        help="allow manual setting of the directory in which log files will be stored",
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

    if log_file_dir := parsed_args_copy.get("log_file_dir"):
        parsed_args_copy["log_file_dir"] = redact_sensitive_info_from_path(log_file_dir)
    # Tanner (1/14/21): Unsure why the back slashes are duplicated when converting the dict to string. Using replace here to remove the duplication, not sure if there is a better way to solve or avoid this problem
    logger.info(f"Command Line Args: {parsed_args_copy}".replace(r"\\", "\\"))


# TODO make this function reusable in tests
def _initialize_system_state(parsed_args: dict[str, Any], log_file_id: uuid.UUID) -> dict[str, Any]:
    system_state = {
        # main
        "system_status": SystemStatuses.SERVER_INITIALIZING_STATE,
        "in_simulation_mode": False,
        "stimulation_running": [False] * NUM_WELLS,
        # updating
        "main_firmware_update": None,
        "channel_firmware_update": None,
        "latest_software_version": None,
        # user options
        "config_settings": {
            "log_directory": parsed_args["log_file_dir"]
        },  # TODO consider not storing this in a dict
        "is_user_logged_in": False,
        # instrument
        "instrument_metadata": {},
        "stim_info": {},
        "stimulator_circuit_statuses": {},
        "stim_barcode": None,
        "plate_barcode": None,
        # misc
        "log_file_id": log_file_id,
    }

    if (expected_software_version := parsed_args["expected_software_version"]) and not parsed_args[
        "skip_software_version_verification"
    ]:
        system_state["expected_software_version"] = expected_software_version

    return system_state


def _log_system_info() -> None:
    uname = platform.uname()
    uname_sys = getattr(uname, "system")
    uname_release = getattr(uname, "release")
    uname_version = getattr(uname, "version")

    # TODO make a function for this
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
