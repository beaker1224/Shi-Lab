import pyautogui
import os
import parameter_interpreter_3
import parameter_sets
import pico_emeraldWatch_1

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def main():
    # interprete the data in parameters.txt
    parameter_interpreter_3.interpreter()
    parameters = load_from_json("parameters.json")
    pico_emerald = load_from_json("pico_emerald_layout.json")
    FV = load_from_json("FV_layout.json")

    while true:
        i = 0
        parameters = load_from_json("parameters.json")

        while i < len()

main()