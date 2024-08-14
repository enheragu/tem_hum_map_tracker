#!/usr/bin/env python3
# encoding: utf-8

import os

from yaml_utils import parseYaml,dumpYaml
from log_config import log_screen

data_dict = None
default_map_config_path = "./../config/map_config.yaml"

def setup_map_cfg_path(map_config):
    global default_map_config_path
    default_map_config_path = map_config

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
        data_dict = parseYaml(default_map_config_path)

    data_new = {key: data}
    update_dict(data_dict, data_new)
    
    dumpYaml(default_map_config_path, data_dict)