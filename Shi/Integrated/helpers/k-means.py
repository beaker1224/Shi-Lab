import argparse
import os
from collections import OrderedDict

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rampy as rp
import tifffile
import umap  # pip install umap-learn
from scipy.interpolate import interp1d
from scipy.stats import fisher_exact
from sklearn.cluster import KMeans


def smooth_spectrum(spectrum, lamda=0.2):
    """
    Smooth spectrum using Whittaker smoothing via rampy.
    Args:
        spectrum (1D array): input spectrum
        lamda (float): smoothing parameter
    """
    if np.all(spectrum == 0):
        return spectrum
    return rp.smooth(np.arange(len(spectrum)), spectrum, method="whittaker", Lambda=lamda)


class hSRSAnalyzer:
    def __init__(
        self,
        group_paths: OrderedDict,
        output_folder,
        n_clusters=6,
        spectra_start=2700,
        spectra_end=3100,
        target_channels=60,
    ):
        """
        group_paths: OrderedDict[str, str] mapping group_name -> tiff_path
        Args:
            output_folder (str): the path to the output folder
            n_clusters (int): number of clusters
            spectra_start (int): default = 2700, the starting raman shift for hyperspectra
            spectra_end (int): default = 3100, the ending raman shift for hyperspectra
            target_channels (int): default = 60, the number of images for each hyperspectra
        """
        self.group_paths = group_paths
        self.group_names = list(group_paths.keys())
        self.output_folder = output_folder
        self.n_clusters = n_clusters
        self.spectra_start = spectra_start
        self.spectra_end = spectra_end
        self.wavenumbers = None
        self.water_baseline = None
        self.target_channels = target_channels

        # Colors for CLUSTERS (not groups). Will cycle if n_clusters > base palette length.
        base_colors = np.array(
            [
                [1.0, 0.0, 0.0],  # red
                [0.0, 1.0, 0.0],  # green
                [0.0, 0.0, 1.0],  # blue
                [1.0, 1.0, 0.0],  # yellow
                [1.0, 0.0, 1.0],  # magenta
                [0.0, 1.0, 1.0],  # cyan
                [1.0, 0.5, 0.0],  # orange
                [0.5, 0.5, 0.5],  # gray
            ]
        )
        if n_clusters <= len(base_colors):
            self.cluster_colors = base_colors[:n_clusters]
        else:
            # fall back to tab20 over cluster index
            cmap = cm.get_cmap("tab20", n_clusters)
            self.cluster_colors = np.array([cmap(i)[:3] for i in range(n_clusters)])

        # Colors for GROUPS (conditions) for UMAP-by-group and composition plots
        g_cmap = cm.get_cmap("tab20", max(3, len(self.group_names)))
        self.group_color_map = {g: g_cmap(i)[:3] for i, g in enumerate(self.group_names)}

        # Global font settings
        plt.rcParams["font.family"] = "Arial"
        plt.rcParams["font.weight"] = "bold"
        plt.rcParams["axes.labelweight"] = "bold"
        plt.rcParams["axes.titleweight"] = "bold"

        self.load_water_baseline()

    # ------------------------------
    # Baseline / preprocessing
    # ------------------------------
    def load_water_baseline(self):
        """Load and prepare the water baseline."""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        water_path = os.path.join(script_dir, "water_HSI_76.csv")
        baseline_data = pd.read_csv(water_path, header=None).values.flatten()
        x_original = np.linspace(self.spectra_start, self.spectra_end, len(baseline_data))
        baseline_data = baseline_data[::-1]  # reverse
        self.baseline_interpolator = interp1d(
            x_original,
            baseline_data,
            kind="cubic",
            fill_value=(baseline_data[0], baseline_data[-1]),
            bounds_error=False,
        )

    def preprocess_spectra(self, spectra):
        """
        Apply baseline subtract, normalize to max, smooth.
        spectra: (N_wavenumbers, N_pixels)
        """
        processed = np.zeros_like(spectra, dtype=np.float32)

        if self.baseline_interpolator is not None:
            water_baseline = self.baseline_interpolator(self.wavenumbers)
            water_baseline = np.clip(water_baseline, 0, 1)
        else:
            water_baseline = None

        for i in range(spectra.shape[1]):
            if np.all(spectra[:, i] == 0):
                continue
            s = spectra[:, i].astype(np.float32)
            s = np.maximum(s, 0)

            if water_baseline is not None:
                scale_factor = float(np.mean(s[:5]))
                scaled_baseline = water_baseline * scale_factor
                s = s - scaled_baseline
                left_point = float(np.mean(s[:5]))
                s = s - left_point
                s = np.maximum(s, 0)

            if np.any(s):
                max_val = float(np.max(s))
                if max_val > 0:
                    s = s / max_val
                    s = smooth_spectrum(s)

            processed[:, i] = s

        processed = np.nan_to_num(processed, nan=0.0, posinf=1.0, neginf=0.0)
        return processed

    def load_and_preprocess(self, image_path):
        """
        Load hyperspectral tif -> interpolate channels if needed -> flatten valid pixels -> preprocess
        Returns:
            processed_spectra (N, P)
            shape_tuple (N, H, W)
            nonzero_indices (tuple of arrays)
        """
        image = tifffile.imread(image_path)
        image = np.flip(image, axis=0)  # keep behavior from your script

        if len(image.shape) != 3:
            raise ValueError("Image must be a hyperspectral stack with shape (N_wavenumbers, H, W).")

        N, H, W = image.shape
        if N != self.target_channels:
            old_axis = np.linspace(self.spectra_start, self.spectra_end, N)
            new_axis = np.linspace(self.spectra_start, self.spectra_end, self.target_channels)
            reshaped = image.reshape(N, -1)
            f = interp1d(old_axis, reshaped, axis=0, kind="linear", bounds_error=False, fill_value="extrapolate")
            image = f(new_axis).reshape(self.target_channels, H, W)
            N = self.target_channels

        if self.wavenumbers is None:
            self.wavenumbers = np.linspace(self.spectra_start, self.spectra_end, N)

        pixel_sum = np.sum(image, axis=0)
        mask = pixel_sum > 0
        nonzero_indices = np.where(mask)

        spectra = image[:, mask].reshape(N, -1)
        processed = self.preprocess_spectra(spectra)
        return processed, (N, H, W), nonzero_indices

    # ------------------------------
    # Analysis
    # ------------------------------
    def analyze_cluster_composition(self, cluster_labels, condition_labels):
        """
        Compute per-cluster composition across arbitrary number of groups.
        Enrichment rule: dominant group ratio > 0.5; Fisher exact test (dominant vs all others).
        Returns a DataFrame with ratio columns per group and enrichment fields.
        """
        groups = self.group_names
        totals_by_group = {g: int(np.sum(condition_labels == g)) for g in groups}

        rows = []
        for cid in range(self.n_clusters):
            c_mask = cluster_labels == cid
            total_cluster = int(np.sum(c_mask))
            counts = {g: int(np.sum((condition_labels == g) & c_mask)) for g in groups}

            if total_cluster == 0:
                row = {"cluster_id": cid, "enrichment": "None", "enrichment_score": 0.0, "pvalue": 1.0}
                row.update({f"{g}_count": 0 for g in groups})
                row.update({f"{g}_ratio": 0.0 for g in groups})
                rows.append(row)
                continue

            ratios = {g: counts[g] / total_cluster for g in groups}
            # find dominant
            dominant = max(groups, key=lambda g: ratios[g])
            dominant_ratio = ratios[dominant]
            dominant_count = counts[dominant]
            dominant_total = totals_by_group[dominant]

            if dominant_ratio > 0.5:
                other_count = total_cluster - dominant_count
                other_total = len(condition_labels) - dominant_total
                table = np.array(
                    [
                        [dominant_count, other_count],
                        [dominant_total - dominant_count, other_total - other_count],
                    ]
                )
                _, pvalue = fisher_exact(table)
                enrichment = dominant
                enrichment_score = dominant_ratio
            else:
                enrichment = "Mixed"
                enrichment_score = 0.0
                pvalue = 1.0

            row = {"cluster_id": cid, "enrichment": enrichment, "enrichment_score": enrichment_score, "pvalue": pvalue}
            row.update({f"{g}_count": counts[g] for g in groups})
            row.update({f"{g}_ratio": ratios[g] for g in groups})
            rows.append(row)

        return pd.DataFrame(rows)

    # ------------------------------
    # Plots
    # ------------------------------
    def plot_cluster_umap(self, embedding, cluster_labels, cluster_stats):
        # UMAP of all points
        plt.figure(figsize=(6, 6))
        plt.style.use("ggplot")
        plt.scatter(embedding[:, 0], embedding[:, 1], c="lightgray", alpha=0.6, s=5, label="All spectra")
        plt.xlabel("UMAP 1", fontsize=12, fontweight="bold")
        plt.ylabel("UMAP 2", fontsize=12, fontweight="bold")
        plt.xticks([]); plt.yticks([])
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10}, loc="best")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_folder, "umap_all.tif"), dpi=300, bbox_inches="tight")
        plt.close()

        # Enriched clusters only
        plt.figure(figsize=(8, 6))
        plt.style.use("ggplot")
        for i in range(self.n_clusters):
            stats_i = cluster_stats[cluster_stats["cluster_id"] == i].iloc[0]
            if stats_i["pvalue"] < 0.05:
                mask = cluster_labels == i
                plt.scatter(embedding[mask, 0], embedding[mask, 1], c=[self.cluster_colors[i]], s=5, alpha=0.6,
                            label=f"Cluster {i+1}")
                cx, cy = float(np.mean(embedding[mask, 0])), float(np.mean(embedding[mask, 1]))
                plt.text(cx, cy, f"{stats_i['enrichment']} enrich", fontsize=12, fontweight="bold",
                         ha="center", va="center")
        plt.xlabel("UMAP 1", fontsize=12, fontweight="bold")
        plt.ylabel("UMAP 2", fontsize=12, fontweight="bold")
        plt.xticks([]); plt.yticks([])
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10}, loc="best")
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_folder, "enriched_clusters_umap.tif"), dpi=300, bbox_inches="tight")
        plt.close()

    def plot_condition_umap(self, embedding, condition_labels):
        plt.figure(figsize=(7, 6))
        plt.style.use("ggplot")
        for g in self.group_names:
            mask = condition_labels == g
            plt.scatter(embedding[mask, 0], embedding[mask, 1],
                        c=[self.group_color_map[g]], label=g, alpha=0.7, s=5)
        plt.xlabel("UMAP 1", fontsize=12, fontweight="bold")
        plt.ylabel("UMAP 2", fontsize=12, fontweight="bold")
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10}, markerscale=3)
        plt.xticks([]); plt.yticks([])
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_folder, "condition_umap.tif"), dpi=300, bbox_inches="tight")
        plt.close()

    def plot_cluster_spectra(self, spectra, cluster_labels):
        plt.figure(figsize=(8, 6))
        offset = 0.5
        for i in range(self.n_clusters):
            mask = cluster_labels == i
            cl = spectra[:, mask]
            if cl.size == 0:
                continue
            mean_s = np.mean(cl, axis=1)
            std_s = np.std(cl, axis=1)
            base = i * offset
            plt.plot(self.wavenumbers, mean_s + base, color=self.cluster_colors[i], label=f"Cluster {i+1}", alpha=0.8)
            plt.fill_between(self.wavenumbers, mean_s + base - std_s, mean_s + base + std_s,
                             color=self.cluster_colors[i], alpha=0.25)
        plt.xlabel(r"Wavenumber (cm$^{-1}$)", fontsize=12, fontweight="bold")
        plt.ylabel("Normalized Intensity", fontsize=12, fontweight="bold")
        plt.title("Clustered Raman Spectra", fontsize=14, fontweight="bold")
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10})
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_folder, "cluster_spectra.svg"), dpi=300, bbox_inches="tight")
        plt.close()

    def plot_cluster_composition(self, cluster_stats: pd.DataFrame):
        """
        Grouped bar chart for arbitrary groups. Bars = per-cluster; colors = groups.
        """
        groups = self.group_names
        x = np.arange(self.n_clusters)
        bar_width = min(0.8 / max(1, len(groups)), 0.25)

        plt.figure(figsize=(max(8, 1.0 * self.n_clusters), 6))
        for j, g in enumerate(groups):
            ratios = cluster_stats[f"{g}_ratio"].values
            plt.bar(x + (j - (len(groups)-1)/2) * bar_width,
                    ratios, width=bar_width, color=self.group_color_map[g], alpha=0.8, label=g)

        plt.axhline(0.5, color="black", linestyle="--", alpha=0.6)
        plt.xticks(x, [f"Cluster {i+1}" for i in x], fontweight="bold", rotation=45)
        plt.ylabel("Fraction of Pixels in Cluster", fontsize=12, fontweight="bold")
        plt.legend(prop={"family": "Arial", "weight": "bold", "size": 10}, ncols=min(4, len(groups)))
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_folder, "cluster_composition.svg"), dpi=300, bbox_inches="tight")
        plt.close()

    # ------------------------------
    # Mapping back to images
    # ------------------------------
    def map_clusters(self, cluster_labels, per_group_counts, per_group_shapes, per_group_indices):
        """
        Save an RGB cluster map per group.
        """
        # partition cluster_labels by contiguous chunks per group (in the same order we concatenated)
        start = 0
        for g in self.group_names:
            count = per_group_counts[g]
            labels_g = cluster_labels[start:start + count]
            start += count

            (N, H, W) = per_group_shapes[g]
            idx = per_group_indices[g]
            label_map = np.full((H, W), -1, dtype=int)
            label_map[idx] = labels_g

            rgb = np.zeros((H, W, 3), dtype=np.float32)
            for i in range(self.n_clusters):
                rgb[label_map == i] = self.cluster_colors[i]

            out_path = os.path.join(self.output_folder, f"{g}_clusters.tif")
            tifffile.imwrite(out_path, (rgb * 255).astype(np.uint8))

    # ------------------------------
    # Orchestrate full run
    # ------------------------------
    def process_combined_data(self):
        # 1) Load all groups
        spectra_by_group = {}
        shapes_by_group = {}
        indices_by_group = {}
        for g, path in self.group_paths.items():
            sp, shape, idx = self.load_and_preprocess(path)
            spectra_by_group[g] = sp
            shapes_by_group[g] = shape
            indices_by_group[g] = idx

        # 2) Combine and build labels
        spectra_list = [spectra_by_group[g] for g in self.group_names]
        combined_spectra = np.concatenate(spectra_list, axis=1)
        condition_labels = np.concatenate(
            [np.array([g] * spectra_by_group[g].shape[1]) for g in self.group_names]
        )

        # 3) UMAP
        reducer = umap.UMAP(n_components=2, random_state=42, n_jobs=1)
        embedding = reducer.fit_transform(combined_spectra.T)
        print("UMAP dimension reduction done.")

        # 4) KMeans
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(combined_spectra.T)

        # 5) Composition & stats
        cluster_stats = self.analyze_cluster_composition(cluster_labels, condition_labels)

        # 6) Visualizations
        self.plot_cluster_umap(embedding, cluster_labels, cluster_stats)
        self.plot_condition_umap(embedding, condition_labels)
        self.plot_cluster_composition(cluster_stats)
        self.plot_cluster_spectra(combined_spectra, cluster_labels)

        # 7) Map back per group
        per_group_counts = {g: spectra_by_group[g].shape[1] for g in self.group_names}
        self.map_clusters(cluster_labels, per_group_counts, shapes_by_group, indices_by_group)
        print("All processing completed.")


