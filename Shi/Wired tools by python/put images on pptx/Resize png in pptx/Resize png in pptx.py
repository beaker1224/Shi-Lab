import pyautogui, os, json, time

def save_to_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

number = input("how many images?")

def main():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.realpath(__file__))
    # Change the working directory to the script's directory
    os.chdir(script_dir)


    filename = "setup for Resize png in pptx.json"
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


    
    i = 0

    
    while i < int(number):
        pyautogui.click(*image_group)
        time.sleep(0.2)
        pyautogui.click(*image_parameter_box)
        pyautogui.write("1")
        pyautogui.hotkey('enter')
        i += 1


main()
while True:
    input("press enter for another loop")
    main()


