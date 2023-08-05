import websockets
import asyncio
import lib_db
import sqlite3

conn = sqlite3.connect("/root/data/data.db")

internet = False

value = None

def check_connection():
    async def ping():
        try:
            async with websockets.connect(uri='wss://ocpp.staging.lynkwell.com/EVM000001', timeout=1) as ws:
                await ws.send('ping')
                pong = await ws.recv()
        except Exception as e:
            global value
            value = e
    asyncio.run(ping())

while not internet:
    check_connection()
    if (value != None):
        if (value.errno != -3):
            lib_db.update('status', "internet_connected", 1, conn)
            internet = True