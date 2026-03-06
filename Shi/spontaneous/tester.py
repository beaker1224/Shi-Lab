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
7. lipid packing ratio: 2875 cm-1 / 2850 cm-1

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


def main():
    pass