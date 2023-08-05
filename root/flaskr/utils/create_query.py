
from utils.valschema import validate
deviceGeneralMap = {
    'fmal':'firmware_max_amps',
    'ipd':'instant_power_delay',
    'rcar':'resume_charge_after_reboot',
    'ventilation':'ventilation_available',
    'led':'led_brightness'
}

deviceAppearanceMap = {
    'llc':'logo_color',
    '1ms':'welcome_msg1',
    '2ms':'welcome_msg2'
}

devicePriceMap = {
    'dpkh':'usd_per_kWh',
    'prk':'usd_per_parked_mins',
    'acf':'usd_activation_fee',
    'olm' : 'online_mode',
    'fm' : 'free_mode'
}

ocppServiceMap={
    'csid':'charge_point_id',
    'csu':'central_system_url',
    'bni':'boot_notif_interval',
    'bnr':'boot_notif_retries',
    'pdut':'pdu_timeout',
    'ct':'connection_timeout',
    'msd':'min_status_duration',
    'wpi':'ping_interval',
    'rr':'reset_retries',
    'chl':'children_list'
}

ocppFirmwareMap= {
    'fdi':'dwnld_fw_interval',
    'fdr':'dwnld_fw_retries',
    'ffu':'ftp_user',
    'ffp':'ftp_password'
}
ocppDiagnosticMap={
    'udi':'upld_diag_interval',
    'udr':'upld_diag_retries'
}

ocppMeterValueMap = {
    'cadi':'clock_aligned_data_interval', 
    'cmk': 'config_max_keys', 
    'mcae': 'mv_al_data_max_len', 
    'mse': 'mv_s_data_max_len', 
    'si': 'mv_s_interval',
    'mstsde': 'stop_trans_s_data_max_len', 
    'mstade': 'stop_trans_al_data_max_len', 
    'msfp': 'max_charging_profiles',
    'sfp': 'supported_charging_profiles' 
}

ocppSessionMap = {
    'meis':'max_e_on_invalid_id', 
    'stevd': 'stop_trans_ev_side_disc', 
    'stia': 'stop_trans_on_invalid_id', 
    'tra': 'trans_num_msg_attempts', 
    'tri': 'trans_msg_retry_interval'
}

ocppChargeProfileMap = {
    'mcpsl': 'chrg_profile_max_stack', 
    'acpu': 'chrg_schedule_rate_unit', 
    'mcpsp': 'chrg_schedule_max_periods', 
    'macp': 'max_charging_profiles'
}

communicationGeneralMap = {
    'nm':'network_mode',
    'nc':'connectivity',
    'hbi':'heartbeat_interval'
}

communicationWifiMap = {
    'wnn':'ssid',
    'wbn':'bssid',
    'sp':'wifi_security_proto',
    'wnp':'wifi_password',
    'ss':'wifi_sig_strength',

}
communicationCellularMap = {
    'iccid':'ICCID',
    'apn':'APN',
    'apnu':'APN_username',
    'apnp':'APN_password',
    'dn':'cell_dial_number',
    'pc':'cell_pin_code',
    'ss':'cell_sig_strength',
    'ri':'cell_reconnect_interval'
}


def create_query(setting,request):
    statement = """UPDATE data SET """
    # length = len(request.form)-1
    query_map = {}
    print(setting)
    if setting == 'device.general':
        hash_map = deviceGeneralMap
    elif setting == 'device.appearence':
        hash_map = deviceAppearanceMap
    elif setting == 'device.price':
        hash_map = devicePriceMap
    elif setting == 'ocpp.service':
        hash_map = ocppServiceMap
    elif setting == 'ocpp.firmware':
        hash_map = ocppFirmwareMap
    elif setting == 'ocpp.diagnostic':
        hash_map = ocppDiagnosticMap
    elif setting == 'ocpp.meter':
        hash_map = ocppMeterValueMap
    elif setting == 'ocpp.session':
        hash_map = ocppSessionMap
    elif setting == 'ocpp.charge':
        hash_map = ocppChargeProfileMap
    elif setting == 'communication.general':
        hash_map = communicationGeneralMap
    elif setting == 'communication.wifi':
        hash_map = communicationWifiMap
    elif setting == 'communication.cellular':
        hash_map = communicationCellularMap
    print(setting)
    print(hash_map)
    for key in request.form.keys():
        values = request.form.getlist(key)
        print(values)
        if key=='upload':
            continue
        for val in values:
            query_map[hash_map[key]] = val
    print(query_map)
    validated_data = validate(setting,query_map)
    if 'error' in validated_data:
        print("ERROR WITH VALIDATING")
        return validated_data
    if setting == 'device.appearence':
        validated_data['logo_color'] = validated_data['logo_color'][1:]
    print("Validated data is",validated_data)
    return validated_data