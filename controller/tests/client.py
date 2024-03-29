# -*- coding: utf-8 -*-
import asyncio
import json

import aioconsole
from websockets import connect


# TODO find a way to reuse this in unit tests?
def _get_command(command):
    comm = {"command": command}

    match command:
        # TEST COMMANDS
        case "test":
            comm |= {"msg": "test_msg"}
        case "err" | "ws_err":
            pass
        # REAL COMMANDS
        case "shutdown":
            pass
        case "login":
            comm |= {
                "customer_id": "test_customer_id",
                "username": "test_username",
                "password": "test_password",
            }
        case "set_latest_software_version":
            comm |= {"version": "6.7.9"}
        case "set_firmware_update_confirmation":
            comm |= {"update_accepted": False}
        case "set_stim_protocols":
            # TODO
            comm |= {"stim_info": {"protocols": {}, "protocol_assignments": {}}}
        case "start_stim_checks":
            comm |= {"well_indices": [0, 10, 20]}
        case "set_stim_status":
            comm |= {"running": True}
        case _:
            print("invalid_command")  # allow-print
            return None

    return comm


async def client(uri):
    async with connect(uri) as websocket:
        await asyncio.wait(
            {asyncio.create_task(producer(websocket)), asyncio.create_task(consumer(websocket))},
            return_when=asyncio.FIRST_COMPLETED,
        )
    print("EXIT")  # allow-print


async def producer(websocket):
    while websocket.open:
        command = await aioconsole.ainput("send: ")
        if command_details := _get_command(command):
            await websocket.send(json.dumps(command_details))


async def consumer(websocket):
    while websocket.open:
        res = await websocket.recv()
        print(f"response: {res}")  # allow-print


asyncio.run(client("ws://localhost:4565"))
