import os
import argparse
import numpy as np
import tifffile as tiff


def load_image(path):
    """Load a TIFF image into a NumPy array."""
    return tiff.imread(path).astype(float)


def save_image(array, path):
    """Save a NumPy array as a TIFF image."""
    tiff.imwrite(path, array.astype(np.float32))


def main(input_dir, threshold, lipids):
    # Create output directory
    out_dir = os.path.join(input_dir, 'standardized')
    os.makedirs(out_dir, exist_ok=True)

    # Identify reference (PC) image
    reference_name = 'PC_convolution_image.tiff'
    reference_path = os.path.join(input_dir, reference_name)
    if not os.path.isfile(reference_path):
        raise FileNotFoundError(f"Reference image '{reference_name}' not found in {input_dir}")

    # Load reference
    reference = load_image(reference_path)
    # Avoid division by zero
    reference[reference == 0] = np.nan

    # Process each target lipid image
    for lipid in lipids:
        fname = f"{lipid}_convolution_image.tiff"
        target_path = os.path.join(input_dir, fname)
        if not os.path.isfile(target_path):
            print(f"Warning: {fname} not found, skipping.")
            continue

        target_img = load_image(target_path)

        # Standardize by dividing by PC reference
        standardized = target_img / reference

        # Apply threshold filter: set values below threshold to zero
        standardized[standardized < threshold] = 0

        # Save result
        out_name = fname.replace('_convolution', f'_std_thresh{threshold}')
        out_path = os.path.join(out_dir, out_name)
        save_image(standardized, out_path)

        print(f"Processed {fname} -> {out_name}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Divide specified lipid images by PC reference and threshold results.'
    )
    parser.add_argument(
        'input_dir', nargs='?', default=r'D:\study\Shi_Lab\Data\Training Muscle\Human Biopsy\Gastrocnemius Cut\CH-zoom4_out',
        help='Folder containing lipid *_convolution.tif images'
    )
    parser.add_argument(
        '--threshold', '-t', type=float, default=0.90,
        help='Threshold below which values are set to zero (default: 0.90)'
    )
    parser.add_argument(
        '--lipids', '-l', nargs='+', default=['TAG', 'Cardiolipin', 'Cholesterol'],
        help='List of lipid names to process (default: TAG, Cardiolipin, Cholesterol)'
    )
    args = parser.parse_args()
    main(args.input_dir, args.threshold, args.lipids)
