# -*- coding: utf-8 -*-
import asyncio
import uuid

from controller.main import initialize_system_state
from controller.main_systems.server import Server
from controller.utils.aio import clean_up_tasks
from controller.utils.state_management import SystemStateManager
import pytest
from websockets import connect
from websockets.server import WebSocketServerProtocol

WS_URI = "ws://localhost:4565"


@pytest.fixture(scope="function", name="test_server_items")
def fixture__test_server_items(mocker):
    ssm = SystemStateManager()
    asyncio.run(
        ssm.update(
            initialize_system_state({"base_directory": None, "expected_software_version": None}, uuid.uuid4())
        )
    )

    from_monitor_queue = asyncio.Queue()
    to_monitor_queue = asyncio.Queue()

    server = Server(ssm.get_read_only_copy, from_monitor_queue, to_monitor_queue)
    yield {
        "server": server,
        "system_state_manager": ssm,
        "from_monitor_queue": from_monitor_queue,
        "to_monitor_queue": to_monitor_queue,
    }

    # TODO any teardown needed here?


@pytest.mark.asyncio
async def test_Server__handles_new_connections_correctly(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_handle_comm = mocker.spy(test_server, "_handle_comm")

    server_run_task = asyncio.create_task(test_server.run(asyncio.Future(), asyncio.Event()))

    assert not test_server._ui_connection_made.is_set()
    assert test_server._websocket is None
    spied_handle_comm.assert_not_called()

    async with connect(WS_URI):
        assert test_server._ui_connection_made.is_set()
        assert isinstance(test_server._websocket, WebSocketServerProtocol)
        spied_handle_comm.assert_called_once()

    await clean_up_tasks({server_run_task})
