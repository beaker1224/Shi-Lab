import pyautogui
import json

class welcomeScreen():
 def __init__(self) -> None:
    print("Please enter the wavelengths and the powers with other information necessary into the txt file 'parameters' within the same folder")
    print("Press 'enter' when you are ready")
    parameters = open("parameters.txt")