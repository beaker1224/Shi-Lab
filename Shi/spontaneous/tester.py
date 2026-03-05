from pathlib import Path
from typing import List, Union, Dict, Any
import re
from helpers import subtract_BG

# import from your helper module
# from raman_bgsub_helper import background_subtraction, ROI_RE, BG_RE

# If you don't want to import regexes, re-define them here:
ROI_RE = re.compile(r"^(?P<prefix>.*)_(?P<roi>\d+)\.txt$", re.IGNORECASE)
BG_RE  = re.compile(r"^(?P<prefix>.*)_(?P<roi>\d+)_BG\.txt$", re.IGNORECASE)

def folder_has_roi_bg(folder: Path, require_bg: bool = False) -> bool:
    """Return True if folder contains ROI files (and optionally BG files) matching required suffix patterns."""
    has_roi = False
    has_bg = False

    for p in folder.iterdir():
        if not p.is_file():
            continue
        name = p.name
        if BG_RE.match(name):
            has_bg = True
        elif ROI_RE.match(name):
            has_roi = True

        if has_roi and (has_bg or not require_bg):
            return True

    return False


def run_background_subtraction_recursively(
    root_folder: Union[str, Path],
    output_subfolder: str = "background_subtracted",
    require_bg: bool = False,
) -> List[Dict[str, Any]]:
    """
    Recursively find data folders under root_folder and run background_subtraction() on each.
    Outputs are written inside each folder as <folder>/<output_subfolder>/.
    """
    root = Path(root_folder).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Not a valid root folder: {root}")

    results: List[Dict[str, Any]] = []

    for folder in [root] + [p for p in root.rglob("*") if p.is_dir()]:
        # Skip output folders (avoid re-processing)
        if folder.name.lower() == output_subfolder.lower():
            continue

        if folder_has_roi_bg(folder, require_bg=require_bg):
            summary = subtract_BG.background_subtraction(folder, output_subfolder=output_subfolder)
            results.append(summary)

    return results


# Example usage:
if __name__ == "__main__":
    root = r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Rapa_D40\Gut"  # or whatever your root is
    summaries = run_background_subtraction_recursively(root, require_bg=False)

    # quick report
    total_pairs = sum(s["paired_written"] for s in summaries)
    total_folders = len(summaries)
    print(f"Processed {total_folders} folder(s), wrote {total_pairs} BG-subtracted spectra total.")

    # show folders with issues
    for s in summaries:
        if s["missing_bg_indices"] or s["missing_roi_indices"] or s["errors"]:
            print("\n--- Issues in:", s["folder"])
            if s["missing_bg_indices"]:
                print("  Missing BG:", s["missing_bg_indices"])
            if s["missing_roi_indices"]:
                print("  Missing ROI:", s["missing_roi_indices"])
            if s["errors"]:
                print("  Errors:")
                for e in s["errors"]:
                    print("   -", e)