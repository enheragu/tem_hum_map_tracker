#!/usr/bin/env python3
# encoding: utf-8

import os

import threading
import cv2
import numpy as np
import math
from tqdm import tqdm

import multiprocessing
from multiprocessing import Pool

if __name__ == "__main__":
    import sys
    sys.path.append('./src')
    sys.path.append('./src/map_configurator')

from yaml_utils import parseYaml, dumpYaml

map_cfg = "./config/map_config.yaml"
media_path = "./media/"
heatmap_intermediate_path = f"{media_path}/raw_heatmaps/"
map_im = f"{media_path}/map.png"
grid_size_cm = 8

def scale_map(occupancy_map, scale_factor):
    map = occupancy_map.copy()
    new_size = (int(occupancy_map.shape[1] / scale_factor), int(occupancy_map.shape[0] / scale_factor))
       
    # Linear and thresholded to mainain contour widht
    resized_map = cv2.resize(map, new_size, interpolation=cv2.INTER_AREA)
    _, resized_map = cv2.threshold(resized_map, 235, 255, cv2.THRESH_BINARY)

    # cv2.imshow('Original map', occupancy_map)
    # cv2.imshow('Scaled map', resized_map)
    # cv2.waitKey(0)

    return resized_map

def scale_point(point, scale_factor):
    # Redimensionar un punto para coincidir con la escala del mapa
    return (int(point[0] / scale_factor), int(point[1] / scale_factor), int(point[2] / scale_factor))


def parse_image_to_map(image_path):
    # Cargar la imagen en escala de grises
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Umbralizar la imagen para obtener la cuadrícula de ocupación (0: libre, 1: ocupado)
    _, occupancy_grid = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    
    return occupancy_grid



def distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

""""
    key: key of the sensor processed, just for display debug :)
    scale_factor is just for debug display :)
"""
def get_distance_map(map, start_node, distance_between_nodes, key = "", 
                     scale_factor = 1, output_path = "", display = False):
    # Inicializar distancias con infinito
    distances = {}
    
    # Remove Z for now -> x,y,z = start_node
    start = (start_node[1],start_node[0])

    # Inicializar distancias con infinito
    distances_local = { (x, y): float('inf') for y in range(map.shape[1]) for x in range(map.shape[0]) if map[x,y] == 255 }
    distances_local[start] = 0
    
    pending_nodes = []
    pending_nodes.append(start)

    # RGB map for display purposes
    if display:
        display_map_original = map.copy()
        display_map_original = cv2.cvtColor(display_map_original, cv2.COLOR_GRAY2BGR)
        display_map = display_map_original.copy()
        display_map[start] = (255,255,0)
        display_map_resized  = cv2.resize(display_map, (int(display_map.shape[1]*scale_factor),int(display_map.shape[0]*scale_factor)))

    while pending_nodes:
        # if display: Copy outside of loop for accumulative effect
        #     display_map = display_map_original.copy()

        ## Current node the one with less distance
        current_node = min(pending_nodes, key=lambda k: distances_local[k])
        pending_nodes.remove(current_node)

        if map[current_node] == 0:
            print(f"!ERROR! {key} - {current_node = }; {map[current_node] = }")
            continue

        # Obtener vecinos
        neighbors = get_neighbors(current_node, map)
        if neighbors is []:
            break
        
        # Actualizar distancias a los vecinos
        for neighbor in neighbors:
            new_distance = distances_local[current_node] + 1 # If using 8 -> distance(current_node,neighbor) # Increment one pixel
            #distance_between_nodes
            # Adds some epsilon to comparison
            if new_distance < distances_local[neighbor]-new_distance*0.1:
                distances_local[neighbor] = new_distance
                pending_nodes.append(neighbor)
        
        for key_coord, value in distances_local.items():
            if value < distances.get(key_coord, float('inf')):
                distances[key_coord] = value
        
        if display:
            for node in pending_nodes:
                display_map[node] = (0,0,255)
            
            display_map_resized  = cv2.resize(display_map, (int(display_map.shape[1]*scale_factor),int(display_map.shape[0]*scale_factor)))
            cv2.imshow(f'Expansion {key}', display_map_resized)
            cv2.pollKey()
    
    if display:
        cv2.imwrite(output_path, display_map_resized)

    return distances

def get_neighbors(node, map):
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]#, With for seems faster
                  #(1, 1), (1, -1), (-1, -1), (-1, 1)]
    neighbors = []
    x, y = node
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < map.shape[0] and 0 <= ny < map.shape[1] and map[nx, ny] == 255:
            neighbors.append((nx, ny))
    return neighbors


