"""
Mask TIFF images in one or more folders using a fractional threshold.

For each input folder:
- Reads all *.tif / *.tiff images (non-recursive by default).
- Computes an absolute threshold from a fraction in [0, 1].
- Sets all pixels BELOW that threshold to 0; preserves dtype and size.
- Saves outputs (same filenames) in a "prm_srs_masked" subfolder.

Examples
--------
# One threshold for all folders:
python mask_tiffs.py /path/to/folder1 /path/to/folder2 --frac 0.8

# Ask interactively per folder (no --frac):
python mask_tiffs.py /path/to/folder1 /path/to/folder2

# Recursive search and overwrite existing outputs:
python mask_tiffs.py /path/to/folder --frac 0.75 --recursive --overwrite
"""
from __future__ import annotations
import argparse
import os, re
from pathlib import Path
from typing import Iterable, List, Tuple, Dict
import numpy as np
import tifffile as tiff


def list_tiffs(folder: Path, recursive: bool = False) -> List[Path]:
    patterns = ["*.tif", "*.tiff", "*.TIF", "*.TIFF"]
    folder = Path(folder)
    if recursive:
        files = [p for pat in patterns for p in folder.rglob(pat)]
    else:
        files = [p for pat in patterns for p in folder.glob(pat)]
    # Deduplicate while preserving order
    seen = set()
    out = []
    for f in files:
        if f.is_file() and f not in seen:
            seen.add(f)
            out.append(f)
    return out

# -----------------------------CD CH----------------------------


# Match: <ROI>-<wavelength>nm-<anything>.tif[f]
NAME_RE = re.compile(
    r"^(?P<roi>\d+)-(?P<wl>787\.6|791\.3|794\.6|797\.2|841\.8|844\.6|862(?:\.0)?)nm-.*\.(?:tif|tiff)$",
    re.IGNORECASE,
)

# Match mask: <ROI>-mask.tif[f]
MASK_RE = re.compile(r"^(?P<roi>\d+)-mask\.(?:tif|tiff)$", re.IGNORECASE)

# Ratio definitions: (output_suffix, numerator_wl, denominator_wl)
RATIOS: Tuple[Tuple[str, float, float], ...] = (
    ("uns_sat",        787.6, 797.2),
    ("CD_CH-protein",  841.8, 791.3),
    ("CD_CH-lipid",    844.6, 794.6),
)

def parse_name(p: Path):
    m = NAME_RE.match(p.name)
    if not m:
        return None
    return m.group("roi"), float(m.group("wl"))

def parse_mask_name(p: Path):
    m = MASK_RE.match(p.name)
    if not m:
        return None
    return m.group("roi")

def safe_divide(numer: np.ndarray, denom: np.ndarray, zero_value: float = 0.0) -> np.ndarray:
    """Elementwise numer/denom with divide-by-zero handling. Returns float32."""
    numer = numer.astype(np.float32, copy=False)
    denom = denom.astype(np.float32, copy=False)
    out = np.empty_like(numer, dtype=np.float32)
    nz = denom != 0.0
    np.divide(numer, denom, out=out, where=nz)
    out[~nz] = zero_value
    return out

def load_tiff_2d(path: Path) -> np.ndarray:
    arr = tiff.imread(path)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D TIFF, got shape {arr.shape} at {path.name}")
    return arr

def apply_mask_CD(arr: np.ndarray, mask: np.ndarray, mask_out_value: float = 0.0) -> np.ndarray:
    """
    Apply mask to arr. Any pixel where mask <= 0 is set to mask_out_value.
    Mask can be binary {0,1} or {0,255} or any positive/zero image.
    """
    if mask.shape != arr.shape:
        raise ValueError(f"Mask shape {mask.shape} does not match image {arr.shape}")
    m = mask > 0
    out = arr.copy()
    out[~m] = mask_out_value
    return out

def compute_turnover(
    folder: str | Path,
    recursive: bool = False,
    overwrite: bool = True,
    zero_value: float = 0.0,       # value used where denominator==0
    mask_out_value: float = 0.0,   # value used outside mask (set to np.nan if preferred)
) -> None:
    """
    Finds TIFFs via list_tiffs(), groups by ROI, computes:
      787.6/797.2 -> ROI-uns_sat.tif
      841.8/791.3 -> ROI-CD_CH-protein.tif
      844.6/794.6 -> ROI-CD_CH-lipid.tif
    If ROI-mask.tif[f] exists, it is applied to the ratio result.
    Saves outputs as float32 TIFFs in the SAME folder.
    """
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(folder)

    paths = list_tiffs(folder, recursive=recursive)

    # Collect: ROI -> wavelength -> path, and ROI -> mask path
    by_roi: Dict[str, Dict[float, Path]] = {}
    masks: Dict[str, Path] = {}
    seen_for_roi_wl: set[tuple[str, float]] = set()

    for p in paths:
        m_roi = parse_mask_name(p)
        if m_roi:
            if m_roi in masks:
                print(f"[warn] Duplicate mask for ROI {m_roi}: {p.name} (keeping first)")
            else:
                masks[m_roi] = p
            continue

        parsed = parse_name(p)
        if not parsed:
            continue
        roi, wl = parsed
        key = (roi, wl)
        if key in seen_for_roi_wl:
            print(f"[warn] Duplicate for ROI {roi}, {wl} nm: {p.name} (keeping first)")
            continue
        seen_for_roi_wl.add(key)
        by_roi.setdefault(roi, {})[wl] = p

    if not by_roi:
        print("[info] No matching TIFFs found.")
        return

    for roi, wl_map in sorted(by_roi.items(), key=lambda kv: int(kv[0])):
        print(f"\n[ROI {roi}]")
        # Load mask once per ROI (optional)
        roi_mask = None
        if roi in masks:
            try:
                roi_mask = load_tiff_2d(masks[roi])
            except Exception as e:
                print(f"  [warn] Could not load mask {masks[roi].name}: {e}. Proceeding without mask.")

        for out_suffix, num_wl, den_wl in RATIOS:
            num_p = wl_map.get(num_wl)
            den_p = wl_map.get(den_wl)
            out_path = (folder / f"{roi}-{out_suffix}.tif")

            if num_p is None or den_p is None:
                missing = []
                if num_p is None: missing.append(str(num_wl))
                if den_p is None: missing.append(str(den_wl))
                print(f"  [skip] Missing wavelength(s): {', '.join(missing)} nm")
                continue

            if out_path.exists() and not overwrite:
                print(f"  [skip] {out_path.name} exists (overwrite=False)")
                continue

            numer = load_tiff_2d(num_p)
            denom = load_tiff_2d(den_p)
            if numer.shape != denom.shape:
                print(f"  [skip] Shape mismatch {numer.shape} vs {denom.shape} for {num_p.name} / {den_p.name}")
                continue

            ratio = safe_divide(numer, denom, zero_value=zero_value)

            # Apply mask if present and shape matches
            if roi_mask is not None:
                if roi_mask.shape == ratio.shape:
                    ratio = apply_mask_CD(ratio, roi_mask, mask_out_value=mask_out_value)
                else:
                    print(f"  [warn] Mask shape {roi_mask.shape} != image {ratio.shape}; skipping mask for this ROI.")

            tiff.imwrite(out_path, ratio, dtype=np.float32)
            print(f"  [ok] {num_wl} / {den_wl} → {out_path.name}" + (" (masked)" if roi_mask is not None else ""))

# --------------------------- PRM SRS ----------------------------
def compute_abs_threshold(img: np.ndarray, frac: float) -> float:
    """
    Convert a fractional threshold in [0,1] to an absolute value suitable for img's dtype.

    Rules:
    - Integer dtype: use dtype max (e.g., 255 for uint8, 65535 for uint16).
    - Float dtype: if data looks normalized (0..1), use 1.0; else use the image's max.
    """
    if np.issubdtype(img.dtype, np.integer):
        maxv = np.iinfo(img.dtype).max
        return float(frac * maxv)
    else:
        # float or other: decide based on observed range
        imax = float(np.nanmax(img))
        imin = float(np.nanmin(img))
        # If data already 0..1 (common), use 1.0; else scale to the observed max
        base = 1.0 if 0.0 <= imin <= 1.0 and 0.0 <= imax <= 1.0 else (imax if imax > 0 else 1.0)
        return float(frac * base)


