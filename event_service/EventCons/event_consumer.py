import pika, sys, os
import mysql.connector,logging, json


db = mysql.connector.connect(host="EventSQL", user="root", password="root",database="event_soa")
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
        if (event == 'new_staff'):
            usernameNew = data['username']
            sql = "INSERT INTO staffs (`username`) VALUES (%s)"
            dbc.execute(sql, [usernameNew] )
            db.commit()
        if (event == 'updated_staff'):
            username = data['username']
            staffId = data['id']
            sql = "UPDATE staffs set `username`=%s where `id`=%s"
            dbc.execute(sql, [username,staffId] )
            db.commit()
        if (event == 'new_order'):
            clientId = data['client_id']
            eventTypeId = data['event_type_id']
            status = data['status']
            contact = data['contact']
            date = data['date']
            location = data['location']
            
            # Insert into orders table
            order_sql = "INSERT INTO orders (`client_id`,`event_type_id`,`status`,`contact`,`date`,`location`) VALUES (%s,%s,%s,%s,%s,%s)"
            dbc.execute(order_sql, [clientId, eventTypeId, status, contact, date, location])
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
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='event.new')
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='event.changed')
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='client.*')
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='staff.*')
    channel.queue_bind(exchange='ProjectEX', queue=new_queue_name, routing_key='order.*')


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