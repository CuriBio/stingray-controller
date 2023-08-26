# -*- coding: utf-8 -*-
import asyncio
from random import choice

from controller.constants import CURI_VID
from controller.constants import SERIAL_COMM_BAUD_RATE
from controller.constants import SERIAL_COMM_BYTESIZE
from controller.constants import SERIAL_COMM_READ_TIMEOUT
from controller.constants import STM_VID
from controller.exceptions import NoInstrumentDetectedError
from controller.subsystems import instrument_comm
from controller.subsystems.instrument_comm import InstrumentComm
import pytest
import serial
from serial.tools.list_ports_common import ListPortInfo

from ..fixtures import fixture__wait_tasks_clean


__fixtures__ = [fixture__wait_tasks_clean]


@pytest.fixture(scope="function", name="test_instrument_comm_obj")
def fixture__test_instrument_comm_obj(mocker):
    ic = InstrumentComm(asyncio.Queue(), asyncio.Queue())
    yield ic
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

    assert test_instrument_comm_obj._to_monitor_queue.get_nowait() == {
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

    assert test_instrument_comm_obj._to_monitor_queue.get_nowait() == {
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
