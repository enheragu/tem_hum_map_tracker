#!/usr/bin/env python3
# encoding: utf-8

import cv2
import math

if __name__ == "__main__":
    import sys
    sys.path.append('./src')
    sys.path.append('./src/map_configurator')

from yaml_utils import parseYaml, dumpYaml

map_cfg = "./config/map_config.yaml"
map_im = "./media/map.png"

# Text and circle settings
text_scale = 0.5
text_thickness = 1
text_color = (0, 0, 0)
circle_radius = 4
circle_color = (0, 0, 255)
prev_color = (255, 255, 0)

configuration_data = parseYaml(map_cfg)
items = configuration_data['sensors']
image = cv2.imread(map_im)
image_original = image.copy()

# Variables to hold reference points
reference_points = []
distance_cm = None
# Initialize the index of the current item
current_item_index = 0
item_keys = list(items.keys())
positioning_printed = False

# Scale to fit image in screen and be able to point locations and stuff
visualiation_scale = 0.55

cv2.namedWindow("Image", cv2.WINDOW_FULLSCREEN) 

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

def get_distance(p1, p2):
    """
    Calculate the Euclidean distance between two points.
    """
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def click_event(event, x, y, flags, param):
    global current_item_index, items, item_keys, image, positioning_printed, reference_points, distance_cm, visualiation_scale
    if event == cv2.EVENT_LBUTTONDOWN and (flags & cv2.EVENT_FLAG_SHIFTKEY):
        if len(reference_points) < 2:
            reference_points.append((x, y))
            if len(reference_points) == 2:
                # Calculate distance in pixels
                distance_pixels = get_distance(reference_points[0], reference_points[1])
                distance_cm = float(input(f"Enter the real distance between these points (in cm): "))
                print(f"Distance in pixels: {distance_pixels}")
                print(f"Distance in cm: {distance_cm}")
                scale_data = {
                    'distance_pixels': int(distance_pixels*(1-visualiation_scale)),
                    'distance_cm': distance_cm
                }
                configuration_data['scale'] = scale_data
                cv2.line(image_original, reference_points[0], reference_points[1], (0, 255, 0), 2)
                
                visualization = cv2.resize(image_original, (0,0), fx=visualiation_scale, fy=visualiation_scale)
                cv2.imshow("Image", visualization)

        else:
            item_key = item_keys[current_item_index]
            if not 'position_px' in items[item_key]:
                items[item_key]['position_px'] = [None,None,None]
            items[item_key]['position_px'][0] = int(x*(1-visualiation_scale))
            items[item_key]['position_px'][1] = int(y*(1-visualiation_scale))
            current_item_index += 1
            positioning_printed = False
    if event == cv2.EVENT_RBUTTONDOWN and (flags & cv2.EVENT_FLAG_SHIFTKEY):
        item_key = item_keys[current_item_index]
        if not 'position_px' in items[item_key]:
            items[item_key]['position_px'] = [None,None,None]
        items[item_key]['position_px'][0] = None
        items[item_key]['position_px'][1] = None
        current_item_index += 1
        positioning_printed = False



def configureSensorAndMapPosition():
    print("Start map and sensor configuration")
    global image, current_item_index, items, item_keys, image, positioning_printed, reference_points, distance_cm
    global visualiation_scale
    # Create the window before setting the mouse callback
    cv2.namedWindow("Image")
    cv2.setMouseCallback("Image", click_event)

    # Wait for the user to set the reference points
    print("Please select two reference points on the image and provide the real distance between them.")

    while len(reference_points) < 2:  
        visualization = cv2.resize(image, (0,0), fx=visualiation_scale, fy=visualiation_scale)
        cv2.imshow("Image", visualization)
        key = cv2.waitKey(1) & 0xFF
        if key in [ord('q'), ord('Q'), 27]:  # 27 is the ASCII code for Esc
            break

    # Proceed with the rest of the functionality
    print(f"Positioning each sensor. Press:  \
          \n\t· shift+left mouse to select point \
          \n\t· shift+right mouse to left as null \
          \n\t· n/N to jump to next  \
          \n\t· q/Q/Esc to exit")
    while current_item_index < len(item_keys):
        if current_item_index > 0:
            prev_item_key = item_keys[current_item_index - 1]
            x, y, _ = items[prev_item_key]['position_px']
            if x is not None and y is not None:
                cv2.circle(image_original, (x, y), circle_radius, circle_color, -1)
                cv2.putText(image_original, f"{prev_item_key} ({x},{y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_color, text_thickness, cv2.LINE_AA)

        image = image_original.copy()
        item_key = item_keys[current_item_index]
        if not positioning_printed:
            print(f"Positioning: {item_key}. \t\t\tPress n/N to jump to next or q/Q/Esc to exit")
            positioning_printed = True

        if 'position_px' in items[item_key]:
            x, y, _ = items[item_key]['position_px']
            if x is not None and y is not None:
                cv2.circle(image, (x, y), circle_radius, prev_color, -1)
                cv2.putText(image, f"{item_key} ({x},{y})", (x + 10, y), cv2.FONT_HERSHEY_SIMPLEX, text_scale, prev_color, text_thickness, cv2.LINE_AA)

        cv2.putText(image, f"Click position for: {item_key}", (5, 14), cv2.FONT_HERSHEY_SIMPLEX, text_scale, text_color, text_thickness, cv2.LINE_AA)
        
        visualization = cv2.resize(image, (0,0), fx=visualiation_scale, fy=visualiation_scale)
        cv2.imshow("Image", visualization)

        key = cv2.pollKey() & 0xFF
        if key in [ord('q'), ord('Q'), 27]:  # 27 is the ASCII code for Esc
            break
        elif key in [ord('n'), ord('N')]:
            current_item_index += 1
            positioning_printed = False



    def cm_to_pixel(value_cm):
        scale = configuration_data['scale']
        distance_cm = scale['distance_cm']
        distance_pixels = scale['distance_pixels']
        cm_to_pixels = distance_pixels / distance_cm
        return int(value_cm * cm_to_pixels)

    if ask_yes_no("Do you want to setup Z coordinates?"):
        for item_key in item_keys:
            if items[item_key]['position_px'][0] is not None and items[item_key]['position_px'][1] is not None:
                z = input(f"Enter the Z coordinate (cm) for {item_key} (leave blank for None): ")
                z = int(z) if z else None
                items[item_key]['position_z_cm'] = z
                items[item_key]['position_px'] = [items[item_key]['position_px'][0], items[item_key]['position_px'][1], cm_to_pixel(z)]

    for key, item in items.items():
        print(f"{key}: {item['position_px']}")

    configuration_data['sensors'] = items
    dumpYaml(map_cfg, configuration_data)

    print("Finished map and sensor configuration")


if __name__ == "__main__":
    configureSensorAndMapPosition()
    cv2.destroyAllWindows()