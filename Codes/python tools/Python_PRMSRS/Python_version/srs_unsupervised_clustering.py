from __future__ import annotations

import argparse

from prm_srs.clustering import srs_unsupervised_clustering


def main() -> None:
    parser = argparse.ArgumentParser(description="Port of srs_unsupervised_clustering.m")
    parser.add_argument("--base-folder", default="..\\PRM_SRS_Matlab_version\\srs_image")
    parser.add_argument("--data-folder", default="fixed brain")
    parser.add_argument("--output-folder", default="unsupervised_clusters")
    parser.add_argument("--n-clusters", type=int, default=8)
    args = parser.parse_args()
    srs_unsupervised_clustering(
        args.base_folder,
        data_folder=args.data_folder,
        output_folder=args.output_folder,
        n_clusters=args.n_clusters,
    )


if __name__ == "__main__":
    main()
