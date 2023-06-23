from flask import Flask, render_template, Response as HTTPResponse, request as HTTPRequest
import mysql.connector, json, pika, logging
from client_producer import *
import bcrypt
import time

def retry_connect(host, user, password, database, max_attempts=10, delay=5):
    attempt = 0
    while attempt < max_attempts:
        try:
            db = mysql.connector.connect(host=host, user=user, password=password, database=database)
            print("Connected to MySQL server successfully.")
            return db
        except mysql.connector.Error as err:
            print(f"Failed to connect to MySQL server. Retrying in {delay} seconds...")
            time.sleep(delay)
            attempt += 1
    raise Exception("Unable to connect to MySQL server after multiple attempts.")


app = Flask(__name__)

# Note, HTTP response codes are
#  200 = OK the request has succeeded.
#  201 = the request has succeeded and a new resource has been created as a result.    
#  401 = Unauthorized (user identity is unknown)
#  403 = Forbidden (user identity is known to the server)
#  409 = A conflict with the current state of the resource
#  429 = Too Many Requests


@app.route('/client', methods = ['POST', 'GET'])
def client():
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        auth = HTTPRequest.authorization
        print(auth)

        # Connect to MySQL server with retries
        db = retry_connect("ClientSQL", "root", "root", "client_soa")
        dbc = db.cursor(dictionary=True)
        # ambil data client
        sql = "SELECT * FROM user_client"
        dbc.execute(sql)
        data_client = dbc.fetchall()

        if data_client != None:
            status_code = 200  # The request has succeeded
            jsondoc = json.dumps(data_client)

        else: 
            status_code = 404  # No resources found


    # ------------------------------------------------------
    # HTTP method = POST
    # ------------------------------------------------------
    elif HTTPRequest.method == 'POST':
        data = json.loads(HTTPRequest.data)
        clientUsername = data['username']
        clientPassword = data['password']
        role = data['role']
        email = data['email']
        duplicate = False
        hashed_password = bcrypt.hashpw(clientPassword.encode('utf-8'), bcrypt.gensalt())
        # Connect to MySQL server with retries
        db = retry_connect("ClientSQL", "root", "root", "client_soa")
        dbc = db.cursor(dictionary=True)
        try:
            # ambil data client
            sql = "SELECT * FROM user_client"
            dbc.execute(sql)
            data_client = dbc.fetchall()
            if data_client != None:
                # kalau data client ada, juga ambil menu dari client tsb.
                for x in range(len(data_client)):
                    client_username = data_client[x]['username']
                    if (client_username == clientUsername):
                        duplicate = True
                        break

            if (not duplicate):
                # simpan nama client, dan clientPassword ke database
                sql = "INSERT INTO user_client (`username`,`email`,`password`,`role`) VALUES (%s,%s,%s,%s)"
                dbc.execute(sql, [clientUsername,email,hashed_password,role] )
                db.commit()
                # dapatkan ID dari data client yang baru dimasukkan
                clientID = dbc.lastrowid
                data_client = {'id':clientID}
                jsondoc = json.dumps(data_client)

                data['event']  = 'new_client'
                data['client_id'] = clientID
                message = json.dumps(data)
                publish_message(message,'client.new')


                status_code = 201
            else:
                data_error = {'error':'Username sudah ada'}
                jsondoc = json.dumps(data_error)
                status_code = 400
        # bila ada kesalahan saat insert data, buat XML dengan pesan error
        except mysql.connector.Error as err:
            status_code = 409


    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke client
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp


@app.route('/client/password/<path:id>', methods = ['PUT'])
def password(id):
    jsondoc = ''

    # ------------------------------------------------------
    # HTTP method = PUT
    # ------------------------------------------------------
    if HTTPRequest.method == 'PUT':
        data = json.loads(HTTPRequest.data)
        oldPassword = data['old_password']
        newPassword = data['new_password']
        hashed_password = bcrypt.hashpw(oldPassword.encode('utf-8'), bcrypt.gensalt())
        new_hashed_password = bcrypt.hashpw(newPassword.encode('utf-8'), bcrypt.gensalt())

        clientID = int(id)
        
        # Connect to MySQL server with retries
        db = retry_connect("ClientSQL", "root", "root", "client_soa")
        dbc = db.cursor(dictionary=True)
        # messagelog = 'PUT id: ' + str(staffID) + ' | nama: ' + staffUsername + ' | staffPassword: ' + staffPassword + ' | role: ' + str(role)
        # logging.warning("Received: %r" % messagelog)

        try:
            sql = "SELECT password FROM user_client WHERE id =%s"
            dbc.execute(sql, [clientID])
            data_staff = dbc.fetchone()



            if data_staff is not None:
                stored_hashed_password = data_staff['password']
                verifyPassword = bcrypt.checkpw(oldPassword.encode('utf-8'), stored_hashed_password.encode('utf-8'))

                if verifyPassword:
                    sql = "UPDATE user_client set `password`=%s where `id`=%s"
                    dbc.execute(sql, [new_hashed_password,clientID] )
                    db.commit()
                    dbc.close()
                    db.close()

                    data_baru = {}
                    data_baru['event']  = "password_client"
                    data_baru['id']     = clientID
                    data_baru['password']   = newPassword
                    jsondoc = json.dumps(data_baru)
                    publish_message(jsondoc,'client.password')


                    result = {'result':'Success'}
                    jsondoc = json.dumps(result)
                    status_code = 201
                else:
                    data_error = {'error':'Password Lama Salah'}
                    jsondoc = json.dumps(data_error)
                    status_code = 401
            else:
                data_error = {'error':'User Not Found'}
                jsondoc = json.dumps(data_error)
                status_code = 402

        except mysql.connector.Error as err:
            status_code = 409
            data_error = {"error": str(err)}
            jsondoc = json.dumps(data_error)

            
    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke staff
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp


@app.route('/client/<path:id>', methods = ['GET', 'PUT', 'DELETE'])
def client2(id):
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        if id.isnumeric():
            # ambil data client
            # Connect to MySQL server with retries
            db = retry_connect("ClientSQL", "root", "root", "client_soa")
            dbc = db.cursor(dictionary=True)
            sql = "SELECT * FROM user_client WHERE id = %s"
            dbc.execute(sql, [id])
            data_client = dbc.fetchone()
            # kalau data client ada, juga ambil menu dari client tsb.
            if data_client != None:
                jsondoc = json.dumps(data_client)

                status_code = 200  # The request has succeeded
            else: 
                status_code = 404  # No resources found
        else: status_code = 400  # Bad Request

    # ------------------------------------------------------
    # HTTP method = PUT
    # ------------------------------------------------------
    elif HTTPRequest.method == 'PUT':
        data = json.loads(HTTPRequest.data)
        clientUsername = data['username']
        email = data['email']
        clientID = int(id)
        duplicate = False

        # Connect to MySQL server with retries
        db = retry_connect("ClientSQL", "root", "root", "client_soa")
        dbc = db.cursor(dictionary=True)
        try:
            sql = "SELECT * FROM user_client"
            dbc.execute(sql)
            data_client = dbc.fetchall()
            if data_client != None:
                # kalau data client ada, juga ambil menu dari client tsb.
                for x in range(len(data_client)):
                    client_username = data_client[x]['username']
                    if (data_client[x]['id'] != clientID):
                        if (client_username == clientUsername):
                            duplicate = True
                            break

            if not duplicate:
                # ubah nama client dan clientPassword di database
                sql = "UPDATE user_client set `username`=%s, `email`=%s where `id`=%s"
                dbc.execute(sql, [clientUsername,email,clientID] )
                db.commit()

                # teruskan json yang berisi perubahan data client yang diterima dari Web UI
                # ke RabbitMQ disertai dengan tambahan route = 'client.tenant.changed'
                data_baru = {}
                data_baru['event']  = "updated_client"
                data_baru['id']     = clientID
                data_baru['username']   = clientUsername
                data_baru['email'] = email
                jsondoc = json.dumps(data_baru)
                publish_message(jsondoc,'client.changed')

                status_code = 200

            else:
                status_code = 400
                data_error = {'error':'Username sudah ada'}
                jsondoc = json.dumps(data_error)
        # bila ada kesalahan saat ubah data, buat XML dengan pesan error
        except mysql.connector.Error as err:
            status_code = 409
            data_error = {"error": str(err)}
            jsondoc = json.dumps(data_error)


    # ------------------------------------------------------
    # HTTP method = DELETE
    # ------------------------------------------------------
    elif HTTPRequest.method == 'DELETE':
        data = json.loads(HTTPRequest.data)




    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke client
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp









