#!/usr/bin/env python3
# encoding: utf-8

import os

# import sparse,
import numpy as np
import threading 
import cv2

import matplotlib.pyplot as plt
from datetime import datetime, timedelta

from yaml_utils import parseYaml,dumpYaml
from log_config import log_screen

config_dict = None
data_dict = None
heatmap_dict = {}
original_image = None
denominator_heatmap = None
default_map_config_path = "./../config/map_config.yaml"
default_map_data_path = "./../config/map_data.yaml"
default_media_path = "./../media/"
default_map_path = f"{default_media_path}map.png"

# Min delay. If sensor data is older than X min from now it is discarded and
# shown as an error
max_time_sensor_min = 10
lock = threading.Lock()

range_configuration = {
    'temperatura': {'range': [25,30], 'units': "deg", 'colormap':cv2.COLORMAP_TURBO},
    # Inverted colormap for humidity, its nicer :)
    'humedad': {'range': [25,30], 'units': '%', 'colormap': cv2.applyColorMap(np.arange(256, dtype=np.uint8),cv2.COLORMAP_WINTER)[::-1]}
}

def setup_map_cfg_path(map_config):
    global default_map_config_path, default_map_data_path, data_dict, config_dict

    log_screen(f"Initialize configuration from {map_config}", level = "INFO", notify = False)

    default_map_config_path = map_config
    default_map_data_path = os.path.join(os.path.dirname(map_config), 'map_data.yaml')

    with lock:
        if config_dict is None:
            config_dict = {}
        parsed_data = parseYaml(default_map_config_path)
        update_dict(config_dict, parsed_data)


        if data_dict is None:
            data_dict = {}
        parsed_data = parseYaml(default_map_data_path)
        update_dict(data_dict, parsed_data)
        update_dict(data_dict, config_dict)

def update_dict(base_dict, new_dict):
    if new_dict is not None:
        for clave, valor in new_dict.items():
            if isinstance(valor, dict):
                base_dict[clave] = update_dict(base_dict.get(clave, {}), valor)
            else:
                base_dict[clave] = valor
    return base_dict

def update_data(data_new):
    global default_map_data_path
    global data_dict

    with lock:
        update_dict(data_dict, data_new)
    dumpYaml(default_map_data_path, data_dict)

def get_data_dict():
    global data_dict

    with lock:
        if data_dict is not None:
            data = data_dict.copy()
            return data
        else:
            data_dict = {}
            return {}


def plotOriginalData(img, positions, values, units = ""):
    # Convertir datos de posiciones y temperaturas a formato adecuado para OpenCV
    x = np.array([pos[0] for pos in positions.values()], dtype=int)
    y = np.array([pos[1] for pos in positions.values()], dtype=int)
    sensor_values = [values[sensor_label] for sensor_label in positions.keys() if sensor_label in values]
    sensor_labels = [sensor_label for sensor_label in positions.keys() if sensor_label in values]

    # Copiar la imagen para no modificar la original
    output_img = img.copy()

    # Definir parámetros para la visualización
    point_color = (0,0,0)  # Rojo en formato BGR
    circunference_color = (0,0,255)  # Rojo en formato BGR
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2
    font_color = (255,255,255)  # Blanco en formato BGR
    font_thickness = 3

    # Dibujar los puntos y etiquetas
    for i, label in enumerate(sensor_labels):
        # Dibujar el punto
        # cv2.circle(output_img, (x[i], y[i]), point_radius, point_color, -1)
        
        # Agregar la etiqueta de temperatura
        text = f'{float(sensor_values[i]):.1f}' if not isinstance(sensor_values[i], str) else 'N/A'
        text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
        text_x = x[i] - text_size[0]//2
        text_y = y[i] - text_size[1]//2


        text2 = f'{units}'
        text_size2, _ = cv2.getTextSize(text2, font, font_scale, font_thickness)
        text_x2 = x[i] - text_size2[0]//2
        text_y2 = y[i] + text_size2[1]//2 + text_size[1]
        
        point_rad = int(max(text_size[0],text_size[1])*0.8)
        cv2.circle(output_img, (x[i], y[i]), point_rad-1, point_color, thickness=-1)
        cv2.circle(output_img, (x[i], y[i]), point_rad+1, circunference_color, thickness=5)
        cv2.putText(output_img, text, (text_x, text_y), font, font_scale, font_color, font_thickness)
        cv2.putText(output_img, text2, (text_x2, text_y2), font, font_scale, font_color, font_thickness)
        
    return output_img

