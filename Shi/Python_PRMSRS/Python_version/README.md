# PRM SRS Python Port

This folder contains a Python rewrite of the project code from `PRM_SRS_Matlab_version`.

## What is included

- A reusable package in `prm_srs/` for spectra processing, reference loading, clustering, spontaneous Raman analysis, and image matching.
- Python entry-point scripts mirroring the main MATLAB workflows and demos.
- A lightweight XLSX reader fallback so the reference workbooks can be used without `openpyxl`.

## Important notes

- The code reads reference data and example datasets directly from the sibling folder `../PRM_SRS_Matlab_version`. This avoids duplicating the large data files.
- Olympus `.oir` and `.oib` files usually require an optional Python image reader such as `aicsimageio` or a prior export to TIFF. The port includes a clean abstraction for this, but the current environment does not ship with an OIR/OIB reader.
- A few MATLAB demos referenced files that are not present in the repository. The Python versions use the closest available inputs and document those substitutions in code comments.
- `process_all_rawdata.m` appears incomplete in MATLAB. The Python implementation uses the intended behavior: process all four datasets consistently.

## Quick start

From `Python_version`:

```powershell
python -m compileall .
python demo_2_subtype_lipid_signal.py
```

For image workflows, pass an absolute input folder:

```powershell
python srs5_image_generation.py `
  --hyperspectra-folder "D:\\data\\brain\\L3\\1-CH" `
  --raman-shift-start 2700 `
  --raman-shift-end 3120 `
  --num-images 62
```

## Suggested dependencies

See `requirements.txt`. The image workflows can run on TIFF stacks with the default environment. For `.oir` and `.oib`, install an optional compatible reader.
