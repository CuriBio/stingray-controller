# -*- coding: utf-8 -*-
import asyncio
import json
import uuid

from controller.constants import ErrorCodes
from controller.main import initialize_system_state
from controller.main_systems.server import Server
from controller.utils.aio import clean_up_tasks
from controller.utils.aio import wait_tasks_clean
from controller.utils.state_management import SystemStateManager
import pytest
import pytest_asyncio
from websockets import connect
from websockets.server import WebSocketServerProtocol

WS_URI = "ws://localhost:4565"


class ServerTestRunner:
    def __init__(self, server):
        self._server = server
        self._run_task = None

    async def run(self, system_error_future, server_running_event):
        self._run_task = asyncio.create_task(self._server.run(system_error_future, server_running_event))
        await server_running_event.wait()
        return self._run_task

    async def clean_up(self):
        if self._run_task:
            await clean_up_tasks({self._run_task})


@pytest_asyncio.fixture(scope="function", name="test_server_items")
async def fixture__test_server_items(mocker):
    ssm = SystemStateManager()
    await ssm.update(
        initialize_system_state({"base_directory": None, "expected_software_version": None}, uuid.uuid4())
    )

    from_monitor_queue = asyncio.Queue()
    to_monitor_queue = asyncio.Queue()

    server = Server(ssm.get_read_only_copy, from_monitor_queue, to_monitor_queue)
    test_runner = ServerTestRunner(server)

    yield {
        "server": server,
        "system_state_manager": ssm,
        "from_monitor_queue": from_monitor_queue,
        "to_monitor_queue": to_monitor_queue,
        "run": test_runner.run,
    }

    await test_runner.clean_up()


@pytest.mark.asyncio
async def test_Server__handles_new_connections_correctly(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_handle_comm = mocker.spy(test_server, "_handle_comm")

    await test_server_items["run"](asyncio.Future(), asyncio.Event())

    assert not test_server._ui_connection_made.is_set()
    assert test_server._websocket is None
    spied_handle_comm.assert_not_called()

    async with connect(WS_URI):
        assert test_server._ui_connection_made.is_set()
        assert isinstance(test_server._websocket, WebSocketServerProtocol)
        spied_handle_comm.assert_called_once()
        # make a second connection and make sure it is ignored
        async with connect(WS_URI):
            spied_handle_comm.assert_called_once()


@pytest.mark.asyncio
async def test_Server__handles_disconnect(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_report = mocker.spy(test_server, "_report_system_error")

    system_error_future = asyncio.Future()
    run_task = await test_server_items["run"](system_error_future, asyncio.Event())

    # TODO make a function for this if this pattern becomes common
    async with connect(WS_URI):
        pass
    # await this so the next assertion isn't made too early
    await wait_tasks_clean({run_task})

    spied_report.assert_not_called()
    # this will not be done since there was no error
    assert not system_error_future.done()


@pytest.mark.asyncio
async def test_Server__handles_cancellation(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_report = mocker.spy(test_server, "_report_system_error")

    system_error_future = asyncio.Future()
    run_task = await test_server_items["run"](system_error_future, asyncio.Event())

    async with connect(WS_URI):
        run_task.cancel()
    # await this so the next assertion isn't made too early
    await wait_tasks_clean({run_task})

    spied_report.assert_called_once_with(system_error_future)
    # this will not be done since there was no error
    assert not system_error_future.done()


@pytest.mark.asyncio
async def test_Server__handles_uncrecognized_command(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_report = mocker.spy(test_server, "_report_system_error")

    system_error_future = asyncio.Future()
    run_task = await test_server_items["run"](system_error_future, asyncio.Event())

    async with connect(WS_URI) as client:
        await client.send(json.dumps({"command": "fake"}))
    # await this so the next assertion isn't made too early
    await wait_tasks_clean({run_task})

    spied_report.assert_called_once_with(system_error_future)
    assert system_error_future.result() == ErrorCodes.UI_SENT_BAD_DATA
