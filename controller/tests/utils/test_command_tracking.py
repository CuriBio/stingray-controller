# -*- coding: utf-8 -*-
import asyncio
from random import randint

from controller.constants import SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS
from controller.utils import command_tracking
from controller.utils.command_tracking import CommandTracker
import pytest


@pytest.mark.asyncio
async def test_CommandTracker__add__sets_up_timer_for_command_expiration(mocker):
    spied_sleep = mocker.spy(command_tracking.asyncio, "sleep")

    await CommandTracker().add(randint(0, 100), {})

    # this is assuming that the last await of asyncio.sleep is the one we're expecting.
    # if this assertion starts failing, try assert_any_await
    spied_sleep.assert_awaited_with(SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS)


@pytest.mark.asyncio
async def test_CommandTracker__pop__returns_most_recent_command_for_given_packet_type():
    ct = CommandTracker()

    test_packet_type = randint(0, 100)
    expected_command = {"expected": "command"}

    # add a few other commands to make sure the correct command is returned
    await ct.add(test_packet_type + 1, {})
    await ct.add(test_packet_type, expected_command)
    await ct.add(test_packet_type - 1, {})
    await ct.add(test_packet_type, {})

    actual_command_info = await ct.pop(test_packet_type)
    assert actual_command_info == expected_command


@pytest.mark.asyncio
async def test_CommandTracker__pop__stops_timeout_for_the_command_returned(mocker):
    # set command to expire instantly, but because we immediately pop it, the expiration will not occur
    mocker.patch.object(command_tracking, "SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS", 0)

    ct = CommandTracker()

    test_packet_type = randint(0, 100)
    await ct.add(test_packet_type, {"test": "command"})
    await ct.pop(test_packet_type)

    # wait a command to expire which shouldn't happen since it is supposed to be completed inside pop().
    # if the command does not expire (the expected behavior), wait_for raise asyncio.TimeoutError
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(ct.wait_for_expired_command(), timeout=0.001)


@pytest.mark.asyncio
async def test_CommandTracker__pop__raises_error_if_packet_type_not_found(mocker):
    test_packet_type = randint(0, 100)

    with pytest.raises(ValueError, match=f"No commands of packet type: {test_packet_type}"):
        await CommandTracker().pop(test_packet_type)


@pytest.mark.asyncio
async def test_CommandTracker__wait_for_expired_command__returns_first_command_to_expire__multiple_commands_expire(
    mocker,
):
    # set commands to expire instantly
    mocker.patch.object(command_tracking, "SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS", 0)

    ct = CommandTracker()

    test_packet_type = randint(0, 100)
    expected_command = {"expected": "command"}

    await ct.add(test_packet_type, expected_command)
    await ct.add(test_packet_type + 1, {})

    # let both commands expire
    await asyncio.sleep(0)

    assert await ct.wait_for_expired_command() == expected_command


@pytest.mark.asyncio
async def test_CommandTracker__wait_for_expired_command__returns_first_command_to_expire__initial_command_is_completed(
    mocker,
):
    ct = CommandTracker()

    test_packet_type = randint(0, 100)
    expected_command = {"expected": "command"}

    # add initial command
    await ct.add(test_packet_type + 1, {})

    # set next command to expire instantly
    mocker.patch.object(command_tracking, "SERIAL_COMM_RESPONSE_TIMEOUT_SECONDS", 0)
    await ct.add(test_packet_type, expected_command)

    # pop the initial command so it doesn't expire
    await ct.pop(test_packet_type + 1)

    assert await ct.wait_for_expired_command() == expected_command
