# -*- coding: utf-8 -*-
import asyncio
import json
from random import choice
from random import randint
import urllib
import uuid

from controller.constants import ErrorCodes
from controller.constants import StimulationStates
from controller.constants import StimulatorCircuitStatuses
from controller.constants import SystemStatuses
from controller.constants import VALID_CREDENTIAL_TYPES
from controller.exceptions import WebsocketCommandError
from controller.main import initialize_system_state
from controller.main_systems import server
from controller.main_systems.server import Server
from controller.utils.aio import wait_tasks_clean
from controller.utils.state_management import SystemStateManager
from pulse3D.constants import NOT_APPLICABLE_H5_METADATA
import pytest
import pytest_asyncio
from websockets import connect
from websockets.server import WebSocketServerProtocol

from ..helpers import random_bool
from ..helpers import random_semver
from ..helpers import random_well_idx
from ..helpers import TEST_PLATE_BARCODE
from ..helpers import TEST_STIM_BARCODE

WS_URI = "ws://localhost:4565"


ALL_SYSTEM_STATUSES = frozenset(SystemStatuses.__members__.values())


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
            await wait_tasks_clean({self._run_task})


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
    async with connect(WS_URI):
        pass
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
    await wait_tasks_clean({run_task})

    spied_report.assert_called_once_with(system_error_future)
    # this will not be done since there was no error
    assert not system_error_future.done()


@pytest.mark.asyncio
async def test_Server__passes_msg_from_incoming_queue_to_websocket_client(test_server_items):
    test_from_monitor_queue = test_server_items["from_monitor_queue"]

    test_msg = {"communication_type": "test"}

    await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await test_from_monitor_queue.put(test_msg)
        assert json.loads(await client.recv()) == test_msg


@pytest.mark.asyncio
async def test_Server__logs_incoming_command(test_server_items, mocker):
    spied_log_info = mocker.spy(server.logger, "info")

    test_comm = {"command": "test"}

    await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_comm))

    spied_log_info.assert_any_call(f"Comm from UI: {test_comm}")


@pytest.mark.asyncio
async def test_Server__handles_uncrecognized_command(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_report = mocker.spy(test_server, "_report_system_error")

    system_error_future = asyncio.Future()
    await test_server_items["run"](system_error_future, asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps({"command": "fake"}))

    spied_report.assert_called_once_with(system_error_future)
    assert system_error_future.result() == ErrorCodes.UI_SENT_BAD_DATA


@pytest.mark.asyncio
async def test_Server__handles_command_that_results_in_no_op(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_report = mocker.spy(test_server, "_report_system_error")
    spied_log_error = mocker.spy(server.logger, "error")

    test_command = "stop_recording"

    system_error_future = asyncio.Future()
    await test_server_items["run"](system_error_future, asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps({"command": test_command}))

    spied_log_error.assert_any_call(f"Command {test_command} resulted in a no-op")
    spied_report.assert_not_called()
    assert not system_error_future.done()


@pytest.mark.asyncio
async def test_Server__handles_failed_command(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_report = mocker.spy(test_server, "_report_system_error")
    spied_handle_error = mocker.spy(server, "handle_system_error")

    # arbitrarily choosing this command
    test_command = "test_cmd"
    test_error = WebsocketCommandError("test msg")
    test_server._handlers[test_command] = mocker.MagicMock(autospec=True, side_effect=test_error)

    system_error_future = asyncio.Future()
    run_task = await test_server_items["run"](system_error_future, asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps({"command": test_command}))
    await wait_tasks_clean({run_task})

    spied_report.assert_called_once_with(system_error_future)
    assert system_error_future.result() == ErrorCodes.UI_SENT_BAD_DATA

    spied_handle_error.assert_called_once_with(test_error, system_error_future)
    assert f"Command {test_command} failed" in test_error.__notes__


@pytest.mark.asyncio
async def test_Server__handles_shutdown_command(test_server_items, mocker):
    test_server = test_server_items["server"]

    spied_report = mocker.spy(test_server, "_report_system_error")

    system_error_future = asyncio.Future()
    run_task = await test_server_items["run"](system_error_future, asyncio.Event())

    async with connect(WS_URI) as client:
        await client.send(json.dumps({"command": "shutdown"}))
    await wait_tasks_clean({run_task})

    assert test_server.user_initiated_shutdown is True

    spied_report.assert_not_called()
    assert not system_error_future.done()


@pytest.mark.asyncio
async def test_Server__handles_login_command__success(test_server_items):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]

    test_command = {"command": "login"} | {cred: "val" for cred in VALID_CREDENTIAL_TYPES}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == test_command


@pytest.mark.asyncio
async def test_Server__handles_login_command__missing_cred(test_server_items, mocker):
    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "login"} | {cred: "val" for cred in VALID_CREDENTIAL_TYPES}
    test_missing_cred = choice(list(VALID_CREDENTIAL_TYPES))
    test_command.pop(test_missing_cred)

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == f"Missing cred type(s): {set([test_missing_cred])}"


@pytest.mark.asyncio
async def test_Server__handles_login_command__invalid_cred(test_server_items, mocker):
    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_invalid_cred = "bad_cred"
    test_command = {"command": "login", test_invalid_cred: "val"} | {
        cred: "val" for cred in VALID_CREDENTIAL_TYPES
    }

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == f"Invalid cred type(s) given: {set([test_invalid_cred])}"


@pytest.mark.asyncio
async def test_Server__handles_set_latest_software_version_command__success(test_server_items, mocker):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]

    test_command = {"command": "set_latest_software_version", "version": random_semver()}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == test_command


@pytest.mark.asyncio
async def test_Server__handles_set_latest_software_version_command__version_missing(
    test_server_items, mocker
):
    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "set_latest_software_version"}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == "Command missing 'version' value"


@pytest.mark.asyncio
async def test_Server__handles_set_latest_software_version_command__invalid_version(
    test_server_items, mocker
):
    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_bad_version = "bad"
    test_command = {"command": "set_latest_software_version", "version": test_bad_version}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == f"Invalid semver: {test_bad_version}"


@pytest.mark.asyncio
async def test_Server__handles_set_firmware_update_confirmation_command__success(test_server_items, mocker):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]

    test_command = {"command": "set_firmware_update_confirmation", "update_accepted": random_bool()}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == test_command


@pytest.mark.asyncio
async def test_Server__handles_set_firmware_update_confirmation_command__invalid_update_accepted_value(
    test_server_items, mocker
):
    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_bad_val = "bad"
    test_command = {"command": "set_firmware_update_confirmation", "update_accepted": test_bad_val}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == f"Invalid value for update_accepted: {test_bad_val}"


@pytest.mark.asyncio
@pytest.mark.parametrize("test_system_status", [SystemStatuses.CALIBRATION_NEEDED, SystemStatuses.IDLE_READY])
async def test_Server__handles_start_calibration_command__success(test_system_status, test_server_items):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": test_system_status})

    test_command = {"command": "start_calibration"}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == test_command


@pytest.mark.asyncio
async def test_Server__handles_start_calibration_command__no_op(test_server_items, mocker):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": SystemStatuses.CALIBRATING})

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_calibration"}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 0
    spied_handle_error.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_system_status",
    ALL_SYSTEM_STATUSES
    - {SystemStatuses.CALIBRATION_NEEDED, SystemStatuses.CALIBRATING, SystemStatuses.IDLE_READY},
)
async def test_Server__handles_start_calibration_command__invalid_system_status(
    test_system_status, test_server_items, mocker
):
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": test_system_status})

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_calibration"}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert (
        str(actual_error)
        == f"Cannot calibrate unless in {(SystemStatuses.CALIBRATION_NEEDED, SystemStatuses.IDLE_READY)}"
    )


@pytest.mark.asyncio
async def test_Server__handles_start_calibration_command__stim_checks_running(test_server_items, mocker):
    ssm = test_server_items["system_state_manager"]

    await ssm.update(
        {
            "system_status": choice([SystemStatuses.CALIBRATION_NEEDED, SystemStatuses.IDLE_READY]),
            "stimulator_circuit_statuses": {
                random_well_idx(): StimulatorCircuitStatuses.CALCULATING.name.lower()
            },
        }
    )

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_calibration"}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == "Cannot calibrate while stimulator checks are running"


