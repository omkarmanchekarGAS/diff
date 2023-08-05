def retrieve_data(con):
    cursor = con.cursor()
    data = []
    try:
        data.append((cursor.execute('SELECT * FROM config WHERE ID=1').fetchall())[0])
        data.append((cursor.execute('SELECT * FROM system_status WHERE ID=1').fetchall())[0])
        data.append((cursor.execute('SELECT * FROM status WHERE ID=1').fetchall())[0])
        if data:
            print(data)
            return data
    finally:
        return data
        #con.close()