def load_temperature_heatmaps(media_path, display_debug = False):
    global heatmap_dict, original_image
    global default_media_path, default_map_path
    global denominator_heatmap

    log_screen(f"Updating heatmap templates from {media_path}:", level = "INFO", notify = False)
    if media_path is not None:
        default_media_path = media_path
    else:
        media_path = default_media_path

    default_map_path = f"{media_path}/map.png"

    original_image = cv2.imread(default_map_path, cv2.IMREAD_GRAYSCALE)

    heatmap_files_path = []
    for file in os.listdir(media_path):
        if file.startswith('map_') and file.endswith('.png') and\
           'debug' not in file:
            heatmap_files_path.append(os.path.join(media_path,file))
    
    for heatmap_path in heatmap_files_path:
        key = heatmap_path.split('/')[-1].replace('map_','').replace('.png',"")
        log_extra = " as cv image."
        heatmap_dict[key] = cv2.imread(heatmap_path, cv2.IMREAD_GRAYSCALE)
        # heatmap_dict[key] = np.load(heatmap_path)

        # log_extra = "as np array."
        ## Right now sparse takes more memory in the end in the whole program.
        ## Wait to check when more maps have much black parts
        # if heatmap_dict[key].nbytes>sparse.COO(heatmap_dict[key]).nbytes:
        #     heatmap_dict[key] = sparse.COO(heatmap_dict[key])
        #     log_extra = "as sparse array."
        

        log_screen(f"\t· Parsed {key} heatmap {log_extra}", level = "INFO", notify = False)


    if display_debug:
        cv2.imshow(f"Heatmap {log_extra}: {next(iter(heatmap_dict.keys()))}",next(iter(heatmap_dict.values())))
        plt.figure(f"Heatmap {log_extra}: {next(iter(heatmap_dict.keys()))}")
        plt.imshow(next(iter(heatmap_dict.values())))
        plt.colorbar()

    # denominator_heatmap = np.load(os.path.join(media_path,'denominator.npy'))

    for sensor_key in get_data_dict()['sensors'].keys():
        if sensor_key not in heatmap_dict:
            log_screen(f"Sensor key from config could not find the heatmap for the integration: {sensor_key}", level = "WARN", notify = False)

def rescaleChannel(channel, max_value, new_max):
    channel = new_max * (channel / max_value)
    channel = channel.astype(np.uint8)
    return channel

def rescale_channel_minmax(channel, min_value=None, max_value=None, new_min=0, new_max=255, mask=None):
    channel_rescaled = channel.copy().astype(np.float32)
    
    if mask is not None:
        mask_index = mask > 0
    else:
        mask_index = np.ones(channel_rescaled.shape, dtype=bool)

    if min_value is None:
        min_value = np.min(channel_rescaled[mask_index])    

    if max_value is None:
        max_value = np.max(channel_rescaled[mask_index])   

    # Set average value to masked parts so that they do not interfere later
    average = np.average(channel_rescaled[mask_index])
    channel_rescaled[~mask_index] = average

    channel_rescaled = (channel_rescaled - min_value) / (max_value - min_value)  # Normalize a [0, 1]
    channel_rescaled = channel_rescaled * (new_max - new_min) + new_min          # Escalar a [new_min, new_max]
        
    # Asegurarse de que los valores estén dentro del rango [new_min, new_max]
    channel_rescaled = np.clip(channel_rescaled, new_min, new_max)
        
    # Convertir de nuevo a uint8 si los nuevos valores están en el rango 0-255
    if new_min >= 0 and new_max <= 255:
        channel_rescaled = channel_rescaled.astype(np.uint8)

    return channel_rescaled, min_value, max_value

def timestampToImage(image):
    text = datetime.now().strftime("%Y-%m-%d | %H:%M:%S")

    # Definir parámetros para la visualización
    background_color = (0,0,0)  # Rojo en formato BGR
    frame_color = (0,0,255)  # Rojo en formato BGR
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2
    font_color = (255,255,255)  # Blanco en formato BGR
    font_thickness = 3

    # Dibujar los puntos y etiquetas
    text_size, _ = cv2.getTextSize(text, font, font_scale, font_thickness)
    text_width, text_height = text_size
    margin = 15
    x = margin*3
    y = image.shape[0] - margin - text_height

    rect_top_left = (x -2, y - text_height - margin -2)
    rect_bottom_right = (x + text_width + margin +2, y + margin +2)

    cv2.rectangle(image, rect_top_left, rect_bottom_right, background_color, thickness=cv2.FILLED)
    cv2.rectangle(image, rect_top_left, rect_bottom_right, frame_color, thickness=2)
    
    cv2.putText(image, text, (x, y), font, font_scale, font_color, font_thickness)
    return image


