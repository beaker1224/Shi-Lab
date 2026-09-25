import json
import os
# Check if necessary libraries are installed, if not, install them
import pyautogui

import time

def get_mouse_position():
    input("Hover Mouse over the LSM start button and press 'Enter': ")
    return pyautogui.position()

def get_pixel_color(x, y):
    return pyautogui.pixel(x, y)


def main():



    lsmstart = get_mouse_position()


    numframes = int(input("number of frames?: "))
    frameduration = int(input("frame duration [s]?: "))
    tobegin = input("start sweep? (yes/no): ").lower()
    if tobegin == 'yes':
       for _ in range(numframes):
        pyautogui.click(*lsmstart)
           
        time.sleep(frameduration)

if __name__ == "__main__":
    main()