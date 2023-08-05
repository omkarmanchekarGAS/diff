import sys
sys.path.insert(0, '/root')
import dash_network as dn
import colander
from utils.schema import *
import os
def validate(setting,data):
    if setting == 'device.general':
        schema = DeviceGeneralSchema()
    elif setting == 'device.appearence':
        schema = DeviceAppearence()
    elif setting == 'device.price':
        schema = DevicePrice()
    elif setting == 'ocpp.service':
        schema = OCPPServiceSchema()
    elif setting == 'ocpp.firmware':
        schema = OCPPFirmwareSchema()
    elif setting == 'ocpp.diagnostic':
        schema  = OCPPDiagnosticSchema()
    elif setting == 'ocpp.meter':
        schema = OCPPMeterSchema()
    elif setting == 'ocpp.session':
        schema  = OCPPSessionSchema()
    elif setting == 'ocpp.charge':
        schema  = OCPPChargingSchema()
    elif setting == 'communication.general':
        schema  = CommunicationGeneral()
    elif setting == 'communication.wifi':
        schema  = CommunicationWifi()
    elif setting == 'communication.cellular':
        schema  = CommunicationCellular()
    try:
        validated_data = schema.deserialize(data)
    except colander.Invalid as e:
        print(e)
        error_message = e.asdict()
        error_message['error']=True
        print("Error message is",error_message)
        return error_message
    if setting == 'communication.wifi':
        val = dn.update_wifi(validated_data['ssid'],validated_data['wifi_password'],validated_data['wifi_security_proto'])
        if(not val):
            error_message = {'wifi': 'cannot connect to wifi', 'error': True}
            return error_message
    if setting == 'communication.general':
        print("dashboard wants to restart wifi_config")
        dn.restart_wifi()
    return validated_data
