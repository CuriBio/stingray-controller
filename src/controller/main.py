# -*- coding: utf-8 -*-
"""Instrument Controller."""
from __future__ import annotations

import argparse
import asyncio
import base64
import copy
import hashlib
import json
import logging
import multiprocessing
import os
from os import getpid
import platform
import queue
from queue import Queue
import socket
import sys
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
import uuid


from stdlib_utils import configure_logging
from stdlib_utils import is_port_in_use

from .constants import COMPILED_EXE_BUILD_TIMESTAMP
from .constants import CURRENT_SOFTWARE_VERSION
from .constants import DEFAULT_SERVER_PORT_NUMBER
from .constants import SERVER_INITIALIZING_STATE
from .constants import SOFTWARE_RELEASE_CHANNEL
from .exceptions import LocalServerPortAlreadyInUseError
from .exceptions import MultiprocessingNotSetToSpawnError

from .main_process.subprocess_monitor import SubprocessMonitor
from .main_process.server import Server

from .utils.generic import redact_sensitive_info_from_path, wait_tasks_clean


logger = logging.getLogger(__name__)


async def main(
    command_line_args: List[str], object_access_for_testing: Optional[Dict[str, Any]] = None
) -> None:
    """Parse command line arguments and run."""
    # if object_access_for_testing is None:
    #     object_access_for_testing = dict()

    try:
        parsed_args = _parse_cmd_line_args(command_line_args)

        startup_options = []
        if parsed_args.startup_test_options:
            startup_options = parsed_args.startup_test_options
        # start_subprocesses = "no_subprocesses" not in startup_options
        start_server = "no_server" not in startup_options

        log_level = logging.DEBUG if parsed_args.log_level_debug else logging.INFO
        path_to_log_folder = parsed_args.log_file_dir
        configure_logging(
            path_to_log_folder=path_to_log_folder, log_file_prefix="stingray_log", log_level=log_level
        )

        logger.info(f"Stingray Controller v{CURRENT_SOFTWARE_VERSION} started")
        logger.info(f"Build timestamp/version: {COMPILED_EXE_BUILD_TIMESTAMP}")
        logger.info(f"Release Channel: {SOFTWARE_RELEASE_CHANNEL}")

        # Tanner (1/14/21): parsed_args_dict is only used to log the command line args at the moment, so initial_base64_settings can be deleted and log_file_dir can just be replaced here without affecting anything that actually needs the original value
        parsed_args_dict = copy.deepcopy(vars(parsed_args))

        scrubbed_path_to_log_folder = redact_sensitive_info_from_path(path_to_log_folder)
        parsed_args_dict["log_file_dir"] = scrubbed_path_to_log_folder
        # Tanner (1/14/21): Unsure why the back slashes are duplicated when converting the dict to string. Using replace here to remove the duplication, not sure if there is a better way to solve or avoid this problem
        logger.info(f"Command Line Args: {parsed_args_dict}".replace(r"\\", "\\"))
        logger.info(f"Using directory for log files: {scrubbed_path_to_log_folder}")

        # multiprocessing_start_method = multiprocessing.get_start_method(allow_none=True)
        # if multiprocessing_start_method != "spawn":
        #     raise MultiprocessingNotSetToSpawnError(multiprocessing_start_method)

        system_state = _initialize_system_state(parsed_args)

        logger.info(f"Log File UUID: {system_state['log_file_id']}")
        logger.info(f"SHA512 digest of Computer Name {system_state['computer_name_hash']}")

        if parsed_args.debug_test_post_build:
            print(f"Successfully opened and closed application v{CURRENT_SOFTWARE_VERSION}.")  # allow-print
            return

        system_state["system_status"] = SERVER_INITIALIZING_STATE
        logger.info(f"Using server port number: {DEFAULT_SERVER_PORT_NUMBER}")

        if is_port_in_use(DEFAULT_SERVER_PORT_NUMBER):  # TODO make sure this still works
            raise LocalServerPortAlreadyInUseError(DEFAULT_SERVER_PORT_NUMBER)

        _log_system_info()
        logger.info("Spawning subprocesses")

        # process_manager = ProcessesManager(system_state=system_state, logging_level=log_level)
        # object_access_for_testing["process_manager"] = process_manager
        # object_access_for_testing["system_state"] = system_state

        # process_manager.create_processes()
        # if start_subprocesses:
        #     logger.info(f"Main Process PID: {getpid()}")
        #     subprocess_id_dict = process_manager.start_processes()
        #     for subprocess_name, pid in subprocess_id_dict.items():
        #         logger.info(f"{subprocess_name} PID: {pid}")

        queues = {
            "to": {
                "server": asyncio.Queue()
                # TODO
                # "instrument_comm": MPQueueAsyncWrapper(process_manager.queue_container.from_instrument_comm),
                # "file_writer": MPQueueAsyncWrapper(process_manager.queue_container.from_file_writer),
                # "data_analyzer": MPQueueAsyncWrapper(process_manager.queue_container.from_data_analyzer),
            },
            "from": {
                "server": asyncio.Queue()
                # "instrument_comm": MPQueueAsyncWrapper(
                #     self._process_manager.queue_container.to_instrument_comm(0)
                # ),
                # "file_writer": MPQueueAsyncWrapper(process_manager.queue_container.to_file_writer),
                # "data_analyzer": MPQueueAsyncWrapper(self._process_manager.queue_container.to_data_analyzer),
            }
            # "outgoing_data_stream": MPQueueAsyncWrapper(
            #     self._process_manager.queue_container.data_analyzer_boards[0][1]
            # ),
        }

        subprocess_monitor = SubprocessMonitor(system_state, queues)

        tasks = {asyncio.create_task(subprocess_monitor.run())}

        if start_server:
            server = Server(system_state, queues["to"]["server"], queues["from"]["server"])
            tasks.add(asyncio.create_task(server.run()))

        await wait_tasks_clean(tasks)

        # TODO
        # upload_log_files_to_s3(system_state["config_settings"])

    except Exception as e:
        logger.error(f"ERROR IN MAIN: {repr(e)}")

    finally:
        # TODO
        # if process_monitor_thread:
        #     process_monitor_thread.soft_stop()
        #     process_monitor_thread.join()
        #     logger.info("Process monitor shut down")
        logger.info("Program exiting")


