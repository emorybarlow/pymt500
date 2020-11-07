import pika
import sys

rabbit_conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
rabbit_conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
rabbit_channel = rabbit_conn.channel()

rabbit_channel.queue_delete(queue='data')
rabbit_channel.queue_delete(queue='command')

rabbit_channel.queue_declare(queue='data', arguments={'x-max-length': 10})
rabbit_channel.queue_declare(queue='command', arguments={'x-max-length': 10})

rabbit_conn.close()
