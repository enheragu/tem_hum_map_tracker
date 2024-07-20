#!/usr/bin/env python3
# encoding: utf-8

import paho.mqtt.client as mqtt
from log_config import log_screen




# Función que se llama cuando se recibe un mensaje
def on_message(client, userdata, message):
    if 'temperatura' in message.topic:
        log_screen(f"[T] Mensaje recibido: {message.payload.decode()}º en el tema {message.topic}")
    elif 'humedad' in message.topic:
        log_screen(f"[H] Mensaje recibido: {message.payload.decode()}% en el tema {message.topic}")

def subscribeAndLoop(config):
    client = mqtt.Client()
    client.username_pw_set(config["mqtt_username"], config["mqtt_password"])
    client.on_message = on_message

    client.connect(config["hostname"], config["mqtt_port"], config["timeout"])
    
    client.subscribe("homeassistant/sensor/+/state")
    
    client.loop_start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Keyboard Interruption :)")

    client.loop_stop()
    client.disconnect()