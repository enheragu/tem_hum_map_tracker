#!/usr/bin/env python3
# encoding: utf-8

import os

# User interface
import argparse
import time


from map_handler import setup_map_cfg_path, update_map, load_temperature_heatmaps
from mqtt_node import subscribe_client, stop_client, mqttMapsDispatchMessage
from log_config import DEFAULT_LOG_PATH, DEFAULT_LOG_TOPIC, DEFAULT_LOG_LEVEL, configureLogger, log_screen
from yaml_utils import parseYaml

"""
    Gets user arguments and parses configuration file to check that input data is valid. Sets up 
    global variables used in the rest of the script.

    :return: returns user input parsed along with user name and password from configuration file

    TBD: add logging level option to be configurable
"""
def getUserOptionsAndSetup():
    global DEFAULT_LOG_TOPIC, DEFAULT_LOG_PATH

    ## Parse arguments and set them to be used
    parser = argparse.ArgumentParser(description='This script monitors a given web page to extract energy prices and send them through MQTT to a Home Assistant Broker')
    parser.add_argument('-cfg', '--config', default = "./../config/config.yaml", help="Configuration file with user and topic. Default is set to config.yaml in config folder.")
    parser.add_argument('-mcfg', '--map_config', default = "./../config/map_config.yaml", help="Configuration file with user and topic. Default is set to config.yaml in config folder.")
    parser.add_argument('-mpath', '--media_path', default = "./../media", help="Path of map folder.")
    
    user_input = vars(parser.parse_args())
    
    # Parse configuration
    data = parseYaml(user_input["config"])
    DEFAULT_LOG_TOPIC = data["ntfy_topic"]
    DEFAULT_LOG_PATH = data["log_path"]
    LOGGING_FILE_PATH = data["log_path"] + "/map_generation_log.log"

    log_screen(f"Notifications will be sent to '{DEFAULT_LOG_TOPIC}' topic", level = "DEBUG")
    log_screen(f"Logging will be stored in {LOGGING_FILE_PATH}", level = "DEBUG")

    # Check that log path is valid
    if not os.path.exists(data["log_path"]):
        raise IOError(f'Log path does not exist: {data["log_path"]}')

    configureLogger(LOGGING_FILE_PATH)

    return data, user_input["map_config"], user_input['media_path']


##############
#### MAIN ####
##############

if __name__ == "__main__":
    log_screen("Parse user options", level = "INFO")
    data, map_config, media_path = getUserOptionsAndSetup()

    setup_map_cfg_path(map_config)
    subscribe_client(data)
    load_temperature_heatmaps(media_path)
    
    time.sleep(5) # Let it rest a bit
    try:
        while True:
            temperatura_map = update_map('temperatura')
            humedad_map = update_map('humedad')

            mqttMapsDispatchMessage(temperatura_map, humedad_map)
            time.sleep(300) # Let it rest a bit
            
    except KeyboardInterrupt:
        print("Keyboard Interruption :)")
        
    stop_client()
    log_screen("Finished dispatching messages", level = "INFO")