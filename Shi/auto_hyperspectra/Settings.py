import pyautogui
import json

class SpecSettings(): 
    def __init__(self) -> None:
        print("Please enter time for each frame (optional but strongly encouraged): ")
        self.time_delay = input()
        print("The following entrees are for log file (optional)")
        self.start_wavelength = input("Wavelength start at: ")
        self.end_wavelength = input("Wavelength end at: ")
        self.intend_steps = input("Intended steps: ")
        self.wavelength_step = 0
        if self.start_wavelength and self.end_wavelength and self.intend_steps: 
            wavelength_step = (float(self.end_wavelength)-float(self.start_wavelength))/int(self.intend_steps)
        self.log_path = input("log file path (default current folder log.txt): ")
        if not self.log_path: 
            self.log_path = "log.txt"

class LayoutSettings(): 
    def __init__(self) -> None:
        try: 
            with open("layout.json") as layout_json: 
                self.layout = json.load(layout_json)
        except FileNotFoundError: 
            self.layout = {
                'lsm_xy': (0, 0), 
                'process_bar': (472, 773),
                'process_color': (0, 187, 34),
                'default_lsm_xy': (0, 0),
                'default_process_bar': (472, 773),
                'default_process_color': (0, 187, 34),
            }
            with open("layout.json", 'w') as layout_json: 
                json.dump(self.layout, layout_json)


    def update_layout(self): 
        print('Please move your cursor onto the "LSM Start" botton. ')
        print('Then press Enter. ')
        input()
        self.layout['lsm_xy'] = pyautogui.position()
        print('Now please start sweep, ')
        print('Then move your cursor to the right end of progress bar, press ENTER when the bar passes your cursor. ')
        input()
        self.layout['process_bar'] = pyautogui.position()
        process_color_obj = pyautogui.pixel(self.layout['process_bar'][0], self.layout['process_bar'][1])
        self.layout['process_color'] = (process_color_obj[0], process_color_obj[1], process_color_obj[2])
        with open("layout.json", 'w') as layout_json: 
            json.dump(self.layout, layout_json)
        print('Layout updated!')
    
    def restore_to_default(self): 
        print('This action will clear existing layout and restore to default layout settings! Y/n')
        flag = input()
        if flag == 'Y': 
            self.layout['lsm_xy'] = self.layout['default_lsm_xy']
            self.layout['process_bar'] = self.layout['default_process_bar']
            self.layout['process_color'] = self.layout['default_process_color']
            with open("layout.json", 'w') as layout_json: 
                json.dump(self.layout, layout_json)
            print('Restored! ')
        else: 
            print('Nothing happened. ')

    def update_default(self): 
        print("This action would set current layout as default! Y/n")
        flag = input()
        if flag == 'Y': 
            self.layout['default_lsm_xy'] = self.layout['lsm_xy']
            self.layout['default_process_bar'] = self.layout['process_bar']
            self.layout['default_process_color'] = self.layout['process_color']
            with open("layout.json", 'w') as layout_json: 
                json.dump(self.layout, layout_json)
            print("Done!")
        else: 
            print('Nothing happened!')

