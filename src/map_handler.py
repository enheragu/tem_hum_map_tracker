#!/usr/bin/env python3
# encoding: utf-8

import os

import numpy as np
import scipy.interpolate
import cv2

import matplotlib.pyplot as plt

from yaml_utils import parseYaml,dumpYaml
from log_config import log_screen

data_dict = None
heatmap_dict = {}
original_image = None
default_map_config_path = "./../config/map_config.yaml"
default_media_path = "./../media/"
default_map_path = f"{default_media_path}map.png"

range_configuration = {
    'temperatura': {'range': [25,30], 'units': "deg", 'colormap':cv2.COLORMAP_TURBO},
    # Inverted colormap for humidity, its nicer :)
    'humedad': {'range': [25,30], 'units': '%', 'colormap': cv2.applyColorMap(np.arange(256, dtype=np.uint8),cv2.COLORMAP_WINTER)[::-1]}
}

def setup_map_cfg_path(map_config):
    global default_map_config_path, data_dict
    default_map_config_path = map_config

    if data_dict is None:
        data_dict = parseYaml(default_map_config_path)

def update_dict(base_dict, new_dict):
    for clave, valor in new_dict.items():
        if isinstance(valor, dict):
            base_dict[clave] = update_dict(base_dict.get(clave, {}), valor)
        else:
            base_dict[clave] = valor
    return base_dict

def update_data(data_new):
    global default_map_config_path
    global data_dict

    update_dict(data_dict, data_new)
    dumpYaml(default_map_config_path, data_dict)


def plotOriginalData(img, positions, values, units = ""):
    # Convertir datos de posiciones y temperaturas a formato adecuado para OpenCV
    x = np.array([pos[0] for pos in positions.values()], dtype=int)
    y = np.array([pos[1] for pos in positions.values()], dtype=int)
    sensor_values = np.array([values[sensor] for sensor in positions.keys()])
    sensor_labels = list(positions.keys())

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
        text = f'{sensor_values[i]:.1f}'
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



def load_temperature_heatmaps(media_path):
    global heatmap_dict, original_image
    global default_media_path, default_map_path

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
            heatmap_files_path.append(os.path.join(media_path+file))
    
    for heatmap_path in heatmap_files_path:
        key = heatmap_path.split('/')[-1].replace('map_','').replace('.png',"")
        heatmap_dict[key] = cv2.imread(heatmap_path, cv2.IMREAD_GRAYSCALE)


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

def update_map(sensor_data_key = 'temperatura', display_debug = False):
    global heatmap_dict, original_image, data_dict, temperature_range
    final_scaling = 4

    positions = {}
    values = {}
    for sensor_key, sensor_data in data_dict['sensors'].items():
        positions[sensor_key] = [sensor_data['position_px'][0]*final_scaling,
                                 sensor_data['position_px'][1]*final_scaling,
                                 sensor_data['position_px'][2]*final_scaling]
        values[sensor_key] = sensor_data[sensor_data_key]['state']


    first_heatmap = next(iter(heatmap_dict.values()))
    integrated_heatmap = np.zeros_like(first_heatmap, dtype=float)

    # Accumulates numerator and denominator to be averaged later
    num = np.zeros_like(first_heatmap, dtype=float)
    dem = np.zeros_like(first_heatmap, dtype=float)

    for sensor_key, sensor_data in data_dict['sensors'].items():
        value = sensor_data[sensor_data_key]['state']
        heatmap = heatmap_dict[sensor_key].copy().astype(float)
        # Power is applied to enhance influence of the sensor in its proximal area
        num = num + (heatmap**5)*value
        dem = dem + (heatmap**5)

        # num = rescaleChannel(num, np.max(num), 255)
        # dem = rescaleChannel(dem, np.max(dem), 255)
        # cv2.imshow(f'Heatmap {sensor_key}; state: {value}', heatmap_dict[sensor_key])
        # cv2.imshow(f'num {sensor_key}; state: {value}', num)
        # cv2.imshow(f'dem {sensor_key}; state: {value}', dem)
        # break

    
    integrated_heatmap = np.divide(num, dem, out=np.zeros_like(num), where=dem != 0)
    
    # cv2.imshow(f'Divided {sensor_data_key}', integrated_heatmap)

    gray_image = original_image
    if gray_image.shape != integrated_heatmap.shape:
        gray_image = cv2.resize(gray_image, (integrated_heatmap.shape[1], integrated_heatmap.shape[0]))
    
    # Dilate to ensure lines are a bit thicker
    kernel = np.ones((3, 3), np.uint8)
    gray_image = cv2.erode(gray_image, kernel, iterations=1)
    
    # plt.figure("Before rescalation")
    # plt.imshow(integrated_heatmap)
    # plt.colorbar()

    min_temp = min(values.values())-1
    max_temp = max(values.values())+1

    # integrated_heatmap = rescaleChannel(integrated_heatmap, np.max(integrated_heatmap), 255)
    integrated_heatmap, min_value, max_value = rescale_channel_minmax(channel=integrated_heatmap, 
                                                min_value=min_temp, #temperature_range[0], 
                                                max_value=max_temp, #temperature_range[1],
                                                new_min = 0, new_max=255,
                                                mask = gray_image)

    # plt.figure("After rescalation")
    # plt.imshow(integrated_heatmap)
    # plt.colorbar()

    # plt.show()

    integrated_heatmap = cv2.applyColorMap(integrated_heatmap, range_configuration[sensor_data_key]['colormap'])
    integrated_heatmap[gray_image<127] = (0,0,0)
    

    integrated_heatmap = cv2.resize(integrated_heatmap, (integrated_heatmap.shape[1]*final_scaling, integrated_heatmap.shape[0]*final_scaling))
    integrated_heatmap = plotOriginalData(integrated_heatmap,positions, values, units=range_configuration[sensor_data_key]['units'])
    
    if display_debug:
        cv2.imshow(f'Heatmap {sensor_data_key}', integrated_heatmap)
        # num = rescaleChannel(num, np.max(num), 255)
        # dem = rescaleChannel(dem, np.max(dem), 255)
        # cv2.imshow(f'num {sensor_data_key}', num)
        # cv2.imshow(f'dem {sensor_data_key}', dem)
        # cv2.imshow(f'Map {sensor_data_key}', gray_image)
        cv2.pollKey()
    
    integrated_heatmap = cv2.rotate(integrated_heatmap, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return integrated_heatmap


if __name__ == "__main__":
    while True:
        update_map()