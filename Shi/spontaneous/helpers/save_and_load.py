from __future__ import annotations

from pathlib import Path
from typing import Literal, Union, Optional, Tuple, Dict, List, Any

import numpy as np
import pandas as pd
import csv


def save_spectrm(fileType: Literal['txt', 'csv'], outpath: Path, wn: np.ndarray, intensity: np.ndarray, bg_curve: Optional[np.ndarray] = None, header: bool = False) -> None:
    '''
    This function saves the wavenumber and intensity data to a file in either txt or csv format.
    Parameters:
    fileType (Literal['txt', 'csv']): The type of file to save, either 'txt' or 'csv'.
    outpath (Path): The path where the file will be saved.
    wn (np.ndarray): The wavenumber axis data.
    intensity (np.ndarray): The intensity data corresponding to the wavenumber axis.
    bg_curve (Optional[np.ndarray]): The fitted background curve data corresponding to the wavenumber axis. default is None.
    header (bool): Whether the output has a header row. default is False.
    Returns:
    None
    '''
    if fileType == 'txt':
        with open(outpath, 'w') as f:
            writer = csv.writer(f, delimiter='\t')
            if header:
                if bg_curve is not None:
                    writer.writerow(['Wavenumber', 'Intensity', 'Background'])
                else:
                    writer.writerow(['Wavenumber', 'Intensity'])
            if bg_curve is not None:
                for w, i, b in zip(wn, intensity, bg_curve):
                    writer.writerow([w, i, b])
            else:
                for w, i in zip(wn, intensity):
                    writer.writerow([w, i])
    elif fileType == 'csv':
        if bg_curve is not None:
            df = pd.DataFrame({'Wavenumber': wn, 'Intensity': intensity, 'Background': bg_curve})
        else:
            df = pd.DataFrame({'Wavenumber': wn, 'Intensity': intensity})
        df.to_csv(outpath, index=False)

def read_spectrum(path: Path, header: bool = False) -> Tuple[np.ndarray, ...]:
    """
    Read spectrum data from txt or csv file.
    
    Supports 2 or 3 columns:
    - 2 columns: wavenumber, intensity
    - 3 columns: wavenumber, intensity, background
    
    Parameters:
    path (Path): Path to the file.
    header (bool): Whether the file has a header row. Default is False.
    
    Returns:
    Tuple[np.ndarray, ...]: Tuple of numpy arrays (wavenumber, intensity) or (wavenumber, intensity, background).
    """
    try:
        df = pd.read_csv(path, delim_whitespace=True, header=0 if header else None, comment="#")
    except Exception:
        df = pd.read_csv(path, sep=None, engine="python", header=0 if header else None, comment="#")

    df = df.dropna(how="all").dropna(axis=1, how="all")
    num_cols = df.shape[1]
    if num_cols not in [2, 3]:
        raise ValueError(f"Expected 2 or 3 columns, got {num_cols} in {path.name}")

    # Convert columns to numeric
    arrays = []
    for i in range(num_cols):
        arr = pd.to_numeric(df.iloc[:, i], errors="coerce").to_numpy()
        arrays.append(arr)
    return tuple(arrays)

def save_ratios(path: Path, data: List[Dict[str, Any]], header: bool = True) -> None:
    '''
    This function saves a list of dictionaries containing ratio data to a csv file.
    Parameters:
    path (Path): The path where the csv file will be saved.
    data (List[Dict[str, Any]]): A list of dictionaries, where each dictionary contains the ratio data for a sample.
    header (bool): Whether to include a header row in the csv file. Default is True.
    Returns:
    None
    '''
    df = pd.DataFrame(data)
    df.to_csv(path, index=False)

def load_ratios(path: Path) -> pd.DataFrame:
    '''
    This function loads ratio data from a csv file into a pandas DataFrame.
    Parameters:
    path (Path): The path to the csv file containing the ratio data.
    Returns:
    pd.DataFrame: A DataFrame containing the ratio data from the csv file.
    '''
    return pd.read_csv(path)