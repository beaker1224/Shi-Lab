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
- Add multiple draggable vertical x-axis cursor lines with different colors and labels.
- Baseline correction by polynomial fit across the current spectrum.
- Manual baseline correction by clicking anchor points and connecting them with interpolation.
- Undo recent edits with `Ctrl+Z` or the `Undo` button.
- Export the corrected spectrum with the same two-column structure as the raw file.

The included `example spectra.txt` is a plain tab-delimited two-column file: x-axis value and intensity.

## Manual Baseline Workflow

1. Open a spectrum.
2. Enable `Manual point mode`.
3. Click points along the visual baseline.
4. Click `Apply point baseline`.
5. Export with `Export corrected`.

The correction subtracts from the current displayed spectrum, so repeated corrections are cumulative. Use `Reset to raw` to start again from the original intensity.
