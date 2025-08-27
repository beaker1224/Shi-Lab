import pyautogui
import os
import json
import zlib



def get_lsm_colorbar_position():
    """
    Gets the position of the colorbar.

    Returns:
        tuple: The (x, y) position.
    """
    print("Hover your mouse on lsm PROGRESSION COLORBAR (the one that between lsm button and estimated time) \n just make sure to not touch the edge of the colorbar")
    input("press 'enter' to advance")
    return pyautogui.position()

def get_pixel_color(x, y):
    '''
    Gets the pixel of the current position
    
    Returns:
        tuple: The (R,G,B) of the position (x,y)
    '''
    return pyautogui.pixel(x, y)

def get_lsm_button_position():
    input("Hover your mouse on 'LSM Start' button's GREY AREA and press 'enter'")
    return pyautogui.position()

def get_filename_position():
    input("Hover your mouse on the end of file naming part (the part you enter the name of the image) \n and press 'enter'")
    return pyautogui.position()

def get_frame_off_position():
    input("Hover your mouse on the None button of the average section, and press 'enter'")
    return pyautogui.position()

def get_frame_on_position():
    input("Hover your mouse on the Frame button of the average section, and press 'enter'")
    return pyautogui.position()

def get_frame_numberpad_position():
    input("Hover your mouse on the Frame NUMBERPAD, and press 'enter'")
    return pyautogui.position()

def get_checkbox_position():
    input("Hover your mouse over the checkbox left-top cornor position, and press 'enter")
    return pyautogui.position()

def save_to_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)
    
def main():
    json_file = "FV_layout.json"
    if os.path.exists(json_file):
        user_choice = input("Update settings on the LSM positions? (yes/no): ").lower()
        if user_choice == 'yes':
            update_required = True
        else:
            update_required = False
    else:
        update_required = True

    if update_required:
        lsm_position = get_lsm_button_position()
        lsm_off_color = get_pixel_color(*lsm_position)
        lsm_colorbar_position = get_lsm_colorbar_position()
        lsm_colorbar_off = get_pixel_color(*lsm_colorbar_position)
        lsm_filename_position = get_filename_position()
        frame_off_position = get_frame_off_position()
        frame_on_position = get_frame_on_position()
        frame_numberpad_position = get_frame_numberpad_position()
        channel_checkbox_position = get_checkbox_position()
        # channel_checkbox_pixel = 
        save_to_json(json_file, {
            'lsm button position': lsm_position,
            'lsm button off color': lsm_off_color,
            'lsm colorbar position': lsm_colorbar_position,
            'lsm colorbar off color': lsm_colorbar_off,
            'file name editor position': lsm_filename_position,
            'frame off position': frame_off_position,
            'frame on position': frame_on_position,
            'frame numberpad position': frame_numberpad_position,
            'channel_checkbox_position' : channel_checkbox_position
        })

    else:
        config = load_from_json(json_file)
        lsm_position = tuple(config['lsm button position'])
        lsm_off_color = tuple(config['lsm button off color'])
        lsm_colorbar_position = tuple(config['lsm colorbar position'])
        lsm_colorbar_off = tuple(config['lsm_colorbar off color'])
        lsm_filename_position = tuple(config['file name editor position'])
        frame_off_position = tuple(config['frame off position'])
        frame_on_position = tuple(config['frame on position'])
        frame_numberpad_position = tuple(config['frame numberpad position'])

    print('lsm button position: ' + str(lsm_position),
        'lsm button off color: ' + str(lsm_off_color),
        'lsm colorbar position: ' + str(lsm_colorbar_position),
        'lsm_colorbar off color: ' + str(lsm_colorbar_off),
        'file name editor position: ' + str(lsm_filename_position),
        'frame off position: ' + str(frame_off_position),
        'frame on position: ' + str(frame_on_position),
        'frame numberpad position: ' + str(frame_numberpad_position))

    
    input("display for information, press 'enter' when you want to exist and finish updating FV layout setting")

# this will make sure when the py script is called directly, the above function will run
if __name__ == "__main__":
    main()