@pytest.mark.asyncio
async def test_Server__handles_start_calibration_command__stim_running(test_server_items, mocker):
    ssm = test_server_items["system_state_manager"]

    await ssm.update(
        {
            "system_status": choice([SystemStatuses.CALIBRATION_NEEDED, SystemStatuses.IDLE_READY]),
            "stimulation_protocol_statuses": [
                choice([StimulationStates.STARTING, StimulationStates.RUNNING])
            ],
        }
    )

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_calibration"}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == "Cannot calibrate while stimulation is running"


@pytest.mark.asyncio
async def test_Server__handles_start_data_stream_command__success(test_server_items):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": SystemStatuses.IDLE_READY})

    test_command = {"command": "start_data_stream", "plate_barcode": TEST_PLATE_BARCODE}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == test_command


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_system_status",
    [SystemStatuses.BUFFERING, SystemStatuses.LIVE_VIEW_ACTIVE, SystemStatuses.RECORDING],
)
async def test_Server__handles_start_data_stream_command__no_op(
    test_system_status, test_server_items, mocker
):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": test_system_status})

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_data_stream", "plate_barcode": TEST_PLATE_BARCODE}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 0
    spied_handle_error.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_system_status",
    ALL_SYSTEM_STATUSES
    - {
        SystemStatuses.IDLE_READY,
        SystemStatuses.BUFFERING,
        SystemStatuses.LIVE_VIEW_ACTIVE,
        SystemStatuses.RECORDING,
    },
)
async def test_Server__handles_start_data_stream_command__invalid_system_status(
    test_system_status, test_server_items, mocker
):
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": test_system_status})

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_data_stream", "plate_barcode": TEST_PLATE_BARCODE}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == f"Cannot start data stream unless in in {SystemStatuses.IDLE_READY.name}"


@pytest.mark.asyncio
async def test_Server__handles_start_data_stream_command__stim_checks_running(test_server_items, mocker):
    ssm = test_server_items["system_state_manager"]
    await ssm.update(
        {
            "system_status": SystemStatuses.IDLE_READY,
            "stimulator_circuit_statuses": {
                random_well_idx(): StimulatorCircuitStatuses.CALCULATING.name.lower()
            },
        }
    )

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_data_stream", "plate_barcode": TEST_PLATE_BARCODE}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == "Cannot start data stream while stimulator checks are running"


@pytest.mark.asyncio
async def test_Server__handles_start_data_stream_command__missing_plate_barcode(test_server_items, mocker):
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": SystemStatuses.IDLE_READY})

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_data_stream"}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == "Command missing 'plate_barcode' value"


@pytest.mark.asyncio
async def test_Server__handles_start_data_stream_command__empty_plate_barcode(test_server_items, mocker):
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": SystemStatuses.IDLE_READY})

    spied_handle_error = mocker.spy(server, "handle_system_error")

    test_command = {"command": "start_data_stream", "plate_barcode": ""}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == "Cannot start data stream without a plate barcode present"


@pytest.mark.asyncio
async def test_Server__handles_start_data_stream_command__invalid_plate_barcode(test_server_items, mocker):
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": SystemStatuses.IDLE_READY})

    spied_handle_error = mocker.spy(server, "handle_system_error")
    spied_check_error = mocker.spy(server, "check_barcode_for_errors")

    test_plate_barcode = "bad"
    test_command = {"command": "start_data_stream", "plate_barcode": test_plate_barcode}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    spied_check_error.assert_called_once_with(test_plate_barcode, "plate_barcode")
    actual_error = spied_handle_error.call_args[0][0]
    assert str(actual_error) == f"Plate {spied_check_error.spy_return}"


@pytest.mark.asyncio
@pytest.mark.parametrize("test_system_status", [SystemStatuses.BUFFERING, SystemStatuses.LIVE_VIEW_ACTIVE])
async def test_Server__handles_stop_data_stream_command__success(test_system_status, test_server_items):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]
    await ssm.update({"system_status": test_system_status})

    test_command = {"command": "stop_data_stream"}

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == test_command


