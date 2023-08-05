from flask import redirect, render_template, request, url_for, session
from flask import Flask
from utils.conn import create_connection
from utils.check_user import checkUser
from utils.create_query import create_query
from utils.retrieve_data import retrieve_data
from utils.scan import get_cell
import sys
from os import system
from time import sleep

sys.path.insert(0, '/root')
import lib_db as ldb
import output_config

app = Flask(__name__)
app.secret_key = '1234'

def update_database(valid_data, conn):
    for item in valid_data:
        if(valid_data[item] == True):
            valid_data[item] = 1
        elif(valid_data[item] == False):
            valid_data[item] = 0
        if(ldb.update('config', f"{item}", valid_data[item],conn) == 0):
            if(ldb.update('system_status', f"{item}", valid_data[item],conn) == 0):
                if(ldb.update('status', f"{item}", valid_data[item],conn) == 0):
                    print("ERROR")

@app.route('/', methods=['GET'])
def default():
    return redirect(url_for('login'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        conn = create_connection('/root/data/users.db')
        if checkUser(conn,request.form['username'],request.form['password']):
            session['username'] = request.form['username']
            conn.close()
            return redirect(url_for('general_settings'))
        else:
            error = 'Invalid Credentials. Please try again.'
            conn.close()       
    return render_template('login.html',error=error)


@app.route('/general/',methods=['GET', 'POST'])
def general_settings():
    success=False
    conn = create_connection('/root/data/data.db')
    data=retrieve_data(conn)
    if('username' not in session):
        return redirect(url_for('login'))
    if request.method == 'POST':
        valid_data = create_query(request.args.get("f"),request)
        print(valid_data)
        if 'error' in valid_data:
            return render_template('general_settings.html',success=success,data=data,error=valid_data)
        update_database(valid_data, conn)
        output_config.update_appearance()
        data=retrieve_data(conn)
        success=True
    conn.close()
    return render_template('general_settings.html',success=success,data=data, error = None)


@app.route('/ocpp/',methods=['GET', 'POST'])
def ocpp_settings():
    print(request.form)
    success=False
    conn = create_connection('/root/data/data.db')
    data=retrieve_data(conn)
    if('username' not in session):
        return redirect(url_for('login'))
    if request.method == 'POST' and 'upload' in request.form:
        valid_data = create_query(request.args.get("f"),request)
        print(valid_data)
        if 'error' in valid_data:
            return render_template('OCPP_settings.html',success=success,data=data,error=valid_data)
        update_database(valid_data, conn)
        success=True
        data=retrieve_data(conn)
    elif request.method == 'POST' and 'file' in request.form:
        #print("2")
        fl = request.files['firm']
        fl.save(f'/tmp/{fl.filename}')
        #print("3")
        system(f"sysupgrade /tmp/{fl.filename}")
        data=retrieve_data(conn)
        success="Uploaded"
    conn.close()
    return render_template('OCPP_settings.html',success=success,data=data,error = None)

@app.route('/communication/',methods=['GET', 'POST'])
def communication_settings():
    print(request.form)
    success=False
    conn = create_connection('/root/data/data.db')
    data=retrieve_data(conn)
    if('username' not in session):
        return redirect(url_for('login'))
    if request.method == 'POST' and 'upload' in request.form:
        valid_data = create_query(request.args.get("f"),request)
        print(valid_data)
        if 'error' in valid_data:
            return render_template('communication_settings.html',success=success,data=data,error=valid_data)
        update_database(valid_data, conn)
        data=retrieve_data(conn)
        success=True
    elif request.method == 'POST' and 'file' in request.form:
        fl = request.files['llm']
        fl.save(f'/root/llm.json')
        #will instead by updated by parent
        #output_config.update_llm(fl.filename)
        print("LLM UPDATED")
        data=retrieve_data(conn)
        success=True
    conn.close()
    return render_template('communication_settings.html',success=success,data=data,error=None)

@app.route('/logout/', methods=['GET'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/wifi/', methods=['GET','POST'])
def wifi():
    return get_cell()

@app.route('/reboot/', methods=['GET','POST'])
def reboot():
    last = request.referrer.split('/')
    conn = create_connection('/root/data/data.db')
    data=retrieve_data(conn)
    conn.close()
    system("reboot")
    if(last[len(last) - 2] == 'ocpp'):
        return render_template('OCPP_settings.html',success=True,data=data,error = None)
    elif(last[len(last) - 2] == 'communication'):
        return render_template('communication_settings.html',success=True,data=data,error=None)
    else:
        return render_template('general_settings.html',success=True,data=data, error = None)
    
@app.route('/reset/', methods=['GET','POST'])
def reset():
    #Currently does nothing but reload the page
    last = request.referrer.split('/')
    #system(rm -r /root/data/)
    #system(mkdir /root/data)
    #system(python3 /root/create_db.py)
    #system(python3 /root/add_defaults.py &)
    #sleep(1)
    conn = create_connection('/root/data/data.db')
    data=retrieve_data(conn)
    conn.close()
    if(last[len(last) - 2] == 'ocpp'):
        return render_template('OCPP_settings.html',success=True,data=data,error = None)
    elif(last[len(last) - 2] == 'communication'):
        return render_template('communication_settings.html',success=True,data=data,error=None)
    else:
        return render_template('general_settings.html',success=True,data=data, error = None)