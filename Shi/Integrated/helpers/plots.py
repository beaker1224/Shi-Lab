import matplotlib.pyplot as plt
import os, sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import List, Union, Tuple, Sequence, Dict, Any

def condition_with_second_col(csv_path: str, condition: str,
                              *, col_index: int = 1, sep: Union[str, None] = None) -> list:
    """
    Returns [condition, <list of numeric values from the CSV's second column>].

    Parameters
    ----------
    csv_path : str
        Path to the CSV/TSV file.
    condition : str
        Condition name to place as the first element.
    col_index : int, default=1
        Which column to use (0-based). 1 = second column.
    sep : str | None, default=None
        Delimiter. Use '\\t' for TSV; None lets pandas try to infer.

    Returns
    -------
    list
        [condition, values_list]
    """
    p = Path(csv_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    df = pd.read_csv(p, sep=sep, engine='python')  # engine='python' helps infer delimiter
    if df.shape[1] <= col_index:
        raise ValueError(f"File has only {df.shape[1]} columns; cannot take index {col_index}.")

    y = pd.to_numeric(df.iloc[:, col_index], errors="coerce").dropna().tolist()
    return [condition, y]

def plot_multi_spectra(
    series: Sequence[Sequence[Any]],
    start: float,
    end: float,
    *,
    colors: Dict[str, str] | None = None,
    xlabel: str = r"Wavenumber (cm$^{-1}$)",
    ylabel: str = "Normalized Intensity (0–1)",
    title: str | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
    normalize: bool = True,           # NEW: per-series normalization on by default
):
    """
    Plot multiple spectra on one axes, optionally normalizing each to [0, 1].

    Parameters
    ----------
    series : iterable of [name, y_values] or [name, y_values, color]
        Each item: name (str), list/array of Y values, optional explicit color.
        All y lengths must match.
    start, end : float
        X-axis range; x is np.linspace(start, end, N).
    colors : dict(name -> color), optional
        Fallback color map if a series doesn't carry its own color.
    xlabel, ylabel, title : str
        Axis labels/title.
    save_path : path-like, optional
        If given, save the figure (PNG/PDF by extension).
    show : bool
        Whether to display the figure.
    normalize : bool
        If True, min–max normalize each series to [0, 1].

    Returns
    -------
    x : np.ndarray
    fig, ax : matplotlib Figure and Axes
    normed_ys : list[np.ndarray]
        The (possibly normalized) Y arrays in the same order as input.
    """
    if not series:
        raise ValueError("Provide at least one series.")

    def _minmax01(arr: np.ndarray) -> np.ndarray:
        arr = np.asarray(arr, dtype=float)
        a_min = np.nanmin(arr)
        a_max = np.nanmax(arr)
        denom = a_max - a_min
        if not np.isfinite(denom) or denom == 0:
            return np.zeros_like(arr)
        return (arr - a_min) / denom

    # unpack and validate
    names: List[str] = []
    ys: List[np.ndarray] = []
    local_colors: List[str | None] = []

    for item in series:
        if len(item) < 2:
            raise ValueError("Each series must be [name, y_values] (optionally [name, y_values, color]).")
        name, y_vals = item[0], item[1]
        col = item[2] if len(item) >= 3 else None
        names.append(str(name))
        ys.append(np.asarray(y_vals, dtype=float))
        local_colors.append(col)

    lengths = {len(y) for y in ys}
    if len(lengths) != 1:
        raise ValueError(f"All series must have the same length; got lengths {sorted(lengths)}.")
    n = lengths.pop()

    # x-axis shared for all series
    x = np.linspace(start, end, n)

    # normalize per series if requested
    normed_ys = [(_minmax01(y) if normalize else y) for y in ys]

    # plot
    fig, ax = plt.subplots()
    for name, y, c_local in zip(names, normed_ys, local_colors):
        c = c_local or (colors.get(name) if colors else None)
        ax.plot(x, y, label=name, color=c)

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.legend()
    ax.margins(x=0.02, y=0.05)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()

    if save_path is not None:
        save_path = Path(save_path)
        fig.savefig(save_path, dpi=300)

    if show:
        plt.show()

    return x, fig, ax, normed_ys

# example of use

# A = condition_with_second_col("D350.tsv",  "D350")
# B = condition_with_second_col("D1100.tsv", "D1100")
# C = condition_with_second_col("LiY350.tsv","LiY350")
# D = condition_with_second_col("LiY1100.tsv","LiY1100")

# plot_multi_spectra(
#     [A, B, C, D],
#     start=2700, end=3100,
#     colors={"D350":"red", "D1100":"#1f77b4", "LiY350":"goldenrod", "LiY1100":"green"},
#     title="CH-stretch spectra"
# )

A = condition_with_second_col(r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\BCR-ABL\high\2-Zplot-cytoplasm.csv",  "BCR-ABL") 
B = condition_with_second_col(r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\DMSO\high\1-Zplot-cytoplasm.csv", "DMSO")
C = condition_with_second_col(r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash\LYni\high\1-Zplot-cytoplasm.csv","LYni")

plot_multi_spectra(
    [A, B, C],
    start=2700, end=3100,
    colors={"BCR-ABL":"red", "DMSO":"#1f77b4", "LYni":"goldenrod"},
    title="With Methanol Wash, High, Cytoplasm",
    save_path=r"D:\study\Shi_Lab\Data\2025-05-25 Cancer Stiffness\with Methanol Wash high"
)