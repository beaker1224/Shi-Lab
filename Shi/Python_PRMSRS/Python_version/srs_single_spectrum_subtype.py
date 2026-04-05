from __future__ import annotations

import argparse

from prm_srs.workflows import score_spectrum_files


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Score a Raman spectrum file against lipid subtype references.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input-path",
        required=True,
        help="Path to a .txt/.csv spectrum file, or a folder containing spectrum files.",
    )
    parser.add_argument(
        "--output-csv",
        help="Optional output CSV path. Defaults beside the input file or inside the input folder.",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        help="Optional number of highest-scoring subtype possibilities to keep per file.",
    )
    args = parser.parse_args()
    score_spectrum_files(
        args.input_path,
        output_csv=args.output_csv,
        top_n=args.top_n,
    )


if __name__ == "__main__":
    main()
