from werkzeug.security import generate_password_hash, check_password_hash

def find_by_username(con, username):
    cursor = con.cursor()
    
    try:
        data = cursor.execute('SELECT * FROM users WHERE username=?', (username,)).fetchone()
        if data:
            print(data[0])
            print(data[1])
            return data[0], data[1]
    finally:
        con.close()

def checkUser(con,user,password):
    username,pwd = find_by_username(con,user)
    return username==user and check_password_hash(pwd,password)
        

    

   
