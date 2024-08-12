import pyautogui

class wavelengthSet(self):
    def __init__(self, order, wavelength, power, IR_status, average, zoom)

    def naming(self):
        order = str(self.order)
        wavelength = str(self.wavelength)
        power = str(self.power)
        average = str(self.average)
        zoom = str(self.zoom)
        name = order + '-' + wavelength + 'nm-' + power + 'mW-avg' + average + "-zoom" + zoom
        pyautogui.typewrite(name, interval=0.01) ## do I have to set this parameter up?