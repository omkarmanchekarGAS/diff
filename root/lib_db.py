import sqlite3

def update(table_name, field, value, conn):
    curs = conn.cursor()
    try:
        curs.execute("""UPDATE """ + f"""\"{table_name}\"""" + """ SET """ + f"""\"{field}\"""" + """=""" + f"""\"{value}\"""" + """ WHERE id=1""")
        conn.commit()
        return 1
    except sqlite3.Error as e:
        print(type(value))
        print(e)
        return 0
    
def read_db(table_name, field, conn):
    curs = conn.cursor()
    value = curs.execute(f"""SELECT {field} FROM {table_name}""").fetchone()
    return value[0]

def add_mv(meter_values, conn):
    curs = conn.cursor()
    meter_values = (None,) + meter_values
    try:
        curs.execute("""INSERT INTO meter_vals VALUES(?,?,?,?,?)""" , meter_values)#+ f"""{meter_values}""")
        conn.commit()
        return 1
    except sqlite3.Error as e:
        print(type(meter_values))
        print(e)
        return 0
