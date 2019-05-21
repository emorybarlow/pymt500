#!/usr/bin/env python

import ConfigParser
import json
import pika

from Tkinter import *
from ttk import *

def check_queue():
    global ui, rabbit_channel
    method_frame, header_frame, body = rabbit_channel.basic_get('data')
    while body:
        insert_record(body)
        rabbit_channel.basic_ack(method_frame.delivery_tag) 
        method_frame, header_frame, body = rabbit_channel.basic_get('data')
    ui.after(5000, check_queue)

def clear_data():
    global data_text
    data_text.delete(1.0,END) 

def test_connection():
    global rabbit_channel
    insert_record('Testing connections')
    command = {'type': 'connection_test', 'data': ''}
    try:
        rabbit_channel.basic_publish(exchange='', routing_key='command', body=json.dumps(command))
    except Exception as e:
        insert_record(str(e))

def insert_record(data):
    global data_text, all_text
    all_text.append(data)
    data_text.insert(END, '{0}\n'.format(data.strip()))
    data_text.see(END)

    if int(data_text.index('end').split('.')[0]) - 2 > 500:
        all_text.pop(0)
        clear_data()
        for line in all_text:
            data_text.insert(END, '{0}\n'.format(line.strip()))
            data_text.see(END)

def on_closing():
    global rabbit_conn
    rabbit_conn.close()

all_text = []

rabbit_conn = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
rabbit_channel = rabbit_conn.channel()
rabbit_channel.queue_declare(queue='data')
rabbit_channel.queue_declare(queue='command')

config = ConfigParser.RawConfigParser()
config.read('mt500.conf')

ui = Tk()
ui.title('MT500')

tabs = Notebook(ui)

data_tab = Frame(tabs)
config_tab = Frame(tabs)

data_text = Text(data_tab, height=20, width=75, borderwidth=3)
data_text.config(font=('consolas', 12), undo=True, wrap='word')
data_text.grid(row=0, column=0, columnspan=3)

test_button = Button(data_tab, text='Test', command=test_connection).grid(row=1, column=0, stick=W, padx=5,pady=10)
clear_button = Button(data_tab, text='Clear', command=clear_data).grid(row=1, column=2, stick=E, pady=10)

data_scroll = Scrollbar(data_tab)
data_scroll.grid(row=0,column=3, sticky='nsew')
data_text['yscrollcommand'] = data_scroll.set

config_label = Label(config_tab, text='Config', font='bold').grid(row=0, column=0, stick=W, padx=5, pady=(10,0))

county_label = Label(config_tab, text='County').grid(row=1, column=0, stick=W, padx=(5,10))
county_data = Label(config_tab, text=config.get('mt500', 'fips')).grid(row=1, column=1, stick=W, padx=(5,10), pady=(10,5))

network_label = Label(config_tab, text='Network ID').grid(row=2, column=0, stick=W, padx=5)
network_data = Label(config_tab, text=config.get('mt500', 'network_id')).grid(row=2, column=1, stick=W, padx=5)

hb_label = Label(config_tab, text='Heartbeat Interval').grid(row=3, column=0, stick=W, padx=5, pady=(5,0))
hb_data = Label(config_tab, text=config.get('mt500', 'heartbeat_interval')+ ' minutes').grid(row=3, column=1, stick=W, padx=5, pady=(5,0))

serin_label = Label(config_tab, text='Serial In').grid(row=4, column=0, stick=W, padx=5, pady=(5,0))
serial_in = json.loads(config.get('serial', 'in'))
serin = '{0}@{1}'.format(serial_in['port'],serial_in['baud'])
serin_data = Label(config_tab, text=serin).grid(row=4, column=1, stick=W, padx=5, pady=(5,0))

serout_label = Label(config_tab, text='Serial Out').grid(row=5, column=0, stick=W, padx=5, pady=(5,0))
serial_out = json.loads(config.get('serial', 'out'))
serout = '{0}@{1}'.format(serial_out['port'],serial_out['baud'])
serout_data = Label(config_tab, text=serout).grid(row=5, column=1, stick=W, padx=5, pady=(5,0))

consumer_label = Label(config_tab, text='Consumers', font='bold').grid(row=6, column=0, stick=W, padx=5, pady=(20,0))

row = 7
consumers = {}
for consumer in config.items('consumers'):
    name = Label(config_tab, text=consumer[0]).grid(row=row, column=0, stick=W, padx=5, pady=(5,0))
    dict = json.loads(consumer[1])
    info = '{0}:{1}, {2}'.format(dict['ip'], dict['port'], dict['type']) 
    consumer_data = Label(config_tab, text=info).grid(row=row, column=1, stick=W, padx=5, pady=(5,0))
    row += 1

tabs.add(data_tab, text='Data')
tabs.add(config_tab, text='Config')
tabs.pack()

check_queue()
ui.mainloop()
