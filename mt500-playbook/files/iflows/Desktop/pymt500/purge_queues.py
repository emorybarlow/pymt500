import pika
import sys

queue = 'data'
if len(sys.argv) > 1:
    queue = sys.argv[1]

rabbit_conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
cnt = 0
method_frame, header_frame, body = rabbit_channel.basic_get(queue)
while body:
    cnt += 1
    print cnt
    rabbit_channel.basic_ack(method_frame.delivery_tag) 
    method_frame, header_frame, body = rabbit_channel.basic_get(queue)
rabbit_conn.close()
