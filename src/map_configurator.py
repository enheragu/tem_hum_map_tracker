#!/usr/bin/env python3
# encoding: utf-8

import cv2

from yaml_utils import parseYaml,dumpYaml

map_cfg = "./config/map_config.yaml"
map_im = "./media/map.png"

# Text and circle settings
text_scale = 0.5
text_thickness = 1
text_color = (0,0,0)
circle_radius = 4
circle_color = (0, 0, 255)
prev_color = (255,255,0)

items = parseYaml(map_cfg)
image = cv2.imread(map_im)
image_original = image.copy()


def ask_yes_no(question):
    """
    Asks a yes/no question and returns True for yes and False for no.
    """
    while True:
        response = input(f"{question} (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("Please answer with 'yes' or 'no'.")

          
for key in items.keys():
    if 'position' not in items[key]:
        items[key]['position'] = [None, None, None]
    else:
        items[key]['position'] = list(items[key]['position'])


def click_event(event, x, y, flags, param):
    global current_item_index, items, item_keys, image, positioning_printed
    if event == cv2.EVENT_LBUTTONDOWN:
        item_key = item_keys[current_item_index]
        items[item_key]['position'][0] = x
        items[item_key]['position'][1] = y
        current_item_index += 1
        positioning_printed = False
    if event == cv2.EVENT_RBUTTONDOWN:
        item_key = item_keys[current_item_index]
        items[item_key]['position'][0] = None
        items[item_key]['position'][1] = None
        current_item_index += 1
        positioning_printed = False

# Initialize the index of the current item
current_item_index = 0
item_keys = list(items.keys())
positioning_printed = False

# Create the window before setting the mouse callback
cv2.namedWindow("Image")
cv2.setMouseCallback("Image", click_event)

while current_item_index < len(item_keys):
    if current_item_index > 0:
        prev_item_key = item_keys[current_item_index-1]
        x,y,_ = items[prev_item_key]['position']
        if x is not None and y is not None:
            cv2.circle(image_original, (x, y), circle_radius, circle_color, -1)
            cv2.putText(image_original, f"{prev_item_key} ({x},{y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_color, text_thickness, cv2.LINE_AA)
        
    image = image_original.copy()
    item_key = item_keys[current_item_index]
    if not positioning_printed:
        print(f"Positioning: {item_key}. \t\t\tPress n/N to jump to next or q/Q/Esc to exit")
        positioning_printed = True
    
    # If has already configured position
    x,y,_ = items[item_key]['position']
    if x is not None and y is not None:
        cv2.circle(image, (x, y), circle_radius, prev_color, -1)
        cv2.putText(image, f"{item_key} ({x},{y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, text_scale, prev_color, text_thickness, cv2.LINE_AA)
    

    cv2.putText(image, f"Click position for: {item_key}", (5,14), cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_color, text_thickness, cv2.LINE_AA)
    cv2.imshow("Image", image)

    key = cv2.waitKey(1) & 0xFF
    if key in [ord('q'), ord('Q'), 27]:  # 27 is the ASCII code for Esc
        break
    elif key in [ord('n'), ord('n')]:
        current_item_index += 1
        positioning_printed = False


if ask_yes_no("Do you want to setup Z coordinates?"):
    for item_key in item_keys:
        if items[item_key]['position'][0] is not None and items[item_key]['position'][1] is not None:
            z = input(f"Enter the Z coordinate (cm) for {item_key} (leave blank for None): ")
            z = int(z) if z else None
            items[item_key]['position'] = (items[item_key]['position'][0], items[item_key]['position'][1], z)

for key, item in items.items():
    print(f"{key}: {item['position']}")

dumpYaml(map_cfg,items)

cv2.destroyAllWindows()