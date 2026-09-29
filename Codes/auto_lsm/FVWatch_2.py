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

def get_resolution_dropdown_position():
    input("Hover your mouse on the resolution dropdown, and press 'enter'")
    return pyautogui.position()

def get_checkbox_position(channel_number):
    print(f"This step is for channel {channel_number} checkbox position.")
    input(f"Make sure the checkbox {channel_number} is UNCHECKED. Hover your mouse over the TOP-LEFT CORNER of thecheckbox {channel_number} and press 'enter'")
    return pyautogui.position()

def get_pixel_strip(x,y, width = 15, height = 10):
    '''
    Gets the pixel strip of the current position
    
    Returns:
        tuple: The (R,G,B) of the position (x,y)
    '''
    return [pyautogui.pixel(x+i, y+j) for i in range(width) for j in range(height)]

def get_checkbox_strip(checkbox_position, width=12, height=3, x_offset=2, y_offset=5):
    """
    Capture a very small horizontal strip from inside a checkbox.

    The saved checkbox position is treated as the top-left corner. Offsets keep
    the sampled area away from the checkbox border so the check mark causes most
    of the detected pixel changes.

    Returns:
        list: RGB values flattened into a JSON-friendly list of [R, G, B].
    """
    x, y = checkbox_position
    image = pyautogui.screenshot(
        region=(x + x_offset, y + y_offset, width, height)
    )

    pixels = []
    for py in range(height):
        for px in range(width):
            pixels.append(list(image.getpixel((px, py))))
    return pixels


def count_changed_pixels(reference_strip, current_strip, tolerance=30):
    """
    Count pixels whose RGB value changed more than ``tolerance``.

    ``tolerance`` is applied to the sum of absolute R/G/B differences. This
    ignores very small GUI rendering differences while still detecting the
    additional pixels produced by a check mark.
    """
    if len(reference_strip) != len(current_strip):
        raise ValueError("Reference strip and current strip must have the same size.")

    changed = 0
    for reference, current in zip(reference_strip, current_strip):
        difference = sum(abs(int(r) - int(c)) for r, c in zip(reference, current))
        if difference > tolerance:
            changed += 1
    return changed


def checkbox_changed_pixel_count(
    channel_number,
    config_file="FV_layout.json",
    tolerance=30,
):
    config = load_from_json(config_file)

    checkbox_position = tuple(
        config[f'channel_{channel_number}_checkbox_position']
    )

    reference_strip = config[
        f'channel_{channel_number}_unchecked_strip'
    ]

    width = config.get('checkbox strip width', 12)
    height = config.get('checkbox strip height', 3)
    x_offset = config.get('checkbox strip x offset', 2)
    y_offset = config.get('checkbox strip y offset', 5)

    current_strip = get_checkbox_strip(
        checkbox_position,
        width=width,
        height=height,
        x_offset=x_offset,
        y_offset=y_offset,
    )

    return count_changed_pixels(
        reference_strip,
        current_strip,
        tolerance=tolerance,
    )

def checkbox_is_checked(
    channel_number,
    config_file="FV_layout.json",
    tolerance=30,
    min_changed_pixels=3,
):
    changed_pixels = checkbox_changed_pixel_count(
        channel_number,
        config_file=config_file,
        tolerance=tolerance,
    )

    return changed_pixels >= min_changed_pixels


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

        channel_1_checkbox_position = get_checkbox_position(1)
        channel_1_unchecked_strip = get_checkbox_strip(
            channel_1_checkbox_position
        )
        channel_2_checkbox_position = get_checkbox_position(2)
        channel_2_unchecked_strip = get_checkbox_strip(
            channel_2_checkbox_position
        )
        channel_3_checkbox_position = get_checkbox_position(3)
        channel_3_unchecked_strip = get_checkbox_strip(
            channel_3_checkbox_position
        )
        channel_4_checkbox_position = get_checkbox_position(4)
        channel_4_unchecked_strip = get_checkbox_strip(
            channel_4_checkbox_position
        )
        channel_5_checkbox_position = get_checkbox_position(5)
        channel_5_unchecked_strip = get_checkbox_strip(
            channel_5_checkbox_position
        )

        save_to_json(json_file, {
            'lsm button position': lsm_position,
            'lsm button off color': lsm_off_color,
            'lsm colorbar position': lsm_colorbar_position,
            'lsm colorbar off color': lsm_colorbar_off,
            'file name editor position': lsm_filename_position,
            'frame off position': frame_off_position,
            'frame on position': frame_on_position,
            'frame numberpad position': frame_numberpad_position,

            'channel_1_checkbox_position': channel_1_checkbox_position,
            'channel_2_checkbox_position': channel_2_checkbox_position,
            'channel_3_checkbox_position': channel_3_checkbox_position,
            'channel_4_checkbox_position': channel_4_checkbox_position,
            'channel_5_checkbox_position': channel_5_checkbox_position,

            'channel_1_unchecked_strip': channel_1_unchecked_strip,
            'channel_2_unchecked_strip': channel_2_unchecked_strip,
            'channel_3_unchecked_strip': channel_3_unchecked_strip,
            'channel_4_unchecked_strip': channel_4_unchecked_strip,
            'channel_5_unchecked_strip': channel_5_unchecked_strip,

            'checkbox strip width': 12,
            'checkbox strip height': 3,
            'checkbox strip x offset': 2,
            'checkbox strip y offset': 5,
        })
        
        print("\nConfig file 'FV_layout.json' has been updated with the new settings. \n")


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
        channel_1_checkbox_position = tuple(config['channel_1_checkbox_position'])
        channel_2_checkbox_position = tuple(config['channel_2_checkbox_position'])
        channel_3_checkbox_position = tuple(config['channel_3_checkbox_position'])
        channel_4_checkbox_position = tuple(config['channel_4_checkbox_position'])
        channel_5_checkbox_position = tuple(config['channel_5_checkbox_position'])


        
    print('lsm button position: ' + str(lsm_position),
        'lsm button off color: ' + str(lsm_off_color),
        'lsm colorbar position: ' + str(lsm_colorbar_position),
        'lsm_colorbar off color: ' + str(lsm_colorbar_off),
        'file name editor position: ' + str(lsm_filename_position),
        'frame off position: ' + str(frame_off_position),
        'frame on position: ' + str(frame_on_position),
        'frame numberpad position: ' + str(frame_numberpad_position),
        'channel 1 checkbox position: ' + str(channel_1_checkbox_position),
        'channel 2 checkbox position: ' + str(channel_2_checkbox_position),
        'channel 3 checkbox position: ' + str(channel_3_checkbox_position),
        'channel 4 checkbox position: ' + str(channel_4_checkbox_position),
        'channel 5 checkbox position: ' + str(channel_5_checkbox_position))

    input("Display for information, press 'enter' when you want to exist and finish updating FV layout setting")

# this will make sure when the py script is called directly, the above function will run
if __name__ == "__main__":
    main()