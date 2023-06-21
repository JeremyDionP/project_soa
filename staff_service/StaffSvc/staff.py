from flask import Flask, render_template, Response as HTTPResponse, request as HTTPRequest
import mysql.connector, json, pika, logging
from staff_producer import *
import bcrypt

db = mysql.connector.connect(host="StaffSQL", user="root", password="root",database="staff_soa")
dbc = db.cursor(dictionary=True)


app = Flask(__name__)

# Note, HTTP response codes are
#  200 = OK the request has succeeded.
#  201 = the request has succeeded and a new resource has been created as a result.    
#  401 = Unauthorized (user identity is unknown)
#  403 = Forbidden (user identity is known to the server)
#  409 = A conflict with the current state of the resource
#  429 = Too Many Requests


@app.route('/staff', methods = ['POST', 'GET'])
def staff():
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        auth = HTTPRequest.authorization
        print(auth)

        # ambil data staff
        sql = "SELECT * FROM user_staff"
        dbc.execute(sql)
        data_staff = dbc.fetchall()

        if data_staff != None:
            status_code = 200  # The request has succeeded
            jsondoc = json.dumps(data_staff)

        else: 
            status_code = 404  # No resources found


    # ------------------------------------------------------
    # HTTP method = POST
    # ------------------------------------------------------
    elif HTTPRequest.method == 'POST':
        data = json.loads(HTTPRequest.data)
        staffUsername = data['username']
        staffPassword = data['password']
        role = data['role']
        duplicate = False
        hashed_password = bcrypt.hashpw(staffPassword.encode('utf-8'), bcrypt.gensalt())

        try:
            # ambil data staff
            sql = "SELECT * FROM user_staff"
            dbc.execute(sql)
            data_staff = dbc.fetchall()
            if data_staff != None:
                # kalau data staff ada, juga ambil menu dari staff tsb.
                for x in range(len(data_staff)):
                    staff_username = data_staff[x]['username']
                    if (staff_username == staffUsername):
                        duplicate = True
                        break

            if (not duplicate):
                # simpan nama staff, dan staffPassword ke database
                sql = "INSERT INTO user_staff (`username`,`password`,`role`) VALUES (%s,%s,%s)"
                dbc.execute(sql, [staffUsername,hashed_password,role] )
                db.commit()
                # dapatkan ID dari data staff yang baru dimasukkan
                staffID = dbc.lastrowid
                data_staff = {'id':staffID}
                jsondoc = json.dumps(data_staff)

                # Publish event "new staff" yang berisi data staff yg baru.
                # Data json yang dikirim sebagai message ke RabbitMQ adalah json asli yang
                # diterima oleh route /staff [POST] di atas dengan tambahan 2 key baru,
                # yaitu 'event' dan staffID.
                data['event']  = 'new_staff'
                data['staff_id'] = staffID
                message = json.dumps(data)
                publish_message(message,'staff.new')


                status_code = 201
            else:
                data_error = {'error':'Username sudah ada'}
                jsondoc = json.dumps(data_error)
                status_code = 400
        # bila ada kesalahan saat insert data, buat XML dengan pesan error
        except mysql.connector.Error as err:
            status_code = 409


    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke staff
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp





@app.route('/staff/<path:id>', methods = ['GET', 'PUT', 'DELETE'])
def staff2(id):
    jsondoc = ''

    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        if id.isnumeric():
            # ambil data staff
            sql = "SELECT * FROM user_staff WHERE id = %s"
            dbc.execute(sql, [id])
            data_staff = dbc.fetchone()
            # kalau data staff ada, juga ambil menu dari staff tsb.
            if data_staff != None:
                jsondoc = json.dumps(data_staff)

                status_code = 200  # The request has succeeded
            else: 
                status_code = 404  # No resources found
        else: status_code = 400  # Bad Request

    # ------------------------------------------------------
    # HTTP method = PUT
    # ------------------------------------------------------
    elif HTTPRequest.method == 'PUT':
        data = json.loads(HTTPRequest.data)
        staffUsername = data['username']
        staffPassword = data['password']
        hashed_password = bcrypt.hashpw(staffPassword.encode('utf-8'), bcrypt.gensalt())
        role = data['role']
        staffID = int(id)
        duplicate = False

        messagelog = 'PUT id: ' + str(staffID) + ' | nama: ' + staffUsername + ' | staffPassword: ' + staffPassword + ' | role: ' + str(role)
        logging.warning("Received: %r" % messagelog)

        try:
            sql = "SELECT * FROM user_staff"
            dbc.execute(sql)
            data_staff = dbc.fetchall()
            if data_staff != None:
                # kalau data staff ada, juga ambil menu dari staff tsb.
                for x in range(len(data_staff)):
                    staff_username = data_staff[x]['username']
                    if (staff_username == staffUsername):
                        duplicate = True
                        break

            if not duplicate:
                # ubah nama staff dan staffPassword di database
                sql = "UPDATE user_staff set `username`=%s, `password`=%s, `role`=%s where `id`=%s"
                dbc.execute(sql, [staffUsername,hashed_password,role,staffID] )
                db.commit()

                # teruskan json yang berisi perubahan data staff yang diterima dari Web UI
                # ke RabbitMQ disertai dengan tambahan route = 'staff.tenant.changed'
                data_baru = {}
                data_baru['event']  = "updated_staff"
                data_baru['id']     = staffID
                data_baru['username']   = staffUsername
                data_baru['password'] = staffPassword
                data_baru['role'] = role
                jsondoc = json.dumps(data_baru)
                publish_message(jsondoc,'staff.changed')

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
    # Kirimkan JSON yang sudah dibuat ke staff
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp





