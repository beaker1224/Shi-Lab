from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Iterable, Optional, Tuple, Union


def nparray_to_dataframe(
    spectra_arrays: Iterable[np.ndarray],
    names: Optional[Iterable[str]] = None,
) -> pd.DataFrame:
    """Combine many (N, 2) arrays into a single DataFrame with paired columns.

    Each array is expected to have:
    - column 0: Raman shift
    - column 1: intensity

    If the first row contains non-numeric values (e.g., a header row), it will be skipped.

    The resulting DataFrame will contain two columns per input array:
        (name, 'raman') and (name, 'intensity')

    This keeps each spectrum's original x-axis intact without forcing a shared index.

    Parameters
    ----------
    spectra_arrays:
        An iterable of 2D numpy arrays, each with at least 2 columns (Raman shift and intensity).
    names:
        Optional iterable of names for each spectrum. 
        If not provided, default names will be assigned as "spectrum_1", "spectrum_2", etc.
    
    Returns
    -------
    pd.DataFrame:
        A DataFrame with MultiIndex columns, 
        where each spectrum has its own pair of columns for Raman shift and intensity.

    """

    def _sanitize_array(arr: np.ndarray) -> np.ndarray:
        arr = np.asarray(arr)
        if arr.ndim != 2 or arr.shape[1] < 2:
            raise ValueError(
                "Each spectra array must be 2D with at least 2 columns (raman shift, intensity)."
            )

        # If the first row contains non-numeric values, drop it.
        first_row = arr[0]
        try:
            first_row.astype(float)
        except Exception:
            arr = arr[1:]

        # Convert to float and return only first two columns
        return arr[:, :2].astype(float)

    frames = []
    names_list = list(names) if names is not None else []

    for idx, arr in enumerate(spectra_arrays):
        arr = _sanitize_array(arr)
        raman = arr[:, 0]
        intensity = arr[:, 1]
        name = names_list[idx] if idx < len(names_list) else f"spectrum_{idx + 1}"

        df = pd.DataFrame({(name, "raman"): raman, (name, "intensity"): intensity})
        frames.append(df)

    if not frames:
        return pd.DataFrame()

    # Join side-by-side without aligning on index, preserving each spectrum's row structure
    combined = pd.concat(frames, axis=1)
    combined.columns = pd.MultiIndex.from_tuples(combined.columns)
    return combined


def single_plot_single_spectra(
    raman_shift: np.ndarray,
    intensity: np.ndarray,
    title: str,
    range_start: float,
    range_end: float,
    color: str = 'blue',
    direct: Optional[Union[str, Path]] = None,
) -> None:
    """
    Plot a single spectrum.

    Parameters
    ----------
    raman_shift:
        1D array of Raman shift values (x-axis).
    intensity:
        1D array of intensity values (y-axis).
    title:
        The title of the plot.
    range_start:
        The starting value of the x-axis (Raman shift).
    range_end:
        The ending value of the x-axis (Raman shift).
    color:
        The color of the plot line. Default is 'blue'.
    direct:
        Optional path to save the plot. If None, the plot will not be saved.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(raman_shift, intensity, color=color, label='Raman Intensity')
    plt.title(title)
    plt.xlabel('Raman Shift (cm$^{-1}$)')
    plt.ylabel('Intensity (a.u.)')
    plt.xlim(range_start, range_end)
    plt.grid()
    plt.legend()

    if direct is not None:
        out_path = Path(direct)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, bbox_inches='tight')
        print(f"Plot saved to {out_path}")

    plt.show()


def single_plot_multiple_spectra(
    spectra: pd.DataFrame,
    title: str,
    range_start: float,
    range_end: float,
    direct: Optional[Union[str, Path]] = None,
    transparency: float = 0.5,
    color: Optional[str] = 'blue',
    ax: Optional[plt.Axes] = None, # <-- Changed to accept an axis IN # type: ignore
) -> Optional[plt.Axes]:# type: ignore
    """Plot multiple spectra overlaid."""

    # If no ax is provided, we create a new standalone figure
    is_standalone = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 6))
        is_standalone = True

    # Plotting logic happens on 'ax' regardless of where it came from
    spectrum_names = spectra.columns.get_level_values(0).unique()

    for name in spectrum_names:
        x = spectra[(name, 'raman')]
        y = spectra[(name, 'intensity')]

        valid_mask = ~x.isna() & ~y.isna()
        x_valid = x[valid_mask]
        y_valid = y[valid_mask]

        # Added color=color here!
        ax.plot(x_valid, y_valid, color=color, alpha=transparency, label=name)

    ax.set_title(title)
    ax.set_xlabel('Raman Shift (cm$^{-1}$)')
    ax.set_ylabel('Intensity (a.u.)')
    ax.set_xlim(range_start, range_end)
    ax.grid()
    ax.legend()

    # If it's part of a bigger subplot manager, hand the axis back and exit
    if not is_standalone:
        return ax

    # If it IS standalone, handle saving and showing
    if direct is not None:
        out_path = Path(direct)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, bbox_inches='tight')
        print(f"Plot saved to {out_path}")

    plt.show()


def multiple_plot_single_graph(
    dataframes: list[pd.DataFrame],
    titles: list[str],
    range_start: float,
    range_end: float,
    colors: Optional[list[str]] = None,
    size: Optional[Tuple[int, int]] = None,
    direct: Optional[Union[str, Path]] = None,
) -> None:
    """Creates a single figure with subplots arranged in a specified grid."""
    
    num_plots = len(dataframes)
    
    if colors is None:
        colors = ['blue'] * num_plots

    # Determine the grid layout
    if size is not None:
        nrows, ncols = size
        if nrows * ncols < num_plots:
            raise ValueError(f"A {nrows}x{ncols} grid only holds {nrows * ncols} plots, but you provided {num_plots} DataFrames.")
    else:
        nrows, ncols = num_plots, 1

    # Create the figure and axes
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(8 * ncols, 4 * nrows))
    
    # Ensure axes_flat is always a flat list, even if there's only 1 plot
    if num_plots == 1 and size is None:
        axes_flat = [axes]
    else:
        axes_flat = fig.axes 

    # Loop through and pass the specific 'ax' into the plotting function
    for i, (df, title, color) in enumerate(zip(dataframes, titles, colors)):
        target_ax = axes_flat[i]
        
        single_plot_multiple_spectra(
            spectra=df,
            title=title,
            range_start=range_start,
            range_end=range_end,
            color=color,
            ax=target_ax,  # <-- Handing the empty box to the worker
        )
        
    # Hide any unused boxes
    for empty_ax_index in range(num_plots, len(axes_flat)):
        axes_flat[empty_ax_index].axis('off')

    plt.tight_layout()

    if direct is not None:
        out_path = Path(direct)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(out_path, bbox_inches='tight')
        print(f"Plot saved to {out_path}")
        
    plt.show()