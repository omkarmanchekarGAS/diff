from enum import Enum


class ChargingRateUnit(str, Enum):
    current = "Current"
    power = "Power"
