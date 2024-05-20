# auto_hyperspectra

[TOC]

## Description

A little tool to capture hyperspectra SRS images

Required package: pyautogui

When used on Windows, python 3.7 or higher might not work properly.  

## How to use

1. Setup all parameters for scanning on both microscopy and laser controlling systems. Ensure that the pop-up window for scanning settings is not moved. Please make sure that the hold time is at least 2 seconds longer than the exposure time to leave enough time for the program to get executed.  

2. Run the script by just clicking it and follow instructions.  

3. Drag the laser controlling interface to the left side of the primary screen, and choose the microscopy controlling interface in the right panel. Ensure there is no window over the laser controlling interface and the 'LSM start' button in the microscopy controlling interface.  

4. Click sweep in the laser controlling interface.  

5. In the script window, click enter to start it.  

6. Just let it run, remember to close the image windows if there is too many images opened. If need to stop earlier, close the script window directly or press ctrl+c in the script window.  
