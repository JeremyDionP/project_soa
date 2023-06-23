from flask import Flask, render_template, Response as HTTPResponse, request as HTTPRequest
import mysql.connector, json, pika, logging
from event_producer import *
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


@app.route('/event', methods = ['GET'])
def event():
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        auth = HTTPRequest.authorization
        print(auth)
        # Connect to MySQL server with retries
        db = retry_connect("EventSQL", "root", "root", "event_soa")
        dbc = db.cursor(dictionary=True)
        # ambil data event
        sql = "SELECT * FROM events"
        dbc.execute(sql)
        data_event = dbc.fetchall()
        dbc.close()
        db.close()

        if data_event != None:

            status_code = 200  # The request has succeeded
            jsondoc = json.dumps(data_event)

        else: 
            status_code = 404  # No resources found

    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke event
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp


@app.route('/event/<path:id>', methods = ['PUT', 'DELETE'])
def event2(id):
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'DELETE':
        auth = HTTPRequest.authorization
        print(auth)
        id_to_delete = int(id)

        db = retry_connect("EventSQL", "root", "root", "event_soa")
        dbc = db.cursor(dictionary=True)
        try:
            # ambil data order
            sql = "DELETE FROM events WHERE id = %s"
            dbc.execute(sql, [id_to_delete])
            db.commit()
            dbc.close()
            db.close()

            data = {}
            data['event']  = 'delete_event'
            data['id'] = id_to_delete
            message = json.dumps(data)
            publish_message(message,'event.delete')
            status_code = 200  # The request has succeeded
            data_order = {'result': 'Data Berhasil Dihapus'}
            jsondoc = json.dumps(data_order)
            
        except mysql.connector.Error as err:
            data_order = {'result': err}
            jsondoc = json.dumps(data_order)
            status_code = 409  # No resources found


    # ------------------------------------------------------
    # HTTP method = POST
    # ------------------------------------------------------
    elif HTTPRequest.method == 'PUT':
        data = json.loads(HTTPRequest.data)
        event_id = int(id)
        order_id = data['order_id']
        event_type_id = data['event_type_id']
        time_start = data['time_start']
        time_end = data['time_end']
        description = data['description']
        pic = data['pic']

        # Connect to MySQL server with retries
        db = retry_connect("EventSQL", "root", "root", "event_soa")
        dbc = db.cursor(dictionary=True)
        try:
            # ubah nama client dan clientPassword di database
            sql = "UPDATE events set `order_id`=%s, `event_type_id`=%s, `time_start`=%s, `time_end`=%s, `description`=%s, `pic`=%s where `id`=%s"
            dbc.execute(sql, [order_id,event_type_id,time_start,time_end,description,pic,event_id] )
            db.commit()

            data_error = {"result": "Data berhasil diubah"}
            jsondoc = json.dumps(data_error)
            status_code = 200
        # bila ada kesalahan saat ubah data, buat XML dengan pesan error
        except mysql.connector.Error as err:
            status_code = 409
            data_error = {"error": str(err)}
            jsondoc = json.dumps(data_error)



    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp

@app.route('/event/type', methods = ['POST'])
def addType():
    jsondoc = ''

    # ------------------------------------------------------
    # HTTP method = POST
    # ------------------------------------------------------
    if HTTPRequest.method == 'POST':
        data = json.loads(HTTPRequest.data)
        event_type = data['event_type']
        

        # Connect to MySQL server with retries
        db = retry_connect("EventSQL", "root", "root", "event_soa")
        dbc = db.cursor(dictionary=True)
        try:    

            sql = "INSERT INTO `event_type` (`type`) VALUES (%s)"
            dbc.execute(sql, [event_type])

                    
            # Commit the transaction if all insertions are successful
            db.commit()

            data_baru = {}
            data_baru['event']  = "new_type"
            data_baru['event_type']   = event_type
            jsondoc = json.dumps(data_baru)
            publish_message(jsondoc,'event.type.new')

            result = {'result':"Success"}
            jsondoc = json.dumps(result)
            status_code = 201

        except Exception as e:
            result = {'result': e}
            jsondoc = json.dumps(result)
            status_code = 409

        dbc.close()
        db.close()



    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke event
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp


