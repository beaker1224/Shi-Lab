from __future__ import annotations

import argparse

from prm_srs.workflows import srs5_image_generation


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Port of srs5_image_generation.m",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--hyperspectra-folder",
        "--root-folder",
        dest="hyperspectra_folder",
        help="Absolute folder path containing the hyperspectral image files or leaf subfolders.",
        default=r"D:\Chrome\temp_group\test\1-CH",
    )
    parser.add_argument(
        "--raman-shift-start",
        type=float,
        help="Starting Raman shift position.",
        default=2700, 
    )
    parser.add_argument(
        "--raman-shift-end",
        type=float,
        help="Ending Raman shift position.",
        default=3100,
    )
    parser.add_argument(
        "--num-images",
        type=int,
        help="Number of images in the hyperspectral folder, used to build the interpolation grid.",
        default=71,
    )
    parser.add_argument("--output-folder", help="Optional output folder.")
    args = parser.parse_args()
    srs5_image_generation(
        args.hyperspectra_folder,
        output_folder=args.output_folder,
        raman_shift_start=args.raman_shift_start,
        raman_shift_end=args.raman_shift_end,
        image_count=args.num_images,
    )


if __name__ == "__main__":
    main()
