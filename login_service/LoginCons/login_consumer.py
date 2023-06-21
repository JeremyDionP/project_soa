import pika, sys, os
import mysql.connector,logging, json
import bcrypt

db = mysql.connector.connect(host="login_service-LoginSQL-1",port='3306', user="root", password="root",database="login_soa")
dbc = db.cursor(dictionary=True)

 
def main():
    def get_message(ch, method, properties, body):

        # Parse json data di dalam 'body' untuk mengambil data terkait event
        data = json.loads(body)
        event = data['event']
        username = data['username']
        password = data['password']
        role = data['role']
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        if (event == 'new_client'):
            clientId = data['client_id']
            sql = "INSERT INTO users (`username`,`password`,`role`, `client_id`) VALUES (%s,%s,%s,%s)"
            dbc.execute(sql, [username,hashed_password,role,clientId] )
            db.commit()
        elif (event == 'new_staff'):
            staffId = data['staff_id']
            sql = "INSERT INTO users (`username`,`password`,`role`, `staff_id`) VALUES (%s,%s,%s,%s)"
            dbc.execute(sql, [username,hashed_password,role,staffId] )
            db.commit()
        if (event == 'updated_client'):
            clientId = data['id']
            sql = "UPDATE users set `username`=%s, `password`=%s, `role`=%s where `client_id`=%s"
            dbc.execute(sql, [username,hashed_password,role,clientId] )
            db.commit()
        elif (event == 'updated_staff'):
            staffId = data['id']
            sql = "UPDATE users set `username`=%s, `password`=%s, `role`=%s where `staff_id`=%s"
            dbc.execute(sql, [username,hashed_password,role,staffId] )
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