def update_map(sensor_data_key = 'temperatura', display_debug = False):
    global heatmap_dict, original_image, temperature_range, denominator_heatmap, config_dict
    final_scaling = 4

    positions = {}
    values = {}

    sensor_key_list = [key for key in get_data_dict()['sensors'].keys() if key in config_dict['sensors'].keys() and sensor_data_key in get_data_dict()['sensors'][key]]

    for sensor_key in sensor_key_list:
        positions[sensor_key] = [config_dict['sensors'][sensor_key]['position_px'][0]*final_scaling,
                                config_dict['sensors'][sensor_key]['position_px'][1]*final_scaling,
                                config_dict['sensors'][sensor_key]['position_px'][2]*final_scaling]
        
        time_sensor = get_data_dict()['sensors'][sensor_key][sensor_data_key]['last_update']
        time_sensor = datetime.strptime(time_sensor, '%Y-%m-%d %H:%M:%S.%f')
        current_time = datetime.now()
        if current_time-time_sensor < timedelta(minutes=max_time_sensor_min):
            values[sensor_key] = get_data_dict()['sensors'][sensor_key][sensor_data_key]['state']
        else:
            values[sensor_key] = ' ~~ '
        
    first_heatmap = next(iter(heatmap_dict.values()))
    integrated_heatmap = np.zeros_like(first_heatmap).astype(np.float32)

    # Accumulates numerator and denominator to be averaged later
    num = np.zeros_like(first_heatmap).astype(np.float32)
    denominator_heatmap = np.zeros_like(first_heatmap).astype(np.float32)
    for sensor_key in sensor_key_list:
        time_sensor = get_data_dict()['sensors'][sensor_key][sensor_data_key]['last_update']
        time_sensor = datetime.strptime(time_sensor, '%Y-%m-%d %H:%M:%S.%f')
        current_time = datetime.now()
        if current_time-time_sensor > timedelta(minutes=max_time_sensor_min):
            continue

        value = get_data_dict()['sensors'][sensor_key][sensor_data_key]['state']
        heatmap = heatmap_dict[sensor_key].copy().astype(np.float32)
        num = num + heatmap*value
        denominator_heatmap = denominator_heatmap + heatmap
        
    if display_debug:
        plt.figure("Numerator")
        plt.imshow(num)
        plt.colorbar()
        plt.figure("Denominator")
        plt.imshow(denominator_heatmap)
        plt.colorbar()

    integrated_heatmap = np.divide(num, denominator_heatmap, out=np.zeros_like(num), where=denominator_heatmap != 0)
    del num, denominator_heatmap
    # cv2.imshow(f'Divided {sensor_data_key}', integrated_heatmap)

    gray_image = original_image.copy()
    if gray_image.shape != integrated_heatmap.shape:
        gray_image = cv2.resize(gray_image, (integrated_heatmap.shape[1], integrated_heatmap.shape[0]))
    
    # Dilate to ensure lines are a bit thicker
    kernel = np.ones((3, 3), np.uint8)
    gray_image = cv2.erode(gray_image, kernel, iterations=1)
    
    if display_debug:
        plt.figure("Before rescalation")
        plt.imshow(integrated_heatmap)
        plt.colorbar()

    values_num = [value for value in values.values() if isinstance(value, (int, float))]
    if not values_num:
        return rescale_channel_minmax(integrated_heatmap)
    
    min_temp = min(values_num)-1
    max_temp = max(values_num)+1

    # integrated_heatmap = rescaleChannel(integrated_heatmap, np.max(integrated_heatmap), 255)
    integrated_heatmap, min_value, max_value = rescale_channel_minmax(channel=integrated_heatmap, 
                                                min_value=min_temp, #temperature_range[0], 
                                                max_value=max_temp, #temperature_range[1],
                                                new_min = 0, new_max=255,
                                                mask = gray_image)

    if display_debug:
        plt.figure("After rescalation")
        plt.imshow(integrated_heatmap)
        plt.colorbar()

    integrated_heatmap = cv2.applyColorMap(integrated_heatmap, range_configuration[sensor_data_key]['colormap'])
    integrated_heatmap[gray_image<127] = (0,0,0)
    
    integrated_heatmap = cv2.resize(integrated_heatmap, (integrated_heatmap.shape[1]*final_scaling, integrated_heatmap.shape[0]*final_scaling))
    integrated_heatmap = plotOriginalData(img=integrated_heatmap, positions=positions, values=values, units=range_configuration[sensor_data_key]['units'])
    
    if display_debug:
        cv2.imshow(f'Heatmap {sensor_data_key}', integrated_heatmap)
        cv2.pollKey()
        plt.show()
    
    # integrated_heatmap = cv2.rotate(integrated_heatmap, cv2.ROTATE_90_COUNTERCLOCKWISE)
    integrated_heatmap = timestampToImage(integrated_heatmap)

    return integrated_heatmap


if __name__ == "__main__":
    while True:
        update_map()
