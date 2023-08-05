# Handles ocpp actions that are initiated by the charge point


import asyncio
from typing import List, Dict, Any, Union
from gas_ocpp_firmware.controllers.configuration_controller import (
    ConfigurationController,
)
from gas_ocpp_firmware.controllers.stpm_controller import StpmController
from ocpp.v16 import call, call_result
from ocpp.charge_point import remove_nones
from ocpp.v16 import ChargePoint as cp
from ocpp.v16.enums import (
    AuthorizationStatus,
    RegistrationStatus,
    Action,
    RemoteStartStopStatus,
    TriggerMessageStatus,
    FirmwareStatus,
    Reason,
    ResetType,
    AvailabilityType,
    AvailabilityStatus,
    ResetStatus,
    MessageTrigger,
    ReadingContext,
    ValueFormat,
    Measurand,
    Location,
    UnitOfMeasure,
    ChargePointErrorCode,
    ChargePointStatus
)
from ocpp.v16.datatypes import MeterValue, SampledValue
from ocpp.routing import on, after
from gas_ocpp_firmware.datatypes import (
    BootNotificationResponse,
    AuthorizeResponse,
    StartTransactionResponse,
)
from gas_ocpp_firmware.controllers.cp_interface import CPInterface
from gas_ocpp_firmware.controllers.hardware_json import Hardware_JSON
from datetime import datetime
from dataclasses import asdict
import os
import sys
sys.path.insert(0, '/root')
import lib_db
import sqlite3
import output_config

# TODO: handle errors for responses from central system
# see 3.7.1 for transaction-related messages

conn = sqlite3.connect("/root/data/data.db")

