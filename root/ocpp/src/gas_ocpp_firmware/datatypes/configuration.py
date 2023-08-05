from dataclasses import asdict, dataclass
from typing import Dict, List
from ocpp.v16.enums import Measurand
from gas_ocpp_firmware.enums import (
    PhaseRotation,
    SupportedFeatureProfile,
    ChargingRateUnit,
)


@dataclass
class Configuration:
    authorize_remote_tx_requests: bool
    clock_aligned_data_interval: int  # in seconds
    connection_time_out: int  # in seconds
    connector_phase_rotation: Dict[
        int, PhaseRotation
    ]  # key is the connector, value is the phase rotation for that connector
    get_configuration_max_keys: int
    heartbeat_interval: int
    local_authorize_offline: bool
    local_pre_authorize: bool
    meter_values_aligned_data: List[Measurand]
    meter_values_aligned_data_max_length: int
    meter_values_sampled_data: List[Measurand]
    meter_values_sampled_data_max_length: int
    meter_value_sample_interval: int  # in seconds
    number_of_connectors: int
    reset_retries: int
    stop_transaction_on_e_v_side_disconnect: bool
    stop_transaction_on_invalid_id: bool
    stop_txn_aligned_data: List[Measurand]
    stop_txn_aligned_data_max_length: int
    stop_txn_sampled_data: List[Measurand]
    stop_txn_sampled_data_max_length: int
    supported_feature_profiles: List[SupportedFeatureProfile]
    supported_feature_profiles_max_length: int
    transaction_message_attempts: int
    transaction_message_retry_interval: int
    unlock_connector_on_e_v_side_disconnect: bool
    local_auth_list_enabled: bool
    local_auth_list_max_length: int
    send_local_list_max_length: int
    charging_profile_max_stack_level: int
    charging_schedule_allowed_charging_rate_unit: List[ChargingRateUnit]
    charging_schedule_max_periods: int
    max_charging_profiles_installed: int
    web_socket_ping_interval: int #TODO: Let Ethan know that that comma syntactical error was really funny
    color: str

    read_only_values = {
        "GetConfigurationMaxKeys",
        "MeterValuesAlignedDataMaxLength",
        "MeterValuesSampledDataMaxLength",
        "NumberOfConnectors",
        "StopTxnAlignedDataMaxLength",
        "StopTxnSampledDataMaxLength",
        "SupportedFeatureProfilesMaxLength",
        "LocalAuthListMaxLength",
        "SendLocalListMaxLength",
        "ChargeProfileMaxStackLevel",
        "ChargingScheduleAllowedChargingRateUnit",
        "ChargingScheduleMaxPeriods",
        "MaxChargingProfilesInstalled",
    }

    def snake_case_to_camel_case(self, s: str) -> str:
        return "".join(word.title() for word in s.split("_"))

    def to_ocpp_format(self):
        config_dict = asdict(self)

        ocpp_dict = {}

        for k, v in config_dict.items():
            if type(v) is int:
                ocpp_dict[self.snake_case_to_camel_case(k)] = str(v)
            elif type(v) is bool:
                ocpp_dict[self.snake_case_to_camel_case(k)] = str(v).lower()
            elif type(v) is list:
                ocpp_dict[self.snake_case_to_camel_case(k)] = ", ".join(v)
            elif k == "connector_phase_rotation":
                connector_phase_rotation_list = []
                for (
                    connector_id,
                    phase_rotation,
                ) in self.connector_phase_rotation.items():
                    connector_phase_rotation_list.append(
                        f"{connector_id}.{phase_rotation}"
                    )

                ocpp_dict[self.snake_case_to_camel_case(k)] = ", ".join(
                    connector_phase_rotation_list
                )

        return ocpp_dict
