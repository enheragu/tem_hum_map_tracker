#!/usr/bin/env python3
# encoding: utf-8

import time
from datetime import datetime

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

import cv2
import base64

import json

from log_config import log_screen
from map_handler import update_data

client = None

def getTimetagNow():
    return datetime.utcnow().strftime('%F %T.%f')[:-3]

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        log_screen("[on_connect] Connection Accepted.", level = "DEBUG")
    elif rc == 1:
        log_screen("[on_connect] Connection Refused. Protocol level not supported.", level = "ERROR")
    elif rc == 2:
        log_screen("[on_connect] Connection Refused. The client-identifier is not allowed by the server.", level = "ERROR")
    elif rc == 3:
        log_screen("[on_connect] Connection Refused. The MQTT service is not available.", level = "ERROR")
    elif rc == 4:
        log_screen("[on_connect] Connection Refused. The data in the username or password is malformed.", level = "ERROR")
    elif rc == 5:
        log_screen("[on_connect] Connection Refused. The client is not authorized to connect.", level = "ERROR")
    else:
        log_screen("[on_connect] Connected With Result Code: {}".format(rc))
      

def on_disconnect(client, userdata, rc):
   log_screen("[on_disconnect] Client Got Disconnected", level = "DEBUG")

# Función que se llama cuando se recibe un mensaje
def on_message(client, userdata, message):
    state = message.payload.decode()
    topic = message.topic
    key = topic.replace("homeassistant/sensor/","").replace("/state","")
    key = key.replace("_temperatura","").replace("_humedad","")

    # no idea where these came from... :)
    if 'temperature_humidity_sensor_' in topic:
        return
    
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


    data_dict = {'sensors': {key: {sensor: {}}}}
    data_dict['sensors'][key][sensor]['topic'] = topic
    data_dict['sensors'][key][sensor]['state'] = float(state)
    data_dict['sensors'][key][sensor]['last_update'] = getTimetagNow()

    update_data(data_new = data_dict)

def subscribe_client(config):
    global client
    client = mqtt.Client()
    client.username_pw_set(config["mqtt_username"], config["mqtt_password"])
    client.on_message = on_message
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    client.connect(config["hostname"], config["mqtt_port"], config["timeout"])
    
    client.subscribe("homeassistant/sensor/+/state")
    
    client.loop_start()


def stop_client():
    global client
    client.loop_stop()
    client.disconnect()


def mqttMapsDispatchMessage(map_temp, map_humid):
    global client
    delay = 5 # Sends a number of messages just in case any is lost

    # Topic and delay setup
    hatype = "camera"
    device_class = None

    topic_discovery_tempperature_map = f"homeassistant/{hatype}/tempperature_map/config"
    topic_discovery_humidity_map = f"homeassistant/{hatype}/humidity_map/config"
    state_topic_tempperature_map = f"homeassistant/{hatype}/tempperature_map/file"
    state_topic_humidity_map = f"homeassistant/{hatype}/humidity_map/file"

    payload_tempperature_map = {
        "name": "Mapa temperatura",
        "unique_id": 'temperature_map',
        "image_encoding": "b64",
        "topic": state_topic_tempperature_map
    }
    
    payload_humidity_map = {
        "name": "Mapa humedad",
        "unique_id": 'humidity_map',
        "image_encoding": "b64",
        "topic": state_topic_humidity_map
    }

    client.publish(topic_discovery_tempperature_map, json.dumps(payload_tempperature_map))
    client.publish(topic_discovery_humidity_map, json.dumps(payload_humidity_map))
    
    # Encode images in Jpeg and send them as text
    _, temperature_map = cv2.imencode('.jpg', map_temp)
    temperature_map = base64.b64encode(temperature_map).decode('utf-8')

    _, humidity_map = cv2.imencode('.jpg', map_humid)
    humidity_map = base64.b64encode(humidity_map).decode('utf-8')

    result1, mid = client.publish(state_topic_tempperature_map, temperature_map)
    result2, mid = client.publish(state_topic_humidity_map, humidity_map)
    
    if result1 == 0 and result2 == 0:
        log_screen(f"Successfully sent payload and messages ({mid = })", level = "DEBUG")