@app.route('/event/type/<path:id>', methods = ['PUT', 'DELETE'])
def type(id):
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = PUT
    # ------------------------------------------------------
    if HTTPRequest.method == 'PUT':
        data = json.loads(HTTPRequest.data)
        event_type = data['event_type']
        typeID = int(id)

        db = retry_connect("EventSQL", "root", "root", "event_soa")
        dbc = db.cursor(dictionary=True)

        try:
            # ubah nama event dan eventPassword di database
            sql = "UPDATE event_type set `type`=%s where `id`=%s"
            dbc.execute(sql, [event_type,typeID] )
            db.commit()

            # teruskan json yang berisi perubahan data event yang diterima dari Web UI
            # ke RabbitMQ disertai dengan tambahan route = 'event.tenant.changed'
            data_baru = {}
            data_baru['event']  = "updated_type"
            data_baru['id']     = typeID
            data_baru['event_type']   = event_type
            jsondoc = json.dumps(data_baru)
            publish_message(jsondoc,'event.type.change')

            status_code = 200

            
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

        db = retry_connect("EventSQL", "root", "root", "event_soa")
        dbc = db.cursor(dictionary=True)
        try:
            # ambil data order
            sql = "DELETE FROM event_type WHERE id = %s"
            dbc.execute(sql, [id_to_delete])
            db.commit()
            dbc.close()
            db.close()

            data = {}
            data['event']  = 'delete_type'
            data['id'] = id_to_delete
            message = json.dumps(data)
            publish_message(message,'event.type.delete')

            status_code = 200  # The request has succeeded
            data_order = {'result': 'Data Berhasil Dihapus'}
            jsondoc = json.dumps(data_order)
            
        except mysql.connector.Error as err:
            data_order = {'result': err}
            jsondoc = json.dumps(data_order)
            status_code = 409  # No resources found



    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke event
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp


