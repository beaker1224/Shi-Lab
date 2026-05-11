# Spontaneous Raman Spectrum Editor

A small Python desktop GUI for loading, inspecting, baseline-correcting, and exporting spontaneous Raman spectra. It is intentionally similar in workflow to a light LabSpec-style editor: load spectra on the left, inspect the selected trace in the main plot, drag x-axis cursor markers, subtract baselines, and export corrected data.

## Run

```powershell
python raman_gui.py
```

## What It Supports

- Open one or more `txt`, `csv`, `tsv`, or `dat` spectra files.
- Plot the selected spectrum in the main window.
- Delete the selected loaded spectrum or clear the full loaded list.
- Set one loaded spectrum as a background spectrum, then subtract it from another selected spectrum.
- Add multiple draggable vertical x-axis cursor lines with different colors and labels.
- Baseline correction by polynomial fit across the current spectrum.
- Manual baseline correction by clicking anchor points and connecting them with interpolation.
- Place manual points snapped to the spectrum, or turn snapping off to place points anywhere in the plot area.
- Zoom with the mouse wheel, the Matplotlib toolbar, or the `Zoom in`, `Zoom out`, and `Reset view` buttons.
- Undo recent edits with `Ctrl+Z` or the `Undo` button.
- Export the corrected spectrum with the same two-column structure as the raw file.

The included `example spectra.txt` is a plain tab-delimited two-column file: x-axis value and intensity.

## Background Subtraction

1. Open at least two spectra.
2. Select the background spectrum.
3. Click `Set selected as BG`.
4. Select the target spectrum.
5. Click `Subtract BG`.

If the x-axis values are not identical, the background is interpolated onto the target spectrum's x-axis before subtraction.

## Manual Baseline Workflow

1. Open a spectrum.
2. Enable `Manual point mode`.
3. Leave `Snap points to spectrum` on for spectrum-following points, or turn it off for free baseline placement.
4. Click points along the visual baseline.
5. Click `Apply point baseline`.
6. Export with `Export corrected`.

The correction subtracts from the current displayed spectrum, so repeated corrections are cumulative. Use `Reset to raw` to start again from the original intensity.
