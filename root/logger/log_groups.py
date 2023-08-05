from enum import Enum

class LogPriority(str, Enum):
    NOTICE = "notice" # default
    INFO = "info"
    ERR = "err"
    DEBUG = "debug"
    WARN = "warn"
    EMERGENCY = "emerg"
    ALERT = "alert"

# We use this enum to show a list of pre-defined tags in the dashboard, however 
# filtering does not have to be dependent on this enum since we allow a way to
# perform regex filtering. For each additional log-group, add new enums here to
# make sure the dashboard is consistently showing the user-defined log groups
class UserDefinedLogGroups(str, Enum):
    ALL = "ALL"
    EEPROM_SCRIPT = "EEPROM_SCRIPT"
    ENABLE_STPM = "ENABLE_STPM"
    FLASK_DASHBOARD = "FLASK_DASHBOARD"
    I2C_DRIVER = "I2C_DRIVER"
    INIT_INTERNET_CHECK = "INIT_INTERNET_CHECK"
    LIB_DB = "LIB_DB"
    LIB_I2C = "LIB_I2C"
    LIB_RTC = "LIB_RTC"
    LLM = "LLM"
    LLM_GROUP = "LLM_GROUP"
    RATE_DRIVER = "RATE_DRIVER"
    UPDATE_USER_PASSWORD = "UPDATE_USER_PASSWORD"
    WIFI_CONFIG = "WIFI_CONFIG"