def apply_mask_PRM(img: np.ndarray, thr: float) -> np.ndarray:
    """
    Set values strictly below threshold to 0, keep others unchanged. Preserves dtype.
    Works for nD arrays (2D images, 3D stacks, multi-channel, etc.).
    """
    # Build a boolean mask of pixels to keep
    keep = img >= thr
    # For integer arrays, direct where() preserves dtype; for float, same.
    return np.where(keep, img, np.zeros(1, dtype=img.dtype))


def mask_prm_srs(folder: Path, frac: float = 0.8, out_subdir: str = "prm_srs_masked",
                recursive: bool = False, overwrite: bool = False) -> Tuple[int, int]:
    """
    Process all TIFFs in a folder.

    Args:
        folder (Path): Path to the root PRM-SRS output folder
        frac (float): default: 0.8. A number that the threshold should be
        out_subdir (str): a name for the output folder, default:"prm_srs_masked"
        recursive (bool): default: False. If the script will recursive search for its subfolder for tiff images
        overwrite (bool): default: False. If the output has similar file name, if the old file be overwritten 

    Returns
    -------
    (num_processed, num_skipped)
    """
    folder = Path(folder)
    files = list_tiffs(folder, recursive=recursive)
    out_dir = folder / out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    n_ok = 0
    n_skip = 0

    for src in files:
        dst = out_dir / src.name
        if dst.exists() and not overwrite:
            n_skip += 1
            continue
        try:
            img = tiff.imread(src)
            thr = compute_abs_threshold(img, frac)
            masked = apply_mask_PRM(img, thr)
            # Write with same dtype; compress modestly to save space
            tiff.imwrite(dst, masked, compression="zlib")
            n_ok += 1
        except Exception as exc:
            print(f"[ERROR] {src} -> {dst}: {exc}")
            n_skip += 1
    return n_ok, n_skip


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Mask TIFF images below a fractional threshold.")
    p.add_argument("folders", nargs="+", type=Path,
                   help="One or more folders containing .tif/.tiff images.")
    p.add_argument("--frac", type=float, default=None,
                   help="Threshold fraction in [0,1]. If omitted, you'll be prompted per folder.")
    p.add_argument("--recursive", action="store_true",
                   help="Search for TIFFs in subfolders recursively.")
    p.add_argument("--overwrite", action="store_true",
                   help="Overwrite existing outputs if present.")
    p.add_argument("--out-subdir", default="prm_srs_masked",
                   help='Name of output subfolder (default: "prm_srs_masked").')
    return p.parse_args()


def main():
    args = parse_args()

    # Validate folders
    folders: List[Path] = []
    for f in args.folders:
        if not f.exists() or not f.is_dir():
            print(f"[WARN] Skipping non-existent or non-directory: {f}")
            continue
        folders.append(f)
    if not folders:
        raise SystemExit("No valid folders provided.")

    # Determine per-folder threshold fractions
    fracs: List[float] = []
    if args.frac is not None:
        if not (0.0 <= args.frac <= 1.0):
            raise SystemExit("--frac must be between 0 and 1")
        fracs = [args.frac] * len(folders)
    else:
        # Prompt interactively per folder
        for f in folders:
            while True:
                try:
                    s = input(f"Enter threshold fraction [0..1] for {f}: ").strip()
                    val = float(s)
                    if 0.0 <= val <= 1.0:
                        fracs.append(val)
                        break
                except Exception:
                    pass
                print("  Invalid input. Please enter a number between 0 and 1 (e.g., 0.8).")

    # Process
    total_ok = 0
    total_skip = 0
    for f, frac in zip(folders, fracs):
        print(f"\n[INFO] Folder: {f}")
        print(f"[INFO] Threshold fraction: {frac}")
        n_ok, n_skip = mask_prm_srs(
            f, frac, out_subdir=args.out_subdir,
            recursive=args.recursive, overwrite=args.overwrite
        )
        print(f"[DONE] Wrote: {n_ok}, Skipped: {n_skip}")
        total_ok += n_ok
        total_skip += n_skip

    print(f"\n[SUMMARY] Total wrote: {total_ok}, total skipped: {total_skip}")


if __name__ == "__main__":
    main()
