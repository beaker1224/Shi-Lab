import pyautogui
import os
import parameter_interpreter_3
import pico_emeraldWatch_1, FVWatch_2
import time
import json

pyautogui.FAILSAFE = False

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

pico_emerald_layout = load_from_json("pico_emerald_layout.json")
shutter_position = tuple(pico_emerald_layout['shutter_position'])
shutter_on_color = tuple(pico_emerald_layout['shutter_on_color'])

def get_pixel_color(x, y):
    return pyautogui.pixel(x, y)

def name_typer(order, wavelength, power, average, zoom):
    name = f"{order}-{wavelength}nm-{power}mW-avg{average}-zoom{zoom}"
    if (average == "off" or average == "no" or int(average) == 0):
        name = f"{order}-{wavelength}nm-{power}mW-zoom{zoom}"
    file = load_from_json("FV_layout.json")
    name_bar_position = tuple(file['file name editor position'])
    pyautogui.click(*name_bar_position)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.typewrite(name)

# will return true once the shutter is turned back on, check every 0.5 second
def shutter_backOn():
    '''
    This function checks the shutter color change every 0.75 second, 
    and returns a boolean True when the color changed to the color on
    for the system shutter.

    '''
    while True:
        current_shutter_color = get_pixel_color(*shutter_position)
        if tuple(current_shutter_color) == shutter_on_color:
            return True
        time.sleep(0.75)  # Check the shutter every 0.75 second

# the average clicker to click average number
parameter_interpreter_3.interpreter()
os.system('cls')
# averages = tuple(load_from_json("parameters.json")['average'])
fvFile = load_from_json("FV_layout.json")
frame_on_position = tuple(fvFile['frame on position'])
frame_off_position = tuple(fvFile['frame off position'])
frame_numberpad_position = tuple(fvFile['frame numberpad position'])
def average_clicker(average):
    if average == 0:
        pyautogui.click(frame_off_position)
    if not average == 0:
        pyautogui.click(frame_on_position)
        pyautogui.click(frame_numberpad_position)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.typewrite(average)


def main():
    print("before you use this script, make sure that both softwares are not covered by each other, and max the window of pico_emerald")

    if not (os.path.exists('pico_emerald_layout.json') or os.path.exists('wavelength_power_keypad.json')):
        input("pico emerald software layout did not setup! press 'enter' to quit")
        pyautogui.hotkey('ctrl', 'c')

    if not os.path.exists('FV_layout.json'):
        input("fv-30s software layout did not setup! press 'enter' to quit")
        pyautogui.hotkey('ctrl', 'c')

    while True:
        try:
            # Get user input and try to convert it to an integer
            order = int(input("which order (#th) roi are you taking image of? number only!"))
            break  # Return the integer if conversion is successful
        except ValueError:
            # If conversion fails, prompt the user again
            print("Invalid input. Please enter an integer.")

#    print(order) this make sure the order is stored as a value we want
            

    while True:
        try:
            # Get user input and try to convert it to an integer
            zoom = float(input("which zoom # are you taking image of? number only!"))
            break  # Return the integer if conversion is successful
        except ValueError:
            # If conversion fails, prompt the user again
            print("Invalid input. Please enter an number.")

    # interprete the data in parameters.txt
    parameter_interpreter_3.interpreter()

    parameters = load_from_json("parameters.json")
    wavelengths = tuple(parameters['wavelength'])
    powers = tuple(parameters['power'])
    averages = tuple(parameters['average'])
    channels = tuple(parameters['channel'])

    print(order, '-', wavelengths[0], '-', powers[0], 'mW-avg', averages[0], '-zoom', zoom)
    input("this will be how the name looks like as files, press 'enter' to advance,\n press ctrl + c to quit when you think something went wrong ")

    FV_layout = load_from_json("FV_layout.json")
    try:
        lsm_start = tuple(FV_layout['lsm button position'])
        lsm_off_color = tuple(FV_layout['lsm button off color'])
        lsm_colorbar_off_color = tuple(FV_layout['lsm colorbar off color'])
        lsm_colorbar_position = tuple(FV_layout['lsm colorbar position'])
    except KeyError:
        input("FVWatch_2 did not run, FV_layout did not setup correctly, press 'ctrl+c' to exit, press 'enter' to setup")
        FVWatch_2.main()

    print(lsm_start)
    print("IMPORTANT: set the wavelength and power to the first set you need to take!!!!!!!!!!!!!!!!!")
    # this is because there is a bug for pico emerald software, if you enter the wavelength 
    # which is the same with your current wavelength, the next adjust will not turn of the 
    # system shutter, so this program will crash
    input("Press 'enter' to start the auto lsm system")

    i = 0

    while i < len(wavelengths):
        if not i == 0:
            if not averages[i] == averages[i-1]:
                average_clicker(averages[i])


       # part 1, when the first time using the script when the parameters are setup by the user 
        if i == 0:
            average_clicker(averages[i])
            name_typer(order, wavelengths[i], powers[i], averages[i], zoom)
            if shutter_backOn():
                pyautogui.click(*lsm_start)
                time.sleep(2.8)
                # monitering start, lsm start, sleep(2.8) gives the lsm button to turn into correct working color some time, 10 us gives 3.16
                while True:
                    current_lsm_color = get_pixel_color(*lsm_start)
                    if tuple(current_lsm_color) == lsm_off_color:
                        break # break when lsm finished
                    time.sleep(0.5) # the color of the button is checked every 0.5 second
                i += 1

        # part 2, changing the power and then the wavelength, and the name of the file
        if powers[i] == powers[i-1]:
            pass
        else:
            pico_emeraldWatch_1.change_power_to(powers[i])
            time.sleep(0.25)
        pico_emeraldWatch_1.change_wavelength_to(wavelengths[i])
        time.sleep(0.5)
        name_typer(order, wavelengths[i], powers[i], averages[i], zoom)

        # part 3, when tuned ok, then click on the lsm start
        if shutter_backOn():
            pyautogui.click(*lsm_start)
            time.sleep(2.8)
            while True:
                current_lsm_color = get_pixel_color(*lsm_start)
                if current_lsm_color == lsm_off_color:
                    break # break when lsm finished
                time.sleep(0.5) # the color of the button is checked every 0.5 second
        i += 1

    pico_emeraldWatch_1.change_power_to(powers[0])
    time.sleep(0.25)
    pico_emeraldWatch_1.change_wavelength_to(wavelengths[0])

main()
