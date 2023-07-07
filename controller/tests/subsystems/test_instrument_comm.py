# -*- coding: utf-8 -*-
import asyncio
from collections import deque
from random import choice
from random import randint

from controller.constants import CURI_VID
from controller.constants import SERIAL_COMM_BAUD_RATE
from controller.constants import SERIAL_COMM_BYTESIZE
from controller.constants import SERIAL_COMM_READ_TIMEOUT
from controller.constants import SerialCommPacketTypes
from controller.constants import STM_VID
from controller.exceptions import InstrumentCommandResponseError
from controller.exceptions import NoInstrumentDetectedError
from controller.subsystems import instrument_comm
from controller.subsystems.instrument_comm import InstrumentComm
from controller.utils.aio import clean_up_tasks
from controller.utils.serial_comm import create_data_packet
import pytest
import serial
from serial.tools.list_ports_common import ListPortInfo

from ..fixtures import fixture__wait_tasks_clean
from ..helpers import compare_exceptions
from ..helpers import random_serial_comm_timestamp


__fixtures__ = [fixture__wait_tasks_clean]


class MockInstrument:
    def __init__(self):
        self.recv = deque()
        self.send = deque()

        self.in_waiting = 123  # arbitrary number

    async def read_async(self, size):
        try:
            return self.send.popleft()
        except IndexError:
            return bytes()

    async def write_async(self, data):
        self.recv.append(data)


@pytest.fixture(scope="function", name="test_instrument_comm_obj")
def fixture__test_instrument_comm_obj(mocker):
    ic = InstrumentComm(*[asyncio.Queue() for _ in range(4)])
    yield ic
    # TODO any teardown needed here?


@pytest.fixture(scope="function", name="test_instrument_comm_obj_with_connection")
def fixture__test_instrument_comm_obj_with_connection(test_instrument_comm_obj, mocker):
    connection = MockInstrument()

    def se():
        test_instrument_comm_obj._instrument = connection

    mocker.patch.object(test_instrument_comm_obj, "_setup", autospec=True, side_effect=se)

    yield test_instrument_comm_obj, connection
    # TODO any teardown needed here?


@pytest.fixture(scope="function", name="patch_comports")
def fixture__patch_comports(mocker):
    comport = "COM1"

    dummy_port_info = ListPortInfo("")
    dummy_port_info.vid = choice([STM_VID, CURI_VID])
    dummy_port_info.name = comport
    dummy_port_info.description = f"Device ({comport})"

    mocked_comports = mocker.patch.object(
        instrument_comm.list_ports,
        "comports",
        autospec=True,
        return_value=[ListPortInfo(""), dummy_port_info, ListPortInfo("")],
    )
    yield mocked_comports, dummy_port_info


@pytest.mark.asyncio
async def test_InstrumentComm__creates_connection_to_real_instrument_correctly(
    patch_wait_tasks_clean, patch_comports, test_instrument_comm_obj, mocker
):
    # mocking to speed up test
    mocker.patch.object(
        test_instrument_comm_obj, "_register_magic_word", autospec=True, side_effect=Exception()
    )

    _, dummy_port_info = patch_comports
    mocked_aioserial = mocker.patch.object(instrument_comm, "AioSerial", autospec=True)

    await test_instrument_comm_obj.run(asyncio.Future())

    mocked_aioserial.assert_called_once_with(
        port=dummy_port_info.name,
        baudrate=SERIAL_COMM_BAUD_RATE,
        bytesize=SERIAL_COMM_BYTESIZE,
        timeout=SERIAL_COMM_READ_TIMEOUT,
        stopbits=serial.STOPBITS_ONE,
    )

    assert test_instrument_comm_obj._instrument is mocked_aioserial.return_value

    assert test_instrument_comm_obj._comm_to_monitor_queue.get_nowait() == {
        "command": "get_board_connection_status",
        "in_simulation_mode": False,
    }


