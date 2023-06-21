from flask import Flask, render_template, Response as HTTPResponse, request as HTTPRequest
import mysql.connector, json, pika, logging
from login_producer import *
import bcrypt




app = Flask(__name__)

# Note, HTTP response codes are
#  200 = OK the request has succeeded.
#  201 = the request has succeeded and a new resource has been created as a result.    
#  401 = Unauthorized (user identity is unknown)
#  403 = Forbidden (user identity is known to the server)
#  409 = A conflict with the current state of the resource
#  429 = Too Many Requests

@app.route('/login', methods = ['GET'])
def login3():
    jsondoc = ''

    
    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        auth = HTTPRequest.authorization
        print(auth)
        db = mysql.connector.connect(host="LoginSQL",port='3306', user="root", password="root",database="login_soa")
        dbc = db.cursor(dictionary=True)
        # ambil data login
        sql = "SELECT * FROM users"
        dbc.execute(sql)
        data_login = dbc.fetchall()
        dbc.close()
        db.close()

        if data_login != None:

            status_code = 200  # The request has succeeded
            jsondoc = json.dumps(data_login)

        else: 
            status_code = 404  # No resources found


    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke login
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp

@app.route('/login/staff', methods = ['POST'])
def login():
    jsondoc = ''
    # ------------------------------------------------------
    # HTTP method = POST
    # ------------------------------------------------------
    if HTTPRequest.method == 'POST':
        data = json.loads(HTTPRequest.data)
        loginUsername = data['username']
        loginPassword = data['password']
        role = 1

        try:
            # ambil data login staff
            db = mysql.connector.connect(host="LoginSQL",port='3306', user="root", password="root",database="login_soa")
            dbc = db.cursor(dictionary=True)
            sql = "SELECT password FROM users WHERE username =%s AND `role`=%s"
            dbc.execute(sql, [loginUsername,role])
            data_login = dbc.fetchone()
            
            dbc.close()
            db.close()

            if data_login is not None:
                stored_hashed_password = data_login['password']
                verifyPassword = bcrypt.checkpw(loginPassword.encode('utf-8'), stored_hashed_password.encode('utf-8'))

                if verifyPassword:
                    # kalau data login ada, juga ambil menu dari login tsb.
                    result = {'result':'Success'}
                    jsondoc = json.dumps(result)
                    status_code = 201
                else:
                    data_error = {'error':'Wrong Username or Password'}
                    jsondoc = json.dumps(data_error)
                    status_code = 401
            else:
                data_error = {'error':'User Not Found'}
                jsondoc = json.dumps(data_error)
                status_code = 402
        # bila ada kesalahan saat insert data, buat XML dengan pesan error
        except mysql.connector.Error as err:
            status_code = 409


    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke login
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp

@app.route('/login/client', methods = ['POST'])
def login2():
    jsondoc = ''
    # ------------------------------------------------------
    # HTTP method = POST
    # ------------------------------------------------------
    if HTTPRequest.method == 'POST':
        data = json.loads(HTTPRequest.data)
        loginUsername = data['username']
        loginPassword = data['password']
        role = 0

        try:
            # ambil data login staff
            db = mysql.connector.connect(host="LoginSQL",port='3306', user="root", password="root",database="login_soa")
            dbc = db.cursor(dictionary=True)
            sql = "SELECT password FROM users WHERE username =%s AND `role`=%s"
            dbc.execute(sql, [loginUsername,role])
            data_login = dbc.fetchone()
            
            dbc.close()
            db.close()

            if data_login is not None:
                stored_hashed_password = data_login['password']
                verifyPassword = bcrypt.checkpw(loginPassword.encode('utf-8'), stored_hashed_password.encode('utf-8'))

                if verifyPassword:
                    # kalau data login ada, juga ambil menu dari login tsb.
                    result = {'result':'Success'}
                    jsondoc = json.dumps(result)
                    status_code = 201
                else:
                    data_error = {'error':'Wrong Username or Password'}
                    jsondoc = json.dumps(data_error)
                    status_code = 401
            else:
                data_error = {'error':'User Not Found'}
                jsondoc = json.dumps(data_error)
                status_code = 402
        # bila ada kesalahan saat insert data, buat XML dengan pesan error
        except mysql.connector.Error as err:
            status_code = 409


    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke login
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp