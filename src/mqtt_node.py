#!/usr/bin/env python3
# encoding: utf-8

from datetime import datetime

import paho.mqtt.client as mqtt
from log_config import log_screen
from map_handler import update_data


def getTimetagNow():
    return datetime.utcnow().strftime('%F %T.%f')[:-3]

# Función que se llama cuando se recibe un mensaje
def on_message(client, userdata, message):
    state = message.payload.decode()
    topic = message.topic
    key = topic.replace("homeassistant/sensor/","").replace("/state","")
    key = key.replace("_temperatura","").replace("_humedad","")

    if not ('temperatura' in topic or 'humedad' in topic):
        return
    
    if not (state != 'unavailable' and state != 'unknown'):
        return 

    if 'temperatura' in topic:
        log_screen(f"[T] Mensaje recibido: {state}º en el tema {topic}")
        sensor = 'temperatura'
    elif 'humedad' in topic:
        log_screen(f"[H] Mensaje recibido: {state}% en el tema {topic}")
        sensor = 'humedad'


    data_dict = {sensor: {}}
    data_dict[sensor]['topic'] = topic
    data_dict[sensor]['state'] = state
    data_dict[sensor]['last_update'] = getTimetagNow()

    update_data(key = key, data = data_dict)

def subscribe_client(config):
    client = mqtt.Client()
    client.username_pw_set(config["mqtt_username"], config["mqtt_password"])
    client.on_message = on_message

    client.connect(config["hostname"], config["mqtt_port"], config["timeout"])
    
    client.subscribe("homeassistant/sensor/+/state")
    
    client.loop_start()


def stop_client():
    client.loop_stop()
    client.disconnect()