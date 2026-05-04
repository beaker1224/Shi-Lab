from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np


def style_axes(ax: plt.Axes, fontsize: int = 12) -> None:
    for spine in ax.spines.values():
        spine.set_linewidth(2)
    ax.tick_params(width=2, labelsize=fontsize)


def save_figure(fig: plt.Figure, path: Path | str, dpi: int = 300) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")


def boxplot_with_scatter(
    values_a: np.ndarray,
    values_b: np.ndarray,
    labels: Sequence[str],
    xlabel: str,
    ylabel: str,
    output_path: Path | str,
    title: str | None = None,
    seed: int = 0,
) -> None:
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.boxplot([values_a, values_b], labels=list(labels), showfliers=False)
    scatter_x = np.concatenate(
        [
            np.ones(values_a.size) + (rng.random(values_a.size) - 0.5) / 10,
            2 * np.ones(values_b.size) + (rng.random(values_b.size) - 0.5) / 10,
        ]
    )
    scatter_y = np.concatenate([values_a, values_b])
    ax.scatter(scatter_x, scatter_y, c="red", s=15)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    style_axes(ax)
    save_figure(fig, output_path)
    plt.close(fig)


def heatmap(
    matrix: np.ndarray,
    x_labels: Sequence[str],
    y_labels: Sequence[str],
    output_path: Path | str,
    figsize: tuple[float, float] = (10, 10),
    xlabel: str | None = None,
    ylabel: str | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=figsize)
    image = ax.imshow(matrix, cmap="viridis", aspect="auto")
    ax.set_xticks(np.arange(len(x_labels)))
    ax.set_yticks(np.arange(len(y_labels)))
    ax.set_xticklabels(x_labels, rotation=90)
    ax.set_yticklabels(y_labels)
    if xlabel:
        ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    style_axes(ax)
    fig.colorbar(image, ax=ax)
    save_figure(fig, output_path)
    plt.close(fig)