@pytest.mark.asyncio
@pytest.mark.parametrize("test_stim_running_status", [True, False])
@pytest.mark.parametrize(
    "test_platemap",
    [
        None,
        {},
        {
            "map_name": "test platemap name",
            "labels": [{"name": "test-label-1", "wells": [0]}, {"name": "test_label_2", "wells": [1]}],
        },
    ],
)
async def test_Server__handles_start_recording_command__success(
    test_stim_running_status, test_platemap, test_server_items
):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]

    await ssm.update({"system_status": SystemStatuses.LIVE_VIEW_ACTIVE})
    test_command = {
        "command": "start_recording",
        "start_timepoint": randint(0, 100000),  # arbitrary bounds
        "plate_barcode": TEST_PLATE_BARCODE,
        "stim_barcode": None,
        "platemap": urllib.parse.quote_plus(json.dumps(test_platemap)),
    }
    if test_stim_running_status:
        test_command["stim_barcode"] = TEST_STIM_BARCODE
        await ssm.update(
            {
                "stimulation_protocol_statuses": [
                    choice([StimulationStates.STARTING, StimulationStates.RUNNING])
                ]
            }
        )

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    expected_command = {**test_command, "platemap": test_platemap}
    if not test_stim_running_status:
        expected_command["stim_barcode"] = NOT_APPLICABLE_H5_METADATA

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == expected_command


@pytest.mark.asyncio
async def test_Server__handles_stop_recording_command__success(test_server_items):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]

    await ssm.update({"system_status": SystemStatuses.RECORDING})
    test_command = {
        "command": "stop_recording",
        "stop_timepoint": randint(0, 100000),  # arbitrary bounds
    }

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == test_command


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_recording_exists,test_replace_existing", [(False, False), (False, True), (True, True)]
)
async def test_Server__handles_update_recording_name_command__success(
    test_recording_exists, test_replace_existing, test_server_items, mocker
):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]

    mocker.patch.object(server, "_recording_exists", autospec=True, return_value=test_recording_exists)

    test_command = {
        "command": "update_recording_name",
        "new_name": " NewRecording ",
        "replace_existing": test_replace_existing,
    }

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == {**test_command, "new_name": test_command["new_name"].strip()}


@pytest.mark.asyncio
async def test_Server__handles_update_recording_name_command__recording_exists_and_not_replacing(
    test_server_items, mocker
):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]

    mocker.patch.object(server, "_recording_exists", autospec=True, return_value=True)

    test_command = {
        "command": "update_recording_name",
        "new_name": " NewRecording ",
        "replace_existing": False,
    }

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
        await client.recv() == {"communication_type": "update_recording_name", "name_updated": False}
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 0


@pytest.mark.asyncio
async def test_Server__handles_set_stim_protocols_command__success(test_server_items, mocker):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]

    test_protocol = get_random_protocol()
    test_protocol_assignments = get_random_protocol_assignments([test_protocol["protocol_id"]])

    await ssm.update({"system_status": SystemStatuses.RECORDING})
    test_command = {
        "command": "set_stim_protocols",
        "stim_barcode": TEST_STIM_BARCODE,
        "stim_info": {"protocols": [test_protocol], "protocol_assignments": test_protocol_assignments},
    }

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
        actual = await asyncio.wait_for(test_to_monitor_queue.get(), timeout=1)
        # set event since the command handler will not exit until this is done
        cpe = actual.pop("command_processed_event")
        assert isinstance(cpe, asyncio.Event)
        cpe.set()

    await wait_tasks_clean({run_task})

    assert actual == test_command


@pytest.mark.asyncio
async def test_Server__handles_start_stim_checks_command__success(test_server_items, mocker):
    test_to_monitor_queue = test_server_items["to_monitor_queue"]
    ssm = test_server_items["system_state_manager"]

    await ssm.update({"system_status": SystemStatuses.RECORDING})
    test_command = {
        "command": "start_stim_checks",
        "well_indices": get_random_well_idxs(),
        "plate_barcode": TEST_PLATE_BARCODE,
        "stim_barcode": TEST_STIM_BARCODE,
    }

    run_task = await test_server_items["run"](asyncio.Future(), asyncio.Event())
    async with connect(WS_URI) as client:
        await client.send(json.dumps(test_command))
    await wait_tasks_clean({run_task})

    assert test_to_monitor_queue.qsize() == 1
    assert await test_to_monitor_queue.get() == test_command


@pytest.mark.asyncio
async def test_Server__handles_set_stim_status_command__success(test_server_items, mocker):
    assert not "TODO"
