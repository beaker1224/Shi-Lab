import pyautogui, os, json

def save_to_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # Change the working directory to the script's directory
    os.chdir(script_dir)

    
    filename = "setup.json"
    if not os.path.exists(filename):
        input("hover mouse to image group")
        image_group = pyautogui.position()
        input("hover mouse to image size parameter input box")
        image_parameter_box = pyautogui.position()
        save_to_json(filename, {
            'image_group' : image_group,
            'image_parameter_box' : image_parameter_box
        })
    else:
        file = load_from_json(filename)
        image_group = tuple(file['image_group'])
        image_parameter_box = tuple(file['image_parameter_box'])


    number = input("how many images?")
    i = 0


    while i < number:
        pyautogui.click(*image_group)
        pyautogui.click(*image_parameter_box)
        pyautogui.write("3.68")
        pyautogui.hotkey('enter')
        i += 1

