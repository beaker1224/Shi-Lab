import pyautogui
import os
import parameter_interpreter_3
import parameter_sets
import pico_emeraldWatch_1
import time
import json

pyautogui.FAILSAFE = False
if not os.path.exists('pico_emerald_layout.json'):
    input("pico emerald software layout did not setup! press 'enter' to quit")
    return
pico_emerald_layout = load_from_json("pico_emerald_layout.json")
shutter_position = tuple(pico_emerald_layout['shutter_position'])
shutter_on_color = tuple(pico_emerald_layout['shutter_on_color'])

def get_pixel_color(x, y):
    return pyautogui.pixel(x, y)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def name_typer(order, wavelength, power, average, zoom):
    name = order + '-' + wavelength + 'nm-' + power + 'mW-avg' + average + "-zoom" + zoom
    file = load_from_json("FV_layout.json")
    name_bar_position = tuple(file['file name editor position'])
    pyautogui.click(name_bar_position)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(name)

# will return true once the shutter is turned back on, check every 0.5 second
def shutter_backOn():
    while True:
        current_shutter_color = get_pixel_color(shutter_position)
        if tuple(current_shutter_color) == shutter_on_color:
            return True
        else:
            pass
        time.sleep(0.5) # check the shutter every 0.5 second




def main():
    print("before you use this script, make sure that both softwares are not covered by each other")
    while True:
        order = input("which order (#th) roi are you taking image of? number only!")
        if type(order) != 'int':
            print("Please enter number only!")
        else:
            break

    while True:
        zoom = input("which zoom # are you taking image of? number only!")
        if type(zoom) != 'int':
            print("Please enter number only!")
        else:
            break

    # interprete the data in parameters.txt
    parameter_interpreter_3.interpreter()

    parameters = load_from_json("parameters.json")
    wavelengths = tuple(parameters['wavelength'])
    powers = tuple(parameters['power'])
    averages = tuple(parameters['average'])
    channels = tuple(parameters['channel'])

    print(order, '-', wavelengths[0], '-', powers[0], 'mW-avg', averages[0], '-zoom', zoom)
    input("this will be how the name looks like as files, press 'enter' to advance, \n press ctrl + c to quit when you think something went wrong ")

    FV_layout = load_from_json("FV_layout.json")
    lsm_start = tuple(FV_layout['lsm button position'])
    lsm_off_color = tuple(FV_layout['lsm button off color'])
    lsm_colorbar_off_color = tuple(FV_layout['lsm colorbar off color'])
    lsm_colorbar_position = tuple(FV_layout['lsm colorbar position'])

    print("IMPORTANT: set the wavelength and power to the first set you need to take!!!!!!!!!!!!!!!!!")
    # this is because there is a bug for pico emerald software, if you enter the wavelength 
    # which is the same with your current wavelength, the next adjust will not turn of the 
    # system shutter, so this program will crash
    input("Press 'enter' to start the auto lsm system")

    i = 0

    while i < len(wavelengths):
        
        if i == 0:
            name_typer(order, wavelengths[i], powers[i], averages[i], zoom)
            pyautogui.click(lsm_start)
            time.sleep(2)
            # monitering start, lsm start, sleep(2) gives the lsm button to turn into correct working color some time
            while True:
                current_lsm_color = get_pixel_color(lsm_start)
                if current_lsm_color == lsm_off color:
                    break # break when lsm finished
                time.sleep(0.5) # the color of the button is checked every 0.5 second
            i ++
        
        if powers[i] == powers[i-1]:
            pass
        else:
            pico_emeraldWatch_1.change_power_to(powers[i])
            time.sleep(0.25)
        pico_emeraldWatch_1.change_wavelength_to(wavelengths[i])
        time.sleep(0.5)
        name_typer(order, wavelengths[i], powers[i], averages[i], zoom)
        if shutter_backOn():
            pyautogui.click(lsm_start)
            time.sleep(2)
            while True:
                current_lsm_color = get_pixel_color(lsm_start)
                if current_lsm_color == lsm_off color:
                    break # break when lsm finished
                time.sleep(0.5) # the color of the button is checked every 0.5 second
        i ++

    pico_emeraldWatch_1.change_power_to(powers[0])
    time.sleep(0.25)
    pico_emeraldWatch_1.change_wavelength_to(wavelengths[0])

main()