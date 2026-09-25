# if you are here for the naming system difference, please search for keyword
# "key_segment" variable or "candidates" variable to make changes
# should be in line 30 to 50 somewhere.
from __future__ import annotations
import tifffile as tiff
import numpy as np
import re
import napari
from skimage.filters import threshold_otsu
from pathlib import Path

def thresholding_mask(path, keyword = "791.3", recursive = True):
    """
    Open the first TIFF under `path` whose filename contains `keyword`,
    create an Otsu-based initial mask, allow interactive editing in napari,
    then save the edited mask as <stem>_mask.tif in the same folder.

    Args:
        path (str | Path): Directory to search under.
        keyword (str): Substring to match in the TIFF filename. Default "791.3".
        recursive (bool): Search subfolders if True (default).

    Returns:
        Path: The path to the saved mask TIFF.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Path does not exist: {path}")
    
    try:
        from magicgui import magicgui
    except Exception as e:
        raise RuntimeError(
            "This workflow needs 'magicgui'. Try: pip install magicgui"
        ) from e
    
    # find all the candidate tiff files
    pats = ["*.tif", "*.tiff", "*.TIF", "*.TIFF"]
    files = [] # the path to all the tif files
        # as this will search for the subfolders
    if recursive:
        for pat in pats: files.extend(path.rglob(pat))
    else:
        for pat in pats: files.extend(path.glob(pat))

    key_segment = f"-{keyword}nm".lower()
    candidates = [p for p in files if key_segment in p.name.lower()]

    if not candidates:
        raise FileNotFoundError(
            f"No Tiff matching '*-{keyword}nm-*' under {path} \n" +
            "please see the helper, create_mask.py if you have different naming system"
        )
    
    saved_paths = []

    # State carried across images
    idx = 0
    img = None
    image_path = None
    prefix = None

    # Start viewer and layers once
    viewer = napari.Viewer()


    # Create empty layers; then populate them on load
    image_layer = viewer.add_image(
        np.zeros((2, 2), dtype = np.float32), name = "image", visible = True
    )
    
    # PREVIEW: Image layer (tinted), not Labels
    preview_layer = viewer.add_image(
        np.zeros((2, 2), dtype=np.uint8),
        name="preview (threshold)",
        colormap="magenta",      # or "red"
        opacity=1.0,
        blending="additive",
        visible=True,
    )
    preview_layer.contrast_limits = (0, 1)

    # MASK: Labels as usual (no custom colormap needed)
    mask_layer = viewer.add_labels(
        np.zeros((2, 2), dtype=np.uint8),
        name="mask (editable)",
        opacity=0.8,
        blending="translucent",
        visible=True
    )

    # Utility: robust display limits
    def robust_limits(a):
        a = a.astype(float, copy=False)
        lo = float(np.percentile(a, 0.5))
        hi = float(np.percentile(a, 99.5))
        if not np.isfinite(lo): lo = float(np.min(a))
        if not np.isfinite(hi): hi = float(np.max(a))
        if lo == hi:
            hi = lo + 1.0
        return lo, hi
    
    # Load image i into layers and reset widgets
    def load_image(i):
        nonlocal idx, img, image_path, prefix
        idx = i
        image_path = candidates[idx]
        img = tiff.imread(str(image_path))

        # Leading number before first '-' (your "#")
        m = re.match(r"^(\d+)-", image_path.name)
        prefix = m.group(1) if m else image_path.stem.split("-")[0]

        # Update image layer
        image_layer.data = img
        lo, hi = robust_limits(img)
        image_layer.contrast_limits = (lo, hi)
        
        viewer.reset_view()

        # reset preview & mask to the new shape
        preview_layer.data = np.zeros_like(img, dtype=np.uint8)
        preview_layer.contrast_limits = (0, 1)   # <-- keep this fixed for binary preview
        mask_layer.data = np.zeros_like(img, dtype=np.uint8)

        # Initial threshold (Otsu or mid)
        if img.dtype == bool:
            init_th = 0.5
        else:
            try:
                init_th = float(threshold_otsu(img))
            except Exception:
                init_th = (lo + hi) / 2.0

        # Clamp threshold to slider range
        init_th = max(min(init_th, hi), lo)

        # Reset preview and mask
        prev = (img > init_th).astype(np.uint8)
        preview_layer.data = prev

        # Update slider bounds/value
        threshold_widget.threshold.min = lo
        threshold_widget.threshold.max = hi
        # Choose a reasonable step (1 for int images, else ~1/200 range)
        threshold_widget.threshold.step = 1.0 if np.issubdtype(img.dtype, np.integer) else (hi - lo) / 200.0
        threshold_widget.threshold.value = init_th
        
        update_preview(init_th)
        viewer.reset_view()
        
        viewer.status = f"{idx+1}/{len(candidates)}  |  {image_path.name}"

 # Live update of preview via slider
    def update_preview(th: float):
        # uses outer-scope variables: img, preview_layer
        if img is None:
            return
        preview_layer.data = (img > th).astype(np.uint8)  # 0/1 overlay

    # 2) Slider widget calls update_preview on every change
    @magicgui(
        auto_call=True,
        threshold={"widget_type": "FloatSlider", "min": 0.0, "max": 1.0, "step": 0.01},
    )
    def threshold_widget(threshold: float = 0.5):
        update_preview(threshold)

    # Confirm: copy preview → editable mask
    @magicgui(call_button="Confirm threshold → Mask")
    def confirm_button():
        mask_layer.data = preview_layer.data.copy()
        viewer.status = "Threshold applied to mask. You can paint/erase, then Save & Next."

    # Save current mask and advance
    @magicgui(call_button="Save & Next")
    def save_next_button():
        if img is None:
            return
        out_path = image_path.with_name(f"{prefix}-mask.tif")
        tiff.imwrite(str(out_path), mask_layer.data.astype(np.uint8), compression='zlib')
        saved_paths.append(out_path)
        viewer.status = f"Saved: {out_path.name}"

        # Advance to next or finish
        if idx + 1 < len(candidates):
            load_image(idx + 1)
        else:
            viewer.status = f"All done. Saved {len(saved_paths)} masks."
            # Optionally close the viewer automatically:
            viewer.close()  # uncomment if you'd like auto-close at the end

    # Skip without saving and advance
    @magicgui(call_button="Skip")
    def skip_button():
        if idx + 1 < len(candidates):
            load_image(idx + 1)
        else:
            viewer.status = f"Finished (skipped last). Saved {len(saved_paths)} masks."

    # Add widgets to the UI
    viewer.window.add_dock_widget(threshold_widget, area="right")
    viewer.window.add_dock_widget(confirm_button, area="right")
    viewer.window.add_dock_widget(save_next_button, area="right")
    viewer.window.add_dock_widget(skip_button, area="right")

    # Kick off with the first image
    load_image(0)

    # Enter the GUI loop; close when you're done
    napari.run()

    return saved_paths

def apply_mask(path):
    """
    find the corresponding mask under one same folder path and apply this to all the same ROI

    Args:
        path (str | Path): the path to the same folder

    Returns:
        None
    """
    folder = Path(path)
    if not folder.is_dir():
        raise NotADirectoryError(f"Not a folder: {folder}")

    # Collect TIFFs
    tiffs = []
    for pat in ("*.tif", "*.tiff", "*.TIF", "*.TIFF"):
        tiffs.extend(folder.glob(pat))

    if not tiffs:
        print(f"No TIFFs found in {folder}")
        return

    # Group by ROI (token before the first '-')
    by_roi: dict[str, list[Path]] = {}
    for p in tiffs:
        stem = p.stem
        parts = stem.split("-", 1)
        if len(parts) < 2:
            continue  # skip files without ROI-prefix pattern
        roi = parts[0]
        by_roi.setdefault(roi, []).append(p)

    out_dir = folder / "processed"
    out_dir.mkdir(exist_ok=True)

    def _read(path: Path) -> np.ndarray:
        return tiff.imread(str(path))

    def _prepare_mask(mask: np.ndarray, target_shape: tuple[int, ...]) -> np.ndarray:
        m = mask != 0  # boolean
        if m.shape == target_shape:
            return m
        if m.ndim == 2 and len(target_shape) >= 3 and m.shape == target_shape[-2:]:
            # expand to broadcast along leading dims
            expand = (1,) * (len(target_shape) - 2)
            return m.reshape(expand + m.shape)
        raise ValueError(
            f"Incompatible mask shape {m.shape} for image shape {target_shape}. "
            "Expected same shape, or 2D mask matching the last two dims."
        )

    for roi, files in by_roi.items():
        # Find mask "<roi>-mask.tif" among this ROI's files
        mask_candidates = [p for p in files if p.stem.lower() == f"{roi}-mask".lower()]
        if not mask_candidates:
            print(f"[WARN] No mask for ROI '{roi}'. Skipping.")
            continue

        mask_path = mask_candidates[0]
        try:
            mask_arr = _read(mask_path)
        except Exception as e:
            print(f"[ERROR] Read mask failed {mask_path.name}: {e}")
            continue

        for src in files:
            if src == mask_path:
                continue
            try:
                img = _read(src)
                m = _prepare_mask(mask_arr, img.shape)
                # multiply with dtype preservation
                out = img * m.astype(img.dtype)
                tiff.imwrite(str(out_dir / src.name), out, photometric="minisblack")
                print(f"[OK] {src.name} -> processed/{src.name}")
            except Exception as e:
                print(f"[FAIL] {src.name}: {e}")



