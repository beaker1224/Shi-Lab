import argparse
import os
import time
from collections import OrderedDict

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import tifffile
import umap  # pip install umap-learn
from scipy.interpolate import interp1d
from scipy.stats import fisher_exact
from sklearn.cluster import KMeans, MiniBatchKMeans
import requests


def whittaker_matrix(n, lamda=0.2, d=2):
    """
    Precompute the Whittaker smoothing operator for spectra of length n.

    Whittaker smoothing (rampy's method="whittaker", uniform weights, d=2) solves
        (I + lamda * D^T D) z = y
    for each spectrum y, where D is the d-th order difference matrix.
    The matrix is the same for every pixel, so it is inverted once here and
    all spectra are smoothed together with one matrix product:
        smoothed = M @ spectra        # spectra: (n, n_pixels)
    This replaces the old per-pixel rampy call and removes the rampy dependency.

    Args:
        n (int): number of spectral channels
        lamda (float): smoothing parameter (same meaning as rampy's Lambda)
        d (int): order of the difference penalty
    """
    D = np.diff(np.eye(n), n=d, axis=0)  # (n-d, n)
    A = np.eye(n) + lamda * (D.T @ D)
    return np.linalg.inv(A)


class hSRSAnalyzer:
    def __init__(
        self,
        group_paths: OrderedDict,
        output_folder,
        n_clusters=6,
        spectra_start=2700,
        spectra_end=3100,
        target_channels=60,
        umap_max_points=50000,
        minibatch=False,
        smooth_lambda=0.2,
        chunk_size=200_000,
    ):
        """
        group_paths: OrderedDict[str, str] mapping group_name -> tiff_path
        Args:
            output_folder (str): the path to the output folder
            n_clusters (int): number of clusters
            spectra_start (int): default = 2700, the starting raman shift for hyperspectra
            spectra_end (int): default = 3100, the ending raman shift for hyperspectra
            target_channels (int): default = 60, the number of images for each hyperspectra
            umap_max_points (int): default = 50000, UMAP is fit on at most this many pixels
                (random sample, each group keeps its share). 0 = use every pixel (old behavior).
                K-means always uses every pixel.
            minibatch (bool): default = False, use MiniBatchKMeans instead of KMeans
                (faster on very large pixel counts, results differ slightly from full KMeans)
            smooth_lambda (float): default = 0.2, Whittaker smoothing strength
            chunk_size (int): pixels preprocessed per block (limits memory use)
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
        self.umap_max_points = umap_max_points
        self.minibatch = minibatch
        self.smooth_lambda = smooth_lambda
        self.chunk_size = chunk_size

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
        water_path = os.path.join(script_dir, "PBS_HSI_76.csv")
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

        Vectorized: each step runs on a whole block of pixels at once instead of
        looping over pixels in Python. Same steps and same result as before:
          1. clip negatives to 0
          2. subtract water baseline scaled by the mean of the first 5 channels,
             subtract the new mean of the first 5 channels, clip to 0
          3. divide by the max, then Whittaker-smooth
        Spectra that are all zero stay all zero.
        """
        n_wn, n_px = spectra.shape
        processed = np.zeros((n_wn, n_px), dtype=np.float32)

        if self.baseline_interpolator is not None:
            water_baseline = self.baseline_interpolator(self.wavenumbers)
            water_baseline = np.clip(water_baseline, 0, 1)[:, None]  # (N, 1), broadcasts over pixels
        else:
            water_baseline = None

        smoother = whittaker_matrix(n_wn, self.smooth_lambda)  # (N, N), built once per call

        for start in range(0, n_px, self.chunk_size):
            stop = min(start + self.chunk_size, n_px)
            # cast to float32 first (as the old per-pixel code did), then do the math in float64
            s = np.maximum(spectra[:, start:stop].astype(np.float32), 0).astype(np.float64)

            if water_baseline is not None:
                scale_factor = s[:5].mean(axis=0)  # one value per pixel
                s -= water_baseline * scale_factor
                s -= s[:5].mean(axis=0)  # left_point, one value per pixel
                np.maximum(s, 0, out=s)

            max_val = s.max(axis=0)
            ok = max_val > 0
            s[:, ok] = smoother @ (s[:, ok] / max_val[ok])
            processed[:, start:stop] = s

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
        # Build each group's pixel mask once instead of re-comparing strings for every cluster
        group_masks = {g: condition_labels == g for g in groups}
        totals_by_group = {g: int(np.count_nonzero(group_masks[g])) for g in groups}

        rows = []
        for cid in range(self.n_clusters):
            c_mask = cluster_labels == cid
            total_cluster = int(np.count_nonzero(c_mask))
            counts = {g: int(np.count_nonzero(group_masks[g] & c_mask)) for g in groups}

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
                if not np.any(mask):
                    # a very small cluster can end up with no points in the UMAP sample
                    continue
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
    # Speed helpers
    # ------------------------------
    def umap_sample_indices(self, condition_labels):
        """
        Pick the pixels UMAP is fit on. UMAP is only used for the scatter plots,
        and its run time grows quickly with point count, so it gets a random
        sample of at most umap_max_points pixels. Each group keeps its share of
        the total so the condition plot still reflects the real proportions.
        Returns None when every pixel should be used.
        """
        n = len(condition_labels)
        if self.umap_max_points <= 0 or n <= self.umap_max_points:
            return None
        rng = np.random.default_rng(42)
        frac = self.umap_max_points / n
        picked = []
        for g in self.group_names:
            g_idx = np.flatnonzero(condition_labels == g)
            k = min(len(g_idx), max(1, int(round(len(g_idx) * frac))))
            picked.append(rng.choice(g_idx, size=k, replace=False))
        return np.sort(np.concatenate(picked))

    # ------------------------------
    # Orchestrate full run
    # ------------------------------
    def process_combined_data(self):
        t_start = time.perf_counter()

        # 1) Load all groups
        spectra_by_group = {}
        shapes_by_group = {}
        indices_by_group = {}
        for g, path in self.group_paths.items():
            t0 = time.perf_counter()
            sp, shape, idx = self.load_and_preprocess(path)
            spectra_by_group[g] = sp
            shapes_by_group[g] = shape
            indices_by_group[g] = idx
            print(f"Loaded + preprocessed '{g}': {sp.shape[1]:,} pixels in {time.perf_counter() - t0:.1f} s")

        # 2) Combine and build labels
        per_group_counts = {g: spectra_by_group[g].shape[1] for g in self.group_names}
        # (pixels, wavenumbers), C-contiguous float32: built once and shared by UMAP and KMeans
        X = np.ascontiguousarray(
            np.concatenate([spectra_by_group[g] for g in self.group_names], axis=1).T
        )
        del spectra_by_group  # free the per-group copies
        condition_labels = np.repeat(
            np.array(self.group_names), [per_group_counts[g] for g in self.group_names]
        )

        # 3) UMAP (on a random sample of pixels, for the plots)
        t0 = time.perf_counter()
        umap_idx = self.umap_sample_indices(condition_labels)
        X_umap = X if umap_idx is None else X[umap_idx]
        reducer = umap.UMAP(n_components=2, random_state=42, n_jobs=1)
        embedding = reducer.fit_transform(X_umap)
        print(f"UMAP dimension reduction done on {len(X_umap):,} pixels in {time.perf_counter() - t0:.1f} s.")

        # 4) KMeans (on every pixel)
        t0 = time.perf_counter()
        if self.minibatch:
            kmeans = MiniBatchKMeans(n_clusters=self.n_clusters, random_state=42, n_init=3, batch_size=4096)
        else:
            kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X)
        print(f"{'MiniBatchKMeans' if self.minibatch else 'KMeans'} done on {len(X):,} pixels "
              f"in {time.perf_counter() - t0:.1f} s.")

        # 5) Composition & stats (on every pixel)
        cluster_stats = self.analyze_cluster_composition(cluster_labels, condition_labels)

        # 6) Visualizations
        if umap_idx is None:
            umap_clusters, umap_conditions = cluster_labels, condition_labels
        else:
            umap_clusters, umap_conditions = cluster_labels[umap_idx], condition_labels[umap_idx]
        self.plot_cluster_umap(embedding, umap_clusters, cluster_stats)
        self.plot_condition_umap(embedding, umap_conditions)
        self.plot_cluster_composition(cluster_stats)
        self.plot_cluster_spectra(X.T, cluster_labels)

        # 7) Map back per group
        self.map_clusters(cluster_labels, per_group_counts, shapes_by_group, indices_by_group)
        print(f"All processing completed in {time.perf_counter() - t_start:.1f} s.")


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

