# PRM SRS Python Port

This folder contains the core Python rewrite of the project code from `PRM_SRS_Matlab_version`.

## What is included

- A reusable package in `prm_srs/` for spectra processing, reference loading, clustering, spontaneous Raman analysis, and image matching.
- Python entry-point scripts for the main workflows.
- A lightweight XLSX reader fallback so the reference workbooks can be used without `openpyxl`.

## Main entry points

- `srs5_image_generation.py`
- `srs5_image_generation_Copy.py`
- `srs5_hippocampus.py`
- `srs_lipid_subtype.py`
- `srs_single_spectrum_subtype.py`
- `srs_unsupervised_clustering.py`

## Important notes

- The code reads reference data and example datasets directly from the sibling folder `../PRM_SRS_Matlab_version`. This avoids duplicating the large data files.
- Olympus `.oir` and `.oib` files usually require an optional Python image reader such as `aicsimageio` or a prior export to TIFF. The port includes a clean abstraction for this, but the current environment does not ship with an OIR/OIB reader.
- `process_all_rawdata.m` appears incomplete in MATLAB. The Python implementation uses the intended behavior: process all four datasets consistently.

## Quick start

From `Python_version`:

```powershell
python -m compileall .
```

For image workflows, pass an absolute input folder:

```powershell
python srs5_image_generation.py `
  --hyperspectra-folder "D:\\data\\brain\\L3\\1-CH" `
  --raman-shift-start 2700 `
  --raman-shift-end 3120 `
  --num-images 62
```

For lipid subtype matching:

```powershell
python srs_lipid_subtype.py `
  --root-folder "D:\\data\\brain\\L3"
```

For a single Raman spectrum file with two columns `(shift, intensity)`:

```powershell
python srs_single_spectrum_subtype.py `
  --input-path "D:\\data\\spectra\\sample_01.csv"
```

This follows the same full-convolution scoring style used by the per-pixel
matching path in `srs_lipid_subtype`.

This writes a CSV of ranked subtype possibilities with columns:
`file_name`, `file_path`, `rank`, `lipid_subtype`, `score`, `peak_index`,
`lag_index`, and `relative_shift_cm_1`.

## Suggested dependencies

See `requirements.txt`. The image workflows can run on TIFF stacks with the default environment. For `.oir` and `.oib`, install an optional compatible reader.
