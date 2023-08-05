from typing import List, Dict, Tuple
from ocpp.v16.datatypes import KeyValue
# from gas_ocpp_firmware.datatypes import Configuration
# no longer need this^ class because config is stored in the db
from gas_ocpp_firmware.enums import PhaseRotation
from ocpp.v16.enums import Measurand, ConfigurationStatus
from ocpp.v16 import call_result
import sys
sys.path.insert(0, '/root')
import lib_db
import sqlite3


class ConfigurationController:
    """
    Handles changing and getting of configuration settings
    """
    def __init__(self):
        self.conn = sqlite3.connect("/root/data/data.db")

    # keys are OCPP config keys, values are corresponding database keys
    key_translator = {
        "ClockAlignedDataInterval": "clock_aligned_data_interval",
        "ConnectionTimeOut": "connection_timeout",
        "ConnectorPhaseRotation": "conn_phase_rotat",
        "HeartbeatInterval": "heartbeat_interval",
        "LocalAuthorizeOffline": "local_auth_offline",
        "LocalPreAuthorize": "local_pre_auth",
        "MeterValuesAlignedData": "mv_al_data",
        "MeterValuesSampledData": "mv_s_data",
        "MeterValuesSampleinterval": "mv_s_interval",
        "ResetRetries": "reset_retries",
        "StopTransactionOnEVSideDisconnect": "stop_trans_ev_side_disc",
        "StopTransactionOnInvalidId": "stop_trans_on_invalid_id",
        "StopTxnAlignedData": "stop_trans_al_data",
        "StopTxnSampledData": "stop_trans_s_data",
        "TransactionMessageAttempts": "trans_num_msg_attempts",
        "TransactionMessageRetryInterval": "trans_msg_retry_interval",
        "UnlockConnectorOnEVSideDisconnect": "unlock_conn_EV_disc",
        "WebSocketPingInterval": "ping_interval",
        "GetConfigurationMaxKeys": "config_max_keys",
        "LightIntensity": "led_brightness",
        "SupportedFeatureProfiles": "feature_profiles",
        "CentralSystemURL": "central_system_url"
    }

    key_translator_ss = {
        "ChargePointVendor": "vendor",
        "ChargePointModel": "model",
        "ChargePointSerialNumber": "serial_num",
        "FirmwareVersion": "firmware_version",
        "ProductionDate": "production_date"
    }

    def parse_boolean(self, value: str) -> bool:
        if value == "true" or value == "false":
            return value == "true"
        else:
            raise ValueError("String must be true or false")

    def change_configuration(
        self, key: str, value: str
    ) -> call_result.ChangeConfigurationPayload:
        try:
            if key == "AuthorizeRemoteTxRequests":
                # must remain on for EVM-1
                return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "ClockAlignedDataInterval":
                if not lib_db.update('config', 'clock_aligned_data_interval', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "ConnectionTimeOut":
                if not lib_db.update('config', 'connection_timeout', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "ConnectorPhaseRotation":
                return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "HeartbeatInterval":
                if not lib_db.update('config', 'heartbeat_interval', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "LocalAuthorizeOffline":
                if not lib_db.update('config', 'local_auth_offline', self.parse_boolean(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "LocalPreAuthorize":
                if not lib_db.update('config', 'local_pre_auth', self.parse_boolean(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "MeterValuesAlignedData":
                if not lib_db.update('config', 'mv_al_data', value.strip(), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "MeterValuesSampledData":
                if not lib_db.update('config', 'mv_s_data', value.strip(), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "MeterValueSampleInterval":
                if not lib_db.update('config', 'mv_s_interval', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "ResetRetries":
                if not lib_db.update('config', 'reset_retries', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "StopTransactionOnEVSideDisconnect":
                if not lib_db.update('config', 'stop_trans_ev_side_disc', self.parse_boolean(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "StopTransactionOnInvalidId":
                if not lib_db.update('config', 'stop_trans_on_invalid_id', self.parse_boolean(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "StopTxnAlignedData":
                if not lib_db.update('config', 'stop_trans_al_data', value.strip(), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "StopTxnSampledData":
                if not lib_db.update('config', 'stop_trans_s_data', value.strip(), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "TransactionMessageAttempts":
                if not lib_db.update('config', 'trans_num_msg_attempts', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "TransactionMessageRetryInterval":
                if not lib_db.update('config', 'trans_msg_retry_interval', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "UnlockConnectorOnEVSideDisconnect":
                if not lib_db.update('config', 'unlock_conn_EV_disc', self.parse_boolean(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "WebSocketPingInterval":
                if not lib_db.update('config', 'ping_interval', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "LocalAuthListEnabled":
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "GetConfigurationMaxKeys":
                if not lib_db.update('config', 'config_max_keys', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "LightIntensity":
                if not lib_db.update('config', 'led_brightness', int(value), self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "SupportedFeatureProfiles":
                return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            elif key == "CentralSystemURL":
                if not lib_db.update('config', 'central_system_url', value, self.conn):
                    return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)
            else:
                return call_result.ChangeConfigurationPayload(
                    ConfigurationStatus.rejected
                )
            return call_result.ChangeConfigurationPayload(ConfigurationStatus.accepted)
        except ValueError:
            return call_result.ChangeConfigurationPayload(ConfigurationStatus.rejected)

    def get_configuration(self, req_keys: List[str]) -> Tuple[List[KeyValue], List[str]]:
        configuration_key: List[KeyValue] = []
        unknown_key: List[str] = []
        for key in req_keys:
            if key in self.key_translator.keys():
                configuration_key.append(KeyValue(
                    key=key,
                    readonly=False,
                    value=str(lib_db.read_db("config", self.key_translator[key], self.conn)),
                ))
            elif key in self.key_translator_ss.keys():
                configuration_key.append(KeyValue(
                    key=key,
                    readonly=True,
                    value=str(lib_db.read_db("system_status", self.key_translator_ss[key], self.conn)),
                ))
            else:
                unknown_key.append(key)

        if len(req_keys) == 0:
            for key in self.key_translator.keys():
                configuration_key.append(KeyValue(
                    key=key,
                    readonly=False,
                    value=str(lib_db.read_db("config", self.key_translator[key], self.conn)),
                ))
            for key in self.key_translator_ss.keys():
                configuration_key.append(KeyValue(
                    key=key,
                    readonly=True,
                    value=str(lib_db.read_db("system_status", self.key_translator_ss[key], self.conn)),
                ))

        return configuration_key, unknown_key