def notify_done_ntfy(title = "Task Complete", message = "Your task has finished running."):
    """Send a notification using ntfy.sh service."""
    url = "https://ntfy.sh/K-means-with-love-from-beaker"
    response = requests.post(
        url,
        data=message.encode('utf-8'),
        headers={"Title": title,
                 "Priority": "5"},
                 timeout=20)
    response.raise_for_status()

def main():
    parser = argparse.ArgumentParser(description="Hyperspectral SRS Image Analysis (multi-group).")
    parser.add_argument("--output_folder", type=str, default=r"D:\study\Shi_Lab\Data\K-means_output",
                        help="Output folder")
    parser.add_argument("--n_clusters", type=int, default=8, help="Number of clusters (recommended <= 20)")
    parser.add_argument("--spectra_start", type=float, default=2700, help="Lowest wavenumber")
    parser.add_argument("--spectra_end", type=float, default=3100, help="Highest wavenumber")
    parser.add_argument("--target_channels", type=int, default=62, help="Resampled spectral channels")
    parser.add_argument("--no_prompt", action="store_true",
                        help="Skip interactive prompts (expects --groups_csv)")
    parser.add_argument("--groups_csv", type=str, default="",
                        help="Optional CSV with two columns: group_name,tiff_path")
    parser.add_argument("--umap_max_points", type=int, default=50000,
                        help="Fit UMAP on at most this many randomly sampled pixels (plots only; "
                             "k-means still uses every pixel). 0 = use every pixel.")
    parser.add_argument("--minibatch", action="store_true",
                        help="Use MiniBatchKMeans (faster for very many pixels, slightly different result)")

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
        umap_max_points=args.umap_max_points,
        minibatch=args.minibatch,
    )
    analyzer.process_combined_data()

    notify_done_ntfy(title="K-means Analysis Complete", message="K-means analysis has finished successfully.")


if __name__ == "__main__":
    main()
