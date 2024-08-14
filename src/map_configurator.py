#!/usr/bin/env python3
# encoding: utf-8

import os
import yaml
from yaml.loader import SafeLoader
import cv2

from main import getYAMLConfig

map_cfg = "/home/pi/temperature_map/config/map_config.yaml"
map_im = "/home/pi/temperature_map/media/map.png"

# Text and circle settings
text_scale = 0.25
text_thickness = 1
text_color = (255, 255, 255)
circle_radius = 4
circle_color = (0, 0, 255)


items = getYAMLConfig(map_cfg)

for key in items.keys():
    if 'position' not in items[key]:
        items[key]['position'] = [None, None, None]

def click_event(event, x, y, flags, param):
    global current_item_index, items, item_keys, image, positioning_printed
    if event == cv2.EVENT_LBUTTONDOWN:
        item_key = item_keys[current_item_index]
        z = input(f"Enter the Z coordinate for {item_key} (leave blank for None): ")
        z = z if z else None
        items[item_key]['position'] = (x, y, z)
        cv2.circle(image_original, (x, y), circle_radius, circle_color, -1)
        cv2.putText(image_original, f"{item_key} ({x},{y},{z})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_color, text_thickness, cv2.LINE_AA)
        current_item_index += 1
        positioning_printed = False
        cv2.imshow("Image", image_original)

# Load the image
image = cv2.imread(map_im)
image_original = image.copy()

# Initialize the index of the current item
current_item_index = 0
item_keys = list(items.keys())
positioning_printed = False


cv2.imshow("Image", image)
cv2.setMouseCallback("Image", click_event)

while current_item_index < len(item_keys):
    image = image_original.copy()
    item_key = item_keys[current_item_index]
    if not positioning_printed:
        cv2.putText(image, f"Positioning: {item_key}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_color, text_thickness, cv2.LINE_AA)
        cv2.imshow("Image", image)
        print(f"Positioning: {item_key}")
        positioning_printed = True
    key = cv2.waitKey(1) & 0xFF
    if key in [ord('q'), ord('Q'), 27]:  # 27 is the ASCII code for Esc
        break

cv2.destroyAllWindows()

for key, item in items.items():
    print(f"{key}: {item['position']}")
