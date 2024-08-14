#!/usr/bin/env python3
# encoding: utf-8

import os
import yaml
from yaml.loader import SafeLoader

from log_config import log_screen

data_dict = None
default_map_config_path = "./../config/map_config.yaml"


def setup_map_cfg_path(map_config):
    global default_map_config_path
    default_map_config_path = map_config

def load_map_config(cfg_file):
    if not os.path.exists(cfg_file):
        log_screen(f"File requested (cfg_file) does not exist.", level = "WARNING", notify = False)
        return {}
    # Parse configuration
    with open(cfg_file) as file:
        data = yaml.load(file, Loader=SafeLoader)
    
    if data is None:
        data = {}

    return data

def dump_map_config(cfg_file, data, mode = "w+"):
    with open(cfg_file, mode) as file:
        yaml.dump(data, file, encoding='utf-8', width=float(5000))
    
def update_dict(base_dict, new_dict):
    for clave, valor in new_dict.items():
        if isinstance(valor, dict):
            base_dict[clave] = update_dict(base_dict.get(clave, {}), valor)
        else:
            base_dict[clave] = valor
    return base_dict

def update_data(key, data):
    global default_map_config_path
    global data_dict

    if data_dict is None:
        data_dict = load_map_config(default_map_config_path)

    data_new = {key: data}
    update_dict(data_dict, data_new)
    
    dump_map_config(default_map_config_path, data_dict)