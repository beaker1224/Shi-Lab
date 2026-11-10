"""
create_mask.py -- build one mask per ROI interactively in napari, then apply it.

Assumed file naming (edit the "Naming conventions" block below if yours differs):
    <ROI>-<anything>.tif     images, e.g. 1-791.3nm-scan.tif, 1-850nm-scan.tif, 2-791.3nm-scan.tif
    <ROI>_CH<anything>.tif   image stacks, e.g. 1_CH.tif (the 2-D mask is applied to every slice)
    <ROI>-mask.tif           the mask for that ROI, saved in the same folder as its images

Typical use:
    saved = thresholding_mask(r"D:/data/session1")     # walk through every ROI, one mask each
    apply_mask(r"D:/data/session1", recursive=True)    # mask images + stacks -> <folder>/processed/
    apply_mask(r"D:/data/session1", include_stacks=False)   # same, but leave the _CH stacks alone

In the napari window, for each ROI:
    1. Pick a threshold method (Otsu, Li, ...) and smoothing; fine-tune with the slider.
    2. Clean up with open/close, fill holes, minimum object size or keep-largest.
    3. Optionally paint/erase on the "mask" layer. Live updating switches itself off as
       soon as you pick a paint, fill or erase tool, so your edits are never overwritten.
    4. "Save & Next" writes <ROI>-mask.tif and loads the next ROI. "Skip" moves on without
       saving, the ROI list jumps anywhere, and ROIs that already have a mask reopen it for editing.
"""
from __future__ import annotations

import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import tifffile as tiff
from scipy import ndimage as ndi
from skimage.filters import (
    threshold_li,
    threshold_mean,
    threshold_otsu,
    threshold_triangle,
    threshold_yen,
)

# ---------------------------------------------------------------------------
# Naming conventions -- if your files are named differently, change these.
# ---------------------------------------------------------------------------
# ROI id = the text before the first "-":  "12-791.3nm-scan.tif" -> "12"
ROI_PATTERN = re.compile(r"^([^-]+)-")
# Image stacks = "<ROI>_CH...":  "12_CH.tif" -> ROI "12"  (checked before ROI_PATTERN)
STACK_PATTERN = re.compile(r"^([^-_]+)_CH", re.IGNORECASE)
# Mask file name = "<ROI>-mask.tif", written next to that ROI's images
MASK_SUFFIX = "-mask"
# Folders that are never searched (apply_mask writes its output into "processed")
SKIP_DIRS = {"processed"}


def reference_tag(keyword: str) -> str:
    """Filename fragment marking the image to threshold on: '791.3' -> '-791.3nm'."""
    return f"-{keyword}nm"


THRESHOLD_METHODS = {
    "Otsu": threshold_otsu,
    "Li": threshold_li,
    "Triangle": threshold_triangle,
    "Yen": threshold_yen,
    "Mean": threshold_mean,
}


# ---------------------------------------------------------------------------
# Finding files and grouping them by ROI
# ---------------------------------------------------------------------------
def _natural_key(text: str):
    """Sort '2' before '10' (plain string sorting puts '10' first)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", text)]


def _find_tiffs(root: Path, recursive: bool) -> list[Path]:
    """Every .tif/.tiff under root, any letter case, each file once.

    Skips SKIP_DIRS and the hidden '._name.tif' files macOS leaves on external drives.
    """
    entries = root.rglob("*") if recursive else root.glob("*")
    found = set()
    for p in entries:
        if p.suffix.lower() not in (".tif", ".tiff") or p.name.startswith("._"):
            continue
        if any(d.lower() in SKIP_DIRS for d in p.relative_to(root).parts[:-1]):
            continue
        if p.is_file():
            found.add(p)
    return sorted(found, key=lambda p: _natural_key(str(p)))


@dataclass
class RoiSet:
    folder: Path
    roi: str
    files: list[Path]                                  # single images of this ROI (mask excluded)
    stacks: list[Path] = field(default_factory=list)   # <ROI>_CH... stacks
    ref_index: int = 0           # index into `candidates`: the image the threshold is computed on
    has_reference: bool = False  # True if one of the files matched the keyword

    @property
    def mask_path(self) -> Path:
        return self.folder / f"{self.roi}{MASK_SUFFIX}.tif"

    @property
    def candidates(self) -> list[Path]:
        """Images that can be thresholded on: single images first, then stacks."""
        return self.files + self.stacks

    @property
    def reference(self) -> Path:
        return self.candidates[self.ref_index]


def find_rois(root, keyword: str | None = "791.3", recursive: bool = True) -> list[RoiSet]:
    """Group the TIFFs under `root` by (folder, ROI) and pick a reference image for each ROI.

    The reference is the first file containing reference_tag(keyword); if a ROI has none,
    its first single image is used instead (or its first stack, if it only has stacks).
    Either way it can be changed in the GUI.
    """
    root = Path(root)
    groups: dict[tuple[Path, str], tuple[list[Path], list[Path]]] = {}
    for p in _find_tiffs(root, recursive):
        m = STACK_PATTERN.match(p.name)
        is_stack = m is not None
        if not is_stack:
            m = ROI_PATTERN.match(p.name)
        if not m:
            continue
        roi = m.group(1)
        if p.stem.lower() == f"{roi}{MASK_SUFFIX}".lower():
            continue  # an existing mask, not an image
        files, stacks = groups.setdefault((p.parent, roi), ([], []))
        (stacks if is_stack else files).append(p)

    tag = reference_tag(keyword).lower() if keyword else None
    rois = []
    for (folder, roi), (files, stacks) in groups.items():
        hits = [i for i, f in enumerate(files) if tag and tag in f.name.lower()]
        rois.append(RoiSet(folder=folder, roi=roi, files=files, stacks=stacks,
                           ref_index=hits[0] if hits else 0, has_reference=bool(hits)))
    rois.sort(key=lambda r: (_natural_key(str(r.folder)), _natural_key(r.roi)))
    return rois


# ---------------------------------------------------------------------------
# Image helpers and the mask pipeline
# ---------------------------------------------------------------------------
def _to_2d(img: np.ndarray) -> np.ndarray:
    """Reduce an image to 2-D float32 for thresholding.

    RGB(A) -> mean of the colour channels; stacks (Z, C, T, ...) -> max projection.
    """
    a = np.squeeze(np.asarray(img))
    if a.ndim < 2:
        raise ValueError(f"Image is not 2-D (shape {np.shape(img)})")
    if a.ndim == 3 and a.shape[-1] in (3, 4):
        a = a[..., :3].mean(axis=-1)
    elif a.ndim > 2:
        a = a.reshape(-1, *a.shape[-2:]).max(axis=0)
    return np.nan_to_num(a.astype(np.float32, copy=False))


def _display_limits(a: np.ndarray) -> tuple[float, float]:
    lo, hi = (float(v) for v in np.percentile(a, (0.5, 99.5)))
    if hi <= lo:
        lo, hi = float(a.min()), float(a.max())
    if hi <= lo:
        hi = lo + 1.0
    return lo, hi


def _disk(r: int) -> np.ndarray:
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def _morph(op, m: np.ndarray, r: int) -> np.ndarray:
    """Binary opening/closing with a disk; edge padding stops objects being eaten at the border."""
    padded = np.pad(m, r, mode="edge")
    return op(padded, structure=_disk(r))[r:-r, r:-r]


def build_mask(
    img2d: np.ndarray,
    threshold: float,
    invert: bool = False,
    open_radius: int = 0,
    close_radius: int = 0,
    fill_holes: bool = True,
    min_size: int = 0,
    keep_largest: bool = False,
) -> np.ndarray:
    """Threshold + clean-up. Returns a boolean mask the same shape as img2d."""
    m = img2d < threshold if invert else img2d > threshold
    if open_radius > 0:
        m = _morph(ndi.binary_opening, m, open_radius)    # removes specks / thin spurs
    if close_radius > 0:
        m = _morph(ndi.binary_closing, m, close_radius)   # bridges small gaps
    if fill_holes:
        m = ndi.binary_fill_holes(m)
    if min_size > 0 or keep_largest:
        lab, n = ndi.label(m)
        if n:
            sizes = np.bincount(lab.ravel())
            sizes[0] = 0  # background
            keep = sizes >= max(min_size, 1)
            if keep_largest and keep.any():
                keep[:] = False
                keep[sizes.argmax()] = True
            m = keep[lab]
    return m


def _set_label_color(layer, color: str) -> None:
    """Show every non-zero label in one colour (napari's API differs between versions)."""
    try:
        from napari.utils.colormaps import DirectLabelColormap
        layer.colormap = DirectLabelColormap(color_dict={None: color, 0: "transparent"})
    except Exception:
        try:
            layer.color = {None: color, 0: "transparent"}
        except Exception:
            pass  # fall back to napari's default label colour


# ---------------------------------------------------------------------------
# The napari session
# ---------------------------------------------------------------------------
class _MaskSession:
    """napari window that steps through the ROIs and builds one mask per ROI."""

    _EDIT_MODES = {"paint", "erase", "fill", "polygon"}

    def __init__(self, rois: list[RoiSet], keyword: str | None = None,
                 close_when_done: bool = True, show: bool = True):
        import napari
        from magicgui.widgets import (CheckBox, ComboBox, Container, FloatSlider,
                                      FloatSpinBox, Label, PushButton, SpinBox)

        self.rois = rois
        self.tag = reference_tag(keyword) if keyword else None
        self.close_when_done = close_when_done
        self.saved: list[Path] = []
        self.i = 0
        self.img: np.ndarray | None = None    # current reference image, 2-D float32
        self._smooth_cache = (None, None)     # (sigma, smoothed image)
        self._busy = False                    # True while code (not the user) changes widgets
        self._has_mask = [r.mask_path.exists() for r in rois]

        # ---- viewer and layers ----------------------------------------------
        self.viewer = napari.Viewer(title="Mask builder", show=show)
        self.image_layer = self.viewer.add_image(np.zeros((2, 2), np.float32), name="image")
        self.mask_layer = self.viewer.add_labels(np.zeros((2, 2), np.uint8), name="mask", opacity=0.5)
        self.mask_layer.selected_label = 1
        self.mask_layer.brush_size = 10
        _set_label_color(self.mask_layer, "magenta")

        # ---- widgets ----------------------------------------------------------
        many_folders = len({r.folder for r in rois}) > 1
        self._names = [f"{r.folder.name} / ROI {r.roi}" if many_folders else f"ROI {r.roi}"
                       for r in rois]

        self.w_roi = ComboBox(label="ROI", choices=list(zip(self._names, range(len(rois)))))
        self.w_ref = ComboBox(label="Threshold on", choices=[("-", 0)],
                              tooltip="Which image of this ROI the threshold is computed on")
        self.w_info = Label(value="")
        self.w_method = ComboBox(
            label="Method", choices=[*THRESHOLD_METHODS, "Manual"], value="Otsu",
            tooltip="Sets the starting threshold for each ROI; drag the slider to fine-tune.\n"
                    "'Manual' keeps the slider where you left it when moving to the next ROI.")
        self.w_sigma = FloatSpinBox(label="Smooth σ (px)", value=1.0, min=0.0, max=20.0, step=0.5,
                                    tooltip="Gaussian blur before thresholding; reduces speckle")
        self.w_thr = FloatSlider(label="Threshold", value=0.5, min=0.0, max=1.0)
        self.w_invert = CheckBox(text="Invert (keep dark regions)", value=False)
        self.w_open = SpinBox(label="Open radius", value=0, min=0, max=50,
                              tooltip="Removes specks and thin spurs")
        self.w_close = SpinBox(label="Close radius", value=0, min=0, max=50,
                               tooltip="Bridges small gaps and notches")
        self.w_min = SpinBox(label="Min object (px)", value=64, min=0, max=100_000_000, step=16,
                             tooltip="Objects smaller than this many pixels are removed")
        self.w_fill = CheckBox(text="Fill holes", value=True)
        self.w_largest = CheckBox(text="Keep largest object only", value=False)
        self.w_live = CheckBox(text="Live update (turns off when you paint)", value=True)
        self.w_outline = CheckBox(text="Show mask as outline", value=False)
        self.w_reapply = PushButton(text="Re-apply threshold (discard edits)")
        self.w_prev = PushButton(text="◀ Prev")
        self.w_skip = PushButton(text="Skip ▶")
        self.w_save = PushButton(text="Save && Next ▶")
        self.w_msg = Label(value="")
        for w in (self.w_info, self.w_msg):
            try:
                w.native.setWordWrap(True)
            except Exception:
                pass

        panel = Container(labels=False, widgets=[
            Label(value="<b>ROI</b>"),
            Container(widgets=[self.w_roi, self.w_ref]),
            self.w_info,
            Label(value="<b>Threshold</b>"),
            Container(widgets=[self.w_method, self.w_sigma, self.w_thr, self.w_invert]),
            Label(value="<b>Clean-up</b>"),
            Container(widgets=[self.w_open, self.w_close, self.w_min, self.w_fill, self.w_largest]),
            Label(value="<b>Mask</b>"),
            Container(widgets=[self.w_live, self.w_outline, self.w_reapply]),
            Container(layout="horizontal", labels=False,
                      widgets=[self.w_prev, self.w_skip, self.w_save]),
            self.w_msg,
        ])
        self.viewer.window.add_dock_widget(panel, area="right", name="Mask tools")

        # ---- wiring -------------------------------------------------------------
        self.w_roi.changed.connect(self._on_roi_selected)
        self.w_ref.changed.connect(self._on_ref_selected)
        self.w_method.changed.connect(lambda _: self._refresh(auto_threshold=True))
        self.w_sigma.changed.connect(lambda _: self._refresh(auto_threshold=True))
        for w in (self.w_thr, self.w_invert, self.w_open, self.w_close,
                  self.w_min, self.w_fill, self.w_largest):
            w.changed.connect(lambda _: self._refresh())
        self.w_live.changed.connect(lambda on: self._refresh() if on else None)
        self.w_outline.changed.connect(self._set_outline)
        self.w_reapply.changed.connect(self._reapply)
        self.w_prev.changed.connect(lambda _: self.go(self.i - 1))
        self.w_skip.changed.connect(lambda _: self.go(self.i + 1))
        self.w_save.changed.connect(lambda _: self.save_and_next())
        self.mask_layer.events.mode.connect(self._on_mode)
        if hasattr(self.mask_layer.events, "paint"):
            self.mask_layer.events.paint.connect(lambda _: self._update_info())

        self.load_roi(0)

    # ---- small helpers ------------------------------------------------------
    @contextmanager
    def _quiet(self):
        """Change widgets from code without triggering their callbacks."""
        prev, self._busy = self._busy, True
        try:
            yield
        finally:
            self._busy = prev

    def _note(self, msg: str, popup: bool = False, warn: bool = False) -> None:
        self.w_msg.value = msg
        if popup or warn:
            try:
                from napari.utils.notifications import show_info, show_warning
                (show_warning if warn else show_info)(msg)
            except Exception:
                pass

    def _set_live(self, on: bool) -> None:
        with self._quiet():
            self.w_live.value = on

    def _set_slider_range(self, lo: float, hi: float, step: float) -> None:
        s = self.w_thr
        with self._quiet():
            s.min = min(lo, s.min)   # widen first so min <= max holds at every step
            s.max = max(hi, s.max)
            s.min = lo
            s.max = hi
            s.step = step

    def _set_threshold(self, t: float) -> None:
        s = self.w_thr
        with self._quiet():
            s.value = float(min(max(t, s.min), s.max))

    def _smoothed(self) -> np.ndarray:
        sigma = float(self.w_sigma.value)
        if self._smooth_cache[0] != sigma:
            sm = ndi.gaussian_filter(self.img, sigma) if sigma > 0 else self.img
            self._smooth_cache = (sigma, sm)
        return self._smooth_cache[1]

    def _auto_threshold(self) -> float:
        fn = THRESHOLD_METHODS.get(self.w_method.value)
        if fn is None:  # "Manual": keep whatever the slider says
            return float(self.w_thr.value)
        a = self._smoothed()
        if a.size > 4_000_000:  # subsample very large images so the UI stays responsive
            k = int(np.ceil(np.sqrt(a.size / 4_000_000)))
            a = a[::k, ::k]
        try:
            return float(fn(a))
        except Exception:
            return float(a.mean())

    def _compute(self) -> np.ndarray:
        return build_mask(
            self._smoothed(), float(self.w_thr.value),
            invert=bool(self.w_invert.value),
            open_radius=int(self.w_open.value),
            close_radius=int(self.w_close.value),
            fill_holes=bool(self.w_fill.value),
            min_size=int(self.w_min.value),
            keep_largest=bool(self.w_largest.value),
        )

    def _refresh(self, auto_threshold: bool = False) -> None:
        if self._busy or self.img is None:
            return
        if auto_threshold:
            self._set_threshold(self._auto_threshold())
        if self.w_live.value:
            self.mask_layer.data = self._compute().astype(np.uint8)
        self._update_info()

    def _update_info(self) -> None:
        r = self.rois[self.i]
        n = len(self.rois)
        lines = [
            f"{self.i + 1} of {n}  ·  {sum(self._has_mask)} of {n} masks saved",
            f"{r.mask_path.name}: {'saved' if self._has_mask[self.i] else 'not saved yet'}",
        ]
        if self.tag and not r.has_reference:
            lines.append(f"No '*{self.tag}*' image for this ROI; pick one in 'Threshold on'.")
        if r.stacks:
            lines.append("Stacks in this ROI: " + ", ".join(p.name for p in r.stacks))
        if self.img is not None:
            frac = np.count_nonzero(self.mask_layer.data) / self.img.size
            lines.append(f"Mask covers {frac:.1%} of the image")
        self.w_info.value = "\n".join(lines)
        self.viewer.title = f"Mask builder: {self._names[self.i]} ({self.i + 1}/{n})"

    def _read_existing_mask(self, r: RoiSet, shape) -> np.ndarray | None:
        if not r.mask_path.exists():
            return None
        try:
            m = np.squeeze(tiff.imread(str(r.mask_path)))
        except Exception as e:
            self._note(f"Could not read {r.mask_path.name} ({e}); starting from the threshold.", warn=True)
            return None
        if m.shape != tuple(shape):
            self._note(f"{r.mask_path.name} is {m.shape} but the image is {tuple(shape)}; "
                       "ignoring the old mask.", warn=True)
            return None
        return (m > 0).astype(np.uint8)

    # ---- loading --------------------------------------------------------------
    def go(self, k: int) -> None:
        if k < 0:
            self._note("Already at the first ROI.")
        elif k >= len(self.rois):
            self._note("That was the last ROI. Pick another from the ROI list, or close the window.")
        else:
            self.load_roi(k)

    def load_roi(self, k: int) -> None:
        self.i = k
        r = self.rois[k]
        with self._quiet():
            self.w_roi.value = k
            self.w_ref.choices = [
                (f"{p.name}  (stack, max projection)" if p in r.stacks else p.name, j)
                for j, p in enumerate(r.candidates)
            ]
            self.w_ref.value = r.ref_index
        self._load_reference(keep_edits=False)

    def _load_reference(self, keep_edits: bool) -> None:
        r = self.rois[self.i]
        previous = np.asarray(self.mask_layer.data) if keep_edits else None
        try:
            raw = tiff.imread(str(r.reference))
            img = _to_2d(raw)
        except Exception as e:
            self.img = None
            self.image_layer.data = np.zeros((2, 2), np.float32)
            self.mask_layer.data = np.zeros((2, 2), np.uint8)
            self._note(f"Could not read {r.reference.name}: {e}. Try another image or Skip.", warn=True)
            self._update_info()
            return
        self.img = img
        self._smooth_cache = (None, None)

        self.image_layer.data = img
        try:
            self.image_layer.reset_contrast_limits_range()
        except Exception:
            pass
        self.image_layer.contrast_limits = _display_limits(img)

        lo, hi = float(img.min()), float(img.max())
        if hi <= lo:
            hi = lo + 1.0
        step = (hi - lo) / 1000
        if np.issubdtype(raw.dtype, np.integer):
            step = max(step, 1.0)
        self._set_slider_range(lo, hi, step)
        self._set_threshold(self._auto_threshold())

        with self._quiet():
            self.mask_layer.mode = "pan_zoom"
        try:
            self.viewer.layers.selection.active = self.mask_layer
        except Exception:
            pass

        existing = None if keep_edits else self._read_existing_mask(r, img.shape)
        if existing is not None:
            self._set_live(False)
            self.mask_layer.data = existing
            self._note(f"Opened the saved {r.mask_path.name} for editing. "
                       "Press 'Re-apply threshold' to start over.")
        elif (keep_edits and not self.w_live.value
              and previous is not None and previous.shape == img.shape):
            self._note("Kept your hand edits. Tick 'Live update' to re-threshold on this image.")
        else:
            self._set_live(True)
            self.mask_layer.data = self._compute().astype(np.uint8)
            self._note("")
        self.viewer.reset_view()
        self._update_info()

    # ---- callbacks ------------------------------------------------------------
    def _on_roi_selected(self, k) -> None:
        if not self._busy and k is not None:
            self.load_roi(k)

    def _on_ref_selected(self, j) -> None:
        if self._busy or j is None:
            return
        self.rois[self.i].ref_index = j
        self._load_reference(keep_edits=True)

    def _on_mode(self, event=None) -> None:
        if self.w_live.value and str(self.mask_layer.mode) in self._EDIT_MODES:
            self._set_live(False)
            self._note("Live update paused so your edits are kept. "
                       "Tick 'Live update' or press 'Re-apply threshold' to recompute.")

    def _set_outline(self, on) -> None:
        try:
            self.mask_layer.contour = 2 if on else 0
        except Exception:
            self._note("Outline view needs a newer napari.")

    def _reapply(self, *_) -> None:
        if self.img is None:
            return
        with self._quiet():
            self.mask_layer.mode = "pan_zoom"
        self._set_live(True)
        self._refresh()
        self._note("Mask reset to the current threshold settings.")

    # ---- saving ---------------------------------------------------------------
    def save_current(self) -> Path | None:
        if self.img is None:
            return None
        r = self.rois[self.i]
        m = (np.asarray(self.mask_layer.data) > 0).astype(np.uint8)  # 0/1, same as before
        tiff.imwrite(str(r.mask_path), m, compression="zlib")
        self._has_mask[self.i] = True
        if r.mask_path not in self.saved:
            self.saved.append(r.mask_path)
        msg = f"Saved {r.mask_path.name} ({m.mean():.1%} of pixels)"
        if not m.any():
            self._note(msg + " -- note: the mask is empty.", warn=True)
        else:
            self._note(msg, popup=True)
        return r.mask_path

    def save_and_next(self) -> None:
        if self.save_current() is None:
            return
        if self.i + 1 < len(self.rois):
            self.load_roi(self.i + 1)
            return
        missing = [self._names[k] for k, done in enumerate(self._has_mask) if not done]
        if missing:
            self._note("Last ROI saved. Still without a mask: " + ", ".join(missing)
                       + ". Pick them from the ROI list, or close the window.", popup=True)
        elif self.close_when_done:
            self.viewer.close()
        else:
            self._note(f"All {len(self.rois)} ROIs have masks.", popup=True)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------
def thresholding_mask(path, keyword: str = "791.3", recursive: bool = True,
                      skip_existing: bool = False, close_when_done: bool = True) -> list[Path]:
    """
    Make one mask per ROI, interactively.

    Every TIFF under `path` is grouped by ROI (the text before the first '-' in the file name,
    per folder). For each ROI the threshold is computed on the file containing
    '-<keyword>nm' (falling back to the ROI's first file), and the result is saved as
    <ROI>-mask.tif next to that ROI's images -- the name apply_mask() looks for.

    Args:
        path: Folder to search.
        keyword: Wavelength that marks the image to threshold on. Default "791.3".
        recursive: Also search subfolders (default). "processed" folders are always skipped.
        skip_existing: Leave out ROIs that already have a mask. By default they are included
            and their saved mask is opened for editing.
        close_when_done: Close the window after the last ROI is saved, provided every ROI
            has a mask by then.

    Returns:
        Paths of the masks saved in this session.
    """
    root = Path(path)
    if not root.exists():
        raise FileNotFoundError(f"Path does not exist: {root}")
    try:
        import magicgui  # noqa: F401
    except ImportError as e:
        raise RuntimeError("This workflow needs 'magicgui'. Try: pip install magicgui") from e
    import napari

    rois = find_rois(root, keyword, recursive)
    if not rois:
        raise FileNotFoundError(
            f"No TIFFs named like '<ROI>-....tif' under {root}.\n"
            "If your files are named differently, edit ROI_PATTERN / reference_tag() "
            "at the top of create_mask.py."
        )
    if skip_existing:
        rois = [r for r in rois if not r.mask_path.exists()]
        if not rois:
            print("Every ROI already has a mask; nothing to do.")
            return []

    print(f"Found {len(rois)} ROI(s): " + ", ".join(r.roi for r in rois))
    tag = reference_tag(keyword) if keyword else None
    for r in rois:
        if tag and not r.has_reference:
            print(f"  [note] ROI {r.roi} in {r.folder} has no '*{tag}*' file; "
                  f"thresholding on {r.reference.name} (changeable in the panel).")

    session = _MaskSession(rois, keyword=keyword, close_when_done=close_when_done)
    napari.run()
    return session.saved


def _prepare_mask(mask: np.ndarray, target_shape: tuple[int, ...],
                  axes: str | None = None) -> np.ndarray:
    """Turn the 2-D mask into a boolean array that broadcasts over the image's Y and X axes.

    Works for single images, stacks (N, Y, X), hyperstacks (T, Z, C, Y, X) and RGB (Y, X, 3).
    """
    m = np.squeeze(mask) != 0
    t = tuple(target_shape)
    if m.shape == t:
        return m
    if m.ndim == 2:
        spots = []
        if axes and len(axes) == len(t) and "Y" in axes and "X" in axes:
            iy = axes.index("Y")
            if axes.index("X") == iy + 1:
                spots.append(iy)                   # trust the file's own axis labels first
        spots += range(len(t) - 2, -1, -1)         # else: the last pair of axes that fits
        for ax in spots:
            if t[ax:ax + 2] == m.shape:
                shape = [1] * len(t)
                shape[ax:ax + 2] = m.shape
                return m.reshape(shape)
    raise ValueError(
        f"Mask shape {m.shape} does not fit image shape {t}: "
        "the mask's height and width must match the image's."
    )


# ImageJ metadata worth carrying over so a masked stack opens in Fiji exactly like the original
_IJ_KEYS = ("spacing", "unit", "finterval", "fps", "loop", "mode", "Labels", "Ranges", "LUTs")


def _read_tiff(path: Path) -> tuple[np.ndarray, dict]:
    """Read a TIFF, plus what's needed to write the result back with the same layout."""
    with tiff.TiffFile(str(path)) as tf:
        data = tf.asarray()
        page = tf.pages[0]
        info = {
            "axes": tf.series[0].axes,
            "imagej": tf.imagej_metadata if tf.is_imagej else None,
            "photometric": int(page.photometric),
            "samples": int(page.samplesperpixel),
            "planar": int(page.planarconfig),
        }
        try:
            info["resolution"] = page.resolution
            info["resolutionunit"] = page.resolutionunit
        except AttributeError:  # older tifffile: pixel size is not carried over
            pass
    return data, info


def _write_like(out_path: Path, data: np.ndarray, info: dict) -> None:
    """Write `data` keeping the source's layout: ImageJ hyperstack axes, RGB, pixel size.

    Falls back to simpler writes if the source metadata can't be reproduced exactly.
    """
    res = {}
    if "resolution" in info:
        res = {"resolution": info["resolution"], "resolutionunit": info["resolutionunit"]}
    attempts = []
    ij = info.get("imagej")
    if ij is not None and data.dtype in (np.uint8, np.uint16, np.float32):
        meta = {"axes": info["axes"], **{k: ij[k] for k in _IJ_KEYS if k in ij}}
        attempts += [dict(imagej=True, metadata=meta, **res),
                     dict(imagej=True, metadata={"axes": info["axes"]})]
    plain = {"photometric": "rgb" if info["photometric"] == 2 else "minisblack"}
    if info["samples"] > 1:
        plain["planarconfig"] = "separate" if info["planar"] == 2 else "contig"
    attempts += [dict(plain, **res), plain]
    for i, kw in enumerate(attempts):
        try:
            tiff.imwrite(str(out_path), data, **kw)
            return
        except Exception:
            if i == len(attempts) - 1:
                raise


def apply_mask(path, recursive: bool = False, include_stacks: bool = True) -> None:
    """
    Apply each ROI's <ROI>-mask.tif to every image of that ROI.

    Output goes to <folder>/processed/<same file name>; pixels outside the mask become 0.
    Stacks (<ROI>_CH....tif) get the same 2-D mask on every slice / channel / frame and keep
    their layout (ImageJ hyperstack axes, pixel size), so they open the same way in Fiji.

    Args:
        path: Folder containing the images and masks.
        recursive: Also process subfolders (each gets its own "processed" folder).
        include_stacks: Also mask the <ROI>_CH... stacks (default). False leaves them alone.
    """
    folder = Path(path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {folder}")

    rois = find_rois(folder, keyword=None, recursive=recursive)
    if not rois:
        print(f"No TIFFs found in {folder}")
        return

    n_img = n_stack = n_fail = 0
    for r in rois:
        targets = r.files + (r.stacks if include_stacks else [])
        if not targets:
            continue
        if not r.mask_path.exists():
            print(f"[WARN] No mask for ROI '{r.roi}' in {r.folder}. Skipping.")
            continue
        try:
            mask = tiff.imread(str(r.mask_path))
        except Exception as e:
            print(f"[ERROR] Read mask failed {r.mask_path.name}: {e}")
            continue

        out_dir = r.folder / "processed"
        out_dir.mkdir(exist_ok=True)
        for src in targets:
            is_stack = src in r.stacks
            try:
                data, info = _read_tiff(src)
                m = _prepare_mask(mask, data.shape, info["axes"])
                np.copyto(data, 0, where=~m)  # in place, so large stacks aren't copied
                _write_like(out_dir / src.name, data, info)
                note = f"  (stack {info['axes']} {data.shape})" if is_stack else ""
                print(f"[OK] {src.name} -> processed/{src.name}{note}")
                if is_stack:
                    n_stack += 1
                else:
                    n_img += 1
            except Exception as e:
                print(f"[FAIL] {src.name}: {e}")
                n_fail += 1
    print(f"Done: {n_img} image(s) and {n_stack} stack(s) masked, {n_fail} failed.")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python create_mask.py <folder> [keyword]")
        sys.exit(1)
    thresholding_mask(sys.argv[1], *(sys.argv[2:3] or []))