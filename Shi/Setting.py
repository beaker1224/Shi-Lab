import pyautogui

## each time calling welcome Screen will check the ability to read the parameters.txt file
## if there is none, create one and say nothing is in
## if the format is wrong, pop up the format error message.
class buttons:
   def __init__(self, position_X, position_Y, colorBefore, colorAfter):
      self.position_X = position_X
      self.position_Y = position_Y
      self.colorBefore = colorBefore
      self.colorAfter = colorAfter

   def welcomeScreen(self):
    print("Please enter the wavelengths and the powers with other information necessary into the txt file 'parameters' within the same folder")
    print("Please choose from the following by type the number")
    print("1. LSM Scan with different wavelengths and power")
    print("2. Set the positions of the buttons on the screen")
    print("3. Reset the settings of positions of the buttons on the screen")


   def settingLayout(self):
      print("Please hover the mouse on 'LSM Start' button")
      print("also make sure the mouse tip is pointing to the place that changes color \n once you put your mouse on")


    