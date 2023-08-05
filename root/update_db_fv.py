import sqlite3
import lib_db
lib_db.update("system_status", "firmware_version", "1.02E", sqlite3.connect("/root/data/data.db"))