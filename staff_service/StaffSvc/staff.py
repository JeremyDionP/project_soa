from flask import Flask, render_template, Response as HTTPResponse, request as HTTPRequest
import mysql.connector, json, pika, logging
from staff_producer import *
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


@app.route('/staff', methods = ['POST', 'GET'])
def staff():
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        auth = HTTPRequest.authorization
        print(auth)

        # Connect to MySQL server with retries
        db = retry_connect("StaffSQL", "root", "root", "staff_soa")
        dbc = db.cursor(dictionary=True)
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
        email = data['email']
        role = data['role']
        duplicate = False
        hashed_password = bcrypt.hashpw(staffPassword.encode('utf-8'), bcrypt.gensalt())

        # Connect to MySQL server with retries
        db = retry_connect("StaffSQL", "root", "root", "staff_soa")
        dbc = db.cursor(dictionary=True)
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
                sql = "INSERT INTO user_staff (`username`,`email`,`password`,`role`) VALUES (%s,%s,%s,%s)"
                dbc.execute(sql, [staffUsername,email,hashed_password,role] )
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
            # Connect to MySQL server with retries
            db = retry_connect("StaffSQL", "root", "root", "staff_soa")
            dbc = db.cursor(dictionary=True)
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
        email = data['email']
        hashed_password = bcrypt.hashpw(staffPassword.encode('utf-8'), bcrypt.gensalt())
        role = data['role']
        staffID = int(id)
        duplicate = False
        
        # Connect to MySQL server with retries
        db = retry_connect("StaffSQL", "root", "root", "staff_soa")
        dbc = db.cursor(dictionary=True)
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
                    if (data_staff[x]['id'] != staffID):
                        if (staff_username == staffUsername):
                            duplicate = True
                            break

            if not duplicate:
                # ubah nama staff dan staffPassword di database
                sql = "UPDATE user_staff set `username`=%s, `email`=%s, `password`=%s, `role`=%s where `id`=%s"
                dbc.execute(sql, [staffUsername,email,hashed_password,role,staffID] )
                db.commit()

                # teruskan json yang berisi perubahan data staff yang diterima dari Web UI
                # ke RabbitMQ disertai dengan tambahan route = 'staff.tenant.changed'
                data_baru = {}
                data_baru['event']  = "updated_staff"
                data_baru['id']     = staffID
                data_baru['username']   = staffUsername
                data_baru['email'] = email
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
        auth = HTTPRequest.authorization
        print(auth)
        id_to_delete = int(id)

        db = retry_connect("StaffSQL", "root", "root", "staff_soa")
        dbc = db.cursor(dictionary=True)
        try:
            # ambil data order
            sql = "DELETE FROM user_staff WHERE id = %s"
            dbc.execute(sql, [id_to_delete])
            db.commit()
            dbc.close()
            db.close()

            data = {}
            data['event']  = 'delete_staff'
            data['id'] = id_to_delete
            message = json.dumps(data)
            publish_message(message,'staff.delete')
            status_code = 200  # The request has succeeded
            data_order = {'result': 'Data Berhasil Dihapus'}
            jsondoc = json.dumps(data_order)
            
        except mysql.connector.Error as err:
            data_order = {'result': err}
            jsondoc = json.dumps(data_order)
            status_code = 409  # No resources found




    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke staff
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp





