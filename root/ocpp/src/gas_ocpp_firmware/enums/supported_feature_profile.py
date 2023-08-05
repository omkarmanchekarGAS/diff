from enum import Enum


class SupportedFeatureProfile(str, Enum):
    core = "Core"
    firmware_management = "FirmwareManagement"
    local_auth_list_management = "LocalAuthListManagement"
    reservation = "Reservation"
    smart_charging = "SmartCharging"
    remote_trigger = "RemoteTrigger"
