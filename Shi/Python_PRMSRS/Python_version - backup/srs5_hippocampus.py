from __future__ import annotations

import argparse

from prm_srs.workflows import srs5_hippocampus


def main() -> None:
    parser = argparse.ArgumentParser(description="Port of srs5_hippocampus.m")
    parser.add_argument("--root-folder", default="..\\PRM_SRS_Matlab_version\\hippocampus_dataset")
    parser.add_argument("--output-folder")
    args = parser.parse_args()
    srs5_hippocampus(args.root_folder, output_folder=args.output_folder)


if __name__ == "__main__":
    main()
