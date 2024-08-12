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
    # interprete the data in parameters.txt
    parameter_interpreter_3.interpreter()
    
    parameters = load_from_json("parameters.json")
    wavelengths = tuple(parameters['wavelength'])
    powers = tuple(parameters['power'])
    averages = tuple(parameters['average'])
    channels = tuple(parameters['channel'])
    
    pico_emerald_layout = load_from_json("pico_emerald_layout.json")
    FV_layout = load_from_json("FV_layout.json")

    while true:
        i = 0

        while i < len(wavelengths):
            pico_emeraldWatch_1.change_wavelength_to(wavelengths[i])

main()
