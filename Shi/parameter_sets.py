import pyautogui
import json
import os


def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)


    
class inputSet():
    def __init__(self, order, wavelength, power, average, zoom):
        self.order = order
        self.wavelength = wavelength
        self.power = power
        self.average = average
        self.zoom = zoom

    

    

# test here
'''
set1 = inputSet(1,791.3,300,2,5)
print(type(set1))
set1.name_typer()
'''