@app.route('/event/order/<path:id>', methods = ['GET', 'PUT', 'POST'])
def eventOrder(id):
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        if id.isnumeric():
            # ambil data event
            # Connect to MySQL server with retries
            db = retry_connect("EventSQL", "root", "root", "event_soa")
            dbc = db.cursor(dictionary=True)
            sql = "SELECT * FROM events WHERE order_id = %s"
            dbc.execute(sql, [id])
            data_event = dbc.fetchall()
            dbc.close()
            db.close()
            # kalau data event ada, juga ambil menu dari event tsb.
            if data_event != None:
                # sql = "SELECT * FROM event_menu WHERE idresto = %s"
                # dbc.execute(sql, [id])
                # data_menu = dbc.fetchall()
                # data_event['produk'] = data_menu
                jsondoc = json.dumps(data_event)

                status_code = 200  # The request has succeeded
            else: 
                status_code = 404  # No resources found
        else: status_code = 400  # Bad Request


    # ------------------------------------------------------
    # HTTP method = POST
    # ------------------------------------------------------
    elif HTTPRequest.method == 'POST':
        data = json.loads(HTTPRequest.data)
        # Iterate over each item in the list
        if id.isnumeric():
            # Connect to MySQL server with retries
            db = retry_connect("EventSQL", "root", "root", "event_soa")
            dbc = db.cursor(dictionary=True)
            try:    
                # Start a transaction
                db.start_transaction()

                for item in data:
                    if isinstance(item, dict):
                        # Extract the values from the JSON item
                        order_id = id
                        event_type_id = item.get('event_type_id')
                        timeStart = item.get('time_start')
                        timeEnd = item.get('time_end')
                        desc = item.get('description')
                        pic = item.get('pic')

                        # Insert into the SQL table
                        sql = "INSERT INTO events (`order_id`, `event_type_id`, `time_start`, `time_end`, `description`, `pic`) VALUES (%s, %s, %s, %s, %s, %s)"
                        dbc.execute(sql, [order_id, event_type_id, timeStart, timeEnd, desc, pic])

                # Commit the transaction if all insertions are successful
                db.commit()
                result = {'result':"Success"}
                jsondoc = json.dumps(result)
                status_code = 201

            except Exception as e:
                # Roll back the transaction if an error occurs
                db.rollback()
                # Handle the exception
                msg = "An error occurred during database insertion:", str(e)
                result = {'result': msg}
                jsondoc = json.dumps(result)
                status_code = 409

            dbc.close()
            db.close()

            # try:
            #     # # simpan nama event, dan eventPassword ke database
            #     # sql = "INSERT INTO user_event (id,username,password,role) VALUES (%s,%s,%s,%s)"
            #     # dbc.execute(sql, [id,eventUsername,hashed_password,role] )
            #     # db.commit()
            #     # # dapatkan ID dari data event yang baru dimasukkan
            #     # eventID = dbc.lastrowid
                # # result = {'result':Berhasil}
                # # jsondoc = json.dumps(data_event)

                # # TODO: Kirim message ke order_service melalui RabbitMQ tentang adanya data event baru


                # status_code = 201
            # # bila ada kesalahan saat insert data, buat XML dengan pesan error
            # except mysql.connector.Error as err:
            #     status_code = 409
        else:
            status_code = 400  # Bad Request


    # ------------------------------------------------------
    # HTTP method = PUT
    # ------------------------------------------------------
    # elif HTTPRequest.method == 'PUT':
        # data = json.loads(HTTPRequest.data)
        # eventUsername = data['username']
        # eventPassword = data['password']
        # # hashed_password = bcrypt.hashpw(eventPassword.encode('utf-8'), bcrypt.gensalt())
        # role = data['role']
        # eventID = int(id)
        # duplicate = False

        # messagelog = 'PUT id: ' + str(eventID) + ' | nama: ' + eventUsername + ' | eventPassword: ' + eventPassword + ' | role: ' + str(role)
        # logging.warning("Received: %r" % messagelog)

        # try:
        #     sql = "SELECT * FROM user_event"
        #     dbc.execute(sql)
        #     data_event = dbc.fetchall()
        #     if data_event != None:
        #         # kalau data event ada, juga ambil menu dari event tsb.
        #         for x in range(len(data_event)):
        #             event_username = data_event[x]['username']
        #             if (event_username == eventUsername):
        #                 duplicate = True
        #                 break

        #     if not duplicate:
        #         # ubah nama event dan eventPassword di database
        #         sql = "UPDATE user_event set `username`=%s, `password`=%s, `role`=%s where `id`=%s"
        #         dbc.execute(sql, [eventUsername,eventPassword,role,eventID] )
        #         db.commit()

        #         # teruskan json yang berisi perubahan data event yang diterima dari Web UI
        #         # ke RabbitMQ disertai dengan tambahan route = 'event.tenant.changed'
        #         data_baru = {}
        #         data_baru['event']  = "updated_tenant"
        #         data_baru['id']     = eventID
        #         data_baru['nama']   = eventUsername
        #         data_baru['password'] = eventPassword
        #         data_baru['role'] = role
        #         jsondoc = json.dumps(data_baru)
        #         publish_message(jsondoc,'event.tenant.changed')

        #         status_code = 200

        #     else:
        #         status_code = 400
        #         data_error = {'error':'Username sudah ada'}
        #         jsondoc = json.dumps(data_error)
        # # bila ada kesalahan saat ubah data, buat XML dengan pesan error
        # except mysql.connector.Error as err:
        #     status_code = 409
        #     data_error = {"error": str(err)}
        #     jsondoc = json.dumps(data_error)


    # ------------------------------------------------------
    # HTTP method = DELETE
    # ------------------------------------------------------




    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke event
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp


@app.route('/status/<path:id>', methods = ['PUT'])
def status(id):
    jsondoc = ''

    # ------------------------------------------------------
    # HTTP method = PUT
    # ------------------------------------------------------
    if HTTPRequest.method == 'PUT':
        data = json.loads(HTTPRequest.data)
        status = data['status']
        # Connect to MySQL server with retries
        db = retry_connect("EventSQL", "root", "root", "event_soa")
        dbc = db.cursor(dictionary=True)
        try:
            
            sql = "UPDATE orders set `status`=%s WHERE id=%s"
            dbc.execute(sql, [status,id])
            db.commit()
            # teruskan json yang berisi perubahan data event yang diterima dari Web UI
            # ke RabbitMQ disertai dengan tambahan route = 'event.tenant.changed'
            data_baru = {}
            data_baru['event']  = "updated_order"
            data_baru['id']     = id
            data_baru['status']   = status
            jsondoc = json.dumps(data_baru)
            publish_message(jsondoc,'order.change')

            status_code = 200
        # bila ada kesalahan saat ubah data, buat XML dengan pesan error
        except mysql.connector.Error as err:
            status_code = 409
            data_error = {"error": str(err)}
            jsondoc = json.dumps(data_error)
        
        dbc.close()
        db.close()

    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke event
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp








