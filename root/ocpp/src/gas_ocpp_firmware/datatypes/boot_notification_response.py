from dataclasses import dataclass
from ocpp.v16.enums import RegistrationStatus


@dataclass
class BootNotificationResponse:
    interval: int
    status: RegistrationStatus
    current_time: str  # date string
