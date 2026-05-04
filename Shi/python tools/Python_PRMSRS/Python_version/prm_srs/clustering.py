from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from skimage.color import label2rgb

from .image_io import read_oir_folder_image, save_tiff
from .plotting import save_figure, style_axes
from .spectra import image_normalization


def split_images2(images: np.ndarray, n_clusters: int, random_state: int = 0) -> np.ndarray:
    images_2d = np.asarray(images, dtype=float).reshape(images.shape[0], -1).T
    kmeans = KMeans(
        n_clusters=n_clusters,
        max_iter=1000,
        n_init=5,
        random_state=random_state,
    )
    clusters = kmeans.fit_predict(images_2d) + 1
    return clusters.reshape(images.shape[1], images.shape[2])


def pairwise_distance(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=float).T
    b = np.asarray(b, dtype=float).T
    difference = a[:, None, :] - b[None, :, :]
    return np.sqrt(np.mean(difference**2, axis=2))


def revise_label3(
    kmeans_labels: np.ndarray,
    representative_spectral: np.ndarray,
    pair_matches: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    revised_labels = np.zeros_like(kmeans_labels)
    revised_spectral = np.zeros_like(representative_spectral)
    for left_label, right_label in np.asarray(pair_matches, dtype=int):
        idx = kmeans_labels == right_label
        revised_labels[idx] = left_label
        revised_spectral[:, left_label - 1] = representative_spectral[:, right_label - 1]
    return revised_labels, revised_spectral


def matchpairs(distance: np.ndarray) -> np.ndarray:
    row_idx, col_idx = linear_sum_assignment(distance)
    return np.column_stack([row_idx + 1, col_idx + 1])


def srs_unsupervised_clustering(
    base_folder: Path | str,
    data_folder: str = "fixed brain",
    output_folder: Path | str = "unsupervised_clusters",
    n_clusters: int = 8,
) -> None:
    dataset_folder = Path(base_folder) / data_folder
    output_root = Path(output_folder) / data_folder
    output_root.mkdir(parents=True, exist_ok=True)

    folder_names = sorted(path.name for path in dataset_folder.iterdir() if path.is_dir())
    task_counts = len(folder_names)
    wavenumber = np.linspace(835, 860, 76)

    labels_per_task: list[np.ndarray] = []
    spectra_per_task: list[np.ndarray] = []

    for folder_name in folder_names:
        folder_path = dataset_folder / folder_name
        image = read_oir_folder_image(folder_path)
        images = image_normalization(image)
        split_image = split_images2(images, n_clusters)
        labels_per_task.append(split_image)

        images_2d = images.reshape(images.shape[0], -1)
        labels_2d = split_image.reshape(-1)
        reference_spectral = np.zeros((images.shape[0], n_clusters), dtype=float)
        for cluster_idx in range(1, n_clusters + 1):
            mask = labels_2d == cluster_idx
            reference_spectral[:, cluster_idx - 1] = images_2d[:, mask].mean(axis=1)
        spectra_per_task.append(reference_spectral)

    revised_labels = [labels_per_task[0]]
    revised_spectra = [spectra_per_task[0]]
    for task_idx in range(1, task_counts):
        distance = pairwise_distance(spectra_per_task[0], spectra_per_task[task_idx])
        pair_matches = matchpairs(distance)
        labels, spectra = revise_label3(
            labels_per_task[task_idx],
            spectra_per_task[task_idx],
            pair_matches,
        )
        revised_labels.append(labels)
        revised_spectra.append(spectra)

    cmaps = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [0.5, 1.0, 1.0],
        ],
        dtype=float,
    )

    for folder_name, labels in zip(folder_names, revised_labels):
        rgb = label2rgb(labels, colors=cmaps[1:], bg_label=0)
        save_tiff(output_root / f"{folder_name}.tiff", (255 * rgb).astype(np.uint8))

    for folder_name, spectra in zip(folder_names, revised_spectra):
        fig, ax = plt.subplots(figsize=(6, 4))
        for cluster_idx in range(n_clusters):
            ax.plot(wavenumber, np.flipud(spectra[:, cluster_idx]), color=cmaps[cluster_idx])
        style_axes(ax)
        save_figure(fig, output_root / f"{folder_name}_spectra.tiff")
        plt.close(fig)
