from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Union, Dict, List, Any

import numpy as np
import pandas as pd


# ROI: <anything>_<INT>.txt
# BG:  <anything>_<INT>_BG.txt
ROI_RE = re.compile(r"^(?P<prefix>.*)_(?P<roi>\d+)\.txt$", re.IGNORECASE)
BG_RE  = re.compile(r"^(?P<prefix>.*)_(?P<roi>\d+)_BG\.txt$", re.IGNORECASE)


@dataclass(frozen=True)
class Spectrum:
    wn: np.ndarray
    y: np.ndarray


def read_spectrum_txt(path: Path) -> Spectrum:
    """Read 2-column, no-header Raman txt: (wavenumber, intensity)."""
    try:
        df = pd.read_csv(path, delim_whitespace=True, header=None, comment="#")
    except Exception:
        df = pd.read_csv(path, sep=None, engine="python", header=None, comment="#")

    df = df.dropna(how="all").dropna(axis=1, how="all")
    if df.shape[1] < 2:
        raise ValueError(f"Expected 2 columns, got {df.shape[1]} in {path.name}")

    x = pd.to_numeric(df.iloc[:, 0], errors="coerce").to_numpy()
    y = pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy()

    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]

    if x.size < 3:
        raise ValueError(f"Too few numeric points in {path.name}")

    if np.any(np.diff(x) < 0):
        order = np.argsort(x)
        x, y = x[order], y[order]

    return Spectrum(wn=x, y=y)


def subtract_bg(roi: Spectrum, bg: Spectrum) -> Spectrum:
    """Subtract BG from ROI; interpolate BG onto ROI axis if needed."""
    if roi.wn.shape == bg.wn.shape and np.allclose(roi.wn, bg.wn, rtol=0, atol=1e-9):
        bg_on_roi = bg.y
    else:
        bg_on_roi = np.interp(roi.wn, bg.wn, bg.y, left=bg.y[0], right=bg.y[-1])
    return Spectrum(wn=roi.wn, y=roi.y - bg_on_roi)


def write_spectrum_txt(path: Path, spec: Spectrum) -> None:
    arr = np.column_stack([spec.wn, spec.y])
    np.savetxt(path, arr, delimiter="\t", fmt="%.10g")


def _discover_pairs(folder: Path) -> tuple[Dict[int, List[Path]], Dict[int, List[Path]]]:
    roi_files: Dict[int, List[Path]] = {}
    bg_files: Dict[int, List[Path]] = {}

    for p in folder.iterdir():
        if not p.is_file():
            continue

        name = p.name

        m_bg = BG_RE.match(name)
        if m_bg:
            idx = int(m_bg.group("roi"))
            bg_files.setdefault(idx, []).append(p)
            continue

        m_roi = ROI_RE.match(name)
        if m_roi:
            idx = int(m_roi.group("roi"))
            roi_files.setdefault(idx, []).append(p)
            continue

    return roi_files, bg_files


def _pick_single(mapping: Dict[int, List[Path]]) -> Dict[int, Path]:
    """Pick one file per index (alphabetically) if duplicates exist."""
    return {idx: sorted(paths, key=lambda x: x.name)[0] for idx, paths in mapping.items()}


def background_subtraction(
    input_folder: Union[str, Path],
    output_subfolder: str = "background_subtracted",
) -> Dict[str, Any]:
    """
    Process ONE folder. Writes outputs into:
        <input_folder>/<output_subfolder>/

    ROI pattern: *_<INT>.txt
    BG pattern:  *_<INT>_BG.txt
    Output:      *_<INT>_BGsub.txt
    """
    folder = Path(input_folder).expanduser().resolve()
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Not a valid folder: {folder}")

    out_dir = folder / output_subfolder
    out_dir.mkdir(parents=True, exist_ok=True)

    roi_map_list, bg_map_list = _discover_pairs(folder)
    roi_map = _pick_single(roi_map_list)
    bg_map = _pick_single(bg_map_list)

    all_idxs = sorted(set(roi_map.keys()) | set(bg_map.keys()))
    if not all_idxs:
        return {
            "folder": str(folder),
            "output_dir": str(out_dir),
            "paired_written": 0,
            "missing_bg_indices": [],
            "missing_roi_indices": [],
            "errors": ["No ROI/BG files matched the required suffix patterns."],
        }

    paired = 0
    missing_bg: List[int] = []
    missing_roi: List[int] = []
    errors: List[str] = []

    for idx in all_idxs:
        roi_path = roi_map.get(idx)
        bg_path = bg_map.get(idx)

        if roi_path is None:
            missing_roi.append(idx)
            continue
        if bg_path is None:
            missing_bg.append(idx)
            continue

        try:
            roi = read_spectrum_txt(roi_path)
            bg = read_spectrum_txt(bg_path)
            sub = subtract_bg(roi, bg)

            out_name = re.sub(rf"_{idx}\.txt$", f"_{idx}_BGsub.txt", roi_path.name, flags=re.IGNORECASE)
            write_spectrum_txt(out_dir / out_name, sub)
            paired += 1

        except Exception as e:
            errors.append(f"{roi_path.name} / {bg_path.name}: {type(e).__name__}: {e}")

    return {
        "folder": str(folder),
        "output_dir": str(out_dir),
        "paired_written": paired,
        "missing_bg_indices": missing_bg,
        "missing_roi_indices": missing_roi,
        "errors": errors,
    }