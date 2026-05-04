from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np

from .spectra import baseline_corrected, normalization


def read_dir_name(folder: Path | str) -> list[str]:
    folder_path = Path(folder)
    return sorted(path.name for path in folder_path.iterdir() if path.is_dir())


def read_file_name(path: Path | str, is_nerve: bool) -> list[Path]:
    group_path = Path(path) / ("Nerve sub" if is_nerve else "Neuron sub")
    return sorted(group_path.glob("*.txt"))


def read_all_file_name(paths: list[Path], is_nerve: bool) -> list[Path]:
    file_names: list[Path] = []
    for path in paths:
        file_names.extend(read_file_name(path, is_nerve))
    return file_names


def read_file(dataset_folder: Path | str, is_control: bool, is_nerve: bool) -> list[Path]:
    group_folder = Path(dataset_folder) / ("control" if is_control else "mutant")
    paths = sorted(path for path in group_folder.iterdir() if path.is_dir())
    return read_all_file_name(paths, is_nerve)


def read_data(file_names: list[Path]) -> tuple[np.ndarray, np.ndarray]:
    if not file_names:
        raise FileNotFoundError("No spontaneous Raman files were found for the requested group.")

    first = np.genfromtxt(file_names[0], dtype=float)
    length = first.shape[0]
    dataset = np.zeros((length, len(file_names)), dtype=float)
    wavenumber = first[:, 0]
    dataset[:, 0] = first[:, 1]

    for idx, file_name in enumerate(file_names[1:], start=1):
        data = np.genfromtxt(file_name, dtype=float)
        if data.shape[0] != length:
            warnings.warn(f"Wavenumber length mismatch in {file_name}")
        dataset[: data.shape[0], idx] = data[:, 1]
    return dataset, wavenumber


def read_all_data(
    dataset_folder: Path | str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    control_nerve_file_name = read_file(dataset_folder, True, True)
    control_neuron_file_name = read_file(dataset_folder, True, False)
    mutant_nerve_file_name = read_file(dataset_folder, False, True)
    mutant_neuron_file_name = read_file(dataset_folder, False, False)

    control_nerve_dataset, wavenumber = read_data(control_nerve_file_name)
    control_neuron_dataset, _ = read_data(control_neuron_file_name)
    mutant_nerve_dataset, _ = read_data(mutant_nerve_file_name)
    mutant_neuron_dataset, _ = read_data(mutant_neuron_file_name)

    control_nerve_dataset = baseline_corrected(control_nerve_dataset)
    control_neuron_dataset = baseline_corrected(control_neuron_dataset)
    mutant_nerve_dataset = baseline_corrected(mutant_nerve_dataset)
    mutant_neuron_dataset = baseline_corrected(mutant_neuron_dataset)

    return (
        wavenumber,
        control_nerve_dataset,
        control_neuron_dataset,
        mutant_nerve_dataset,
        mutant_neuron_dataset,
    )


def process(dataset: np.ndarray) -> np.ndarray:
    return normalization(baseline_corrected(dataset))
