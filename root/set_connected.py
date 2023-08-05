import sqlite3
import lib_db as ldb

conn = sqlite3.connect('/root/data/data.db')
ldb.update('status', 'wifi_sig_strength', 2, conn)