try:
    import pyautogui
except ImportError:
    input("Error: pyautogui is not installed.")

import os
import parameter_interpreter_3
import pico_emeraldWatch_1, FVWatch_2
import time
import json

# # Get the directory of the current script
# script_dir = os.path.dirname(os.path.realpath(__file__))
# # Change the working directory to the script's directory
# os.chdir(script_dir)

# input("enter to test")
# pico_emeraldWatch_1.change_power_to("250")
# time.sleep(3)
# pico_emeraldWatch_1.change_wavelength_to("791.3")
# time.sleep(3)

# input("displaying error msg")

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_dir)


def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)


def print_channel_states():
    """
    Test checkbox recognition for CH1-CH5.
    """
    print("\nCurrent channel states:")

    for channel in range(1, 6):

        changed_pixels = FVWatch_2.checkbox_changed_pixel_count(channel)
        checked = FVWatch_2.checkbox_is_checked(channel)

        if checked:
            state = "CHECKED"
        else:
            state = "UNCHECKED"

        print(
            f"CH{channel}: {state} "
            f"(changed pixels = {changed_pixels})"
        )


def click_channel(channel_number):
    """
    Click one channel checkbox using its saved position.
    """

    FV_layout = load_from_json("FV_layout.json")

    position = tuple(
        FV_layout[f'channel_{channel_number}_checkbox_position']
    )

    # Click slightly inside the checkbox instead of exactly
    # on the saved top-left corner
    x, y = position

    pyautogui.click(x + 7, y + 7)

    time.sleep(0.3)


def set_channels(desired_channels):
    """
    Make the FV checkboxes match desired_channels.

    Example:
        set_channels([1, 3, 5])

    Result:
        CH1 -> ON
        CH2 -> OFF
        CH3 -> ON
        CH4 -> OFF
        CH5 -> ON
    """

    print("\nSetting channels...")

    for channel in range(1, 6):

        currently_checked = FVWatch_2.checkbox_is_checked(channel)

        should_be_checked = channel in desired_channels

        print(
            f"CH{channel}: "
            f"current={currently_checked}, "
            f"desired={should_be_checked}"
        )

        # Only click when current state does not match desired state
        if currently_checked != should_be_checked:

            print(f" -> Clicking CH{channel}")

            click_channel(channel)

    print("\nFinished setting channels.")


# -----------------------
# TEST
# -----------------------

input("Press Enter to test checkbox recognition...")

print_channel_states()


input("\nPress Enter to test channel clicking...")

# Example test:
set_channels([1, 2])


time.sleep(1)

print("\nChecking states again:")
print_channel_states()

input("\nPress Enter to test setting channels to [5]...")
set_channels([5])
print("\nChecking states again:")
print_channel_states()

input("\nPress Enter to exit.")