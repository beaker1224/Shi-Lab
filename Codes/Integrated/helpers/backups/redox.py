import argparse
import concurrent.futures
import glob
import os
import re
from collections import defaultdict

import numpy as np
from skimage import io

# Recognize channel tokens; avoid files like "*masked*.tif" as masks
CHAN_RE = re.compile(r'(?i)(fad|nadh|mask)')
MASKED_RE = re.compile(r'(?i)masked')

def stem_and_channel(path):
    """
    Return (stem, channel) from a filename, where channel ∈ {'fad','nadh','mask'}.
    The 'stem' is the filename with the channel token removed.
    Examples:
      '1-fad.tif'        -> ('1', 'fad')
      'sample2_nadh.tif' -> ('sample2', 'nadh')
      'img-03_mask.tif'  -> ('img-03', 'mask')
    """
    base = os.path.splitext(os.path.basename(path))[0]
    if MASKED_RE.search(base):  # explicitly skip "masked" variants
        return None, None
    m = CHAN_RE.search(base)
    if not m:
        return None, None
    chan = m.group(1).lower()
    # remove the matched token and any adjacent separators to form the stem
    start, end = m.span()
    stem = (base[:start] + '_' + base[end:]).strip('_- .')
    # collapse leftover separators
    stem = re.sub(r'[\W_]+', '_', stem).strip('_')
    if not stem:
        stem = "unnamed"
    return stem.lower(), chan

def first_plane(a):
    # If a stack, take first plane (customize if you want max/projection)
    return a[0] if a.ndim > 2 else a

def process_images(root_dir: str) -> None:
    """
    For each subfolder under root_dir, group files by stem and compute:
      redox = FAD / (FAD + NADH) * mask
    Saves one TIFF per group: redox_ratio_<stem>.tif (float32).
    """
    for subdir, _, _ in os.walk(root_dir):
        tif_files = sorted(glob.glob(os.path.join(subdir, "*.tif")))
        if not tif_files:
            continue

        # Group files by stem
        groups = defaultdict(dict)  # stem -> { 'fad': path, 'nadh': path, 'mask': path }
        for f in tif_files:
            stem, chan = stem_and_channel(f)
            if stem and chan:
                # warn on duplicate channel per stem, last one wins
                if chan in groups[stem]:
                    print(f"[WARN] Duplicate {chan} for stem '{stem}' in {subdir}; using {os.path.basename(f)}")
                groups[stem][chan] = f

        if not groups:
            continue

        for stem, files in groups.items():
            fad_path  = files.get('fad')
            nadh_path = files.get('nadh')
            mask_path = files.get('mask')

            if not mask_path:
                missing = "Mask"
                print(f"[Warn] Missing {missing} for stem '{stem}' in {subdir}")
                continue

            if not fad_path or not nadh_path:
                missing = " and ".join([k for k in ('FAD','NADH') if files.get(k.lower()) is None])
                print(f"[SKIP] Missing {missing} for stem '{stem}' in {subdir}")
                continue

            out_path = os.path.join(subdir, f"{stem}-redox_ratio.tif")
            if os.path.exists(out_path):
                print(f"[SKIP] Exists: {out_path}")
                continue

            try:
                fad  = first_plane(io.imread(fad_path)).astype(np.float32)
                nadh = first_plane(io.imread(nadh_path)).astype(np.float32)
                if mask_path:
                    m = first_plane(io.imread(mask_path))
                    # binarize mask: any >0 becomes 1.0
                    mask = (m > 0).astype(np.float32)
                else:
                    mask = np.ones_like(fad, dtype=np.float32)
            except Exception as e:
                print(f"[READ FAIL] '{stem}' in {subdir}: {e}")
                continue

            if fad.shape != nadh.shape or fad.shape != mask.shape:
                print(f"[SHAPE MISMATCH] '{stem}' in {subdir}: FAD{fad.shape}, NADH{nadh.shape}, MASK{mask.shape}")
                continue

            denom = fad + nadh
            redox = np.divide(fad, denom, out=np.zeros_like(fad, dtype=np.float32), where=denom != 0)
            redox *= mask

            try:
                io.imsave(out_path, redox.astype(np.float32), check_contrast=False)
                print(f"[SAVED] {out_path}")
            except Exception as e:
                print(f"[WRITE FAIL] {out_path}: {e}")

def process_folder(folder_path: str) -> None:
    print(f"Processing folder: {folder_path}")
    process_images(folder_path)
    print(f"Finished processing folder: {folder_path}")

def main():
    parser = argparse.ArgumentParser(description="Process images to calculate redox ratios.")
    parser.add_argument(
        "folders",
        nargs="*",
        default=[r"D:\Chrome\Rapamycin\data\gut\Ctrl2\tiff_files"],
        help="Folders to process."
    )
    args = parser.parse_args()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(process_folder, args.folders)

if __name__ == "__main__":
    main()
