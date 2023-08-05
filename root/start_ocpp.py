import lib_db
import sqlite3
import os

conn = sqlite3.connect("/root/data/data.db")
if lib_db.read_db("config", "online_mode", conn) == 0:
    lib_db.update("status", "charge_authorized", 1, conn)
else:
    conn.close()
    os.system("python /root/ocpp/src/connect_to_central_system.py 0 &")