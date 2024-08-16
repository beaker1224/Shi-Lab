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

def get_wavelength_position():
    input("Hover your mouse over the wavelength adjust position, and press 'enter'")
    return pyautogui.position()

def get_power_position():
    input("Hover your mouse over the power adjust position, and press 'enter'")
    return pyautogui.position()

def get_key_position(num):
    """
    Get the position of the mouse cursor based on a keypad input prompt.

    This function displays a prompt message instructing the user to hover their mouse 
    over the specified number and press 'Enter'. It then returns the current mouse cursor 
    position using `pyautogui.position()`.

    Parameters:
    num (str): A string input representing the number on the keypad. The prompt message 
               will indicate the number the user should hover over.

    Returns:
    tuple: A tuple representing the current mouse cursor position (x, y) as integers.

    Example:
    >>> position = get_key_position("5")
    Hover your mouse over the number '5' and press 'Enter'
    >>> print(position)
    (x, y)
    """
    prompt_message = f"Hover your mouse over the number '{num}' and press 'Enter'"
    input(prompt_message)
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
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # Change the working directory to the script's directory
    os.chdir(script_dir)

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


    json_file = "wavelength_power_keypad.json"
    if os.path.exists(json_file):
        user_choice = input("Update settings on the wavelength and power keypad positions? (yes/no): ").lower()
        if user_choice == 'yes':
            update_required = True
        else:
            update_required = False
    else:
        print("now entering wavelength and power number button setup")
        update_required = True

    keys = ("0","1","2","3","4","5","6","7","8","9",".","clear","enter")
    key_positions = {}
    if update_required:

        input("Hover your mouse on the wavelength setting, press 'enter' for next")
        for key in keys:
            key_position = get_key_position(key)
            key_name = f"wavelength_key_{key}"
            key_positions[key_name] = [key_position[0], key_position[1]]

        input("Hover your mouse on the power setting, press 'enter' for next")
        for key in keys:
            key_position = get_key_position(key)
            key_name = f"power_key_{key}"
            key_positions[key_name] = [key_position[0], key_position[1]]

        save_to_json(json_file, key_positions)
    else:
        input("Press 'enter' to quit the update")

    
    input("display for information, press 'enter' when you want to exist and finish updating pico emerald layout setting")
'''
not sure why I wrote this.....

def position_getter():
    pico_emerald_layout = load_from_json("pico_emerald_layout.json")
    shutter_position = tuple(pico_emerald_layout['shutter_position'])
    shutter_on = tuple(pico_emerald_layout['shutter_on_color'])
    IR_position = tuple(pico_emerald_layout['IR_position'])
    IR_on = tuple(pico_emerald_layout['IR_on_color'])
    wavelength_position = tuple(pico_emerald_layout['wavelength_position'])
    power_position = tuple(pico_emerald_layout['power_position'])
'''

def turn_off_IR():
    pico_emerald_layout = load_from_json("pico_emerald_layout.json")
    IR_position = tuple(pico_emerald_layout['IR_position'])
    IR_on = tuple(pico_emerald_layout['IR_on_color'])
    if tuple(get_pixel_color(*IR_position)) == IR_on:
        pyautogui.click(IR_position)

def click(wavelength_power_keypad, type, key):
    """
    Clicks the specified key based on the type and key value.

    Parameters:
    wavelength_power_keypad (dict): The dictionary containing key positions.
    type (str): Must be a string, "wavelength" or "power".
    key (str): The key to click, must be a string representing the key. keys = ("0","1","2","3","4","5","6","7","8","9",".","clear","enter")

    """
    # for wavelength
    if type == "wavelength":
        key_mapping = {
            "0": "wavelength_key_0",
            "1": "wavelength_key_1",
            "2": "wavelength_key_2",
            "3": "wavelength_key_3",
            "4": "wavelength_key_4",
            "5": "wavelength_key_5",
            "6": "wavelength_key_6",
            "7": "wavelength_key_7",
            "8": "wavelength_key_8",
            "9": "wavelength_key_9",
            ".": "wavelength_key_.",
            "clear": "wavelength_key_clear",
            "enter": "wavelength_key_enter"
        }

        key_name = key_mapping.get(key)
        if key_name and key_name in wavelength_power_keypad:
            position = tuple(wavelength_power_keypad[key_name])
            pyautogui.click(position)
        else:
            input(f"Key '{key}' for '{key_name}' not found.")

    # for power
    if type == "power":
        key_mapping = {
            "0": "power_key_0",
            "1": "power_key_1",
            "2": "power_key_2",
            "3": "power_key_3",
            "4": "power_key_4",
            "5": "power_key_5",
            "6": "power_key_6",
            "7": "power_key_7",
            "8": "power_key_8",
            "9": "power_key_9",
            ".": "power_key_.",
            "clear": "power_key_clear",
            "enter": "power_key_enter"
        }

        key_name = key_mapping.get(key)
        if key_name and key_name in wavelength_power_keypad:
            position = tuple(wavelength_power_keypad[key_name])
            pyautogui.click(position)
        else:
            input(f"Key '{key}' for '{key_name}' not found.")



def change_wavelength_to(wavelength):
    """
    ### pass in must be strings of wavelength

    this function intake a string of wavelength, stripe the spaces
    for example, input as "791.3", it will be converted into a tuple of 
    ("7","9","1",".","3"), then click on the wavelength setting, then click "clear" then
    on each of the number one by one with a delay of 0.2, then click on "enter" to finish the change
    """
    pico_emerald_layout = load_from_json("pico_emerald_layout.json")
    wavelength_position = tuple(pico_emerald_layout['wavelength_position'])
    wavelength_power_keypad = load_from_json("wavelength_power_keypad.json")
    # open the wavelength setting
    pyautogui.click(wavelength_position)
    # clear the previous
    click(wavelength_power_keypad, "wavelength", "clear")
    # click on the number
    for w in wavelength:
        click(wavelength_power_keypad, "wavelength", w)
        time.sleep(0.1)
    # click enter
    click(wavelength_power_keypad, "wavelength", "enter")

    


# pass in must be strings
def change_power_to(power):
    pico_emerald_layout = load_from_json("pico_emerald_layout.json")
    power_position = tuple(pico_emerald_layout['power_position'])
    wavelength_power_keypad = load_from_json("wavelength_power_keypad.json")
    # open the wavelength setting
    pyautogui.click(power_position)
    # clear the previous
    click(wavelength_power_keypad, "power", "clear")
    # click on the number
    for p in power:
        click(wavelength_power_keypad, "power", p)
        time.sleep(0.1)
    # click enter
    click(wavelength_power_keypad, "power", "enter")

# this will make sure when the py script is called directly, the above function will run
if __name__ == "__main__":
    main()
