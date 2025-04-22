import argparse
import os

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rampy as rp
import tifffile
import umap
from scipy.interpolate import interp1d
from scipy.stats import fisher_exact
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE

# need to check: condition_labels, cluster stats

def smooth_spectrum(spectrum, lamda=0.2):
    """
    Smooth spectrum using Savitzky-Golay filter
    Args
        spectrum: input spectrum
        lamda: smoothing parameter
    """
    if np.all(spectrum == 0):
        return spectrum

    smoothed = rp.smooth(np.arange(len(spectrum)), spectrum, method="whittaker", Lambda=lamda)
    return smoothed


class hSRSAnalyzer:
    # initializer
    def __init__(
        self,
        ctrl_path,
        smo_path,
        fer1_path,
        output_folder,
        n_clusters=6,
        spectra_start=2700,
        spectra_end=3100,
        target_channels=60,
    ):
        self.ctrl_path = ctrl_path
        self.smo_path = smo_path
        self.fer1_path = fer1_path
        self.output_folder = output_folder
        self.n_clusters = n_clusters
        self.spectra_start = spectra_start
        self.spectra_end = spectra_end
        self.wavenumbers = None
        self.water_baseline = None
        self.target_channels = target_channels
        self.colors = np.array(
            [
                [1.0, 0.0, 0.0],  # Pure red
                [0.0, 1.0, 0.0],  # Pure green
                [0.0, 0.0, 1.0],  # Pure blue
                [1.0, 1.0, 0.0],  # Yellow
                [1.0, 0.0, 1.0],  # Magenta
                [0.0, 1.0, 1.0],  # Cyan
                [1.0, 0.5, 0.0],  # Orange
                [0.5, 0.5, 0.5],  # Gray
            ]
        )

        # Set global font settings
        plt.rcParams["font.family"] = "Arial"
        plt.rcParams["font.weight"] = "bold"
        plt.rcParams["axes.labelweight"] = "bold"
        plt.rcParams["axes.titleweight"] = "bold"

        self.load_water_baseline()

    def load_water_baseline(self):
        """Load and process the water baseline data"""
        # this to a abs path is better, since OS is imported
        script_dir = os.path.dirname(os.path.abspath(__file__))  # folder of the current script
        water_path  = os.path.join(script_dir, "water_HSI_76.csv")

        baseline_data = pd.read_csv(water_path, header=None).values.flatten()
        x_original = np.linspace(self.spectra_start, self.spectra_end, len(baseline_data))

        # Reverse the baseline data order
        baseline_data = baseline_data[::-1]
        self.baseline_interpolator = interp1d(
            x_original,
            baseline_data,
            kind="cubic",
            fill_value=(baseline_data[0], baseline_data[-1]),
            bounds_error=False,
        )

    def preprocess_spectra(self, spectra):
        """
        Preprocess each spectrum with water baseline correction, normalization and smoothing
        Args:
            spectra: input spectra (N x n_pixels)
        """
        processed_spectra = np.zeros_like(spectra, dtype=np.float32)
        if self.baseline_interpolator is not None:
            water_baseline = self.baseline_interpolator(self.wavenumbers)
            # Ensure baseline is between 0 and 1
            water_baseline = np.clip(water_baseline, 0, 1)
        else:
            water_baseline = None

        for i in range(spectra.shape[1]):
            if np.all(spectra[:, i] == 0):
                continue

            spectrum = spectra[:, i].astype(np.float32)
            spectrum = np.maximum(spectrum, 0)

            if water_baseline is not None:
                # Scale baseline using mean of first few points instead of just first point
                scale_factor = np.mean(spectrum[:5])
                scaled_baseline = water_baseline * scale_factor

                spectrum = spectrum - scaled_baseline
                left_point = np.mean(spectrum[:5])  # using average of first 5 points for stability
                spectrum = spectrum - left_point
                spectrum = np.maximum(spectrum, 0)

            # Only normalize if spectrum has non-zero values
            if np.any(spectrum):
                max_val = np.max(spectrum)
                if max_val > 0:  # Avoid division by zero
                    spectrum = spectrum / max_val
                    spectrum = smooth_spectrum(spectrum)

            processed_spectra[:, i] = spectrum

        processed_spectra = np.nan_to_num(processed_spectra, nan=0.0, posinf=1.0, neginf=0.0)

        return processed_spectra

    def load_and_preprocess(self, image_path):
        """
        Load and preprocess the hyperspectral image stack
        """
        # Load image stack
        image = tifffile.imread(image_path)
        # flip the image
        image = np.flip(image, axis=0)
        if len(image.shape) != 3:
            raise ValueError("Image should be a hyperspectral image stack")

        N, height, width = image.shape  # N is the number of wavenumbers
        target_N = self.target_channels

        if N != target_N:
            old_axis = np.linspace(self.spectra_start, self.spectra_end, N)
            new_axis = np.linspace(self.spectra_start, self.spectra_end, target_N)
            reshaped_image = image.reshape(N, -1)
            f = interp1d(
                old_axis, reshaped_image, axis=0, kind="linear", bounds_error=False, fill_value="extrapolate"
            )
            interpolated_image = f(new_axis)

            image = interpolated_image.reshape(target_N, height, width)
            N = target_N

        if self.wavenumbers is None:
            self.wavenumbers = np.linspace(self.spectra_start, self.spectra_end, N)

        pixel_intensities = np.sum(
            image, axis=0
        )  # Sum intensities across all wavenumbers, make sure we use the positive pixels
        mask = pixel_intensities > 0

        self.background = ~mask
        nonzero_indices = np.where(mask)  # Get the indices of the nonzero pixels

        reshaped_spectra = image[:, mask].reshape(N, -1)
        processed_spectra = self.preprocess_spectra(reshaped_spectra)

        return processed_spectra, (N, height, width), nonzero_indices

    def analyze_cluster_composition(self, cluster_labels, condition_labels):
        """
        Analyze the composition of each cluster and calculate enrichment statistics
        using 0.5 threshold for enrichment determination

        """
        # cluster_stats is not a global variable, it is local, within this function, but it is returned.
        cluster_stats = []
        # condition_labels is an input, probably a np array, has total 2000 labels.
        # this counts how many conditions in all condition labels
        # condition_labels could be found in later function: process_combined_data
        total_ctrl = np.sum(condition_labels == "GAS_CUT")
        total_fer1 = np.sum(condition_labels == "GAS_MTI")
        total_smo = np.sum(condition_labels == "SOL")

        for cluster_id in range(self.n_clusters): # default n_clusters is 6
            cluster_mask = cluster_labels == cluster_id
            ctrl_count = np.sum((condition_labels == "GAS_CUT") & cluster_mask)
            fer1_count = np.sum((condition_labels == "GAS_MTI") & cluster_mask)
            smo_count = np.sum((condition_labels == "SOL") & cluster_mask)

            total_cluster = ctrl_count + fer1_count + smo_count

            if total_cluster == 0:
                # Avoid division by zero in degenerate cluster
                cluster_stats.append(
                    {
                        "cluster_id": cluster_id,

                        "ctrl_count": 0,
                        "fer1_count": 0,
                        "smo_count": 0,

                        "ctrl_ratio": 0,
                        "fer1_ratio": 0,
                        "smo_ratio": 0,

                        "enrichment": "None",
                        "enrichment_score": 0,
                        "pvalue": 1.0,
                    }
                )
                continue
            # Compute ratios
            ctrl_ratio = ctrl_count / total_cluster
            fer1_ratio = fer1_count / total_cluster
            smo_ratio = smo_count / total_cluster

            # Find dominant condition
            ratio_list = [ # change this will change the name of "enrichment"
                ("GAS_CUT", ctrl_ratio, ctrl_count, total_ctrl),
                ("GAS_MTI", fer1_ratio, fer1_count, total_fer1),
                ("SOL", smo_ratio, smo_count, total_smo),
            ]
            ratio_list.sort(key=lambda x: x[1], reverse=True)
            # The first one in ratio_list is the largest ratio
            dominant_condition, dominant_ratio, dominant_count, dominant_total = ratio_list[0]

            if dominant_ratio > 0.5:
                enrichment = dominant_condition
                enrichment_score = dominant_ratio

                other_count = total_cluster - dominant_count
                other_total = len(condition_labels) - dominant_total

                contingency_table = np.array(
                    [
                        [dominant_count, other_count],
                        [dominant_total - dominant_count, other_total - other_count],
                    ]
                )
                _, pvalue = fisher_exact(contingency_table)
            else:
                # If no single condition is above 0.5, mark cluster as “Mixed”
                enrichment = "Mixed"
                enrichment_score = 0
                pvalue = 1.0

            cluster_stats.append(
                {
                    "cluster_id": cluster_id,

                    "ctrl_count": ctrl_count,
                    "fer1_count": fer1_count,
                    "smo_count": smo_count,

                    "ctrl_ratio": ctrl_ratio,
                    "fer1_ratio": fer1_ratio,
                    "smo_ratio": smo_ratio,

                    "enrichment": enrichment,
                    "enrichment_score": enrichment_score,
                    "pvalue": pvalue,
                }
            )

        return pd.DataFrame(cluster_stats)
        # returned cluster_stats structure:
        # {"cluster_id", "ctrl_count", "fer1_count", "smo_count", "ctrl_ratio", "fer1_ratio", "smo_ratio", "enrichment", "enrichment_score", "pvalue"}

    def plot_cluster_umap(self, embedding, cluster_labels, condition_labels, cluster_stats):
        """Plot enhanced UMAP visualization with cluster annotations"""
        plt.figure(figsize=(6, 6))
        plt.style.use("ggplot")

        plt.scatter(embedding[:, 0], embedding[:, 1], c="lightgray", alpha=0.6, s=5, label="All spectra")
        plt.xlabel("UMAP 1", fontfamily="Arial", fontweight="bold", fontsize=12)
        plt.ylabel("UMAP 2", fontfamily="Arial", fontweight="bold", fontsize=12)
        plt.xticks([])
        plt.yticks([])
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10}, loc="best")
        plt.tight_layout()

        plt.savefig(os.path.join(self.output_folder, "umap_all.tif"), dpi=300, bbox_inches="tight")
        plt.close()

        # Plot clustered UMAP with cluster annotations
        plt.figure(figsize=(8, 6))
        plt.style.use("ggplot")
        for i in range(self.n_clusters):
            cluster_mask = cluster_labels == i
            stats_i = cluster_stats.iloc[i] # see cluster_stats structure annotation
            # stats_i is the for each element in the cluster_stats (dict)

            if stats_i["pvalue"] < 0.05:
                plt.scatter(
                    embedding[cluster_mask, 0],
                    embedding[cluster_mask, 1],
                    c=[self.colors[i]],
                    label=f"Cluster {i+1}", # cluster legend label
                    alpha=0.6,
                    s=5,
                )

                center_x = np.mean(embedding[cluster_mask, 0])
                center_y = np.mean(embedding[cluster_mask, 1])
                plt.text(
                    center_x,
                    center_y,
                    f"{stats_i['enrichment']} enrich",
                    fontsize=12,
                    fontweight="bold",
                    ha="center",
                    va="center",
                )

        plt.xlabel("UMAP 1", fontfamily="Arial", fontweight="bold", fontsize=12)
        plt.ylabel("UMAP 2", fontfamily="Arial", fontweight="bold", fontsize=12)
        plt.xticks([])
        plt.yticks([])
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10}, loc="best")
        plt.tight_layout()

        plt.savefig(
            os.path.join(self.output_folder, "enriched_clusters_umap.tif"), dpi=300, bbox_inches="tight"
        )
        plt.close()

    def plot_condition_umap(self, embedding, condition_labels):
        """
        Plot UMAP visualization colored by condition: ctrl vs. fer-1 vs. smo
        """
        plt.figure(figsize=(7, 6))
        plt.style.use("ggplot")

        ctrl_mask = condition_labels == "GAS_CUT"
        fer1_mask = condition_labels == "GAS_MTI"
        smo_mask = condition_labels == "SOL"

        plt.scatter(
            embedding[ctrl_mask, 0], embedding[ctrl_mask, 1], c="royalblue", label="GAS_CUT", alpha=0.7, s=5
        )
        plt.scatter(
            embedding[fer1_mask, 0], embedding[fer1_mask, 1], c="salmon", label="GAS_MTI", alpha=0.7, s=5
        )
        plt.scatter(embedding[smo_mask, 0], embedding[smo_mask, 1], c="green", label="SOL", alpha=0.7, s=5)

        plt.xlabel("UMAP 1", fontfamily="Arial", fontweight="bold", fontsize=12)
        plt.ylabel("UMAP 2", fontfamily="Arial", fontweight="bold", fontsize=12)
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10})
        plt.tight_layout()
        plt.xticks([])
        plt.yticks([])

        plt.savefig(os.path.join(self.output_folder, "condition_umap.tif"), dpi=300, bbox_inches="tight")
        plt.close()

    def plot_cluster_spectra(self, spectra, cluster_labels):
        """
        Plot mean ± std for each cluster's spectra
        """
        plt.figure(figsize=(8, 6))

        for i in range(self.n_clusters):
            cluster_mask = cluster_labels == i
            cluster_spectra = spectra[:, cluster_mask]
            if cluster_spectra.size == 0:
                continue

            mean_spectrum = np.mean(cluster_spectra, axis=1)
            std_spectrum = np.std(cluster_spectra, axis=1)

            plt.plot(
                self.wavenumbers,
                mean_spectrum + i * 0.5,
                color=self.colors[i],
                label=f"Cluster {i+1}",
                alpha=0.5,
            )
            plt.fill_between(
                self.wavenumbers,
                mean_spectrum + i * 0.5 - std_spectrum,
                mean_spectrum + i * 0.5 + std_spectrum,
                color=self.colors[i],
                alpha=0.2,
            )

        plt.xlabel(r"Wavenumber (cm$^{-1}$)", fontfamily="Arial", fontweight="bold", fontsize=12)
        plt.ylabel("Normalized Intensity", fontfamily="Arial", fontweight="bold", fontsize=12)
        plt.title("Clustered Raman Spectra", fontfamily="Arial", fontweight="bold", fontsize=14)
        plt.xticks(fontweight="bold")
        plt.yticks(fontweight="bold")
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10})
        plt.tight_layout()

        plt.savefig(os.path.join(self.output_folder, "cluster_spectra.svg"), dpi=300, bbox_inches="tight")
        plt.close()

    def map_clusters(
        self,
        cluster_labels,
        n_ctrl_spectra,
        ctrl_shape,
        n_fer1_spectra,
        fer1_shape,
        n_smo_spectra,
        smo_shape,
        ctrl_indices,
        fer1_indices,
        smo_indices,
    ):
        """
        Map cluster labels back to the original images for each condition.
        """
        # Slice cluster_labels for each condition
        ctrl_labels = cluster_labels[:n_ctrl_spectra]
        fer1_labels = cluster_labels[n_ctrl_spectra : n_ctrl_spectra + n_fer1_spectra]
        smo_labels = cluster_labels[n_ctrl_spectra + n_fer1_spectra :]

        # Initialize label images with -1
        ctrl_map = np.full(ctrl_shape[1:], -1)
        fer1_map = np.full(fer1_shape[1:], -1)
        smo_map = np.full(smo_shape[1:], -1)

        # Assign cluster labels back to the correct pixel positions
        ctrl_map[ctrl_indices] = ctrl_labels
        fer1_map[fer1_indices] = fer1_labels
        smo_map[smo_indices] = smo_labels

        # Create RGB overlays
        ctrl_rgb = np.zeros((*ctrl_shape[1:], 3), dtype=np.float32)
        fer1_rgb = np.zeros((*fer1_shape[1:], 3), dtype=np.float32)
        smo_rgb = np.zeros((*smo_shape[1:], 3), dtype=np.float32)

        for i in range(self.n_clusters):
            ctrl_rgb[ctrl_map == i] = self.colors[i]
            fer1_rgb[fer1_map == i] = self.colors[i]
            smo_rgb[smo_map == i] = self.colors[i]

        tifffile.imwrite(
            os.path.join(self.output_folder, "GAS_CUT_clusters.tif"), (ctrl_rgb * 255).astype(np.uint8)
        )
        tifffile.imwrite(
            os.path.join(self.output_folder, "GAS_MTI_clusters.tif"), (fer1_rgb * 255).astype(np.uint8)
        )
        tifffile.imwrite(
            os.path.join(self.output_folder, "SOL_clusters.tif"), (smo_rgb * 255).astype(np.uint8)
        )

    def plot_cluster_composition(self, cluster_stats: pd.DataFrame):
        """
        Show each cluster’s fraction of ctrl, fer-1, and smo in a grouped bar chart.
        """
        plt.figure(figsize=(8, 6))
        x = np.arange(self.n_clusters)
        bar_width = 0.25

        # Plot ctrl ratio
        plt.bar(
            x - bar_width,
            cluster_stats["ctrl_ratio"],
            width=bar_width,
            color="royalblue",
            alpha=0.7,
            label="GAS_CUT",
        )
        # Plot fer-1 ratio
        plt.bar(x, cluster_stats["fer1_ratio"], width=bar_width, color="salmon", alpha=0.7, label="GAS_MTI")
        # Plot smo ratio
        plt.bar(
            x + bar_width, cluster_stats["smo_ratio"], width=bar_width, color="green", alpha=0.7, label="SOL"
        )

        plt.axhline(y=0.5, color="black", linestyle="--", alpha=0.6)
        plt.xticks(x, [f"Cluster {i+1}" for i in x], fontweight="bold", fontsize=10, rotation=45)
        plt.ylabel("Fraction of Pixels in Cluster", fontsize=12, fontweight="bold")
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10})
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_folder, "cluster_composition.svg"), dpi=300, bbox_inches="tight")
        plt.close()

    def process_combined_data(self):
        """
        Load, preprocess, combine, and analyze data from three conditions.
        """
        # 1) Load + Preprocess
        ctrl_spectra, ctrl_shape, ctrl_indices = self.load_and_preprocess(self.ctrl_path)
        fer1_spectra, fer1_shape, fer1_indices = self.load_and_preprocess(self.fer1_path)
        smo_spectra, smo_shape, smo_indices = self.load_and_preprocess(self.smo_path)

        # 2) Combine
        combined_spectra = np.concatenate([ctrl_spectra, fer1_spectra, smo_spectra], axis=1)
        condition_labels = np.array(
            ["GAS_CUT"] * ctrl_spectra.shape[1]
            + ["GAS_MTI"] * fer1_spectra.shape[1]
            + ["SOL"] * smo_spectra.shape[1]
        )

        # 3 UMAP embedding
        reducer = umap.UMAP(n_components=2, random_state=42, n_jobs=1)
        embedding = reducer.fit_transform(combined_spectra.T)
        print("UMAP dimension reduction done.")

        # 4 K-means clustering
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(combined_spectra.T)

        # 5 Analyze cluster composition
        cluster_stats = self.analyze_cluster_composition(cluster_labels, condition_labels)

        # 6 Visualizations
        self.plot_cluster_umap(embedding, cluster_labels, condition_labels, cluster_stats)
        self.plot_condition_umap(embedding, condition_labels)
        self.plot_cluster_composition(cluster_stats)
        self.plot_cluster_spectra(combined_spectra, cluster_labels)

        # 7 Map clusters back to images
        self.map_clusters(
            cluster_labels,
            ctrl_spectra.shape[1],
            ctrl_shape,
            fer1_spectra.shape[1],
            fer1_shape,
            smo_spectra.shape[1],
            smo_shape,
            ctrl_indices,
            fer1_indices,
            smo_indices,
        )
        print("All processing completed.")


