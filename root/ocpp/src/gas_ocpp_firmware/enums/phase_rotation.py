from enum import Enum


class PhaseRotation(str, Enum):
    not_applicable = "NotApplicable"
    unknown = "Unknown"
    rst = "RST"
    rts = "RTS"
    srt = "SRT"
    str = "STR"
    trs = "TRS"
    tsr = "TSR"
