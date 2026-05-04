from __future__ import annotations

import argparse

from prm_srs.workflows import srs5_image_generation_copy


def main() -> None:
    parser = argparse.ArgumentParser(description="Port of srs5_image_generation_Copy.m")
    parser.add_argument("--root-folder", required=True, help="Folder containing the CH subfolders.")
    parser.add_argument("--output-folder", help="Optional output folder.")
    args = parser.parse_args()
    srs5_image_generation_copy(args.root_folder, output_folder=args.output_folder)


if __name__ == "__main__":
    main()
