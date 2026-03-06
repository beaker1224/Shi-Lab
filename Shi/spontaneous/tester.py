'''
here I will gather the following information:
a. row file after fitted background subtraction (this part is special, should be the intensity from subtracted spectra vs fitted background curve)
1. total lipid ratio to water: 2850 cm-1 / 3420 cm-1
2. total protein ratio to water: 2940 cm-1 / 3420 cm-1

b. row file after spectra bg subtraction
3. total lipid to protein ratio: 2850 cm-1 / 2940 cm-1
4. lipid CD/CH ratio: 2140 cm-1 / 2850 cm-1
5. protein CD/CH ratio: 2180 cm-1 / 2940 cm-1
6. lipid unsaturation ratio: 3005 cm-1 / 2850 cm-1

c. put all the above ratios in a table, and do statistical analysis
1. save all the ratios in a csv file, with columns: sample name, group, ratio values, with headers
2. do statistical analysis (t-test or ANOVA) on the ratios, and save the results in a separate csv file, with columns: ratio name, p-value, significance level, with headers

d. row file after spectra bg subtraction and simple baseline correction
1. plot statistical analysis results, with boxplots and significance annotations
2. plot baseline corrected spectra, for shape analysis

e. discussion
1. gut should be focused on the r2 region instead of r5 region
2. ovary should be focused on the posterior region, instead of the anterior region
'''
from helpers.analysis import peak_ratio_calculator, t_test_calculator
from helpers.preprocessing import spectra_bg_subtraction, simple_baseline_correction, fitted_bg_subtraction
from helpers.save_and_load import read_spectrum, save_ratios, save_spectrum
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any

bg_subtracted_group_dirs: Dict[str, Path] = {
    "Gut_D10_Rapa": Path(r"D:\Chrome\BG_Subed\D10_Gut\1_RAPA"),
    "Gut_D10_Ctrl": Path(r"D:\Chrome\BG_Subed\D10_Gut\4_CTRL"),
    "Gut_D40_Rapa": Path(r"D:\Chrome\BG_Subed\D40_Gut\1_RAPA"),
    "Gut_D40_Ctrl": Path(r"D:\Chrome\BG_Subed\D40_Gut\4_CTRL"),
    "Ovary_D10_Rapa": Path(r"D:\Chrome\BG_Subed\D10_Ovary\1_RAPA"),
    "Ovary_D10_Ctrl": Path(r"D:\Chrome\BG_Subed\D10_Ovary\4_CTRL"),
    "Ovary_D40_Rapa": Path(r"D:\Chrome\BG_Subed\D40_Ovary\1_RAPA"),
    "Ovary_D40_Ctrl": Path(r"D:\Chrome\BG_Subed\D40_Ovary\4_CTRL"),
}

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
output_csv_path = Path(r"D:\Chrome\ratios.csv")

# Process the data for parts a and b
all_ratios = []

for group in raw_group_dirs.keys():
    raw_dir = raw_group_dirs[group]
    bg_sub_dir = bg_subtracted_group_dirs[group]
    
    print(f"Processing group: {group}")
    print(f"Raw dir: {raw_dir}, exists: {raw_dir.exists()}")
    print(f"BG sub dir: {bg_sub_dir}, exists: {bg_sub_dir.exists()}")
    
    raw_files = list(raw_dir.glob('*.txt')) if raw_dir.exists() else []
    print(f"Found {len(raw_files)} raw .txt files")
    
    ratios_for_group = {}  # dict of sample_name to ratios dict
    
    # Part a: fitted background subtraction on raw
    if raw_dir.exists():
        for raw_file in raw_files:
            print(f"Processing raw file: {raw_file}")
            sample_name = raw_file.stem
            try:
                wn, intensity = read_spectrum(raw_file)
                print(f"Read spectrum: wn shape {wn.shape}, intensity shape {intensity.shape}")
                wn_a, sub_intensity, _ = fitted_bg_subtraction(wn, intensity)
                print(f"Fitted bg: wn_a shape {wn_a.shape}, sub_intensity shape {sub_intensity.shape}")
                if wn_a.size == 0:
                    print(f"Skipping {raw_file} due to fitting error")
                    continue
                ratio1 = peak_ratio_calculator(wn_a, sub_intensity, 2850, 3420)
                ratio2 = peak_ratio_calculator(wn_a, sub_intensity, 2940, 3420)
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
        print(f"Found {len(bg_files)} bg sub .txt files")
        for bg_file in bg_files:
            print(f"Processing bg file: {bg_file}")
            sample_name = bg_file.stem
            try:
                wn_b, intensity_b = read_spectrum(bg_file)
                print(f"Read bg spectrum: wn_b shape {wn_b.shape}, intensity_b shape {intensity_b.shape}")
                ratio3 = peak_ratio_calculator(wn_b, intensity_b, 2850, 2940)
                ratio4 = peak_ratio_calculator(wn_b, intensity_b, 2140, 2850)
                ratio5 = peak_ratio_calculator(wn_b, intensity_b, 2180, 2940)
                ratio6 = peak_ratio_calculator(wn_b, intensity_b, 3005, 2850)
                print(f"Ratios b: {ratio3}, {ratio4}, {ratio5}, {ratio6}")
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
save_ratios(output_csv_path, all_ratios)
print(f"Ratios saved to {output_csv_path}")

# Part c: statistical analysis
import pandas as pd
from scipy.stats import f_oneway

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
stats_df.to_csv(stats_csv_path, index=False)
print(f"Stats saved to {stats_csv_path}")