class ChargePointController(cp):
    instance = None
    model: str = lib_db.read_db("system_status", "model", conn)
    vendor: str = lib_db.read_db("system_status", "vendor", conn)
    registration_status: Union[RegistrationStatus, None]
    interval_time: int = lib_db.read_db("config", "heartbeat_interval", conn)
    interval_task: Union[asyncio.Task, None]
    updater_task: Union[asyncio.Task, None]
    current_transaction: Union[int, None]
    current_id_tag: Union[str, None]  # id_tag that started the current_transaction
    meter_value_sample_interval_time: int = 10
    meter_values_sample_task: Union[asyncio.Task, None]
    configuration_controller: ConfigurationController
    availability: AvailabilityType
    online_mode: int
    free_mode: int
    offline_mode_configured: int
    last_state: int

    @staticmethod
    def get_instance(evse_id: str, ws, configuration_controller: ConfigurationController):
        if not ChargePointController.instance:
            ChargePointController.instance = ChargePointController(evse_id, ws, configuration_controller)
        return ChargePointController.instance

    def __init__(
        self,
        evse_id: str,
        ws,
        configuration_controller: ConfigurationController,
    ):
        if ChargePointController.instance:
            raise Exception("ChargePointController is a singleton. Don't invoke the constructor directly.")
        super().__init__(evse_id, ws)
        self.configuration_controller = configuration_controller
        self.registration_status = None
        self.interval_task = None
        self.updater_task = None
        self.current_transaction = None
        self.current_id_tag = None
        self.meter_values_sample_task = None
        self.online_mode = 0
        self.free_mode = 0
        self.offline_mode_configured = 0
        self.stpm = StpmController()
        self.last_state = 0

    def now_timestamp(self):
        timestamp = datetime.utcnow().isoformat()
        return timestamp[:-3] + "Z"

    def get_meter_values(self):
        meter_values = self.stpm.get_meter_values()

        timestamp = self.now_timestamp()

        return MeterValue(
            timestamp=timestamp,
            sampled_value=[
                SampledValue(
                    value=str(meter_values[0]),
                    context=ReadingContext.sample_periodic,
                    format=ValueFormat.raw,
                    measurand=Measurand.current_offered,
                    location=Location.outlet,
                    unit=UnitOfMeasure.a,
                ),
                SampledValue(
                    value=str(meter_values[1]),
                    context=ReadingContext.sample_periodic,
                    format=ValueFormat.raw,
                    measurand=Measurand.voltage,
                    location=Location.outlet,
                    unit=UnitOfMeasure.v,
                ),
                SampledValue(
                    value=str(meter_values[2]),
                    context=ReadingContext.sample_periodic,
                    format=ValueFormat.raw,
                    measurand=Measurand.energy_active_import_register,
                    location=Location.outlet,
                    unit=UnitOfMeasure.wh,
                ),
                SampledValue(
                    value=str(meter_values[3]),
                    context=ReadingContext.sample_periodic,
                    format=ValueFormat.raw,
                    measurand=Measurand.power_offered,
                    location=Location.outlet,
                    unit=UnitOfMeasure.w,
                )
            ],
        )

    # ensure we take appropraite steps for transactions if we just rebooted
    async def check_reboot(self):
        await asyncio.sleep(1)
        # update local transaction_id and tag
        self.current_transaction = int(lib_db.read_db("current_transaction", "trans_id", conn))
        if self.current_transaction == -1:
            self.current_transaction = None

        # eventually this will all change when stpm_controller becomes an object for charge_point to hold
        # only worry about restarting transactions if we're in an online mode (meaning we care about transactions)
        if self.online_mode == 1:
            auth = lib_db.read_db("status", "charge_authorized", conn)
            if lib_db.read_db("config", "resume_charge_after_reboot", conn):
                if auth:
                    print("charge was previously authorized and we need to resume")

                    # stop the old transaction with saved meter values
                    await self.send_stop_transaction(int(lib_db.read_db("current_transaction", "trans_id", conn)))

                    # dont automatically start new transaction if we're in free mode
                    # so that we can do resume charge after reboot without remote start in paid mode
                    if self.free_mode != 1 and (lib_db.read_db("status", "pilot_state", conn) == 2 or lib_db.read_db("status", "pilot_state", conn) == 3):
                        await self.send_start_transaction(1, lib_db.read_db("current_transaction", "id_tag", conn))
                
                else:
                    print("charge not previously authorized")

            else:
                if auth:
                    print("charge was authorized but we do not resume charge after reboot")

                    # stop the old transaction with saved meter values
                    await self.send_stop_transaction(int(lib_db.read_db("current_transaction", "trans_id", conn)))

                else:

                    print("charge not authorized and we don't resume :(")




    async def interval(self) -> None:  # pragma: no cover
        while True:
            await asyncio.sleep(self.interval_time)
            await self.send_interval_message()

    async def send_interval_message(self) -> None:
        if (
            self.registration_status is not None
            and self.registration_status == RegistrationStatus.accepted
        ):
            await self.send_heartbeat()
        else:
            await self.send_boot_notification()
    
    async def update(self) -> None:
        while True:
            await self.updater()
            await asyncio.sleep(15)

    async def updater(self) -> None:
        self.interval_time = lib_db.read_db("config", "heartbeat_interval", conn)
        self.online_mode = lib_db.read_db("config", "online_mode", conn)
        self.free_mode = lib_db.read_db("config", "free_mode", conn)

    async def send_meter_value_sample_interval(self):
        while True:
            await asyncio.sleep(lib_db.read_db('config', 'mv_s_interval', conn))

            meter_value_measurement = self.get_meter_values()

            await self.send_meter_value_message(
                1, [meter_value_measurement], self.current_transaction
            )

    async def status_read(self) -> None:
        while True:
            await self.status_reader()
            await asyncio.sleep(5)

    async def status_reader(self) -> None:
        pilot_state = lib_db.read_db("status", "pilot_state", conn)
        if(pilot_state != self.last_state):
            if self.online_mode == 1:
                if self.free_mode == 0:
                    print("Online and paid!")
                    if (not self.current_transaction is None) and (pilot_state != 3):
                        # stop transaction automatically on disconnect when online and paid
                        await self.send_stop_transaction(self.current_transaction)
                else:
                    print("Online and free!")
                    print(self.current_transaction)
                    if self.current_transaction is None and (pilot_state == 2 or pilot_state == 3):
                        # start free transaction (TAG MAY NEED TO CHANGE)
                        # this ID tag only works on PRODUCTION
                        await self.send_start_transaction(connector_id = 1, id_tag="ChargePortFreeUse", reservation_id=None)
                    elif (not self.current_transaction is None) and (pilot_state != 3):
                        # stop free transaction
                        await self.send_stop_transaction(self.current_transaction)
            else:
                if self.free_mode == 0:
                    # not a thing that can happen
                    print("We're in a mode that shouldn't exist")
                else:
                    print("Offline and free!")
                    if self.offline_mode_configured == 0:
                        lib_db.update("status", "charge_authorized", 1, conn)
                        output_config.update_output_current(32)
                        self.offline_mode_configured = 1
            
            await self.send_status_notification_message()
        self.last_state = pilot_state


    async def send_boot_notification(self) -> Union[BootNotificationResponse, None]:
        request = call.BootNotificationPayload(
            charge_point_model=self.model, charge_point_vendor=self.vendor
        )

        response: Union[BootNotificationResponse, None] = await self.call(request)

        if response is None:
            return

        self.registration_status = response.status
        self.interval_time = response.interval
        lib_db.update("config", "heartbeat_interval", response.interval, conn)

        # TODO: do something with response.current_time
        # set the interval for sending a heartbeat or boot notification
        if self.interval_task is None:
            loop = asyncio.get_running_loop()
            self.interval_task = await loop.create_task(self.interval())

        return response

    async def send_heartbeat(self) -> None:
        request = call.HeartbeatPayload()

        # TODO: use response.current_time to sync clocks
        # response: HeartbeatResponse = await self.call(request)

        await self.call(request)

    async def get_diagnostics(self) -> None:
        request = call.GetDiagnosticsPayload()
        await self.call(request)

    async def reserve_now(self) -> None:
        request  = call.ReserveNowPayload()
        await self.call(request)
    
    async def send_local_list(self) -> None:
        request  = call.SendLocalListPayload()
        await self.call(request)
    
    
    async def send_firmware_status_notification(self) -> None:
        # TODO: actually check status of firmware download
        # what does the process of a firmware download even look like?

        # charge point shall only send the status Idle after receipt of a TriggerMessage
        # for a Firmware Status Notification, when it is not busy
        # downloading/installing firmware
        request = call.FirmwareStatusNotificationPayload(status=FirmwareStatus.downloading)

        await self.call(request)

    async def send_authorize(self, id_tag: str) -> Union[AuthorizeResponse, None]:
        request = call.AuthorizePayload(id_tag=id_tag)

        response: Union[AuthorizeResponse, None] = await self.call(request)

        return response

    async def send_start_transaction(
        self,
        connector_id: int,
        id_tag: str,
        reservation_id: Union[int, None] = None,
    ) -> None:
        
        if self.free_mode == 0:
            authorize_response = await self.send_authorize(id_tag)

            if (
                authorize_response is None
                or authorize_response.id_tag_info["status"] != AuthorizationStatus.accepted
            ):
                return

        # authorize charge
        lib_db.update("status", "charge_authorized", 1, conn)
        output_config.update_output_current(32)
        
        timestamp = self.now_timestamp()

        transaction_begin_measurement = self.get_meter_values()

        meter_start = int(float(transaction_begin_measurement.sampled_value[2].value))

        request = call.StartTransactionPayload(
            connector_id, id_tag, meter_start, timestamp
        )

        response: Union[StartTransactionResponse, None] = await self.call(request)

        if response is None:
            return

        # update db transaction data
        lib_db.update("current_transaction", "id_tag", id_tag, conn)
        lib_db.update("current_transaction", "trans_id", response.transaction_id, conn)
        self.current_id_tag = id_tag
        self.current_transaction = response.transaction_id

        loop = asyncio.get_running_loop()
        self.meter_values_sample_task = loop.create_task(
            self.send_meter_value_sample_interval()
        )

    def remove_meter_values_nones(
        self, meter_values: List[MeterValue]
    ) -> List[Dict[str, Any]]:
        """
        Removes any nones from the transaction_data field for
        send_stop_transaction
        """
        transaction_data_without_nones = []

        for meter_value in meter_values:
            if meter_value is None:
                continue
            sampled_values = []
            for sampled_value in meter_value.sampled_value:
                sampled_values.append(remove_nones(asdict(sampled_value)))

            meter_value_dict = asdict(meter_value)
            meter_value_dict["sampled_value"] = sampled_values
            transaction_data_without_nones.append(meter_value_dict)

        return transaction_data_without_nones

    async def send_stop_transaction(self, transaction_id: int):
        
        # clear charge authorization
        lib_db.update("status", "charge_authorized", 0, conn)
        lib_db.update("current_transaction", "trans_id", "-1", conn)
        output_config.update_output_current(32)

        # decide reason for stop
        match(lib_db.read_db("status", "pilot_state", conn)):
            case 1:
                reason = Reason.local
            case _:
                reason = Reason.remote
        
        timestamp = self.now_timestamp()
    
        transaction_end_measurement = self.get_meter_values()
        meter_stop = int(float(transaction_end_measurement.sampled_value[2].value))
        

        self.current_transaction = None

        if self.meter_values_sample_task is not None:
            print('Trying to cancel meter values task!')
            self.meter_values_sample_task.cancel()

        self.meter_values_sample_task = None

        request = call.StopTransactionPayload(
            meter_stop=meter_stop,
            timestamp=timestamp,
            transaction_id=transaction_id,
            reason=reason,
            id_tag=self.current_id_tag,
        )

        response = await self.call(request)

        return response

    async def send_meter_value_message(
        self,
        connector_id: int,
        meter_values: List[MeterValue],
        transaction_id: Union[int, None] = None,
    ):
        meter_values_without_nones = self.remove_meter_values_nones(meter_values)

        request = call.MeterValuesPayload(
            connector_id=connector_id,
            meter_value=meter_values_without_nones,
            transaction_id=transaction_id,
        )

        response = await self.call(request)

        return response
    
    async def send_status_notification_message(self):

        match(lib_db.read_db("status", "fault_code", conn)):
            case 1:
                error_code = ChargePointErrorCode.no_error
                vendor_error_code = "1"
                info = ""
            case 2:
                error_code = ChargePointErrorCode.ground_failure
                vendor_error_code = "2"
                info = "Ground Fault"
            case 4:
                error_code = ChargePointErrorCode.other_error
                vendor_error_code = "4"
                info = "Input AC Fault"
            case 5:
                error_code = ChargePointErrorCode.ground_failure
                vendor_error_code = "5"
                info = "Missing Ground"
            case 7:
                error_code = ChargePointErrorCode.power_switch_failure
                vendor_error_code = "7"
                info = "Stuck Relays"
            case 9:
                error_code = ChargePointErrorCode.ev_communication_error
                vendor_error_code = "9"
                info = "EV Sending bad pilot signal"
            case 10:
                error_code = ChargePointErrorCode.other_error
                vendor_error_code = "10"
                info = "Trying to charge with Ventilation"
            case 11:
                error_code = ChargePointErrorCode.internal_error
                vendor_error_code = "11"
                info = "GFI Self Test Failure"
            case 12:
                error_code = ChargePointErrorCode.internal_error
                vendor_error_code = "12"
                info = "Internal Communication Error"
            case _:
                error_code = ChargePointErrorCode.internal_error
                vendor_error_code = ""
                info = "Unknown Error"

        authorization = lib_db.read_db("status", "charge_authorized", conn)
        match(lib_db.read_db("status", "pilot_state", conn)):
            case 1:
                status = ChargePointStatus.available
            case 2:
                if (authorization == 1):
                    status = ChargePointStatus.suspended_ev
                else:
                    status = ChargePointStatus.suspended_evse
            case 3:
                if (authorization == 1):
                    status = ChargePointStatus.charging
                else:
                    # shouldnt be possible
                    status = ChargePointStatus.faulted
                    error_code = ChargePointErrorCode.other_error
            case _:
                status = ChargePointStatus.faulted


        request = call.StatusNotificationPayload(
            connector_id=1,
            error_code=error_code,
            status=status,
            timestamp=self.now_timestamp(),
            info = info,
            vendor_id = self.vendor,
            vendor_error_code = vendor_error_code,
        )
        await self.call(request)

    @on(Action.UpdateFirmware)
    async def on_update_firmware(
        self, location: str, retrieve_date: str, retries: Union[int, None] = None, retry_interval: Union[int, None] = None
    ) -> call_result.UpdateFirmwarePayload:
        
        # create persistent timer and start checker process (may have been dead after being started by procd)
        os.system(f"""echo "{retrieve_date}\n{location}" > /tmp/update_time""")

        os.system("python /root/upgrade_firmware.py &")

        return call_result.UpdateFirmwarePayload()

    # @after(Action.UpdateFirmware)
    # async def after_update_firmware(
    #     self, 
    # )

    @on(Action.TriggerMessage)
    async def on_trigger_message(
        self, requested_message: str, connector_id: Union[int, None] = None
    ) -> call_result.TriggerMessagePayload:
        try:
            message_trigger = MessageTrigger(requested_message)
            if message_trigger == Action.DiagnosticsStatusNotification:
                return call_result.TriggerMessagePayload(
                    status=TriggerMessageStatus.not_implemented
                )
            elif message_trigger == Action.MeterValues:
                return call_result.TriggerMessagePayload(
                    status=TriggerMessageStatus.accepted
                )
            elif message_trigger == Action.Reset:
                return call_result.TriggerMessagePayload(
                    status=TriggerMessageStatus.accepted
                )
            elif message_trigger == Action.Heartbeat:
                return call_result.TriggerMessagePayload(
                    status=TriggerMessageStatus.accepted
                )
            elif message_trigger == Action.StatusNotification:
                return call_result.TriggerMessagePayload(
                    status=TriggerMessageStatus.accepted
                )
            elif message_trigger == Action.BootNotification:
                return call_result.TriggerMessagePayload(
                    status=TriggerMessageStatus.accepted
                )
            return call_result.TriggerMessagePayload(
                status=TriggerMessageStatus.rejected
            )
        except ValueError:
            return call_result.TriggerMessagePayload(
                status=TriggerMessageStatus.rejected
            )

    @after(Action.TriggerMessage)
    async def after_trigger_message(
        self, requested_message: str, connector_id: int = 0
    ) -> None:
        if requested_message == Action.Heartbeat:
            await self.send_heartbeat()
        elif requested_message == Action.BootNotification:
            await self.send_boot_notification()
        elif requested_message == Action.StatusNotification:
            await self.send_status_notification_message()
        elif requested_message == Action.MeterValues:

            meter_value_measurement = self.get_meter_values()

            await self.send_meter_value_message(
                1, [meter_value_measurement], self.current_transaction
            )
        elif requested_message == Action.Reset:
            return

    @on(Action.RemoteStartTransaction)
    async def on_remote_start_transaction(
        self, id_tag: str, connector_id: Union[int, None] = None, charging_profile=None
    ) -> call_result.RemoteStartTransactionPayload:
        # TODO handle charging profiles
        # TODO handle scenarios when the remote start transaction should be rejected
        if self.current_transaction != None:
            return call_result.RemoteStartTransactionPayload(RemoteStartStopStatus.rejected)
        return call_result.RemoteStartTransactionPayload(RemoteStartStopStatus.accepted)

    @after(Action.RemoteStartTransaction)
    async def after_remote_start_transaction(
        self, id_tag: str, connector_id: Union[int, None] = None, charging_profile=None
    ) -> None:
        if connector_id is None and self.current_transaction == None:
            # default to connector 1
            await self.send_start_transaction(1, id_tag)
            return
        if self.current_transaction == None:
            await self.send_start_transaction(connector_id, id_tag)

    @on(Action.RemoteStopTransaction)
    async def on_remote_stop_transcation(
        self, transaction_id: int
    ) -> call_result.RemoteStopTransactionPayload:
        if self.current_transaction != transaction_id:
            return call_result.RemoteStopTransactionPayload(
                RemoteStartStopStatus.rejected
            )

        return call_result.RemoteStopTransactionPayload(RemoteStartStopStatus.accepted)

    @after(Action.RemoteStopTransaction)
    async def after_remote_stop_transaction(self, transaction_id: int) -> None:
        if self.current_transaction != transaction_id:
            return

        await self.send_stop_transaction(transaction_id)

    @on(Action.ChangeConfiguration)
    async def on_change_configuration(
        self, key: str, value: str
    ) -> call_result.ChangeConfigurationPayload:
        return self.configuration_controller.change_configuration(key, value)

    @on(Action.GetConfiguration)
    async def on_get_configuration(
        self, key: List[str] = []
    ) -> call_result.GetConfigurationPayload:
        (
            configuration_key,
            unknown_key,
        ) = self.configuration_controller.get_configuration(key)

        return call_result.GetConfigurationPayload(
            configuration_key=configuration_key, unknown_key=unknown_key
        )

    @on(Action.Reset)
    async def on_reset(self, type: str) -> call_result.ResetPayload:
        try:
            ResetType(type)
            return call_result.ResetPayload(status=ResetStatus.accepted)
        except ValueError:
            return call_result.ResetPayload(status=ResetStatus.rejected)

    @after(Action.Reset)
    async def after_reset(self, type: str) -> None:
        lib_db.update("status", "charge_authorized", 1, conn)
        if type == ResetType.soft:
            # restart python program
            os.system("""ps | grep connect_to_central | grep -v grep | awk '{print $1}' | xargs kill; python /root/ocpp/src/connect_to_central_system.py 0""")
        elif type == ResetType.hard:
            # restart computer
            os.system("reboot")
            pass

