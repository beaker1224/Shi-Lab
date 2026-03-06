from helpers.analysis import peak_ratio_calculator, t_test_calculator
from helpers.preprocessing import spectra_bg_subtraction, simple_baseline_correction, fitted_bg_subtraction
from helpers.save_and_load import read_spectrum, save_ratios, save_spectrum
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from scipy.stats import f_oneway
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt

raw_group_dirs: Dict[str, Path] = {
    "Gut_D10_Rapa": Path(r"D:\Chrome\Raw\D10_Gut\1_RAPA"),
    "Gut_D10_Ctrl": Path(r"D:\Chrome\Raw\D10_Gut\4_CTRL"),
    "Gut_D40_Rapa": Path(r"D:\Chrome\Raw\D40_Gut\1_RAPA"),
    "Gut_D40_Ctrl": Path(r"D:\Chrome\Raw\D40_Gut\4_CTRL"),
    "Ovary_D10_Rapa": Path(r"D:\Chrome\Raw\D10_Ovary\1_RAPA"),
    "Ovary_D10_Ctrl": Path(r"D:\Chrome\Raw\D10_Ovary\4_CTRL"),
    "Ovary_D40_Rapa": Path(r"D:\Chrome\Raw\D40_Ovary\1_RAPA"),
    "Ovary_D40_Ctrl": Path(r"D:\Chrome\Raw\D40_Ovary\4_CTRL"),
}

# Process spectra: fitted BG subtraction + simple baseline correction
print("Processing spectra with fitted BG subtraction and baseline correction...")

group_spectra = {}  # Store processed spectra for each group

for group_name, group_dir in raw_group_dirs.items():
    if not group_dir.exists():
        print(f"Skipping {group_name}, directory not found")
        continue
    
    group_spectra[group_name] = []
    raw_files = list(group_dir.glob('*.txt'))
    
    for raw_file in raw_files:
        try:
            wn, intensity = read_spectrum(raw_file)
            
            # Step 1: Fitted background subtraction
            wn_fitted, sub_intensity, bg_intensity = fitted_bg_subtraction(wn, intensity)
            
            if wn_fitted.size == 0:
                print(f"Skipping {raw_file.name} due to fitting error")
                continue
            
            # Step 2: Simple baseline correction
            wn_baseline, baseline_corrected = simple_baseline_correction(wn_fitted, sub_intensity)
            
            # Store the processed spectra
            group_spectra[group_name].append({
                'filename': raw_file.stem,
                'wn': wn_baseline,
                'intensity': baseline_corrected
            })
            
            print(f"Processed: {raw_file.name}")
            
        except Exception as e:
            print(f"Error processing {raw_file.name}: {e}")
            continue

print(f"Total groups processed: {len(group_spectra)}")

# Create 2x4 subplot layout for all 8 groups
fig, axes = plt.subplots(2, 4, figsize=(20, 10))
fig.suptitle('Fitted BG Subtracted + Baseline Corrected Spectra by Group', fontsize=16, fontweight='bold')
axes = axes.flatten()

group_names = list(raw_group_dirs.keys())

for idx, (group_name, spectra_list) in enumerate(group_spectra.items()):
    ax = axes[idx]
    
    # Plot all spectra from this group overlaid
    for spectrum in spectra_list:
        ax.plot(spectrum['wn'], spectrum['intensity'], alpha=0.7, linewidth=1.5, label=spectrum['filename'])
    
    ax.set_xlabel('Wavenumber (cm⁻¹)')
    ax.set_ylabel('Intensity')
    ax.set_title(f'{group_name} (n={len(spectra_list)})')
    ax.grid(True, alpha=0.3)
    
    # Only show legend if there are a few spectra
    if len(spectra_list) <= 3:
        ax.legend(fontsize=8)

plt.tight_layout()
output_fig_path = Path(r"D:\Chrome\plots\baseline_corrected_spectra.png")
output_fig_path.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(output_fig_path, dpi=300, bbox_inches='tight')
print(f"\nSaved: {output_fig_path}")

print("\nProcessing complete!")