def rescaleChannel(channel, max_value, new_max):
    channel = new_max * (channel / max_value)
    channel = channel.astype(np.uint8)
    return channel

def distances_to_image(distances, occupancy_map):

    max_distance = np.max([float(value) for value in distances.values()]) + 1
    # max_distance = np.max(occupancy_map.shape)
    distance_image = np.full(shape=occupancy_map.shape, fill_value=(max_distance))
    for (x, y), distance in distances.items():
        distance_image[x,y] = distance

    # Invertir los valores del array
    inverted_distance_image = np.max(distance_image) - distance_image
    distance_image = rescaleChannel(inverted_distance_image, max_distance, 255)
    # Convertir la imagen a BGR (de escala de grises) para mostrarla con OpenCV
    distance_image_bgr = cv2.cvtColor(distance_image, cv2.COLOR_GRAY2BGR)
    
    return distance_image_bgr


def find_room_for_point(point, room_masks):
    for i, mask in enumerate(room_masks):
        if mask[point[1], point[0]] == 255:
            return i
    return None


def process_sensor(sensor_data):
    key, data, config_data, scaled_map, map_im, scale_factor, grid_size_cm = sensor_data
    start_point = scale_point(data['position_px'], scale_factor)
    distances = get_distance_map(map=scaled_map, start_node=start_point, distance_between_nodes=grid_size_cm, 
                         key=key, scale_factor=scale_factor, output_path=os.path.join(heatmap_intermediate_path, f'map_{key}_debug.png'))
    distance_image_bgr = distances_to_image(distances, scaled_map)

    # Mostrar la imagen
    resize_factor = scale_factor
    distance_image_bgr  = cv2.resize(distance_image_bgr, (int(distance_image_bgr.shape[1] * resize_factor), int(distance_image_bgr.shape[0] * resize_factor)))
    
    # print(f"Display distance map {key}")
    # cv2.imshow(f'Distance Map {key}', distance_image_bgr)
    # cv2.pollKey()
    
    # Opcionalmente, guardar la imagen en un archivo
    output_path = os.path.join(heatmap_intermediate_path, f'map_{key}.png')
    cv2.imwrite(output_path, distance_image_bgr)
    print(f"Stored heat map in {output_path}")


def propagateHeatmaps():
    global map_cfg, map_im, grid_size_cm

    print("Start heatmap propagation")

    config_data = parseYaml(map_cfg)
    occupancy_map = parse_image_to_map(map_im)

    def cm_to_pixel(value_cm):
        scale = config_data['scale']
        distance_cm = scale['distance_cm']
        distance_pixels = scale['distance_pixels']
        cm_to_pixels = distance_pixels / distance_cm
        return int(value_cm * cm_to_pixels)
    
    def pixel_to_cm(value_pix):
        scale = config_data['scale']
        distance_cm = scale['distance_cm']
        distance_pixels = scale['distance_pixels']
        pixels_to_cm = distance_cm / distance_pixels
        return int(value_pix * pixels_to_cm)

    scale_factor = cm_to_pixel(grid_size_cm)
    scaled_map = scale_map(occupancy_map, scale_factor)


    print("Multiprocess propapagion")
    sensor_data = [(key, data, config_data, scaled_map, map_im, scale_factor, grid_size_cm) for key, data in config_data['sensors'].items()]
    # with Pool(1) as pool: 
    with Pool(multiprocessing.cpu_count()-1) as pool:
        pool.map(process_sensor, sensor_data)

    print("Finished heatmap propagation")

def computePreprocessedHeatmaps():
    heatmap_files_path = []
    for file in os.listdir(heatmap_intermediate_path):
        if file.startswith('map_') and file.endswith('.png') and\
           'debug' not in file:
            heatmap_files_path.append(os.path.join(heatmap_intermediate_path,file))
    
    denominator_heatmap = None

    for heatmap_path in heatmap_files_path:
        heatmap = cv2.imread(heatmap_path, cv2.IMREAD_GRAYSCALE).astype(np.uint16)
        
        if denominator_heatmap is None:
            denominator_heatmap = np.zeros_like(heatmap, dtype=np.uint16)

        # Power is applied to enhance influence of the sensor in its proximal area
        heatmap = (heatmap**2)
        denominator_heatmap = denominator_heatmap + (heatmap**2)

        output_path = heatmap_path.replace(heatmap_intermediate_path,media_path)
        np.save(output_path, heatmap)

    print(f"Computed denominator from heatmaps: {heatmap_files_path}")
    np.save(os.path.join(media_path, 'denominator'), denominator_heatmap)
    


if __name__ == "__main__":
    propagateHeatmaps()
    computePreprocessedHeatmaps()
    cv2.destroyAllWindows()