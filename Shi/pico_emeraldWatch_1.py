import json
import os
# Check if necessary libraries are installed, if not, install them
import pyautogui


def get_shutter_position():
    input("Turn on Shutter. Hover your mouse over the BLUE PORTION(!!!) of the 'System Shutter' button and press 'Enter': ")
    return pyautogui.position()

def get_IR_position():
    input("Turn on Laser IR. Hover your mouse over the BLUE PORTION(!!!) of the 'Laser IR 1031nm' button and press 'Enter': ")
    return pyautogui.position()

def get_wavelength_position():
    input("Hover your mouse over the wavelength adjust position, and press 'enter'")
    return pyautogui.position()

def get_power_position():
    input("Hover your mouse over the power adjust position, and press 'enter'")
    return pyautogui.position()

def get_pixel_color(x, y):
    return pyautogui.pixel(x, y)

def save_to_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def main():
    json_file = "pico_emerald_layout.json"
    if os.path.exists(json_file):
        user_choice = input("Update settings on the Shutter position and IR position? (yes/no): ").lower()
        if user_choice == 'yes':
            update_required = True
        else:
            update_required = False
    else:
        update_required = True

    if update_required:
        shutter_position = get_shutter_position()
        shutter_on = get_pixel_color(*shutter_position)
        IR_position = get_IR_position()
        IR_on = get_pixel_color(*IR_position)
        wavelength_position = get_wavelength_position()
        power_position = get_power_position()
        save_to_json(json_file, {
            'shutter_position': shutter_position,
            'shutter_on_color': shutter_on,
            'IR_position': IR_position,
            'IR_on_color': IR_on,
            'wavelength_position': wavelength_position,
            'power_position': power_position
        })

    else:
        config = load_from_json(json_file)
        shutter_position = tuple(config['shutter_position'])
        shutter_on = tuple(config['shutter_on_color'])
        IR_position = tuple(config['IR_position'])
        IR_on = tuple(config['IR_on_color'])
        wavelength_position = tuple(config['wavelength_position'])
        power_position = tuple(config['power_position'])

    print('shutter_position: ' + str(shutter_position),
        'shutter_on_color: ' + str(shutter_on),
        'IR_position: ' + str(IR_position),
        'IR_on_color: ' + str(IR_on))

    
    input("display for information, press 'enter' when you want to exist and finish updating pico emerald layout setting")

def position_getter():
    config = load_from_json("pico_emerald_layout.json")
    shutter_position = tuple(config['shutter_position'])
    shutter_on = tuple(config['shutter_on_color'])
    IR_position = tuple(config['IR_position'])
    IR_on = tuple(config['IR_on_color'])
    wavelength_position = tuple(config['wavelength_position'])
    power_position = tuple(config['power_position'])

def turn_off_IR():
    config = load_from_json("pico_emerald_layout.json")
    IR_position = tuple(config['IR_position'])
    IR_on = tuple(config['IR_on_color'])
    if tuple(get_pixel_color(*IR_position)) == IR_on:
        pyautogui.click(IR_position)

def change_wavelength_to(wavelength):
    config = load_from_json("pico_emerald_layout.json")
    wavelength_position = tuple(config['wavelength_position'])
    pyautogui.click(wavelength_position)
    pyautogui.typewrite(['backspace','backspace','backspace','backspace','backspace'], interval = 0.2)
    pyautogui.typewrite(wavelength)
    pyautogui.PAUSE = 0.5
    pyautogui.typewrite('enter')

def change_power_to(power):
    config = load_from_json("pico_emerald_layout.json")
    power_position = tuple(config['power_position'])
    pyautogui.click(power_position)
    pyautogui.typewrite(['backspace','backspace','backspace','backspace','backspace'], interval = 0.2)
    pyautogui.typewrite(str(power))
    pyautogui.PAUSE = 0.5
    pyautogui.typewrite(['enter'])

change_power_to(300)
pyautogui.typewrite(1234)
# this will make sure when the py script is called directly, the above function will run
if __name__ == "__main__":
    main()
