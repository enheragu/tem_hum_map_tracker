

import requests
from datetime import datetime

# File logger
import logging

DEFAULT_LOG_PATH = None
DEFAULT_LOG_TOPIC = None
DEFAULT_LOG_LEVEL = "ALL"

# Stores possible log level with its tag to be sent through ntfy server
LOG_LEVEL = {
             "NOTSET": {"id": 0, "tag": "", "priority": "default"},
             "ALL": {"id": 5, "tag": "white_check_mark", "priority": "default"},
             "DEBUG": {"id": 10, "tag": "white_check_mark", "priority": "default"},
             "INFO": {"id": 20, "tag": "white_check_mark", "priority": "default"},
             "WARNING": {"id": 30, "tag": "warning", "priority": "high"},
             "ERROR": {"id": 40, "tag": "no_entry", "priority": "urgent"}
            }


#####################
# LOGGING FUNCTIONS #
#####################


def configureLogger(LOGGING_FILE_PATH):
    # Logger to store data in a file
    logging.basicConfig(
        format = '[%(asctime)s][%(levelname)s] - %(message)s',
        level  = logging.DEBUG,      # Nivel de los eventos que se registran en el logger
        filename = LOGGING_FILE_PATH, # Fichero en el que se escriben los logs
        filemode = "a",             # a ("append"), en cada escritura, si el archivo de logs ya existe,
                                    # se abre y añaden nuevas lineas.
        force=True
    )

    
"""
    Logging function to print information on screen and save it to file.

    :param msg: str with the message to post.
    :param level: logging level based on LOG_LEVEL.
    :param notify: if set to True a notification is sent to the ntfy topic configured.

    TBD: Check that logging level provided is in line with the expected.
"""
def log_screen(msg, level = "INFO", notify = False):
    global DEFAULT__LOG_TOPIC
    global DEFAULT_LOG_LEVEL

    timestamp = datetime.now().strftime("%Y-%m-%d|%H:%M:%S")
    print(f"[{timestamp}][{level}] {msg}")
    
    # Access logging level by attribute
    getattr(logging, level.lower())(msg)

    # Notification setup    
    if notify:
        if DEFAULT__LOG_TOPIC is None:
            log_screen("No topic was configured to send notifications", level = "WARNING", notify = False)
            return False
        
        log_level = LOG_LEVEL[level]
        # If message log level is lower than configured, no loging is made as notification
        if log_level["id"] < LOG_LEVEL[DEFAULT_LOG_LEVEL]["id"]:
            log_screen("No notification is sent as logging level is below configured", level = "INFO", notify = False)
            return False

        requests.post("https://ntfy.sh/"+str(DEFAULT__LOG_TOPIC),
            data=str(msg).encode(encoding='utf-8'),
            headers={
            "Title": "UMH - Time check in",
            "Priority": log_level["priority"],
            "Tags": log_level["tag"]
        })