def _parse_cmd_line_args(command_line_args: List[str]) -> "TODO":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--debug-test-post-build",
        action="store_true",
        help="simple test to run after building executable to confirm libraries are linked/imported correctly",
    )
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
        "--initial-base64-settings",
        type=str,
        help="allow initial configuration of user settings",
    )
    parser.add_argument(
        "--expected-software-version",
        type=str,
        help="used to make sure flask server and GUI are the same version",
    )
    parser.add_argument(
        "--skip-software-version-verification",
        action="store_true",
        help="override any supplied expected software version and disable the check",
    )
    parser.add_argument(
        "--startup-test-options",
        type=str,
        nargs="+",
        choices=["no_flask", "no_subprocesses"],
        help="indicate how much of the main script should not be started",
    )
    return parser.parse_args(command_line_args)


def _initialize_system_state(parsed_args: "TODO") -> Dict[str, Any]:
    system_state = dict()

    # system_state["connected_to_fe"] = False

    if parsed_args.initial_base64_settings:
        # Eli (7/15/20): Moved this ahead of the exit for debug_test_post_build so that it could be easily unit tested. The equals signs are adding padding..apparently a quirk in python https://stackoverflow.com/questions/2941995/python-ignore-incorrect-padding-error-when-base64-decoding
        decoded_settings: bytes = base64.urlsafe_b64decode(str(parsed_args.initial_base64_settings) + "===")
        settings_dict = json.loads(decoded_settings)
    else:  # pragma: no cover
        settings_dict = {
            "recording_directory": os.path.join(os.getcwd(), "recordings"),
            "mag_analysis_output_dir": os.path.join(os.getcwd(), "analysis"),
            "log_file_id": uuid.uuid4(),
        }

    system_state["config_settings"] = {
        "recording_directory": settings_dict["recording_directory"],
        "log_directory": parsed_args.log_file_dir,
        "mag_analysis_output_dir": settings_dict["mag_analysis_output_dir"],
    }

    if parsed_args.expected_software_version:
        if not parsed_args.skip_software_version_verification:
            system_state["expected_software_version"] = parsed_args.expected_software_version

    system_state["log_file_id"] = settings_dict["log_file_id"]

    computer_name_hash = hashlib.sha512(socket.gethostname().encode(encoding="UTF-8")).hexdigest()
    system_state["computer_name_hash"] = computer_name_hash

    num_wells = 24
    system_state["stimulation_running"] = [False] * num_wells
    system_state["latest_software_version"] = None
    system_state["stimulation_info"] = None
    system_state["stimulator_circuit_statuses"] = {}

    return system_state


def _log_system_info() -> None:
    uname = platform.uname()
    uname_sys = getattr(uname, "system")
    uname_release = getattr(uname, "release")
    uname_version = getattr(uname, "version")

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
    ):
        logger.info(msg)
