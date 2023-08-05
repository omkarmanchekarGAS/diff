#!/usr/bin/env python3

import argparse
import asyncio

import websockets

parser = argparse.ArgumentParser(description="Ping a websocket endpoint")
parser.add_argument(
    "-w",
    dest="url",
    help="ws to ping, use -w flag followed by ws pattern [wss://host/ws/endpoint] to ping",
)
parser.add_argument(
    "-d",
    dest="delay",
    type=int,
    help="delay in seconds to 2nd ping, use -d flag followed by int",
    default=1,
)
args = parser.parse_args()


async def ping(url, delay):
    try:
        async with websockets.connect(uri=url) as ws:
            await ws.send('ping')
            pong = await ws.recv()
            print(f"Successfully connected to {url}, response to ping: {pong}")

            await asyncio.sleep(delay)
            await ws.send('ping')
            pong = await ws.recv()
            print(f"Maintained connection to {url}, response to ping: {pong}")
            print("Success!")

    except (RuntimeError, websockets.exceptions.ConnectionClosed) as e:
        print(e.args)
    except (websockets.exceptions.InvalidStatusCode, ConnectionResetError, websockets.exceptions.InvalidMessage) as e:
        print('Connection to wss unsuccessful:', e)



if __name__ == "__main__":
    asyncio.run(ping(args.url, args.delay))
