# -*- coding: utf-8 -*-


import asyncio
from datetime import datetime
import json
import os
import subprocess

from controller.constants import DEFAULT_SERVER_PORT_NUMBER
from controller.constants import SystemStatuses
import pytest
from stdlib_utils import confirm_port_available
from stdlib_utils import confirm_port_in_use
from stdlib_utils import is_system_windows
from websockets import connect
from websockets.exceptions import ConnectionClosedOK


def _print_with_timestamp(msg):
    print(f"[PYTEST {datetime.utcnow().strftime('%H:%M:%S.%f')}] - {msg}")  # allow-print


@pytest.mark.only_exe
@pytest.mark.timeout(300)
def test_exe__launches_and_connects_to_websocket_client_and_shutdowns_cleanly():
    # make sure all the server instances launched during the unit tests have closed
    confirm_port_available(DEFAULT_SERVER_PORT_NUMBER, timeout=10)

    exe_file_name = "instrument-controller"
    if is_system_windows():
        exe_file_name += ".exe"

    subprocess_args = [
        os.path.join(
            os.path.dirname(__file__),
            os.pardir,
            os.pardir,
            "electron",
            "dist-python",
            "instrument-controller",
            exe_file_name,
        )
    ]

    with subprocess.Popen(subprocess_args) as sub_process:
        _print_with_timestamp("confirm port is in use")
        confirm_port_in_use(DEFAULT_SERVER_PORT_NUMBER, timeout=30)

        asyncio.run(_connect())

        _print_with_timestamp("waiting for subprocess to terminate")
        # wait for subprocess to fully terminate and make sure the exit code is 0 (no error)
        assert sub_process.wait() == 0
        _print_with_timestamp("subprocess terminated")

    _print_with_timestamp("done")


async def _connect():
    _print_with_timestamp("connecting to websocket server")
    async with connect(f"ws://localhost:{DEFAULT_SERVER_PORT_NUMBER}") as websocket:
        msg = None
        while msg != {
            "communication_type": "status_update",
            "system_status": str(SystemStatuses.SERVER_INITIALIZING_STATE.value),
        }:
            msg = json.loads(await websocket.recv())
        _print_with_timestamp("system status update received. Sending shutdown command")

        await websocket.send(json.dumps({"command": "shutdown"}))

        _print_with_timestamp("waiting for connection to close")
        # just wait for the exception to be raised, ignore any other messages
        try:
            while True:
                await websocket.recv()
        except ConnectionClosedOK:
            pass
        _print_with_timestamp("connection closed")
