from flask import Flask, render_template, Response as HTTPResponse, request as HTTPRequest
import mysql.connector, json, pika, logging
from order_producer import *
import bcrypt
from datetime import date
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

@app.route('/order/client', methods = ['GET'])
def order():
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        auth = HTTPRequest.authorization
        print(auth)
        # Connect to MySQL server with retries
        db = retry_connect("OrderSQL", "root", "root", "order_soa")
        dbc = db.cursor(dictionary=True)
        # ambil data order
        sql = "SELECT * FROM clients"
        dbc.execute(sql)
        data_order = dbc.fetchall()
        dbc.close()
        db.close()


        if data_order != None:
            status_code = 200  # The request has succeeded
            jsondoc = json.dumps(data_order)

        else: 
            status_code = 404  # No resources found


    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke order
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp

@app.route('/order/type', methods = ['GET'])
def order3():
    jsondoc = ''

    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        auth = HTTPRequest.authorization
        print(auth)
        db = retry_connect("OrderSQL", "root", "root", "order_soa")
        dbc = db.cursor(dictionary=True)
        # ambil data order
        sql = "SELECT * FROM event_type"
        dbc.execute(sql)
        data_order = dbc.fetchall()
        dbc.close()
        db.close()


        if data_order != None:
            status_code = 200  # The request has succeeded
            jsondoc = json.dumps(data_order)

        else: 
            status_code = 404  # No resources found


    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke order
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp

@app.route('/order', methods = ['POST', 'GET'])
def order4():
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        auth = HTTPRequest.authorization
        print(auth)
        db = retry_connect("OrderSQL", "root", "root", "order_soa")
        dbc = db.cursor(dictionary=True)
        # ambil data order
        sql = "SELECT * FROM orders"
        dbc.execute(sql)
        data_order = dbc.fetchall()
        dbc.close()
        db.close()


        if data_order != None:
            status_code = 200  # The request has succeeded
            jsondoc = json.dumps(data_order)

        else: 
            status_code = 404  # No resources found


    # ------------------------------------------------------
    # HTTP method = POST
    # ------------------------------------------------------
    elif HTTPRequest.method == 'POST':
        data = json.loads(HTTPRequest.data)
        clientId = data['client_id']
        eventTypeId = data['event_type_id']
        status = data['status']
        contact = data['contact']
        date = data['date']
        location = data['location']

        try:
            db = retry_connect("OrderSQL", "root", "root", "order_soa")
            dbc = db.cursor(dictionary=True)
            sql = "INSERT INTO orders (`client_id`,`event_type_id`,`status`,`contact`,`date`,`location`) VALUES (%s,%s,%s,%s,%s,%s)"
            dbc.execute(sql, [clientId,eventTypeId,status,contact,date,location] )
            db.commit()
            # dapatkan ID dari data order yang baru dimasukkan
            orderID = dbc.lastrowid
            data_order = {'id':orderID}
            jsondoc = json.dumps(data_order)

            # simpan menu-menu untuk order di atas ke database
            # for i in range(len(data['produk'])):
            #     menu = data['produk'][i]['menu']
            #     price = data['produk'][i]['price']

            #     sql = "INSERT INTO order_menu (idresto,menu,price) VALUES (%s,%s,%s)"
            #     dbc.execute(sql, [orderID,menu,price] )
            #     db.commit()


            # Publish event "new order" yang berisi data order yg baru.
            # Data json yang dikirim sebagai message ke RabbitMQ adalah json asli yang
            # diterima oleh route /order [POST] di atas dengan tambahan 2 key baru,
            # yaitu 'event' dan orderID.
            data['event']  = 'new_order'
            data['order_id'] = orderID
            message = json.dumps(data)
            publish_message(message,'order.new')
            dbc.close()
            db.close()



            status_code = 201
        # bila ada kesalahan saat insert data, buat XML dengan pesan error
        except mysql.connector.Error as err:
            status_code = 409


    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke order
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp





@app.route('/order/<path:id>', methods = ['GET', 'DELETE'])
def order2(id):
    jsondoc = ''


    # ------------------------------------------------------
    # HTTP method = GET
    # ------------------------------------------------------
    if HTTPRequest.method == 'GET':
        if id.isnumeric():
            # ambil data order
            db = retry_connect("OrderSQL", "root", "root", "order_soa")
            dbc = db.cursor(dictionary=True)
            sql = "SELECT * FROM user_order WHERE id = %s"
            dbc.execute(sql, [id])
            data_order = dbc.fetchone()
            # kalau data order ada, juga ambil menu dari order tsb.
            if data_order != None:
                # sql = "SELECT * FROM order_menu WHERE idresto = %s"
                # dbc.execute(sql, [id])
                # data_menu = dbc.fetchall()
                # data_order['produk'] = data_menu
                jsondoc = json.dumps(data_order)

                status_code = 200  # The request has succeeded
            else: 
                status_code = 404  # No resources found
        else: status_code = 400  # Bad Request


    # ------------------------------------------------------
    # HTTP method = DELETE
    # ------------------------------------------------------
    elif HTTPRequest.method == 'DELETE':
        auth = HTTPRequest.authorization
        print(auth)
        id_to_delete = int(id)

        db = retry_connect("OrderSQL", "root", "root", "order_soa")
        dbc = db.cursor(dictionary=True)
        try:
            # ambil data order
            sql = "DELETE FROM orders WHERE id = %s"
            dbc.execute(sql, [id_to_delete])
            db.commit()
            dbc.close()
            db.close()

            data = {}
            data['event']  = 'delete_order'
            data['id'] = id_to_delete
            message = json.dumps(data)
            publish_message(message,'order.delete')
            status_code = 200  # The request has succeeded
            data_order = {'result': 'Data Berhasil Dihapus'}
            jsondoc = json.dumps(data_order)
            
        except mysql.connector.Error as err:
            data_order = {'result': err}
            jsondoc = json.dumps(data_order)
            status_code = 409  # No resources found




    # ------------------------------------------------------
    # Kirimkan JSON yang sudah dibuat ke order
    # ------------------------------------------------------
    resp = HTTPResponse()
    if jsondoc !='': resp.response = jsondoc
    resp.headers['Content-Type'] = 'application/json'
    resp.status = status_code
    return resp









