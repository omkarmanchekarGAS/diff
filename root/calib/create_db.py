import sqlite3

conn = None
try:
    conn = sqlite3.connect("calibration_data.db")
    with open("Untitled.sql", "r") as sqlfile:
        conn.cursor().executescript(sqlfile.read())
    conn.commit()
    conn.close()
except sqlite3.Error as e:
    print(e)
    conn.close()