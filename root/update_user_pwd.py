import sqlite3
from werkzeug.security import generate_password_hash


conn = sqlite3.connect("flaskr/users.db")
cursor = conn.cursor()
password = generate_password_hash('admin')
statement = """UPDATE users SET password=""" + f"""\"{password}\"""" + """ WHERE username=\"admin\""""
print(statement)
cursor.execute(statement)
conn.commit()
conn.close()
