# helper_oir2tif.py

from pathlib import Path
import subprocess
from typing import List, Union
import argparse


def _find_bfconvert() -> Path:
    '''
    Args:
        None 
    Returns: 
        the path to bfconvert.bat for converting .oir to .tif
    Raise:
        when the bat file was not able to locate 
        in the folder where this script is
    '''
    # the underscore in the front of the function means that the function is private
    # which means that when importing, this function will not be imported
    # -> Path means that this function suppose to return a Path object.
    here = Path(__file__).resolve().parent
    parent = here.parent
    candidates = [
        here / "bfconvert.bat", here / "bftools" / "bfconvert.bat",
        parent / "bfconvert.bat", parent / "bftools" / "bfconvert.bat",
        # non-Windows fallbacks
        here / "bfconvert", here / "bftools" / "bfconvert",
        parent / "bfconvert", parent / "bftools" / "bfconvert",
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(
        "Could not find 'bfconvert' near this script. Expected in:\n"
        "  ./bfconvert(.bat) or ./bftools/bfconvert(.bat)\n"
        "  ../bfconvert(.bat) or ../bftools/bfconvert(.bat)"
    )


def _run(cmd: list):
    # Convenience: run bfconvert and show a readable error if it fails
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"bfconvert failed (exit {e.returncode}): {' '.join(cmd)}") from e


def oir_to_tiff(
    oir_root: Union[str, Path],
    recursive: bool = False,
    overwrite: bool = True,
    split_redox: bool = True,
) -> List[Path]:
    """
    Convert .oir -> plain .tif using bfconvert.
    - Standard files: <basename>.tif in a 'tiff_files' sibling folder.
    - 'redox' files (names containing '-redox-'): split channel 0/1 into
      <prefix>-fad.tif and <prefix>-nadh.tif, where prefix is ROI before '-redox-'.

    Variables:
    - oir_root: a path to the oir files you want to convert from oir to tif
    - recursive: True if the oir file under the subfolder also be found
    - overwrite: True if the current directory exist a such file and will rewrite this file
    - split_redox: True if you want the redox to be saved as fad and nadh (order matters)
    Returns:
        list of written TIFF paths.
    """
    bfconvert = _find_bfconvert()
    root = Path(oir_root).resolve()
    pattern = "**/*.oir" if recursive else "*.oir"

    written: List[Path] = []
    for oir in sorted(root.glob(pattern)):
        out_dir = oir.parent / "tiff_files"
        out_dir.mkdir(exist_ok=True)

        name_lower = oir.stem.lower()
        is_redox = split_redox and ("-redox-" in name_lower)

        if is_redox:
            # Everything before "-redox-" becomes the base prefix
            prefix = oir.stem.split("-redox-")[0]  # preserves original case before -redox-
            # Channel 0 -> FAD
            fad_path = out_dir / f"{prefix}-fad.tif"
            # Channel 1 -> NADH
            nadh_path = out_dir / f"{prefix}-nadh.tif"

            # Build commands
            base_cmd = [str(bfconvert)]
            if overwrite:
                base_cmd.append("-overwrite")

            # Channel 0
            cmd0 = base_cmd + ["-channel", "0", str(oir), str(fad_path)]
            _run(cmd0)
            written.append(fad_path)
            print(f"Wrote: {fad_path}")

            # Channel 1 (warn but continue if missing)
            cmd1 = base_cmd + ["-channel", "1", str(oir), str(nadh_path)]
            try:
                _run(cmd1)
                written.append(nadh_path)
                print(f"Wrote: {nadh_path}")
            except RuntimeError as e:
                print(f"Warning: could not write channel 1 for {oir.name} ({e}).")

        else:
            # Standard single-file conversion: all channels/planes in one multipage TIFF
            out_path = out_dir / f"{oir.stem}.tif"
            cmd = [str(bfconvert)]
            if overwrite:
                cmd.append("-overwrite")
            cmd.extend([str(oir), str(out_path)])
            _run(cmd)
            written.append(out_path)
            print(f"Wrote: {out_path}")

    if not written:
        print(f"No .oir files found under: {root}")
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Convert .oir -> .tif using bfconvert near this script. "
                                             "Special-case '-redox-' files into FAD/NADH per-channel TIFFs.")
    ap.add_argument("oir_root", help="Path to folder containing .oir files.")
    ap.add_argument("--no-recursive", dest="recursive", action="store_false", help="Do not recurse into subfolders.")
    ap.add_argument("--no-overwrite", dest="overwrite", action="store_false", help="Do not pass -overwrite.")
    ap.add_argument("--no-split-redox", dest="split_redox", action="store_false",
                    help="Treat '-redox-' files like normal (no per-channel split).")
    args = ap.parse_args()
    oir_to_tiff(args.oir_root, recursive=args.recursive, overwrite=args.overwrite, split_redox=args.split_redox)
