from __future__ import annotations

import argparse

from prm_srs.workflows import srs_lipid_subtype


def main() -> None:
    parser = argparse.ArgumentParser(description="Port of srs_lipid_subtype.m")
    parser.add_argument("--root-folder", required=True)
    parser.add_argument("--output-folder")
    args = parser.parse_args()
    srs_lipid_subtype(args.root_folder, output_folder=args.output_folder)


if __name__ == "__main__":
    main()
