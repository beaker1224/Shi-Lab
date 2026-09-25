import os
import numpy as np
import tifffile as tiff
import tkinter as tk
from tkinter import filedialog

def select_directory():
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title="Select Directory Containing TIFF Image")
    return directory

def load_tiff_image(directory):
    # Find the TIFF file named "redox_ratio.tif" in the directory
    image_path = os.path.join(directory, "redox_ratio.tif")
    if not os.path.exists(image_path):
        raise FileNotFoundError("No TIFF file named 'redox_ratio.tif' found in the selected directory.")
    
    image = tiff.imread(image_path)
    return image

def compute_redox_ratio_average(image):
    # Mask out background (zero values)
    masked_image = image[image > 0]
    if masked_image.size == 0:
        raise ValueError("No valid redox ratio values found in the image.")
    
    average_redox = np.mean(masked_image)
    return average_redox

def main():
    try:
        directory = select_directory()
        if not directory:
            print("No directory selected. Exiting.")
            return
        
        image = load_tiff_image(directory)
        average_redox = compute_redox_ratio_average(image)
        
        print(f"Average Redox Ratio (excluding background): {average_redox:.6f}")
        
        # Save the average redox ratio to a text file
        with open(os.path.join(directory, "redox_ratio.txt"), "w") as f:
            f.write(f"Average Redox Ratio: {average_redox:.6f}\n")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
