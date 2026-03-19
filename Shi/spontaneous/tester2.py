'''
here I will gather the following information:
1. intake raw data
2. perform background subtraction
3. smoothing
4. baseline correction
5. save the processed spectra
'''
from helpers.analysis import peak_ratio_calculator, t_test_calculator
from helpers.preprocessing import spectra_bg_subtraction, simple_baseline_correction, smoothing
from helpers.save_and_load import read_spectrum, save_ratios, save_spectrum
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple

raw_group_dirs: Dict[str, Path] = {
    "Gut_D10_Rapa": Path(r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Raw\D10_Gut\1_RAPA"),
    "Gut_D10_Ctrl": Path(r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Raw\D10_Gut\4_CTRL"),
    "Gut_D40_Rapa": Path(r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Raw\D40_Gut\1_RAPA"),
    "Gut_D40_Ctrl": Path(r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Raw\D40_Gut\4_CTRL"),
    "Ovary_D10_Rapa": Path(r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Raw\D10_Ovary\1_RAPA"),
    "Ovary_D10_Ctrl": Path(r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Raw\D10_Ovary\4_CTRL"),
    "Ovary_D40_Rapa": Path(r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Raw\D40_Ovary\1_RAPA"),
    "Ovary_D40_Ctrl": Path(r"D:\Chrome\Workspace\Projects\Rapamycin\data\spontaneous\Raw\D40_Ovary\4_CTRL"),
}

output_spectra_folder = Path(r"D:\Chrome\processed_spectra")

for group in raw_group_dirs.keys():
    raw_dir = raw_group_dirs[group]
    
    raw_files = list(raw_dir.glob('*.txt')) if raw_dir.exists() else []
    
    ratios_for_group = {}  # dict of sample_name to ratios dict
    
    # Part a: fitted background subtraction on raw
    if raw_dir.exists():
        for raw_file in raw_files:
            sample_name = raw_file.stem
            try:
                wn, intensity = read_spectrum(raw_file)
                wn_a, sub_intensity, bg_intensity = fitted_bg_subtraction(wn, intensity)
                if wn_a.size == 0:
                    print(f"Skipping {raw_file} due to fitting error")
                    continue
                ratio1 = peak_ratio_calculator(wn_a, sub_intensity, 2850, 3420, bg_intensity)
                ratio2 = peak_ratio_calculator(wn_a, sub_intensity, 2940, 3420, bg_intensity)
                print(f"Ratios a: {ratio1}, {ratio2}")
                if sample_name not in ratios_for_group:
                    ratios_for_group[sample_name] = {'group': group, 'sample_name': sample_name}
                ratios_for_group[sample_name]['total_lipid_to_water'] = ratio1
                ratios_for_group[sample_name]['total_protein_to_water'] = ratio2
            except Exception as e:
                print(f"Error processing fitted bg for {raw_file}: {e}")
                continue
    else:
        print(f"Raw dir does not exist for group {group}, skipping part a")
    
    # Part b: use bg_subtracted spectra
    if bg_sub_dir.exists():
        bg_files = list(bg_sub_dir.glob('*.txt'))
        for bg_file in bg_files:
            sample_name = bg_file.stem
            try:
                wn_b, intensity_b = read_spectrum(bg_file)
                ratio3 = peak_ratio_calculator(wn_b, intensity_b, 2850, 2940)
                ratio4 = peak_ratio_calculator(wn_b, intensity_b, 2140, 2850)
                ratio5 = peak_ratio_calculator(wn_b, intensity_b, 2180, 2940)
                ratio6 = peak_ratio_calculator(wn_b, intensity_b, 3005, 2850)
                if sample_name not in ratios_for_group:
                    ratios_for_group[sample_name] = {'group': group, 'sample_name': sample_name}
                ratios_for_group[sample_name]['total_lipid_to_protein'] = ratio3
                ratios_for_group[sample_name]['lipid_CD_CH'] = ratio4
                ratios_for_group[sample_name]['protein_CD_CH'] = ratio5
                ratios_for_group[sample_name]['lipid_unsaturation'] = ratio6
            except Exception as e:
                print(f"Error processing bg sub for {bg_file}: {e}")
                continue
    else:
        print(f"BG sub dir does not exist for group {group}, skipping part b")
    
    # Collect complete ratios
    for sample, ratios in ratios_for_group.items():
        all_ratios.append(ratios)

print(f"Total ratios collected: {len(all_ratios)}")

# Save to CSV
try:
    save_ratios(output_csv_path, all_ratios)
    print(f"Ratios saved to {output_csv_path}")
except PermissionError:
    print(f"Warning: Could not save to {output_csv_path} (file may be open). Continuing with plotting...")

# Part c: statistical analysis


# Load the ratios
ratios_df = pd.read_csv(output_csv_path)

# Define the ratios to analyze
ratios_cols = ['total_lipid_to_water', 'total_protein_to_water', 'total_lipid_to_protein', 'lipid_CD_CH', 'protein_CD_CH', 'lipid_unsaturation', 'lipid_packing']

# Prepare results
stats_results = []

tissues = ['Gut', 'Ovary']
days = ['D10', 'D40']

for tissue in tissues:
    for day in days:
        rapa_group = f"{tissue}_{day}_Rapa"
        ctrl_group = f"{tissue}_{day}_Ctrl"
        
        rapa_data = ratios_df[ratios_df['group'] == rapa_group]
        ctrl_data = ratios_df[ratios_df['group'] == ctrl_group]
        
        for ratio in ratios_cols:
            if ratio in rapa_data.columns and ratio in ctrl_data.columns:
                rapa_vals = rapa_data[ratio].dropna().values
                ctrl_vals = ctrl_data[ratio].dropna().values
                
                if len(rapa_vals) > 1 and len(ctrl_vals) > 1:
                    t_stat, p_val = t_test_calculator(rapa_vals, ctrl_vals)
                    significance = 'significant' if p_val < 0.05 else 'not significant'
                    stats_results.append({
                        'ratio_name': ratio,
                        'tissue': tissue,
                        'day': day,
                        'p_value': p_val,
                        'significance_level': significance
                    })

# Save stats to CSV
stats_csv_path = Path(r"D:\Chrome\stats.csv")
stats_df = pd.DataFrame(stats_results)
try:
    stats_df.to_csv(stats_csv_path, index=False)
    print(f"Stats saved to {stats_csv_path}")
except PermissionError:
    print(f"Warning: Could not save to {stats_csv_path} (file may be open). Continuing with plotting...")

# Part d: Plot histograms for ratios
import matplotlib.pyplot as plt

ratios_to_plot = ['total_lipid_to_water', 'total_protein_to_water', 'total_lipid_to_protein', 
                  'lipid_CD_CH', 'protein_CD_CH', 'lipid_unsaturation']
ratio_labels = ['Lipid/Water', 'Protein/Water', 'Lipid/Protein', 
                'Lipid CD/CH', 'Protein CD/CH', 'Lipid Unsat.']

def plot_ratio_pair(tissue, day, rapa_data, ctrl_data, ratios, labels):
    """Plot 6 histograms for a tissue-day pair comparing Rapa vs Ctrl"""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle(f'{tissue} - {day}: Rapa vs Ctrl', fontsize=16, fontweight='bold')
    axes = axes.flatten()
    
    for idx, (ratio, label) in enumerate(zip(ratios, labels)):
        ax = axes[idx]
        
        rapa_vals = rapa_data[ratio].dropna().values
        ctrl_vals = ctrl_data[ratio].dropna().values
        
        # Create histograms
        ax.hist(rapa_vals, bins=5, alpha=0.6, label='Rapa', color='blue', edgecolor='black')
        ax.hist(ctrl_vals, bins=5, alpha=0.6, label='Ctrl', color='red', edgecolor='black')
        
        ax.set_xlabel(label)
        ax.set_ylabel('Frequency')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        # Add statistics on plot
        p_val = stats_df[(stats_df['ratio_name'] == ratio) & 
                         (stats_df['tissue'] == tissue) & 
                         (stats_df['day'] == day)]['p_value'].values
        if len(p_val) > 0:
            sig_text = f"p={p_val[0]:.4f}"
            ax.text(0.5, 0.95, sig_text, transform=ax.transAxes, 
                   ha='center', va='top', fontsize=9, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    return fig

# Plot D10 first
print("\n=== Plotting D10 ===")
for tissue in ['Gut', 'Ovary']:
    rapa_group = f"{tissue}_D10_Rapa"
    ctrl_group = f"{tissue}_D10_Ctrl"
    
    rapa_data = ratios_df[ratios_df['group'] == rapa_group]
    ctrl_data = ratios_df[ratios_df['group'] == ctrl_group]
    
    if len(rapa_data) > 0 and len(ctrl_data) > 0:
        fig = plot_ratio_pair(tissue, 'D10', rapa_data, ctrl_data, ratios_to_plot, ratio_labels)
        output_fig_path = Path(r"D:\Chrome\plots") / f"{tissue}_D10_histograms.png"
        output_fig_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_fig_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_fig_path}")
        plt.show()

# Plot D40
print("\n=== Plotting D40 ===")
for tissue in ['Gut', 'Ovary']:
    rapa_group = f"{tissue}_D40_Rapa"
    ctrl_group = f"{tissue}_D40_Ctrl"
    
    rapa_data = ratios_df[ratios_df['group'] == rapa_group]
    ctrl_data = ratios_df[ratios_df['group'] == ctrl_group]
    
    if len(rapa_data) > 0 and len(ctrl_data) > 0:
        fig = plot_ratio_pair(tissue, 'D40', rapa_data, ctrl_data, ratios_to_plot, ratio_labels)
        output_fig_path = Path(r"D:\Chrome\plots") / f"{tissue}_D40_histograms.png"
        output_fig_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_fig_path, dpi=300, bbox_inches='tight')
        print(f"Saved: {output_fig_path}")
        plt.show()