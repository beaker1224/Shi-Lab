# calib_helper.py
from __future__ import annotations
import re
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable
import tifffile as tiff

# ---------- Module paths ----------
MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_ROYAL_LUT = MODULE_DIR / "Royal.lut"   # put Royal.lut beside this file

# ---------- LUT helpers ----------
def load_imagej_lut(lut_path: str | Path) -> ListedColormap:
    p = Path(lut_path)
    raw = p.read_bytes()
    if len(raw) < 768:
        raise ValueError("LUT file too small to be a valid ImageJ LUT.")
    rgb = np.frombuffer(raw[-768:], dtype=np.uint8).reshape(256, 3) / 255.0
    return ListedColormap(rgb, name=p.stem)

def get_royal_cmap(lut_path: str | Path | None = None) -> ListedColormap:
    if lut_path is None and DEFAULT_ROYAL_LUT.exists():
        lut_path = DEFAULT_ROYAL_LUT
    if lut_path and Path(lut_path).exists():
        try:
            return load_imagej_lut(lut_path)
        except Exception as e:
            print(f"[warn] Failed to load LUT at {lut_path}: {e} — using fallback.")
    return mpl.cm.get_cmap("viridis")  # perceptually similar fallback

# ---------- Small helpers ----------
_LEAD_RE = re.compile(r"^(\d+)-redox_ratio\.(?:tif|tiff)$", re.IGNORECASE)

def leading_number(fname: Path) -> str:
    m = _LEAD_RE.match(fname.name)
    if not m:
        raise ValueError(f"Filename does not match '<num>-redox_ratio.tif[f]': {fname.name}")
    return m.group(1)

def display_range(img: np.ndarray, p_low=1, p_high=99):
    vmin, vmax = np.percentile(img, (p_low, p_high))
    if vmin == vmax:
        vmax = vmin + 1.0
    return float(vmin), float(vmax)

# ---------- Save image with calibration bar to the RIGHT ----------
def save_image_with_cbar_right(
    img2d: np.ndarray,
    out_png: Path,
    lut: ListedColormap,
    vmin=None, vmax=None,
    n_ticks=5,
    label="Intensity (a.u.)",
    figure_dpi=300,
    interpolate="bilinear",   # 'nearest'|'bilinear'|'bicubic' (display-only smoothing)
    pad_fraction=0.02,
    cbar_width="3%",
):
    if vmin is None or vmax is None:
        vmin, vmax = display_range(img2d)

    fig, ax = plt.subplots(figsize=(5, 5), dpi=figure_dpi)
    ax.imshow(img2d, cmap=lut, vmin=vmin, vmax=vmax, interpolation=interpolate)
    ax.set_axis_off()

    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size=cbar_width, pad=pad_fraction)
    norm = Normalize(vmin=vmin, vmax=vmax)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=lut); sm.set_array([])
    cbar = fig.colorbar(sm, cax=cax, orientation="vertical")

    ticks = np.linspace(vmin, vmax, n_ticks)
    cbar.set_ticks(ticks)
    cbar.ax.tick_params(length=3, width=0.8, labelsize=8)
    cbar.outline.set_linewidth(0.8)
    cbar.set_label(label, fontsize=9)

    fig.tight_layout(pad=0)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    return vmin, vmax

# ---------- Standalone calibration bar (transparent PNG) ----------
def save_standalone_calbar_png(
    out_png: Path,
    lut: ListedColormap,
    vmin, vmax,
    n_ticks=5,
    label="Intensity (a.u.)",
    horizontal=True,
    dpi=300,
):
    size = (4, 1) if horizontal else (1, 4)
    fig, ax = plt.subplots(figsize=size, dpi=dpi)
    fig.subplots_adjust(left=0.20, right=0.92,
                        bottom=0.45 if horizontal else 0.10, top=0.90)
    norm = Normalize(vmin=vmin, vmax=vmax)
    sm = mpl.cm.ScalarMappable(norm=norm, cmap=lut); sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation=("horizontal" if horizontal else "vertical"))
    ticks = np.linspace(vmin, vmax, n_ticks)
    cbar.set_ticks(ticks)
    cbar.outline.set_linewidth(0.8)
    cbar.ax.tick_params(length=3, width=0.8, labelsize=9)
    cbar.set_label(label, fontsize=10)
    ax.remove()

    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, transparent=True, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)

# ---------- Single-file conversion (kept for reuse) ----------
def tiff_to_png_with_bar(
    tiff_path: str | Path,
    royal_lut_path: str | Path | None = None,
    save_separate_bar: bool = True,
    out_dir: str | Path | None = None,
    percentiles=(1, 99),
    n_ticks=5,
):
    tiff_path = Path(tiff_path)
    img = tiff.imread(tiff_path)   # expects 2D
    if img.ndim != 2:
        raise ValueError(f"Expected 2D TIFF, got shape {img.shape} at {tiff_path}")

    cmap = get_royal_cmap(royal_lut_path)
    lead = leading_number(tiff_path)  # enforces the naming pattern
    base_out = Path(out_dir) if out_dir else tiff_path.parent
    base_out = base_out / lead

    vmin, vmax = np.percentile(img, percentiles)
    vmin, vmax = float(vmin), float(vmax)
    img_png = base_out.with_name(f"{lead}_image").with_suffix(".png")
    vmin, vmax = save_image_with_cbar_right(
        img, img_png, cmap,
        vmin=vmin, vmax=vmax, n_ticks=n_ticks,
        label="a.u.", interpolate="bilinear"
    )
    bar_png = None
    if save_separate_bar:
        bar_png = base_out.with_name(f"{lead}_cbar").with_suffix(".png")
        save_standalone_calbar_png(bar_png, cmap, vmin, vmax, n_ticks=n_ticks, label="a.u.")
    return img_png, bar_png

# ---------- NEW: folder entry point ----------
def calibration_bar(
    folder_path: str | Path,
    royal_lut_path: str | Path | None = None,
    out_dir: str | Path | None = None,
    save_separate_bar: bool = True,
    percentiles=(1, 99),
    n_ticks=5,
):
    """
    Convert all 2D TIFFs inside `folder_path` whose filenames are exactly:
        <leadingnumber>-redox_ratio.tif  or  .tiff  (case-insensitive)
    Returns a list of (image_png, bar_png_or_None) paths.
    """
    folder = Path(folder_path)
    if not folder.is_dir():
        raise NotADirectoryError(folder)

    results = []
    for p in sorted(folder.iterdir()):
        if not p.is_file():
            continue
        if not _LEAD_RE.match(p.name):
            continue
        try:
            img_png, bar_png = tiff_to_png_with_bar(
                p,
                royal_lut_path=royal_lut_path,
                save_separate_bar=save_separate_bar,
                out_dir=(out_dir or folder),
                percentiles=percentiles,
                n_ticks=n_ticks,
            )
            results.append((img_png, bar_png))
            print(f"[ok] {p.name} → {img_png.name}" + (f", {bar_png.name}" if bar_png else ""))
        except Exception as e:
            print(f"[skip] {p.name}: {e}")
    return results

# ---------- CLI-ish example ----------
if __name__ == "__main__":
    # change this to your folder
    folder = r"path\to\folder\with\tifs"
    # Royal.lut is auto-discovered next to this file; override by passing a path:
    # lut = r"C:\Fiji.app\luts\Royal.lut"
    calibration_bar(folder, royal_lut_path=None, save_separate_bar=True)
