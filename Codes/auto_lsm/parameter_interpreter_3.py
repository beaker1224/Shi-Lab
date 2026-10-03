import json
import os
import pandas as pd


# Define ANSI color codes
CYAN = '\033[96m'
GREEN = '\033[92m'
RESET = '\033[0m'

def table_stdout(data):
    """Print parameter rows as a bordered table without extra dependencies."""
    table = pd.DataFrame(data, columns=['wavelength', 'power', 'average', 'channel'])
    table = table.rename(columns={'channel': 'channels'})
    table['channels'] = table['channels'].apply(
        lambda channels: ', '.join(f'CH{channel}' for channel in channels)
    )

    headers = list(table.columns)
    rows = table.astype(str).values.tolist()

    # Determine column widths based on longest element (header or data)
    col_widths = [
        max(len(str(val)) for val in [header] + [row[i] for row in rows])
        for i, header in enumerate(headers)
    ]

    # Border templates
    sep_line = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    row_fmt = "| " + " | ".join(f"{{:<{w}}}" for w in col_widths) + " |"

    # Print table
    print(sep_line)
    print(row_fmt.format(*headers))
    print(sep_line)
    for row in rows:
        print(row_fmt.format(*row))
    print(sep_line)

def save_to_json(file_name, data):
    with open(file_name, 'w') as file:
        json.dump(data, file)

def load_from_json(file_name):
    with open(file_name, 'r') as file:
        return json.load(file)

def create_empty_txt(file_name):
    with open(file_name, 'w') as file:
        return
#def main():

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)


def interpreter():
    '''
    This function interprets the parameters from 'parameters.txt' and saves them into 'parameters.json'.
    It reads the parameters in groups of four lines, where each group represents a set of parameters:
    1. Wavelength (float)
    2. Power (int)
    3. Average (string)
    4. Channels (comma-separated string, e.g., "CH1,CH2,CH3")
    The function checks for the existence of 'parameters.json' and 'parameters.txt'. 
    If 'parameters.json' does not exist, it creates an empty one. 
    If 'parameters.txt' does not exist, it creates an empty one and prompts the user to input parameters.
    '''
    json_file = "parameters.json"
    txt_file = "parameters.txt"
    if not os.path.exists(json_file):
        save_to_json(json_file, {})
    if not os.path.exists(txt_file):
        create_empty_txt(txt_file)
        input("nothing input into 'parameters.txt', press 'enter' to exit")
        return
    # Initialize a dictionary with keys and empty lists
    data = {
        'wavelength': [],
        'power': [],
        'average': [],
        'channel': []
    }

    with open(txt_file, 'r') as file:
        lines = file.readlines()  # Read all lines at once
        i = 0  # Initialize line index
        section = 1
        while i < len(lines):
            line = lines[i].strip()  # Remove leading/trailing whitespace
            if line == '--':
                # Skip the separator and move to the next section
                i += 1
                continue
            if i + 4 > len(lines):
                input("there is a formatting error in 'parameters.txt', for more detail please see 'readMe.md', press 'enter' to exist")

            channel_line = lines[i + 3].strip()
            channels = [
                int(channel.strip().upper().replace("CH", "")) for channel in channel_line.split(",") if channel.strip()
            ]
            for channel in channels:
                if channel not in (1, 2, 3, 4, 5):
                    raise ValueError(
                        f"Invalid channel CH{channel}. Valid channels are CH1 to CH5."
                    )
            data['wavelength'].append(float(lines[i].strip()))
            data['power'].append(int(lines[i + 1].strip()))
            data['average'].append(lines[i + 2].strip())
            
            data['channel'].append(channels)
            # print("end of section interpretation: ", section)
            section += 1
            # Move to the next section after the current set of 4 lines
            i += 4

    print("======================= total parameter input: =======================")
    table_stdout(data)
    print("total number of parameter sets interpreted: ", len(data['wavelength']))
    input("please double check the parameters you input, press 'enter' to advance")
    save_to_json(json_file,data)
# this will directly ask how user want to set up things, should be avaliable in the future

if __name__ == "__main__":
    #main()
    interpreter()

# this will interpret the data in parameter.txt file into json format
if __name__ == "__parameter_interpreter.py__":
    interpreter()
