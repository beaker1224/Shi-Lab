"""
quantitative.py -- ratio maps (CD/CH, unsaturation, redox), masked with create_mask's masks.

Pipeline:
    1. create_mask.thresholding_mask(folder)   ->  <ROI>-mask.tif for every ROI
    2. quantitative.quantify(folder)           ->  <ROI>-<ratio>.tif for every ROI

File naming (the same ROI convention as create_mask.py: ROI = text before the first "-"):
    <ROI>-<wavelength>nm-<anything>.tif      e.g. 1-841.8nm-scan.tif
    <ROI>-...fad....tif / <ROI>-...nadh....tif   e.g. 1-fad.tif, 1-NADH-ctrl.tif
    <ROI>-mask.tif                           made by create_mask.py
Outputs go next to the inputs as <ROI>-<ratio name>.tif (float32).

Each ratio in RATIOS is computed for every ROI that has all of its images:
    uns_sat        787.6 nm / 797.2 nm
    CD_CH-protein  841.8 nm / 791.3 nm
    CD_CH-lipid    844.6 nm / 794.6 nm
    redox_ratio    FAD / (FAD + NADH)
Ratios are computed from the raw images; the mask only decides which pixels are kept.

Usage:
    from quantitative import quantify, compute_turnover, compute_redox
    quantify(r"D:/data/session1")                        # every ratio that applies
    quantify(r"D:/data/session1", recursive=True)        # ... in subfolders too
    compute_turnover(r"D:/data/session1")                # CD/CH + uns_sat only
    compute_redox(r"D:/data/gut/Ctrl2/tiff_files")       # redox only (searches subfolders)

    python quantitative.py D:/data/session1 D:/data/session2 --recursive
    python quantitative.py D:/data/session1 --ratios redox_ratio --outside nan
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import tifffile as tiff


# Naming rules and the mask file name live in mask.py (same folder as this file)
if __package__:   # imported as part of a package, e.g. "from helpers.quantitative import ..."
    from .mask import MASK_SUFFIX, ROI_PATTERN, _find_tiffs, _natural_key
else:             # run directly, e.g. "python quantitative.py ..." inside helpers/
    from mask import MASK_SUFFIX, ROI_PATTERN, _find_tiffs, _natural_key

# ---------------------------------------------------------------------------
# Ratio definitions -- add or edit entries here.
#   name: (numerator channels, denominator channels); channels listed together are summed.
#   A channel is a wavelength (e.g. "841.8", found as "-841.8nm" in the file name)
#   or a named channel ("fad", "nadh").
# ---------------------------------------------------------------------------
RATIOS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "uns_sat":       (("787.6",), ("797.2",)),
    "CD_CH-protein": (("841.8",), ("791.3",)),
    "CD_CH-lipid":   (("844.6",), ("794.6",)),
    "redox_ratio":   (("fad",),   ("fad", "nadh")),   # FAD / (FAD + NADH)
}
CD_CH_RATIOS = ("uns_sat", "CD_CH-protein", "CD_CH-lipid")
REDOX_RATIOS = ("redox_ratio",)

# How channels are recognised in a file name (the part after "<ROI>-")
NAMED_CHANNEL_RE = re.compile(r"(?<![a-z])(fad|nadh)(?![a-z])", re.IGNORECASE)
WAVELENGTH_RE = re.compile(r"(?:^|-)(\d+(?:\.\d+)?)nm(?![a-z])", re.IGNORECASE)
SKIP_NAME_RE = re.compile(r"masked", re.IGNORECASE)   # e.g. 1-fad-masked.tif: an output, not an input
EXTRA_SKIP_DIRS = {"prm_srs_masked"}                  # left over from the old threshold-masking step


# ---------------------------------------------------------------------------
# Finding the images
# ---------------------------------------------------------------------------
def _norm_channel(c: str) -> str:
    """'862.0' -> '862', '791.3' -> '791.3', 'FAD' -> 'fad'."""
    try:
        return f"{float(c):g}"
    except ValueError:
        return c.lower()


def _label(c: str) -> str:
    return c.upper() if c.isalpha() else f"{c} nm"


def channel_of(rest: str) -> str | None:
    """Channel of a file, from the part of its name after '<ROI>-'. Named channels win,
    so '1-fad-890nm.tif' is FAD, not 890 nm."""
    m = NAMED_CHANNEL_RE.search(rest)
    if m:
        return m.group(1).lower()
    m = WAVELENGTH_RE.search(rest)
    if m:
        return _norm_channel(m.group(1))
    return None


def find_channels(root, recursive: bool = False) -> dict[tuple[Path, str], dict[str, Path]]:
    """Group the input TIFFs under `root` by (folder, ROI) -> {channel: path}.

    Skips masks, previous ratio outputs, '*masked*' files and the processed / prm_srs_masked
    folders. If a ROI has two images of the same channel, the first is used.
    """
    root = Path(root)
    outputs = {n.lower() for n in RATIOS}
    groups: dict[tuple[Path, str], dict[str, Path]] = {}
    for p in _find_tiffs(root, recursive):
        if any(d.lower() in EXTRA_SKIP_DIRS for d in p.relative_to(root).parts[:-1]):
            continue
        m = ROI_PATTERN.match(p.name)
        if not m:
            continue
        roi = m.group(1)
        rest = p.stem[len(roi) + 1:]
        if (p.stem.lower() == f"{roi}{MASK_SUFFIX}".lower() or rest.lower() in outputs
                or SKIP_NAME_RE.search(rest)):
            continue
        ch = channel_of(rest)
        if ch is None:
            continue
        chans = groups.setdefault((p.parent, roi), {})
        if ch in chans:
            print(f"[warn] {p.parent.name} / ROI {roi}: two {_label(ch)} images "
                  f"({chans[ch].name}, {p.name}); using {chans[ch].name}")
            continue
        chans[ch] = p
    return groups


# ---------------------------------------------------------------------------
# Maths
# ---------------------------------------------------------------------------
def safe_divide(numer: np.ndarray, denom: np.ndarray, zero_value: float = 0.0) -> np.ndarray:
    """Elementwise numer / denom; `zero_value` where denom == 0. Returns float64."""
    out = np.full(np.broadcast(numer, denom).shape, zero_value, dtype=np.float64)
    np.divide(numer, denom, out=out, where=denom != 0)
    return out


def _load_plane(path: Path) -> np.ndarray:
    """Read a single-channel 2-D image; for a stack, use its first plane."""
    a = np.squeeze(tiff.imread(str(path)))
    if a.ndim == 2:
        return a
    if a.ndim == 3 and a.shape[-1] in (3, 4):
        raise ValueError(f"{path.name} looks like an RGB image {a.shape}; "
                         "ratios need single-channel images")
    print(f"    [note] {path.name} is a stack {a.shape}; using its first plane")
    return a.reshape(-1, *a.shape[-2:])[0]


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def quantify(
    folder,
    ratios=None,
    recursive: bool = False,
    overwrite: bool = True,
    require_mask: bool = True,
    outside: float = 0.0,
    zero_value: float = 0.0,
) -> list[Path]:
    """
    Compute ratio maps for every ROI under `folder` and save <ROI>-<ratio>.tif next to the inputs.

    Args:
        folder: Folder with the images and the <ROI>-mask.tif files from create_mask.py.
        ratios: Names from RATIOS to compute (default: all; each runs only where its images exist).
        recursive: Also process subfolders. Each folder is handled on its own.
        overwrite: Replace existing outputs (default). False keeps them.
        require_mask: Skip ROIs without <ROI>-mask.tif (default). False computes them unmasked.
        outside: Value written outside the mask, e.g. 0.0 (default) or np.nan.
        zero_value: Value where the denominator is 0 inside the mask.

    Returns:
        Paths of the ratio images written.
    """
    root = Path(folder)
    if not root.is_dir():
        raise NotADirectoryError(root)
    names = list(RATIOS) if ratios is None else [ratios] if isinstance(ratios, str) else list(ratios)
    unknown = [n for n in names if n not in RATIOS]
    if unknown:
        raise ValueError(f"Unknown ratio(s) {unknown}; choose from {list(RATIOS)}")
    defs = {n: (tuple(map(_norm_channel, RATIOS[n][0])), tuple(map(_norm_channel, RATIOS[n][1])))
            for n in names}

    groups = find_channels(root, recursive)
    written: list[Path] = []
    n_roi = 0
    for sub, roi in sorted(groups, key=lambda k: (_natural_key(str(k[0])), _natural_key(k[1]))):
        chans = groups[(sub, roi)]
        todo, partial = [], []
        for name, (num, den) in defs.items():
            needed = set(num) | set(den)
            have = needed & chans.keys()
            if have == needed:
                todo.append(name)
            elif have:  # some but not all images of this ratio: worth a warning
                partial.append((name, sorted(needed - have)))
        if not todo and not partial:
            continue  # none of the requested ratios apply to this ROI

        n_roi += 1
        where = f"ROI {roi}" if sub == root else f"{sub.relative_to(root).as_posix()} / ROI {roi}"
        print(f"\n[{where}]")
        for name, missing in partial:
            print(f"  [skip] {name}: missing " + ", ".join(_label(c) for c in missing))
        if not todo:
            continue

        mask_path = sub / f"{roi}{MASK_SUFFIX}.tif"
        mask = None
        if mask_path.exists():
            try:
                mask = np.squeeze(tiff.imread(str(mask_path))) > 0
            except Exception as e:
                print(f"  [warn] could not read {mask_path.name}: {e}")
        if mask is None:
            if require_mask:
                print(f"  [skip] no {mask_path.name}; make it with create_mask.thresholding_mask(), "
                      "or pass require_mask=False to compute without a mask")
                continue
            print(f"  [warn] no {mask_path.name}; ratios are UNMASKED")

        planes: dict[str, np.ndarray] = {}
        for name in todo:
            num, den = defs[name]
            out_path = sub / f"{roi}-{name}.tif"
            if out_path.exists() and not overwrite:
                print(f"  [skip] {out_path.name} exists (overwrite=False)")
                continue
            try:
                for c in (*num, *den):
                    if c not in planes:
                        planes[c] = _load_plane(chans[c]).astype(np.float64)
            except Exception as e:
                print(f"  [fail] {name}: could not read {chans[c].name}: {e}")
                continue
            shapes = {_label(c): planes[c].shape for c in dict.fromkeys((*num, *den))}
            if mask is not None:
                shapes["mask"] = mask.shape
            if len(set(shapes.values())) > 1:
                print(f"  [skip] {name}: image sizes differ: "
                      + ", ".join(f"{k} {v}" for k, v in shapes.items()))
                continue

            ratio = safe_divide(sum(planes[c] for c in num), sum(planes[c] for c in den), zero_value)
            if mask is not None:
                ratio[~mask] = outside
            tiff.imwrite(str(out_path), ratio.astype(np.float32))
            written.append(out_path)

            top = " + ".join(_label(c) for c in num)
            bottom = " + ".join(_label(c) for c in den)
            formula = f"{top} / ({bottom})" if len(den) > 1 else f"{top} / {bottom}"
            print(f"  [ok] {name} = {formula} -> {out_path.name}"
                  + ("" if mask is not None else "  (unmasked)"))

    if not n_roi:
        print(f"[info] No images for {', '.join(names)} found in {root}")
    return written


def compute_turnover(folder, recursive: bool = False, overwrite: bool = True,
                     zero_value: float = 0.0, mask_out_value: float = 0.0,
                     require_mask: bool = True) -> list[Path]:
    """CD/CH and unsaturation ratios only (same name and arguments as the old function)."""
    return quantify(folder, ratios=CD_CH_RATIOS, recursive=recursive, overwrite=overwrite,
                    require_mask=require_mask, outside=mask_out_value, zero_value=zero_value)


def compute_redox(folder, recursive: bool = True, overwrite: bool = True,
                  require_mask: bool = True, outside: float = 0.0) -> list[Path]:
    """Redox ratio FAD / (FAD + NADH) only (what redox.py did); searches subfolders by default."""
    return quantify(folder, ratios=REDOX_RATIOS, recursive=recursive, overwrite=overwrite,
                    require_mask=require_mask, outside=outside)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------
def main(argv=None) -> None:
    p = argparse.ArgumentParser(
        description="Ratio maps (CD/CH, unsaturation, redox) masked with create_mask's <ROI>-mask.tif.")
    p.add_argument("folders", nargs="+", type=Path, help="One or more folders to process.")
    p.add_argument("--ratios", nargs="+", choices=list(RATIOS), default=None,
                   help="Only these ratios (default: every ratio whose images are present).")
    p.add_argument("-r", "--recursive", action="store_true", help="Also process subfolders.")
    p.add_argument("--no-overwrite", action="store_true", help="Keep existing outputs.")
    p.add_argument("--allow-unmasked", action="store_true",
                   help="Also compute ROIs that have no <ROI>-mask.tif (output is unmasked).")
    p.add_argument("--outside", type=float, default=0.0,
                   help="Value outside the mask, e.g. 0 (default) or nan.")
    args = p.parse_args(argv)

    total = 0
    for folder in args.folders:
        if not folder.is_dir():
            print(f"[warn] Not a folder, skipping: {folder}")
            continue
        print(f"\n=== {folder}")
        total += len(quantify(folder, ratios=args.ratios, recursive=args.recursive,
                              overwrite=not args.no_overwrite,
                              require_mask=not args.allow_unmasked, outside=args.outside))
    print(f"\n[summary] wrote {total} ratio image(s)")


if __name__ == "__main__":
    main()