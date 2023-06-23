import pika, sys, os
import mysql.connector,logging, json
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

# Connect to MySQL server with retries
db = retry_connect("LoginSQL", "root", "root", "login_soa")
dbc = db.cursor(dictionary=True)

 
def main():
    def get_message(ch, method, properties, body):

        # Parse json data di dalam 'body' untuk mengambil data terkait event
        data = json.loads(body)
        event = data['event']
        if (event == 'new_client'):
            username = data['username']
            password = data['password']
            email = data['email']
            role = data['role']
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            clientId = data['client_id']
            sql = "INSERT INTO users (`username`,`email`,`password`,`role`, `client_id`) VALUES (%s,%s,%s,%s,%s)"
            dbc.execute(sql, [username,email,hashed_password,role,clientId] )
            db.commit()
        elif (event == 'new_staff'):
            username = data['username']
            password = data['password']
            email = data['email']
            role = data['role']
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            staffId = data['staff_id']
            sql = "INSERT INTO users (`username`,`email`,`password`,`role`, `staff_id`) VALUES (%s,%s,%s,%s,%s)"
            dbc.execute(sql, [username,email,hashed_password,role,staffId] )
            db.commit()
        if (event == 'updated_client'):
            username = data['username']
            email = data['email']
            clientId = data['id']
            sql = "UPDATE users set `username`=%s,`email`=%s where `client_id`=%s"
            dbc.execute(sql, [username,email,clientId] )
            db.commit()
        elif (event == 'updated_staff'):
            username = data['username']
            email = data['email']
            staffId = data['id']
            sql = "UPDATE users set `username`=%s,`email`=%s where `staff_id`=%s"
            dbc.execute(sql, [username,email,staffId] )
            db.commit()
        if (event == 'password_client'):
            password = data['password']
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            clientId = data['id']
            sql = "UPDATE users set `password`=%s where `client_id`=%s"
            dbc.execute(sql, [hashed_password,clientId] )
            db.commit()
        elif (event == 'password_staff'):
            password = data['password']
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            staffId = data['id']
            sql = "UPDATE users set `password`=%s where `staff_id`=%s"
            dbc.execute(sql, [hashed_password,staffId] )
            db.commit()
        # tampilkan pesan bahwa event sudah diproses
        message = str(event)
        logging.warning("Received: %r" % message)

        # acknowledge message dari RabbitMQsecara manual yang 
        # menandakan message telah selesai diproses
        ch.basic_ack(delivery_tag=method.delivery_tag)



    # buka koneksi ke server RabbitMQ di PetraMQ
    credentials = pika.PlainCredentials('radmin', 'rpass')
    connection = pika.BlockingConnection(pika.ConnectionParameters('ProjectMQ',5672,'/',credentials))
    channel = connection.channel()

    # Buat exchange dan queue
    channel.exchange_declare(exchange='ProjectEX', exchange_type='topic')
    new_queue = channel.queue_declare(queue='', exclusive=True)
    new_queue_name = new_queue.method.queue
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='login.new')
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='login.changed')
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='client.*')
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='staff.*')


    # Ambil message dari RabbitMQ (bila ada)
    channel.basic_qos(prefetch_count=1, global_qos=True)
    channel.basic_consume(queue=new_queue_name, on_message_callback=get_message)
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)