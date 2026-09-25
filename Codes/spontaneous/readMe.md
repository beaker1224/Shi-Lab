# Raman ROI / Background File Naming Requirements

To run the Raman background-subtraction pipeline, **your text files must follow these exact filename suffix rules**.
Everything else in the filename (sample name, organ, day, replicate, etc.) can be anything.
For all files under one folder, should be from the same sample, instead of mixed samples

---

## Required filename patterns

### ROI spectrum (signal)
- Must end with:
  - `_ROI<INTEGER>.txt`

Examples (✅ valid):
- `Ovary_D10_Rep1_1.txt`
- `gut40d_12.txt`
- `brain_sampleA_anything_3.txt`

### Background spectrum (for that ROI)
- Must end with:
  - `_ROI<INTEGER>_BG.txt`

Examples (✅ valid):
- `Ovary_D10_Rep1_1_BG.txt`
- `gut40d_12_BG.txt`
- `brain_sampleA_anything_3_BG.txt`

**Important:** The `<INTEGER>` (ROI number) must match between the ROI and BG file to be paired.

---

## Files that will be ignored

The code will **ignore any file** that does not match one of the two patterns above.

Examples (❌ ignored):
- `sample_BG.txt` (no `_ROI<INTEGER>_BG.txt`)
- `sample_1_BG_modified.txt` (does not end with `_ROI1_BG.txt`)
- `sample_1_processed.txt` (does not end with `_ROI1.txt`)

---

## Folder assumption
- The script processes **one folder at a time**.
- It will find all ROI files and match each ROI to its BG by ROI number.
- If a ROI has no matching BG (or vice versa), the script will report it.

---

## Output
For each ROI/BG pair, the script writes a background-subtracted spectrum file:
- `..._ROI<INTEGER>_BGsub.txt`

The output file uses the ROI wavenumber axis and subtracts BG intensity (interpolating BG if needed).