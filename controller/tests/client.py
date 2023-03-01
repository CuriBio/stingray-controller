# -*- coding: utf-8 -*-
import asyncio
import json

import aioconsole
from websockets import connect


async def hello(uri):
    async with connect(uri) as websocket:
        while websocket.open:
            msg = await aioconsole.ainput("send: ")

            command, *msg = msg.split(",")

            formatted_msg = {"command": command}
            if command in ("test", "monitor_test"):
                formatted_msg["msg"] = msg[0]

            await websocket.send(json.dumps(formatted_msg))

            res = await websocket.recv()
            print(f"response: {res}")  # allow-print

        print("EXIT")  # allow-print


asyncio.run(hello("ws://localhost:4567"))
