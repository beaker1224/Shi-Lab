import sys, time
import pyautogui

import running_functions, Settings

pyautogui.FAILSAFE = False
print('If want to exit, close window directly or press ctrl+c')

try: 
    layout = Settings.LayoutSettings()
    print('Press enter to continue, type "layout" to layout settings')
    procedure = input()
    if procedure == 'layout': 
        print("Choose options: ")
        print("1. Update layout   2. Restore layout   3. Update default")
        while True: 
            choice = input()
            if choice == "1": 
                layout.update_layout()
                break
            elif choice == "2": 
                layout.restore_to_default()
                break
            elif choice == "3": 
                layout.update_default()
                break
    
    settings = Settings.SpecSettings()
    log_file = running_functions.LogFile(settings.start_wavelength, settings.end_wavelength, settings.wavelength_step, settings.log_path)
    log_file.init_log()
    click_flag = False
    n_img = 0
    input("Press enter to start. ")
    while True: 
        if pyautogui.pixelMatchesColor(layout.layout['default_process_bar'][0], layout.layout['default_process_bar'][1], layout.layout['process_color'], tolerance = 50): 
            if click_flag == False: 
                click_flag = True
                pyautogui.click((layout.layout['lsm_xy'])[0], (layout.layout['lsm_xy'])[1])
                log_file.log_image(n_img)
                n_img += 1
                if settings.time_delay: 
                    time.sleep(int(settings.time_delay))
        else: 
            click_flag = False
except KeyboardInterrupt: 
    print('exit')
    sys.exit()
