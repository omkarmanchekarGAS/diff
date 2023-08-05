import sqlite3
#import gpm8213_lan as gpm
import datetime
import stpm_iface
import eeprom_iface
import sys

table_exists = True

class calibrator():
    db_connection = sqlite3.Connection
    curs = sqlite3.Cursor
    #GPM = gpm.gpm
    stpm = stpm_iface.STPM
    eeprom = eeprom_iface.EEPROM
    serial_num = ''

    def __init__(self, num, calv=.875, cali=.875):
        self.db_connection = sqlite3.connect('calibration_data.db')
        self.curs = self.db_connection.cursor()
        #self.GPM = gpm.gpm()
        self.stpm = stpm_iface.STPM(calv, cali)
        self.eeprom = eeprom_iface.EEPROM()
        self.serial_num = num
        self.eeprom.enable_stpm()

    def authorize_charge(self):
        self.eeprom.authorize_charge()
    
    #returns 1 upon successful calibration, 0 otherwise
    #adds constants and other info to db
    def calibrate(self, vavg_gpm, cavg_gpm):#, user, slot):

        success = self.stpm.enable_auto_latch()
        if success == 0:
            print("CALIBRATION FAILED :(")
            return
        self.stpm.set_gain()

        self.authorize_charge()

        # calibration_data = {}
        # stpm_data = {}

        #sampling RMS values and averaging them together
        #should do this for both?
        vavg_stpm = 0
        cavg_stpm = 0
        # vavg_gpm = 0
        # cavg_gpm = 0
        samples = 25
        for i in range(0,samples):
            values_stpm = self.stpm.get_rms_values()
            # vavg_gpm = vavg_gpm + self.GPM.getVoltage()
            # cavg_gpm = cavg_gpm + self.GPM.getCurrent()
            vavg_stpm = vavg_stpm + values_stpm[0]
            cavg_stpm = cavg_stpm + values_stpm[1]

        self.eeprom.end_charge()

        vavg_stpm = vavg_stpm/samples
        cavg_stpm = cavg_stpm/samples
        # vavg_gpm = vavg_gpm/samples
        # cavg_gpm = cavg_gpm/samples

        # print('average voltage from GPM: ' + str(vavg_gpm))
        # print('average current from GPM: ' + str(cavg_gpm))
        print('average voltage from STPM: ' + str(vavg_stpm))
        print('average current from STPM: ' + str(cavg_stpm))

        calib_consts = self.stpm.calculate_calibration_constants(vavg_gpm, cavg_gpm, vavg_stpm, cavg_stpm)

        if(calib_consts == 0):
            print("CALIBRATION FAILED :(")
            return

        try:
            print('CHC: ' + str(calib_consts[0]))
            print('CHV: ' + str(calib_consts[1]))
            self.stpm.set_calibration_value_voltage([(int(calib_consts[0]) & 0xFF), ((int(calib_consts[0]) >> 8) + 0xF0)])
            self.stpm.set_calibration_value_current([(int(calib_consts[1]) & 0xFF), ((int(calib_consts[1]) >> 8) + 0xF0)])
        except Exception as e:
            print(e)
            return
        
        self.eeprom.write_serial_num(self.serial_num)
        self.eeprom.write_prod_date(datetime.datetime.utcnow())
        self.eeprom.write_calib_consts(calib_consts[0], calib_consts[1])
        
        self.update_db()

        #calibration_data['Voltage'] = self.GPM.getVoltage()
        #calibration_data['Current'] = self.GPM.getCurrent()
        #calibration_data['Power'] = self.GPM.getPower()
        #calibration_data['Line Frequency'] = self.GPM.getLineFrequency()
        #calibration_data['Power Factor'] = self.GPM.getPowerFactor()

        #stpm_data['Voltage'] = rms[0]
        #calibration_data['Current'] = rms[1]
        #calibration_data['Power'] = self.stpm.get_active_power()
        #calibration_data['Line Frequency'] = self.stpm.getLineFrequency()
        #calibration_data['Power Factor'] = self.stpm.getPowerFactor()

        #SET EEPROM DOWN HERE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        #ADD DATA TO DATABASE HERE
        # STATUS = 'PASSED'
        # SERIAL_NUM = 1011102
        # CAL_RIG_ID = 1
        
        # curs.execute("INSERT INTO all_calibration_data VALUES(?, ?, ?, ?, ?, ?, ?)", (user, datetime.now().strftime("%d-%m-%Y %H:%M:%S"), (slot+1)
        #             , STATUS, SERIAL_NUM, CAL_RIG_ID, str(calibration_data)))
        # db_connection.commit()
        # return (STATUS == "PASSED")

    def update_db(self, CHC, CHV):
        entry = (None, self.serial_num, datetime.datetime.utcnow(), CHC, CHV)
        self.curs.execute("INSERT INTO calibration VALUES(?, ?, ?, ?, ?)", entry)
        self.db_connection.commit()

    def end_calibration(self):
        self.stpm.disable_auto_latch()
        self.db_connection.close()
        #self.GPM.close_connection()

# def print_db():
#     curs.execute("SELECT * FROM all_calibration_data")
#     print(curs.fetchall())
#     curs.execute("SELECT * FROM users")
#     print(curs.fetchall())

# def create_tables():
#     #access to sqlite database
#     #creates tables if they do not exist
#     global curs
#     global table_exists
    
#     curs = db_connection.cursor()

#     tables = curs.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
#     if(not ('all_calibration_data' in tables and 'users' in tables)):
#         #calibration data table
#         curs.execute("""CREATE TABLE all_calibration_data(name, timestamp, slot,
#                 status, serial_number, calibration_rig_id, calibration_data)""")
#         #data table of users
#         curs.execute("""CREATE TABLE users(username)""")
#         db_connection.commit()

# def add_user(user):
#     if(curs.execute("""SELECT EXISTS (SELECT 1 FROM users WHERE username=?)"""
#                         , (user,)).fetchone() != (0,)):
#         return 'User already exists, press enter to log in'
#     else:
#         curs.execute("""INSERT INTO users VALUES(?)""", (user,))
#         db_connection.commit()
#         return 'User added, press enter to log in'
    
# def check_user_exists(user):
#     if(curs.execute("""SELECT EXISTS (SELECT 1 FROM users WHERE username=?)"""
#                         , (user,)).fetchone() == (0,)):
#         return 0
#     return 1

if __name__ == "__main__":
    if(len(sys.argv) != 4 and len(sys.argv) != 6):
        print("wrong number of arguments!!\nREQUIRED:\n\tserial number\n\tgpm voltage\n\tgpm current\nOPTIONAL:\n\tprevious calibration value for voltage\n\tprevious calibration value for voltage")
    
    serial_num = sys.argv[1]
    VN = sys.argv[2]
    IN = sys.argv[3]

    if(len(sys.argv) == 6):
        CALV = sys.argv[4]
        CALI = sys.argv[5]
    
    if(len(serial_num) != 9):
        print("Serial number wrong length")
    else:
        c = calibrator(serial_num)
        c.calibrate(VN, IN)
        c.end_calibration()