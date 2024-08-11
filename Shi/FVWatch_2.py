import pyautogui
import os

def get_lsm_colorbar_position():
    print("Hover your mouse on lsm PROGRESSION COLORBAR (the one that between lsm button and estimated time) \n just make sure to not touch the edge of the colorbar")
    input("press 'enter' to advance")
    return pyautogui.position()

def get_lsm_colorbar_colorOff(x, y):
    return pyautogui.pixel(x, y)

def get_lsm_button_position():
    input("Hover your mouse on 'LSM Start' button and press 'enter'")
    return pyautogui.position()

def get_filename_position():
    input("Hover your mouse on the file naming part (the part you enter the name of the image) \n and press 'enter'")
    return pyautogui.position()
