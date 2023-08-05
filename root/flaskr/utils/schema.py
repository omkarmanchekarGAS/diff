import colander

def validate_input_words(node, value):
    words = value.split(',')
    if len(words) > 10:
        raise colander.Invalid(node, 'Max profile supported exceeds 10. Provided {} profiles'.format(len(words)))
        

class DeviceGeneralSchema(colander.MappingSchema):
    firmware_max_amps = colander.SchemaNode(
        colander.Integer(), 
        validator=colander.Range(min=0, max=1000000)
    )
    instant_power_delay = colander.SchemaNode(
        colander.Integer(), 
        missing=0,
        validator=colander.Range(min=0, max=900)
    )
    resume_charge_after_reboot = colander.SchemaNode(
        colander.Boolean(),
        missing=0
    )
    ventilation_available = colander.SchemaNode(
        colander.Boolean()
    )
    led_brightness = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=100)
    )

class DeviceAppearence(colander.MappingSchema):
    logo_color = colander.SchemaNode(
        colander.String(),
        validator=colander.All(colander.Length(min=7, max=7),colander.Regex("^#([A-Fa-f0-9]{6})$")),
        preparer=lambda s: s.upper()
    )
    welcome_msg1 = colander.SchemaNode(
        colander.String(),
        missing=' ',
        validator=colander.All(colander.Length(max=21), colander.Regex("^[\x20-\x7E]*$"))
    )
    welcome_msg2 = colander.SchemaNode(
        colander.String(),
        missing=' ',
        validator=colander.All(colander.Length(max=21), colander.Regex("^[\x20-\x7E]*$"))
    )

class DevicePrice(colander.MappingSchema):
    usd_per_kWh = colander.SchemaNode(
        colander.String(),
        validator=colander.Regex("^(\$)*[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?$"),
        missing=0.00
    )
    usd_per_parked_mins = colander.SchemaNode(
        colander.String(),
        validator=colander.Regex("^(\$)*[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?$"),
        missing=0.00
    )
    usd_activation_fee = colander.SchemaNode(
        colander.String(),
        validator=colander.Regex("^(\$)*[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?$"),
        missing=0.00
    )
    online_mode = colander.SchemaNode(
        colander.Boolean(),
        missing=False
    )
    free_mode = colander.SchemaNode(
        colander.Boolean(),
        missing=False
    )

class OCPPServiceSchema(colander.MappingSchema):
    charge_point_id = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(max=25)
    )
    central_system_url = colander.SchemaNode(
        colander.String(),
        #validator = colander.Length(max=255)
        validator=colander.All(colander.Length(max=255), colander.Regex("^(wss?://)([0-9a-zA-Z]+)((?:.[0-9a-zA-Z]+){3})/$")),
    )
    # boot_notif_interval = colander.SchemaNode(
    #     colander.Integer(),
    #     validator=colander.Range(min=0, max=86400)
    # )
    # boot_notif_retries = colander.SchemaNode(
    #     colander.Integer(),
    #     validator=colander.Range(min=0, max=10),
    # )
    # pdu_timeout = colander.SchemaNode(
    #     colander.Integer(),
    #     validator=colander.Range(min=0, max=900),
    # )
    # connection_timeout = colander.SchemaNode(
    #     colander.Integer(),
    #     validator=colander.Range(min=0, max=900),
    # )
    # min_status_duration = colander.SchemaNode(
    #     colander.Integer(),
    #     validator=colander.Range(min=0, max=60),
    # )
    # ping_interval = colander.SchemaNode(
    #     colander.Integer(),
    #     validator=colander.Range(min=0, max=86400),
    # )
    # reset_retries = colander.SchemaNode(
    #     colander.Integer(),
    #     validator=colander.Range(min=0, max=10),
    # )
    children_list = colander.SchemaNode(
        colander.String(),
        missing = '',
        validator=colander.All(colander.Length(max=255),colander.Regex('^[0-9a-zA-Z]+(,[0-9a-zA-Z]+)*$')),
    )


class OCPPFirmwareSchema(colander.MappingSchema):
    dwnld_fw_interval = colander.SchemaNode(
        colander.Integer(),
        missing=1,
        validator=colander.Range(min=0, max=900)
    )
    dwnld_fw_retries = colander.SchemaNode(
        colander.Integer(),
        missing=1,
        validator=colander.Range(min=0, max=10)
    )

