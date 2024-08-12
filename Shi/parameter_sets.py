import pyautogui
import json
import os


def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)


    
class wavelengthSet():
    def __init__(self, order, wavelength, power, average, zoom):
        self.order = order
        self.wavelength = wavelength
        self.power = power
        self.average = average
        self.zoom = zoom

    def name_typer(self):
        order = str(self.order)
        wavelength = str(self.wavelength)
        power = str(self.power)
        average = str(self.average)
        zoom = str(self.zoom)
        name = order + '-' + wavelength + 'nm-' + power + 'mW-avg' + average + "-zoom" + zoom
        file = load_from_json("FV_layout.json")
        name_bar_position = tuple(file['file name editor position'])
        pyautogui.click(name_bar_position)
        pyautogui.typewrite(name)

    

# test here
set1 = wavelengthSet(1,791.3,300,2,5)
print(type(set1))
set1.name_typer()
