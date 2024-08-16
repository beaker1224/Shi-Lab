import pyautogui
import os
import parameter_interpreter_3
import pico_emeraldWatch_1, FVWatch_2
import time
import json

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

input("enter to test")
pico_emeraldWatch_1.change_power_to("250")
time.sleep(3)
pico_emeraldWatch_1.change_wavelength_to("791.3")
input("displaying error msg")