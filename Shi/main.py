import pyautogui
import os
import parameter_interpreter_3
import parameter_sets
import pico_emeraldWatch_1
import time

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def main():
    order = input("which order (#th) roi are you taking image of? number only!")
    # interprete the data in parameters.txt
    parameter_interpreter_3.interpreter()

    parameters = load_from_json("parameters.json")
    wavelengths = tuple(parameters['wavelength'])
    powers = tuple(parameters['power'])
    averages = tuple(parameters['average'])
    channels = tuple(parameters['channel'])
    i = 0
    while i < len(wavelengths):
        sets = []
        sets.append(inputSet(order, wavelengths[i], powers[i], averages[i], channels[i]))
    print(sets)

    pico_emerald_layout = load_from_json("pico_emerald_layout.json")


    FV_layout = load_from_json("FV_layout.json")

    input("IMPORTANT: set the wavelength and power to the first set you need to take!!!!!!!!!!!!!!!!!")

    input("Press 'enter' to start the auto lsm system")

    while true:
        
        i = 1
        while i < len(wavelengths):
            pico_emeraldWatch_1.change_wavelength_to(wavelengths[i])

main()
