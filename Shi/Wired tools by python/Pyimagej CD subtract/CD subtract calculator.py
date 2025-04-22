import imagej
import os
import re
import tifffile
import numpy as np

# Initialize ImageJ
ij = imagej.init("sc.fiji:fiji")
ij.getVersion()

# Define input and output directories
INPUT_DIR = "path/to/your/images"
OUTPUT_DIR = "path/to/output/folder"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Regex pattern to extract metadata from filenames
FILENAME_PATTERN = re.compile(
    r"(?P<roi>\d+)[-_](?P<wavelength>[\d\.]+)nm[-_](?P<power>\d+)mW[-_]zoom(?P<zoom>\d+)"
)

# Organize files by ROI
roi_data = {}
for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".oir"):
        match = FILENAME_PATTERN.match(filename)
        if match:
            roi, wavelength = match.group("roi"), match.group("wavelength")
            roi_data.setdefault(roi, {"background": None, "cd_images": [], "mask": None})
            
            if wavelength == "862":
                roi_data[roi]["background"] = filename
            elif wavelength.lower() == "mask":
                roi_data[roi]["mask"] = filename
            else:
                roi_data[roi]["cd_images"].append(filename)

def process_roi(roi, files):
    """Processes images for a specific ROI."""
    background, cd_images = files["background"], files["cd_images"]
    if not background or not cd_images:
        print(f"Skipping ROI {roi} due to missing images.")
        return
    
    bg_path = os.path.join(INPUT_DIR, background)
    bg_img = ij.io().open(bg_path)
    
    for cd_file in cd_images:
        cd_path = os.path.join(INPUT_DIR, cd_file)
        cd_img = ij.io().open(cd_path)
        
        # Subtract background
        result_img = ij.op().image().calculator(cd_img, "Subtract", bg_img)
        
        # Apply LUT
        ij.op().image().applyLut(result_img, "Fire")
        
        # Save output
        output_filename = f"Processed_{cd_file.replace('.oir', '.tiff')}"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        ij.io().save(result_img, output_path)
        print(f"Saved: {output_filename}")

# Process all ROIs
for roi, files in roi_data.items():
    process_roi(roi, files)

print("Image processing complete.")
