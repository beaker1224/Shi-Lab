import json
import os

def save_to_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)
    
#def main():

def interpreter():
    json_file = "parameters.json"

    # Initialize a dictionary with keys and empty lists
    data = {
        'wavelength': [],
        'power': [],
        'average': [],
        'channel': []
    }

    with open(json_file, 'r') as file:
        lines = file.readlines()  # Read all lines at once
        i = 0  # Initialize line index

        while i < len(lines):
            line = lines[i].strip()  # Remove leading/trailing whitespace

            if line == '--' or line == '-' or line == '---' or line == '----' or line == '-----':
                # Skip the separator and move to the next section
                i += 1
                continue
            else:
                i = len(lines)
                input("there is a formatting error in 'parameters.txt', for more detail please see 'readMe.md', press 'enter' to exist")
                
            data['wavelength'].append(float(lines[i].strip()))
            data['power'].append(int(lines[i + 1].strip()))
            data['average'].append(lines[i + 2].strip())
            data['channel'].append(lines[i + 3].strip())

            # Move to the next section after the current set of 4 lines
            i += 4
    save_to_json(json_file,{data})
# this will directly ask how user want to set up things, should be avaliable in the future

if __name__ == "__main__":
    #main()
    interpreter()

# this will interpret the data in parameter.txt file into json format
if __name__ == "__parameter_interpreter.py__":
    interpreter()