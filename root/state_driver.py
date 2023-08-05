import lib_db as ldb

current_lims = [0,0,0,0]
current_lims[0] = ldb.read_db('system_status', 'hardware_max_amps')
current_lims[1] = ldb.read_db('system_status', 'connector_max_amps')
current_lims[3] = ldb.read_db('status', 'dip_switch_current')


while(1):

    status = ldb.read_db('status', 'pilot_state')

    line3 = ''
    side_led_vals = []
    led_brightness = ldb.read_db('config', 'led_brightness')/100.0
    if(status < 4 and current_lims[3] == 0):
        line3 = 'Invalid DIP Switches'
        side_led_vals = [255*led_brightness,255*led_brightness,255*led_brightness]
    elif status == 1:
        line3 = 'Available'
        side_led_vals = [0,255*led_brightness,0]
    elif status == 2:
        line3 = 'Vehicle Plugged In'
        side_led_vals = [255*led_brightness,0,255*led_brightness]
    elif status == 3:
        line3 = 'Charging'
        side_led_vals = [0,0,255*led_brightness]
    elif status > 3:
        fault_code = ldb.read_db('status', 'fault_code')
        line3 = 'FAULTED: CODE ' + str(fault_code)
        side_led_vals = [255*led_brightness,0,0]
    
    side_led = (hex(int(side_led_vals[0]))[2:].zfill(2) + hex(int(side_led_vals[1]))[2:].zfill(2) + hex(int(side_led_vals[2]))[2:].zfill(2)).upper()

    t = ldb.update('output', 'line3', line3)
    ldb.update('output', 'side_led', side_led)

    logo_color = ldb.read_db('config', 'logo_color')
    try:
        int(logo_color, 16)
        ldb.update('output', 'logo_led', logo_color)
    except:
        ldb.update('output', 'logo_led', 'FFFFFF')

    ldb.update('output', 'anim_num', 1)
    ldb.update('output', 'temp_num', 1)

    charge_auth = ldb.read_db('status', 'charge_authorized')
    if(charge_auth):
        current_lims[2] = ldb.read_db('config', 'firmware_max_amps')
        current_lims[3] = ldb.read_db('status', 'dip_switch_current')
        ldb.update('output', 'current', min(current_lims))
    else:
        ldb.update('output', 'current', 0)

