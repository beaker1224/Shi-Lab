import json
import os, sys
import pandas as pd
from pathlib import Path
import re

def table_stdout(data):
    """Print parameter rows as a bordered table without extra dependencies."""
    table = pd.DataFrame(data, columns=['wavelength', 'power', 'average', 'channel', 'resolution', 'dwell time'])
    table = table.rename(columns={'channel': 'channels'})
    table['channels'] = table['channels'].apply(
        lambda channels: ', '.join(f'CH{channel}' for channel in channels)
    )

    table = table.fillna('-')
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
    """Create an empty template text file with brief formatting instructions."""
    template = (
        "# Parameter input file\n"
        "# Format per block:\n"
        "# Line 1: Wavelength (float)\n"
        "# Line 2: Power (int)\n"
        "# Line 3: Average (string/float)\n"
        "# Line 4: Channels (comma-separated, e.g., CH1, CH2)\n"
        "# Line 5: Resolution (optional)\n"
        "# Line 6: Dwell Time (optional)\n"
        "# Separate each block with '--'\n\n"
    )
    Path(file_name).write_text(template, encoding='utf-8')

def parse_channels(channel_str: str, section_num: int) -> list[int]:
    """Parse and validate comma-separated channels (e.g., 'CH1, CH2' or '1, 2')."""
    raw_tokens = [tok.strip() for tok in channel_str.split(',') if tok.strip()]
    if not raw_tokens:
        raise ValueError(f"Channel line is empty.")

    channels = []
    for tok in raw_tokens:
        clean = tok.upper().replace("CH", "").strip()
        if not clean.isdigit():
            raise ValueError(f"Invalid channel '{tok}'. Must be in the format 'CH1' to 'CH5'.")
        
        ch_num = int(clean)
        if ch_num not in {1, 2, 3, 4, 5}:
            raise ValueError(f"Invalid channel 'CH{ch_num}'. Only channels CH1 to CH5 are allowed.")
        
        channels.append(ch_num)
    return channels

def parse_resolution(res_str: str) -> str:
    '''
    Parse and validate the resolution string. Accepts formats like "64", "64x64", or "  64 x 64  ".
    Returns the standardized format "64x64".
    '''
    clean = res_str.strip().lower()
    clean = clean.replace(" ", "").replace("*", "x")

    if clean.isdigit():
        clean = f"{clean}x{clean}"

    valid = {
        "64x64", "128x128", "256x256",
        "512x512", "1024x1024",
        "2048x2048", "4096x4096"
    }

    if clean not in valid:
        raise ValueError(
            f"Unsupported resolution: {res_str}"
        )

    return clean

def prompt_exit_error(message: str) -> None:
    """Display an error message and cleanly wait for user input before exiting."""
    print(f"\n[Formatting Error]: {message}")
    print("For formatting guidance, please see 'readMe.md'.")
    input("Press Enter to exit...")
    sys.exit(1)

def interpreter() -> None:
    '''
    This function interprets the parameters from 'parameters.txt' and saves them into 'parameters.json'.
    It reads the parameters in groups of four lines, where each group represents a set of parameters:
    1. Wavelength (float)
    2. Power (int)
    3. Average (string)
    4. Channels (comma-separated string, e.g., "CH1,CH2,CH3")
    5. Resolution (optional)
    6. Dwell Time (optional)
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
        print(f"Created template file '{txt_file}'.")
        input("Nothing input into 'parameters.txt'. Please populate it and press Enter to exit...")
        return
    # Initialize a dictionary with keys and empty lists
    data = {
        'wavelength': [],
        'power': [],
        'average': [],
        'channel': [],
        'resolution': [],
        'dwell time': []
    }

    try:
        content = Path(txt_file).read_text(encoding='utf-8')
    except Exception as err:
        prompt_exit_error(f"Could not read '{txt_file}': {err}")

    raw_sections = content.split('--')
    section_count = 0

    last_resolution = None
    last_dwell_time = None

    for raw_block in raw_sections:
        # Strip trailing/leading spaces, drop blank lines, and ignore comment lines (#)
        lines = [
            line.strip() 
            for line in raw_block.splitlines() 
            if line.strip() and not line.strip().startswith('#')
        ]

        if not lines:
            continue  # Blank block or trailing separator

        section_count += 1

        if len(lines) < 4:
            prompt_exit_error(
                f"Section {section_count} only has {len(lines)} line(s). "
                "Each set of parameters must have at least 4 lines: Wavelength, Power, Average, Channels."
            )

        try:
            wavelength = float(lines[0])
            power = int(lines[1])
            average = lines[2]
            channels = parse_channels(lines[3], section_count)

            # Optional 5th and 6th lines
            if len(lines) >= 5 and lines[4].strip():
                resolution = parse_resolution(lines[4])
                last_resolution = resolution
            else:
                resolution = last_resolution

            # Dwell Time: parse if provided and update last seen, otherwise carry forward
            if len(lines) >= 6 and lines[5].strip():
                dwell_time = float(lines[5])
                last_dwell_time = dwell_time
            else:
                dwell_time = last_dwell_time

        except ValueError as err:
            prompt_exit_error(f"Section {section_count} parsing error - {err}")

        # Store validated parameters
        data['wavelength'].append(wavelength)
        data['power'].append(power)
        data['average'].append(average)
        data['channel'].append(channels)
        data['resolution'].append(resolution)
        data['dwell time'].append(dwell_time)

    if section_count == 0:
        prompt_exit_error(f"No parameter blocks were found in '{txt_file}'.")

    print("\n======================= total parameter input: =======================")
    table_stdout(data)
    print("total number of parameter sets interpreted:", len(data['wavelength']))
    input("\nPlease double check the parameters above. Press Enter to confirm")
    
    save_to_json(json_file, data)
# this will directly ask how user want to set up things, should be avaliable in the future

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))
# Change the working directory to the script's directory
os.chdir(script_dir)

if __name__ == "__main__":
    #main()
    interpreter()

# this will interpret the data in parameter.txt file into json format
if __name__ == "__parameter_interpreter.py__":
    interpreter()
