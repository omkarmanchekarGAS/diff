#!/usr/bin/env python


import asyncio
from ocpp.v16.enums import Measurand
import websockets
from gas_ocpp_firmware.enums import (
    PhaseRotation,
    SupportedFeatureProfile,
    ChargingRateUnit,
)
from gas_ocpp_firmware.controllers.charge_point import ChargePointController

from gas_ocpp_firmware.controllers.configuration_controller import (
    ConfigurationController,
)
from gas_ocpp_firmware.datatypes import Configuration
import logging
import sys
from time import sleep

sys.path.insert(0, '/root')
import lib_db
import sqlite3

conn = sqlite3.connect("/root/data/data.db")

logging.basicConfig(level=logging.INFO)

EVSE_ID = lib_db.read_db("config", "charge_point_id", conn)
WSS_URL = lib_db.read_db("config", "central_system_url", conn) + EVSE_ID

async def main():
    # weird typing issues with websockets package
    while True:
        try:
            async with websockets.connect(WSS_URL, subprotocols=["ocpp1.6"], ping_timeout = 60) as ws:  # type: ignore # noqa
                configuration_controller = ConfigurationController()
                cp = ChargePointController.get_instance(
                    EVSE_ID, ws, configuration_controller
                )

                await asyncio.gather(cp.start(), cp.send_boot_notification(), cp.update(), 
                cp.send_status_notification_message(), cp.status_read())
        except Exception as e:
            if lib_db.read_db("config", "free_mode", conn) == 1:
                lib_db.update("status", "charge_authorized", 1, conn)
            print(e)
            sleep(5)



if __name__ == "__main__":  # pragma: no cover
    asyncio.run(main())
        
    
