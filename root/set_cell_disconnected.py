import sqlite3
import lib_db as ldb

conn = sqlite3.connect('/root/data/data.db')
ldb.update('status', 'cell_sig_strength', 0, conn)