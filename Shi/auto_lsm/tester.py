import pyautogui
import os
import parameter_interpreter_3
import pico_emeraldWatch_1, FVWatch_2
import time
import json

input("enter to test")
pico_emeraldWatch_1.change_power_to("250")
time.sleep(3)
pico_emeraldWatch_1.change_wavelength_to("791.3")
input("displaying error msg")