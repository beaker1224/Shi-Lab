# This is a code updated by Shuo, original code please see ratio_analysis.py in Fung's paper.


import argparse
import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy.stats as stats
import seaborn as sns
from skimage import io

# --- Configuration Constants ---
# Moved out of __init__ methods and defined globally for easy adjustments
LABEL_INFO = {1: "Nuclei", 2: "Cytoplasm", 3: "Cell", 4: "Lipid droplets"} # Fixed "Nuceli" typo
REGIONS_TO_PLOT = ["Nuclei", "Cytoplasm", "Cell"]


# --- Data Extraction Functions ---

def process_roi(roi_path, folder_name, folder_type):
    """Process a single ROI folder and extract pixel data using fast vectorization."""
    roi_name = os.path.basename(roi_path).lower()
    try:
        lipid_img = io.imread(os.path.join(roi_path, "lipid_unsaturation.tif"))
        redox_img = io.imread(os.path.join(roi_path, "redox_ratio.tif"))
        seg_img = io.imread(os.path.join(roi_path, f"{roi_name}_labels.tif"))
    except FileNotFoundError as e:
        print(f"Error loading images in {roi_path}: {e}")
        return pd.DataFrame() # Return empty DataFrame on failure

    # Vectorized filtering: Create a master mask for valid signals (>= 0.05)
    valid_signal_mask = (lipid_img >= 0.05) & (redox_img >= 0.05)
    
    extracted_data = []
    
    for label_val, label_name in LABEL_INFO.items():
        # Combine the segmentation mask with our valid signal mask
        final_mask = (seg_img == label_val) & valid_signal_mask
        
        # Instantly extract all valid pixels using boolean indexing (No for-loops!)
        valid_lipids = lipid_img[final_mask]
        valid_redox = redox_img[final_mask]
        
        if len(valid_lipids) > 0:
            # Build a dataframe directly from the arrays
            df_region = pd.DataFrame({
                "name": folder_name,
                "type": folder_type,
                "roi": os.path.basename(roi_path),
                "label": label_name,
                "lipid_unsaturation": valid_lipids,
                "redox_ratio": valid_redox
            })
            extracted_data.append(df_region)
            
    # Combine all regions into one DataFrame, or return empty if nothing was found
    return pd.concat(extracted_data, ignore_index=True) if extracted_data else pd.DataFrame()


def process_folder(folder_path):
    """Process an entire folder containing multiple ROI subfolders."""
    folder_name = os.path.basename(folder_path)
    folder_type = "control" if "control" in folder_name.lower() else "disease"

    folder_dataframes = []
    for roi_folder in glob.glob(os.path.join(folder_path, "ROI*")):
        df_roi = process_roi(roi_folder, folder_name, folder_type)
        if not df_roi.empty:
            folder_dataframes.append(df_roi)
            
    return pd.concat(folder_dataframes, ignore_index=True) if folder_dataframes else pd.DataFrame()


# --- Data Processing Functions ---

def load_and_sample_data(csv_files, sample_size=10000):
    """Load, filter, and sample data from multiple CSVs."""
    all_data = []
    for file in csv_files:
        df = pd.read_csv(file)
        # Ensure type is explicitly set based on filename to prevent mismatch bugs later
        df["type"] = "control" if "control" in file.lower() else "disease"

        # Filter out extreme values
        df = df[df["lipid_unsaturation"].between(0.1, 1, inclusive="neither")]
        df = df[df["redox_ratio"].between(0.1, 1, inclusive="neither")]

        # Sample data to prevent massive memory usage
        if len(df) > sample_size:
            samples_per_label = sample_size // len(df["label"].unique())
            df = (
                df.groupby("label")
                .apply(lambda x: x.sample(n=min(len(x), samples_per_label), random_state=42))
                .reset_index(drop=True)
            )
        all_data.append(df)
        
    return pd.concat(all_data, ignore_index=True)


# --- Plotting Functions ---

def get_significance(p_val):
    """Convert p-value to significance stars."""
    if p_val < 0.001: return "***"
    elif p_val < 0.01: return "**"
    elif p_val < 0.05: return "*"
    return "ns"


def plot_boxplot_comparison(data, output_path, metric):
    """Generate and save a boxplot comparing control vs disease."""
    plt.style.use("ggplot")
    plt.figure(figsize=(8, 5))
    
    # Filter data for just the regions we want to plot
    plot_data = data[data["label"].isin(REGIONS_TO_PLOT)]

    sns.boxplot(
        x="label", y=metric, hue="type", data=plot_data,
        order=REGIONS_TO_PLOT, hue_order=["control", "disease"],
        palette={"control": "#7FB2D5", "disease": "#F47F72"},
        width=0.2, boxprops=dict(alpha=0.7), medianprops=dict(color="black")
    )

    # Calculate and draw significance markers (Fixed group name mismatch here)
    y_max = plot_data[metric].max()
    y_range = y_max - plot_data[metric].min()

    for i, region in enumerate(REGIONS_TO_PLOT):
        disease_data = plot_data[(plot_data["type"] == "disease") & (plot_data["label"] == region)][metric]
        control_data = plot_data[(plot_data["type"] == "control") & (plot_data["label"] == region)][metric]

        if not disease_data.empty and not control_data.empty:
            _, p_val = stats.ttest_ind(disease_data, control_data)
            y_pos = y_max + 0.05 * y_range

            # Draw the bracket and text
            plt.plot(
                [i - 0.2, i - 0.2, i + 0.2, i + 0.2],
                [y_pos, y_pos + 0.03 * y_range, y_pos + 0.03 * y_range, y_pos],
                lw=1, c="black"
            )
            plt.text(i, y_pos + 0.04 * y_range, get_significance(p_val), ha="center", va="bottom", fontsize=10)

    # Formatting
    metric_title = metric.replace('_', ' ').title()
    plt.title(f"Disease vs Control: {metric_title}", fontsize=12, fontweight="bold")
    plt.xlabel("Region", fontsize=12, fontweight="bold")
    plt.ylabel(metric_title, fontsize=12, fontweight="bold")
    plt.xticks(fontsize=12, fontweight="bold")
    plt.yticks(fontsize=12, fontweight="bold")

    plt.tight_layout()
    plt.savefig(os.path.join(output_path, f"disease_vs_control_comparison_{metric}.svg"), dpi=300)
    plt.close()


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Analyze tissue images and generate statistical plots.")
    parser.add_argument("--folders", nargs="+", required=True, help="List of folder paths containing tissue images")
    parser.add_argument("--output-dir", default="figures/boxplot", help="Output directory for generated plots")
    parser.add_argument("--sample-size", type=int, default=50000, help="Number of samples to take per label")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Process folders and generate CSV files
    csv_files = []
    for folder in args.folders:
        df_folder = process_folder(folder)
        if not df_folder.empty:
            csv_path = os.path.join(folder, f"{os.path.basename(folder)}.csv")
            df_folder.to_csv(csv_path, index=False)
            csv_files.append(csv_path)

    # Load, sample, and plot
    if csv_files:
        all_data = load_and_sample_data(csv_files, args.sample_size)
        for metric in ["lipid_unsaturation", "redox_ratio"]:
            plot_boxplot_comparison(all_data, args.output_dir, metric)
    else:
        print("No valid data was found to process.")


if __name__ == "__main__":
    main()