def main():
    parser = argparse.ArgumentParser(description="Hyperspectral SRS Image Analysis for 3 conditions.")
    parser.add_argument("--ctrl_path", type=str, default="D:\\study\\Shi Lab\\Data\\Training Muscle\\Human Biopsy\\hSRS tiffs\\GAS Cut CH-zoom4.tif", help="Path to ctrl/hsi.tif")
    parser.add_argument("--fer1_path", type=str, default="D:\\study\\Shi Lab\\Data\\Training Muscle\\Human Biopsy\\hSRS tiffs\\GAS MTI CH-zoom4.tif", help="Path to fer-1/hsi.tif")
    parser.add_argument("--smo_path", type=str, default="D:\\study\\Shi Lab\\Data\\Training Muscle\\Human Biopsy\\hSRS tiffs\\SOL CH-zoom4.tif", help="Path to smo/hsi.tif")
    parser.add_argument("--output_folder", type=str, default="D:\\Chrome\\Workspace\\Codes\\cluster_shuo", help="Output folder")
    parser.add_argument("--n_clusters", type=int, default=6, help="Number of clusters (<= 8)")
    parser.add_argument("--spectra_start", type=float, default=2700, help="Lowest wavenumber")
    parser.add_argument("--spectra_end", type=float, default=3100, help="Highest wavenumber")

    args = parser.parse_args()
    os.makedirs(args.output_folder, exist_ok=True)

    analyzer = hSRSAnalyzer(
        ctrl_path=args.ctrl_path,
        fer1_path=args.fer1_path,
        smo_path=args.smo_path,
        output_folder=args.output_folder,
        n_clusters=args.n_clusters,
        spectra_start=args.spectra_start,
        spectra_end=args.spectra_end,
    )
    analyzer.process_combined_data()


if __name__ == "__main__":
    main()
