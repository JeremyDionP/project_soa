from flask import Flask, render_template, Response as HTTPResponse, request as HTTPRequest
import mysql.connector, json, pika, logging
from client_producer import *
import bcrypt

db = mysql.connector.connect(host="ClientSQL", user="root", password="root",database="client_soa")
dbc = db.cursor(dictionary=True)


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
        duplicate = False
        hashed_password = bcrypt.hashpw(clientPassword.encode('utf-8'), bcrypt.gensalt())

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
                sql = "INSERT INTO user_client (`username`,`password`,`role`) VALUES (%s,%s,%s)"
                dbc.execute(sql, [clientUsername,hashed_password,role] )
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





@app.route('/client/<path:id>', methods = ['GET', 'PUT', 'DELETE'])
def client2(id):
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        if id.isnumeric():
            # ambil data client
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
        clientPassword = data['password']
        hashed_password = bcrypt.hashpw(clientPassword.encode('utf-8'), bcrypt.gensalt())
        role = data['role']
        clientID = int(id)
        duplicate = False

        messagelog = 'PUT id: ' + str(clientID) + ' | nama: ' + clientUsername + ' | clientPassword: ' + clientPassword + ' | role: ' + str(role)
        logging.warning("Received: %r" % messagelog)

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
                sql = "UPDATE user_client set `username`=%s, `password`=%s, `role`=%s where `id`=%s"
                dbc.execute(sql, [clientUsername,hashed_password,role,clientID] )
                db.commit()

                # teruskan json yang berisi perubahan data client yang diterima dari Web UI
                # ke RabbitMQ disertai dengan tambahan route = 'client.tenant.changed'
                data_baru = {}
                data_baru['event']  = "updated_client"
                data_baru['id']     = clientID
                data_baru['username']   = clientUsername
                data_baru['password'] = clientPassword
                data_baru['role'] = role
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









