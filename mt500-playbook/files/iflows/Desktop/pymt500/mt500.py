#!/usr/bin/env python

import configparser
import json
import logging
import pika
import serial
import socket
import time

from datetime import datetime
from uuid import getnode

VERSION='v1.0'

class MT500:
    def __init__(self, config):
        self.fips = config.get('mt500', 'fips')
        self.network_id = config.get('mt500', 'network_id')
        self.heartbeat_interval = config.getint('mt500', 'heartbeat_interval') * 60

        self.consumers = []
        for consumer in config.items('consumers'):
            self.consumers.append(json.loads(consumer[1]))

        self.ser_in = json.loads(config.get('serial', 'in'))
        self.ser_out = json.loads(config.get('serial', 'out'))

        self.hw_addr = ':'.join(("%012X" % getnode())[i:i+2] for i in range(0, 12, 2))

        self.last_hb = 0
        self.serial_read = None
        self.serial_write = None
        self.msg_count = 0

        self.data_queue = 'data'
        self.command_queue = 'command'

        self.setup_logging()
        self.setup_queues()

        self.run()

    def __del__(self):
        self.rabbit_conn.close()

    def setup_logging(self):
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        self.debug_logger = logging.getLogger('debug_logger')
        debug_handler = logging.FileHandler('/var/log/mt500/debug.log')
        debug_handler.setFormatter(formatter)
        self.debug_logger.addHandler(debug_handler)
        self.debug_logger.setLevel(logging.DEBUG)

        self.error_logger = logging.getLogger('error_logger')
        error_handler = logging.FileHandler('/var/log/mt500/error.log')
        error_handler.setFormatter(formatter)
        self.error_logger.addHandler(error_handler)
        self.error_logger.setLevel(logging.ERROR)

        self.data_logger = logging.getLogger('data_logger')
        data_handler = logging.FileHandler('/var/log/mt500/data.log')
        self.data_logger.addHandler(data_handler)
        self.data_logger.setLevel(logging.INFO)

    def setup_queues(self):
        for i in range(0, 5):
            try:
                self.rabbit_conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
                break
            except Exception as e:
                time.sleep(10)
                if i == 5:
                    self.error_logger.error('Failed to open connection to rabbitmq')
                    return

        try:
            self.rabbit_channel = self.rabbit_conn.channel()
            self.rabbit_channel.queue_declare(queue=self.data_queue)
            self.rabbit_channel.queue_declare(queue=self.command_queue)
        except Exception as e:
            self.error_logger.exception('Failed to setup rabbitmq queues')

    def open_serial_in(self):
        try:
            self.serial_read.close()
        except Exception as e:
            pass

        try:
            self.serial_read = serial.Serial(self.ser_in['port'], self.ser_in['baud'], timeout = 0)
        except Exception as e:
            self.error_logger.exception('Failed opening incoming serial port')
            raise

    def open_serial_out(self):
        try:
            self.serial_write.close()
        except Exception as e:
            pass

        try:
            self.serial_write = serial.Serial(self.ser_out['port'], self.ser_out['baud'], timeout = 0)
        except Exception as e:
            self.error_logger.exception('Failed opening outgoing serial port')
            raise

    def decode_iflows(self, data):
        gid = (int(data[2], 16) & 0x01) << 12 | (int(data[1], 16) & 0x3f) << 6 | (int(data[0], 16) & 0x3f)
        data = (int(data[3], 16) & 0x3f) << 5 | (int(data[2], 16) & 0x3f) >> 1

        return (gid, data)

    def send_heartbeat(self):
        global VERSION
        if time.time() - self.last_hb > self.heartbeat_interval:
            now = datetime.now()
            ts = now.strftime('%m/%d/%Y %H:%M:%S')
            heartbeat = '{0},{1},{2},{3},{4},{5}'.format(self.fips,ts,self.msg_count,self.network_id,VERSION,self.hw_addr)
            self.debug_logger.debug('Sending heartbeat: {0}'.format(heartbeat))
            try:
                self.write_data_to_queue(heartbeat)
            except Exception as e:
                pass

            for consumer in self.consumers:
                host = consumer['ip']
                port = int(consumer['port'])
                data_type = consumer['type']

                if data_type == 'server':
                    self.send_data(host, port, heartbeat)

            self.last_hb = time.time()

    def test_connection(self):
        self.debug_logger.debug('testing connection')
        for consumer in self.consumers:
            host = consumer['ip']
            port = int(consumer['port'])

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            try:
                s.connect((host,port))
                s.sendall('connection test'.encode())
                self.write_data_to_queue('Successfully connected to {0}:{1}'.format(host,port))
            except Exception as e:
                self.write_data_to_queue('Failed to connect to {0}:{1}'.format(host,port))
            finally:
                s.close()

    def send_to_consumers(self, record, raw):
        for consumer in self.consumers:
            host = consumer['ip']
            port = int(consumer['port'])
            data_type = consumer['type']

            if data_type == 'server':
                self.send_data(host, port, record)
            elif data_type == 'raw':
                pass
                for byte in raw:
                    self.send_data(host, port, chr(int(byte, 16)))

    def send_to_serial(self, raw):
        if not self.serial_write or not self.serial_write.readable():
            self.open_serial_out()
        for byte in raw:
            self.serial_write.write(byte.encode())

    def read_command_queue(self):
        self.debug_logger.debug('Reading command queue')
        try:
            method_frame, header_frame, body = self.rabbit_channel.basic_get(self.command_queue)
            while body:
                self.rabbit_channel.basic_ack(method_frame.delivery_tag)
                try:
                    command = json.loads(body.decode())
                    self.debug_logger.debug(command)
                except Exception as e:
                    self.error_logger.error('Invalid command')
                    continue

                if command:
                    command_type = command['type']
                    if command_type == 'connection_test':
                        self.test_connection()
                method_frame, header_frame, body = self.rabbit_channel.basic_get(self.command_queue)
        except Exception as e:
            self.error_logger.exception('Failed to read from command queue')

    def write_data_to_queue(self, data):
        try:
            self.rabbit_channel.basic_publish(exchange='',
                                              routing_key=self.data_queue,
                                              body=data)
        except Exception as e:
            self.error_logger.exception('Failed writing {0} to data queue'.format(data))

    def send_data(self, server, port, data):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((server,port))
        except Exception as e:
            self.error_logger.exception('Unable to connect to {0} on port {1}'.format(server, port))
            s.close()
            return

        try:
            s.sendall(data.encode())
        except Exception as e:
            self.error_logger.exception('Failed to send data to {0} on port {1}')
        finally:
            s.close()

    def run(self):
        initial_byte = True
        last_byte = time.time()
        rx_data = []
        self.open_serial_in()
        last_check = datetime.now()
        while True:
            self.send_heartbeat()

            # Only read the command queue every 60 sec
            if (datetime.now() - last_check).seconds > 60:
                last_check = datetime.now()
                self.read_command_queue()

            # Ensure that the serial port is open and readable
            if not self.serial_read.readable():
                self.open_serial_in()

            if self.serial_read.inWaiting() > 0:
                # Allow at most 1 second between each byte
                if not initial_byte and (time.time() - last_byte) > 1000:
                    rx_data = []

                if initial_byte:
                    initial_byte = False

                last_byte = time.time()
                byte = self.serial_read.read(1)
                rx_data.append(byte.hex())
                if len(rx_data) == 4:
                    gid, data =  self.decode_iflows(rx_data)
                    now = datetime.now()
                    record = '{0},{1},{2},{3},{4}'.format(now.strftime('%m/%d/%Y %H:%M:%S'), gid, data, ''.join(rx_data), self.network_id)
                    try:
                        self.write_data_to_queue(record)
                    except:
                        pass
                    self.send_to_consumers(record, rx_data)
                    try:
                        self.send_to_serial(rx_data)
                    except:
                        pass
                    self.data_logger.info(record)
                    self.msg_count += 1
                    rx_data= []


def main():
    config = configparser.RawConfigParser()
    config.read('mt500.conf')
    MT500(config)


if __name__ == '__main__':
    main()
