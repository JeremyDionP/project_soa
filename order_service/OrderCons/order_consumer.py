import pika, sys, os
import mysql.connector,logging, json
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
db = retry_connect("OrderSQL", "root", "root", "order_soa")
dbc = db.cursor(dictionary=True)

def main():
    def get_message(ch, method, properties, body):

        # Parse json data di dalam 'body' untuk mengambil data terkait event
        data = json.loads(body)
        event = data['event']
        if (event == 'new_client'):
            usernameNew = data['username']
            sql = "INSERT INTO clients (`username`) VALUES (%s)"
            dbc.execute(sql, [usernameNew] )
            db.commit()
        if (event == 'updated_client'):
            username = data['username']
            clientId = data['id']
            sql = "UPDATE clients set `username`=%s where `id`=%s"
            dbc.execute(sql, [username,clientId] )
            db.commit()
        if (event == 'updated_order'):
            orderId = data['id']
            status = data['status']
            sql = "UPDATE orders set `status`=%s where `id`=%s"
            dbc.execute(sql, [status,orderId] )
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
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='order.*')
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='client.*')


    # Ambil message dari RabbitMQ (bila ada)
    channel.basic_qos(prefetch_count=1)
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