@pytest.mark.asyncio
async def test_InstrumentComm__creates_connection_to_virtual_instrument_correctly(
    patch_wait_tasks_clean, patch_comports, test_instrument_comm_obj, mocker
):
    # mocking to speed up test
    mocker.patch.object(
        test_instrument_comm_obj, "_register_magic_word", autospec=True, side_effect=Exception()
    )

    _, dummy_port_info = patch_comports
    dummy_port_info.vid = None  # set this to None so no real instrument is found
    mocked_aioserial = mocker.patch.object(instrument_comm, "AioSerial", autospec=True)
    mocked_vic_init = mocker.patch.object(
        instrument_comm.VirtualInstrumentConnection, "__init__", autospec=True, return_value=None
    )
    mocked_vic_connect = mocker.patch.object(
        instrument_comm.VirtualInstrumentConnection, "connect", autospec=True
    )

    await test_instrument_comm_obj.run(asyncio.Future())

    mocked_aioserial.assert_not_called()
    mocked_vic_init.assert_called_once_with(test_instrument_comm_obj._instrument)
    mocked_vic_connect.assert_awaited_once_with(test_instrument_comm_obj._instrument)

    assert test_instrument_comm_obj._comm_to_monitor_queue.get_nowait() == {
        "command": "get_board_connection_status",
        "in_simulation_mode": True,
    }


# TODO assert correct message put into queue after connection


@pytest.mark.asyncio
async def test_InstrumentComm__reports_system_error_if_no_real_or_virtual_instrument_found(
    patch_wait_tasks_clean, patch_comports, test_instrument_comm_obj, mocker
):
    _, dummy_port_info = patch_comports
    dummy_port_info.vid = None  # set this to None so no real instrument is found

    # mock this so no virtual instrument found
    mocked_vic = mocker.patch.object(instrument_comm, "VirtualInstrumentConnection", autospec=True)
    mocked_vic.return_value.connect.side_effect = Exception()

    mocked_handle_error = mocker.patch.object(instrument_comm, "handle_system_error", autospec=True)

    system_error_future = asyncio.Future()
    await test_instrument_comm_obj.run(system_error_future)

    # TODO make a function for this if it becomes common
    assert isinstance(mocked_handle_error.call_args[0][0], NoInstrumentDetectedError)
    assert mocked_handle_error.call_args[0][1] is system_error_future


# TODO add tests for each individual step of the setup


# TODO in one of the success tests for each of the commands, assert that the correct message was sent to the instrument


@pytest.mark.asyncio
async def test_InstrumentComm__handles_start_data_stream_command__success__no_stim_packets_to_be_sent(
    test_instrument_comm_obj_with_connection,
):
    test_ic, test_instrument = test_instrument_comm_obj_with_connection

    test_global_time_at_stream_start = randint(0, 0xFFFF)  # arbitrary range
    test_command = {"command": "start_data_stream"}

    run_task = asyncio.create_task(test_ic.run(asyncio.Future()))

    await test_ic._from_monitor_queue.put(test_command)
    # set up response
    test_instrument.send.append(
        create_data_packet(
            random_serial_comm_timestamp(),
            SerialCommPacketTypes.START_DATA_STREAMING,
            bytes([0]) + test_global_time_at_stream_start.to_bytes(8, byteorder="little"),
        )
    )

    assert await asyncio.wait_for(test_ic._comm_to_monitor_queue.get(), timeout=1) == test_command

    assert test_ic._data_stream_manager._base_global_time_of_data_stream == test_global_time_at_stream_start
    assert test_ic._data_stream_manager.is_streaming

    assert test_ic._data_stream_manager._data_to_file_writer_queue.qsize() == 0

    await clean_up_tasks({run_task})


# TODO
# @pytest.mark.asyncio
# async def test_InstrumentComm__handles_start_data_stream_command__success__stim_packets_buffered(
#     test_instrument_comm_obj_with_connection,
# ):


@pytest.mark.asyncio
async def test_InstrumentComm__handles_start_data_stream_command__fail(
    test_instrument_comm_obj_with_connection, mocker
):
    test_ic, test_instrument = test_instrument_comm_obj_with_connection

    spied_handle_error = mocker.spy(instrument_comm, "handle_system_error")

    test_command = {"command": "start_data_stream"}

    system_error_future = asyncio.Future()
    run_task = asyncio.create_task(test_ic.run(system_error_future))

    await test_ic._from_monitor_queue.put(test_command)
    # set up response
    test_instrument.send.append(
        create_data_packet(
            random_serial_comm_timestamp(),
            SerialCommPacketTypes.START_DATA_STREAMING,
            bytes([1]),
        )
    )

    await asyncio.wait_for(system_error_future, timeout=1)

    assert compare_exceptions(
        spied_handle_error.call_args[0][0], InstrumentCommandResponseError(test_command["command"])
    )
    assert spied_handle_error.call_args[0][1] is system_error_future

    await clean_up_tasks({run_task})


@pytest.mark.asyncio
async def test_InstrumentComm__handles_stop_data_stream_command__success(
    test_instrument_comm_obj_with_connection,
):
    test_ic, test_instrument = test_instrument_comm_obj_with_connection

    test_command = {"command": "stop_data_stream"}

    run_task = asyncio.create_task(test_ic.run(asyncio.Future()))

    await test_ic._from_monitor_queue.put(test_command)
    # set up response
    test_instrument.send.append(
        create_data_packet(
            random_serial_comm_timestamp(), SerialCommPacketTypes.STOP_DATA_STREAMING, bytes([0])
        )
    )

    assert await asyncio.wait_for(test_ic._comm_to_monitor_queue.get(), timeout=1) == test_command

    assert test_ic._data_stream_manager._base_global_time_of_data_stream is None
    assert not test_ic._data_stream_manager.is_streaming

    await clean_up_tasks({run_task})


@pytest.mark.asyncio
async def test_InstrumentComm__handles_stop_data_stream_command__fail(
    test_instrument_comm_obj_with_connection, mocker
):
    test_ic, test_instrument = test_instrument_comm_obj_with_connection

    spied_handle_error = mocker.spy(instrument_comm, "handle_system_error")

    test_command = {"command": "stop_data_stream"}

    system_error_future = asyncio.Future()
    run_task = asyncio.create_task(test_ic.run(system_error_future))

    await test_ic._from_monitor_queue.put(test_command)
    # set up response
    test_instrument.send.append(
        create_data_packet(
            random_serial_comm_timestamp(),
            SerialCommPacketTypes.STOP_DATA_STREAMING,
            bytes([1]),
        )
    )

    await asyncio.wait_for(system_error_future, timeout=1)

    assert compare_exceptions(
        spied_handle_error.call_args[0][0], InstrumentCommandResponseError(test_command["command"])
    )
    assert spied_handle_error.call_args[0][1] is system_error_future

    await clean_up_tasks({run_task})


@pytest.mark.asyncio
async def test_InstrumentComm__handles_start_stim_checks_command__success(
    test_instrument_comm_obj_with_connection,
):
    test_ic, test_instrument = test_instrument_comm_obj_with_connection

    test_command = {"command": "start_stim_checks"}

    run_task = asyncio.create_task(test_ic.run(asyncio.Future()))

    await test_ic._from_monitor_queue.put(test_command)
    # set up response
    test_instrument.send.append(
        create_data_packet(
            random_serial_comm_timestamp(), SerialCommPacketTypes.STIM_IMPEDANCE_CHECK, bytes([0])
        )
    )

    assert await asyncio.wait_for(test_ic._comm_to_monitor_queue.get(), timeout=1) == test_command

    # TODO assert something else here?

    await clean_up_tasks({run_task})
