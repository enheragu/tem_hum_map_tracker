#!/usr/bin/env python3
# encoding: utf-8

import os
import yaml
from yaml.loader import SafeLoader

# User interface
import argparse


from map_handler import setup_map_cfg_path
from mqtt_node import subscribe_client, stop_client
from log_config import DEFAULT_LOG_PATH, DEFAULT_LOG_TOPIC, DEFAULT_LOG_LEVEL, configureLogger, log_screen



####################
# HELPER FUNCTIONS #
####################
"""
    Parses configuration yaml file and returns data dict.
"""
def getYAMLConfig(cfg_file):
    if not os.path.exists(cfg_file):
        log_screen(f"File requested ({cfg_file}) does not exist.", level = "WARNING", notify = False)
        return {}
    # Parse configuration
    with open(cfg_file) as file:
        data = yaml.load(file, Loader=SafeLoader)
        return data
    


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
    user_input = vars(parser.parse_args())
    
    # Parse configuration
    data = getYAMLConfig(user_input["config"])
    DEFAULT_LOG_TOPIC = data["ntfy_topic"]
    DEFAULT_LOG_PATH = data["log_path"]
    LOGGING_FILE_PATH = data["log_path"] + "/energy_script_log.log"

    log_screen(f"Notifications will be sent to '{DEFAULT_LOG_TOPIC}' topic", level = "DEBUG")
    log_screen(f"Logging will be stored in {LOGGING_FILE_PATH}", level = "DEBUG")

    # Check that log path is valid
    if not os.path.exists(data["log_path"]):
        raise IOError(f'Log path does not exist: {data["log_path"]}')

    configureLogger(LOGGING_FILE_PATH)

    return data, user_input["map_config"]


##############
#### MAIN ####
##############

if __name__ == "__main__":
    log_screen("Parse user options", level = "INFO")
    data, map_config = getUserOptionsAndSetup()

    setup_map_cfg_path(map_config)
    subscribe_client(data)
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Keyboard Interruption :)")
        
    stop_client()
    log_screen("Finished dispatching messages", level = "INFO")