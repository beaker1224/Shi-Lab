“A template of how to write a readMe.md file lol, this sentence need to be deleted later!”

# Auto LSM System User Manual

This script is written mainly for you to save time during lsm process. By this script, you don't have to stare at the monitor during SRS.
This script is just a auto clicker that can detect the color change of the buttons from two softwares: FV and pico emerald. Right now, this script cannot help you change the CD channels, for example, if you are taking the SRS, this script cannot change the channel to auto_fluoro for you, but this will be a feature added in the future.

## Installation
Make sure the local machine has following packages installed:
1. [pyautogui](https://pyautogui.readthedocs.io/en/latest/)
2. [Pillow](https://pypi.org/project/pillow/)
3. [openCV](https://opencv.org/) (this is optional but maybe will be utilized in the future)

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install those packages stated above


If unsure, please use following code to check if the proper packages are installed
```bash
pip show pyautogui
```
```bash
pip show Pillow
```
If the package is not installed, please use the following code to install
```
pip install package_name
```

## Setup

after the package is unzipped, please running pico_emeraldWatch_1.py and FVWatch_2.py

### pico_meraldWatch_1.py

This script will ask you about positions and colors of buttons from software pico_emerald.exe. There are three main portions:
1. the script will ask to move the mouse to the System shutter button while the button is ON. This will help the script get the position and current color of the system shutter button. This script can run because every time the wavelength get changed, the system shutter will automatically turned off to protect the machine.
2. the script will ask about positions where to click to open up the keypad of wavelength and power.
3. the script will go through the positions of almost each button on the keypad, including:{0,1,2,3,4,5,6,7,8,9,clear,enter}. Becareful, because of my mistake, "enter" button means "OK" button from the keypad.
   
### FVWatch_2.py

This part of script will ask about positions and colors of buttons from software FV. There are two main portions:
1. The script will get location and color of "LSM" start button
2. The script will get the location of the naming text input

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change. Everyone is free to use this script, and this script
did get help from ChatGPT. And thanks to the inspiration brought by the author of "auto_hyperspectra".


## License

MIT License

Copyright (c) [2024] [Shuo]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