# ------------------------------
# Interactive group setup
# ------------------------------
def prompt_groups_from_user() -> OrderedDict:
    """
    Ask:
      1) how many groups?
      2) group name for each
      3) tiff path for each
    Returns OrderedDict[group_name] = path
    """
    print("\n=== Group Setup ===")
    while True:
        try:
            n = int(input("How many groups do you have? (e.g., 3): ").strip())
            if n <= 0:
                raise ValueError
            break
        except ValueError:
            print("Please enter a positive integer.")

    groups = OrderedDict()
    for i in range(1, n + 1):
        while True:
            gname = input(f"Enter name for group #{i} (e.g., ctrl, treatedA): ").strip()
            if gname and gname not in groups:
                break
            print("Name cannot be empty or duplicated.")
        while True:
            gpath = input(f"Enter TIFF file path for group '{gname}': ").strip().strip('"').strip("'")
            if os.path.isfile(gpath):
                break
            print("Path does not exist or is not a file. Please try again.")
        groups[gname] = gpath

    print("\nGroups configured:")
    for k, v in groups.items():
        print(f"  - {k}: {v}")
    return groups


def main():
    parser = argparse.ArgumentParser(description="Hyperspectral SRS Image Analysis (multi-group).")
    parser.add_argument("--output_folder", type=str, default=r"D:\Chrome\Rapamycin\data\gut\Cluster Tiffs\Cluster Results\All",
                        help="Output folder")
    parser.add_argument("--n_clusters", type=int, default=6, help="Number of clusters (recommended <= 20)")
    parser.add_argument("--spectra_start", type=float, default=2700, help="Lowest wavenumber")
    parser.add_argument("--spectra_end", type=float, default=3100, help="Highest wavenumber")
    parser.add_argument("--target_channels", type=int, default=62, help="Resampled spectral channels")
    parser.add_argument("--no_prompt", action="store_true",
                        help="Skip interactive prompts (expects --groups_csv)")
    parser.add_argument("--groups_csv", type=str, default="",
                        help="Optional CSV with two columns: group_name,tiff_path")

    args = parser.parse_args()
    os.makedirs(args.output_folder, exist_ok=True)

    # Build group map either from CSV or interactive prompt
    group_paths = OrderedDict()
    if args.no_prompt and args.groups_csv:
        df = pd.read_csv(args.groups_csv)
        if not {"group_name", "tiff_path"} <= set(df.columns):
            raise ValueError("CSV must have columns: group_name,tiff_path")
        for _, row in df.iterrows():
            g = str(row["group_name"])
            p = str(row["tiff_path"])
            if not os.path.isfile(p):
                raise FileNotFoundError(f"Missing file for group '{g}': {p}")
            if g in group_paths:
                raise ValueError(f"Duplicate group name in CSV: {g}")
            group_paths[g] = p
    else:
        group_paths = prompt_groups_from_user()

    analyzer = hSRSAnalyzer(
        group_paths=group_paths,
        output_folder=args.output_folder,
        n_clusters=args.n_clusters,
        spectra_start=args.spectra_start,
        spectra_end=args.spectra_end,
        target_channels=args.target_channels,
    )
    analyzer.process_combined_data()


if __name__ == "__main__":
    main()
