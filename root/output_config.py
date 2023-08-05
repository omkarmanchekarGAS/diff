import lib_db as ldb
import sqlite3

def update_appearance():
    conn = sqlite3.connect("/root/data/data.db")
    logo_color = ldb.read_db('config', 'logo_color', conn)
    line1 = ldb.read_db('config', 'welcome_msg1', conn)
    line2 = ldb.read_db('config', 'welcome_msg2', conn)
    
    if(line1 == ''):
        line1 = ' '
    if(line2 == ''):
        line2 = ' '

    try:
        int(logo_color, 16)
        ldb.update('output', 'logo_led', logo_color, conn)
    except:
        ldb.update('output', 'logo_led', 'FFFFFF', conn)

    ldb.update('output', 'anim_num', 1, conn)
    ldb.update('output', 'temp_num', 1, conn)
    ldb.update('output', 'line1', line1, conn)
    ldb.update('output', 'line2', line2, conn)

def update_output_current(llm_limit):
    conn = sqlite3.connect("/root/data/data.db")
    current_lims = [0,0,0,0]
    if(ldb.read_db('config','network_mode',conn) != 'Direct'):
        current_lims.append(llm_limit)
    current_lims[0] = ldb.read_db('system_status', 'hardware_max_amps', conn)
    current_lims[1] = ldb.read_db('system_status', 'connector_max_amps', conn)
    charge_auth = ldb.read_db('status', 'charge_authorized', conn)
    if(charge_auth):
        current_lims[2] = ldb.read_db('config', 'firmware_max_amps', conn)
        current_lims[3] = ldb.read_db('status', 'dip_switch_current', conn)
        ldb.update('output', 'current', min(current_lims), conn)
        print("Updating output current with authorized charge")
    else:
        ldb.update('output', 'current', 0, conn)
        print("Updating output current with no auth")