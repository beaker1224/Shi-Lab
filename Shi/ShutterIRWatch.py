import json
import os
# Check if necessary libraries are installed, if not, install them
import pyautogui

import time

def get_shutter_position():
    input("Turn on Shutter. Hover your mouse over the BLUE PORTION(!!!) of the 'System Shutter' button and press 'Enter': ")
    return pyautogui.position()

def get_IR_position():
    input("Turn on Laser IR. Hover your mouse over the BLUE PORTION(!!!) of the 'Laser IR 1031nm' button and press 'Enter': ")
    return pyautogui.position()

def get_pixel_color(x, y):
    return pyautogui.pixel(x, y)

def save_to_json(file_path, data):
    with open(file_path, 'w') as file:
        json.dump(data, file)

def load_from_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def main():
    json_file = 'monitor_config.json'
    if os.path.exists(json_file):
        user_choice = input("Update settings? (yes/no): ").lower()
        if user_choice == 'yes':
            update_required = True
        else:
            update_required = False
    else:
        update_required = True

    if update_required:
        position = get_shutter_position()
        shutter_on = get_pixel_color(*position)
        save_to_json(json_file, {'shutter_position': position, 'shutter_on': shutter_on})
        position = get_IR_position()
        IR_on = get_pixel_color()
        save_to_json(json_file, {'IR_position': position, 'IR_on': IR_on})
    else:
        config = load_from_json(json_file)
        position = config['position']
        shutter_on = tuple(config['shutter_on'])

    print("Monitoring for color change...")

    # Calculate the position of the second pixel
    second_pixel_x, second_pixel_y = position[0] + 150, position[1] + 175
    click_position = (position[0] + 100, position[1] + 270)

    while True:
        current_color = get_pixel_color(*position)
        if current_color != shutter_on:
            second_pixel_color = get_pixel_color(second_pixel_x, second_pixel_y)
            if second_pixel_color == (0, 102, 178):
                pyautogui.click(*click_position)
                print("Windows Update Cancelled")
            pyautogui.click(*position)
            print("Clicked at position:", position)
            
         
        time.sleep(1)

if __name__ == "__main__":
    main()