class OCPPDiagnosticSchema(colander.MappingSchema):
    upld_diag_interval = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=900),
    )
    upld_diag_retries = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=10),
    )

class OCPPMeterSchema(colander.MappingSchema):
    # clock_aligned_data_interval = colander.SchemaNode(
    #     colander.Int(),
    #     validator=colander.Any(colander.Range(min=10, max=86400), colander.Range(min=0,max=0)))
    # config_max_keys = colander.SchemaNode(
    #     colander.Int(),
    #     validator=colander.Range(min=0, max=10))
    # mv_al_data_max_len = colander.SchemaNode(
    #     colander.Int(),
    #     validator=colander.Range(min=0, max=100))
    # mv_s_data_max_len = colander.SchemaNode(
    #     colander.Int(),
    #     validator=colander.Range(min=0, max=100))
    mv_s_interval = colander.SchemaNode(
        colander.Int(),
        validator=colander.Any(colander.Range(min=10, max=86400), colander.Range(min=0,max=0)))
    # stop_trans_al_data_max_len = colander.SchemaNode(
    #     colander.Int(),
    #     validator=colander.Range(min=0, max=100))
    # stop_trans_s_data_max_len = colander.SchemaNode(
    #     colander.Int(),
    #     validator=colander.Range(min=0, max=100))
    # max_charging_profiles = colander.SchemaNode(
    #     colander.Int(),
    #     validator=colander.Range(min=0, max=10))

class OCPPSessionSchema(colander.MappingSchema):
    max_e_on_invalid_id = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=1000000),
    )
    stop_trans_ev_side_disc = colander.SchemaNode(
        colander.Boolean(),
        missing=False,
    )
    stop_trans_on_invalid_id = colander.SchemaNode(
        colander.Boolean(),
        missing=False,
    )
    trans_num_msg_attempts = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=10),
    )
    trans_msg_retry_interval = colander.SchemaNode(
        colander.Integer(),
        validator=colander.Range(min=0, max=86400),
    )
    #session_stop_invalid_auth = colander.SchemaNode(
    #    colander.Boolean(),
    #    missing=False,
    #)

class OCPPChargingSchema(colander.MappingSchema):
    # chrg_profile_max_stack = colander.SchemaNode(
    #     colander.Integer(),
    #     validator=colander.Range(min=0, max=1000),
    # )
    # chrg_schedule_rate_unit = colander.SchemaNode(
    #     colander.String(),
    #     validator=validate_input_words
    # )
    chrg_schedule_max_periods = colander.SchemaNode(
        colander.Int(),
        missing=1,
        validator=colander.Range(min=0, max=50),
    )
    max_charging_profiles = colander.SchemaNode(
        colander.Int(),
        missing=1,
        validator=colander.Range(min=0, max=10),
    )

class CommunicationGeneral(colander.MappingSchema):
    network_mode = colander.SchemaNode(colander.String(), missing=None)
    connectivity = colander.SchemaNode(colander.String(), missing=None)
    heartbeat_interval = colander.SchemaNode(colander.Integer(), validator=colander.Range(min=0, max=86400))


class CommunicationWifi(colander.MappingSchema):
    ssid = colander.SchemaNode(colander.String(), missing=None)
    bssid = colander.SchemaNode(colander.String(), missing=None)
    wifi_security_proto = colander.SchemaNode(colander.String(), missing=None)
    wifi_password = colander.SchemaNode(colander.String(), missing=None, validator=colander.Length(max=100))
    wifi_sig_strength = colander.SchemaNode(colander.String(), missing=None)



class CommunicationCellular(colander.MappingSchema):
    ICCID = colander.SchemaNode(colander.String(), missing=None, validator=colander.Length(max=19))
    APN = colander.SchemaNode(colander.String(), missing=None, validator=colander.Length(max=255))
    APN_username = colander.SchemaNode(colander.String(), missing=None, validator=colander.Length(max=100))
    APN_password = colander.SchemaNode(colander.String(), missing=None, validator=colander.Length(max=100))
    cell_dial_number = colander.SchemaNode(colander.String(), missing=None, validator=colander.Length(max=100))
    cell_pin_code = colander.SchemaNode(colander.String(), missing=None, validator=colander.Length(max=100))
    cell_sig_strength = colander.SchemaNode(colander.String(), missing=None)
    cell_reconnect_interval = colander.SchemaNode(colander.Integer(), missing=None, validator=colander.Range(min=0, max=900))


