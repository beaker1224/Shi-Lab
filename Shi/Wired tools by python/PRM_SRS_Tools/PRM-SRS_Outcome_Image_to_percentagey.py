import os
import numpy as np
import tifffile

def filter_tiff_images_by_threshold(input_dir, threshold_percentage=0.9):
    """
    Reads all TIFF images in a directory, filters them based on a pixel
    value threshold, and saves the result in a subfolder named 'Percentage_filtered'.

    Args:
        input_dir (str): The path to the directory containing the original .tif files.
        threshold_percentage (float): The threshold (from 0.0 to 1.0) to apply.
                                      Pixel values above this will be set to max (white),
                                      and the rest to min (black).
    """
    # Automatically create the output directory as a subfolder
    output_dir = os.path.join(input_dir, f"{desired_threshold}_Percent_filtered")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created subfolder for output: {output_dir}")

    # Walk through every file in the input directory
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.tif', '.tiff')):
            input_path = os.path.join(input_dir, filename)
            
            # Save the filtered image with the same name in the new subfolder
            output_path = os.path.join(output_dir, filename)

            try:
                # Read the TIFF image into a NumPy array
                with tifffile.TiffFile(input_path) as tif:
                    image_array = tif.asarray()

                # Convert pixel values (0-255) to a percentage (0.0-1.0)
                percentage_array = image_array.astype(np.float32) / 255.0

                # Apply the threshold. The result is a boolean array (True/False).
                binary_array = percentage_array > threshold_percentage

                # Convert the boolean array to an 8-bit integer array (0 or 255)
                output_array = binary_array.astype(np.uint8) * 255

                # Save the new filtered array as a TIFF image
                tifffile.imwrite(output_path, output_array)

            except Exception as e:
                print(f"Could not process {filename}. Error: {e}")

if __name__ == '__main__':
    # --- Configuration ---
    # 1. Set the path to your folder containing the TIFF images.
    input_directory = r"D:\study\Shi_Lab\Data\Training Muscle\mice Biopsy\SOL\2-zoom4_out"

    # 2. Set your desired threshold value (e.g., 0.9 for 90%).
    desired_threshold = 0.75
    # --- End of Configuration ---

    # --- Script Execution ---
    if not os.path.isdir(input_directory):
        print(f"Error: Input directory not found at '{input_directory}'")
    else:
        filter_tiff_images_by_threshold(input_directory, desired_threshold)
        output_subfolder = os.path.join(input_directory, f"{desired_threshold}_Percent_filtered")
        print(f"\nProcessing complete. Filtered images are in: {output_subfolder}")