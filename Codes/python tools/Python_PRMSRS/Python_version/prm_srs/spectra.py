from __future__ import annotations

import warnings

import numpy as np

from .baseline_correction import asysm


def eliminate_nan(signal: np.ndarray) -> np.ndarray:
    signal = np.asarray(signal, dtype=float)
    return signal[~np.isnan(signal[:, 0])]


def interpolation(signal: np.ndarray, wavenumber: np.ndarray) -> np.ndarray:
    signal = np.asarray(signal, dtype=float)
    wavenumber = np.asarray(wavenumber, dtype=float)
    x = signal[:, 0]
    values = signal[:, 1]
    interpolated = np.interp(wavenumber, x, values, left=np.nan, right=np.nan)
    if np.isnan(interpolated).any():
        finite = np.isfinite(interpolated)
        if finite.any():
            fill_value = np.nanmin(interpolated[finite])
            interpolated = np.where(finite, interpolated, fill_value)
        else:
            interpolated = np.zeros_like(wavenumber, dtype=float)
    return interpolated


def signal_normalization(signal: np.ndarray, wavenumber_samples: np.ndarray) -> np.ndarray:
    temp = interpolation(signal, wavenumber_samples)
    temp = _minmax_scale(temp)
    norm = np.linalg.norm(temp)
    if norm == 0:
        return temp
    return temp / norm


def normalization(dataset: np.ndarray) -> np.ndarray:
    dataset = np.asarray(dataset, dtype=float)
    normalized_dataset = _minmax_scale(dataset, axis=0)
    column_sums = normalized_dataset.sum(axis=0, keepdims=True)
    column_sums = np.where(column_sums == 0, 1.0, column_sums)
    return normalized_dataset / column_sums * dataset.shape[0]


def image_normalization(images: np.ndarray) -> np.ndarray:
    images = np.asarray(images, dtype=float)
    minimum = images.min(axis=0, keepdims=True)
    maximum = images.max(axis=0, keepdims=True)
    denominator = maximum - minimum + 0.01
    return (images - minimum) / denominator


def baseline_corrected(dataset: np.ndarray) -> np.ndarray:
    dataset = np.asarray(dataset, dtype=float)
    corrected_dataset = np.zeros_like(dataset)
    for idx in range(dataset.shape[1]):
        corrected_dataset[:, idx] = dataset[:, idx] - asysm(dataset[:, idx], 1e7, 0.001, 2)
    return corrected_dataset


def rawdataprocess(
    raw_wavenumber: np.ndarray,
    raw_dataset: np.ndarray,
    idx: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    raw_wavenumber = np.asarray(raw_wavenumber, dtype=float)
    raw_dataset = np.asarray(raw_dataset, dtype=float)
    idx = np.asarray(idx, dtype=bool)
    wavenumber = raw_wavenumber[idx]
    part_dataset = raw_dataset[idx, :]
    normalized_dataset = _minmax_scale(part_dataset, axis=0)
    norms = np.linalg.norm(normalized_dataset, axis=0, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    dataset = normalized_dataset / norms
    return wavenumber, dataset


def process_all_rawdata(
    raw_wavenumber: np.ndarray,
    raw_control_nerve_dataset: np.ndarray,
    raw_control_neuron_dataset: np.ndarray,
    raw_mutant_nerve_dataset: np.ndarray,
    raw_mutant_neuron_dataset: np.ndarray,
    idx: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    wavenumber, control_nerve_dataset = rawdataprocess(raw_wavenumber, raw_control_nerve_dataset, idx)
    _, control_neuron_dataset = rawdataprocess(raw_wavenumber, raw_control_neuron_dataset, idx)
    _, mutant_nerve_dataset = rawdataprocess(raw_wavenumber, raw_mutant_nerve_dataset, idx)
    _, mutant_neuron_dataset = rawdataprocess(raw_wavenumber, raw_mutant_neuron_dataset, idx)
    return (
        wavenumber,
        control_nerve_dataset,
        control_neuron_dataset,
        mutant_nerve_dataset,
        mutant_neuron_dataset,
    )


def retrieve_image(images: np.ndarray) -> np.ndarray:
    frame = np.squeeze(np.asarray(images, dtype=float))
    return _minmax_scale(frame)


def window_estimation(wavenumber_samples: np.ndarray, potential_shift: float) -> int:
    wavenumber_samples = np.asarray(wavenumber_samples, dtype=float)
    gap = abs(wavenumber_samples[1] - wavenumber_samples[0])
    return int(np.ceil(potential_shift / gap))


def penalty_on_shift(shift_matrix: np.ndarray, window_size: int) -> np.ndarray:
    shift_matrix = np.asarray(shift_matrix, dtype=float)
    penalty_coeff = -1.0 / max(window_size**2, 1)
    centered_shift_matrix = shift_matrix - window_size
    return penalty_coeff * centered_shift_matrix**2


def cutoff_matrix(reference_dataset: np.ndarray) -> np.ndarray:
    subtype_size, stack_size, scan_size = reference_dataset.shape
    centered_shift = scan_size // 2
    signal = reference_dataset[:, :, centered_shift]
    confusion_matrix = np.zeros((subtype_size, subtype_size), dtype=float)
    for i in range(subtype_size):
        for j in range(subtype_size):
            confusion_matrix[i, j] = np.max(signal[i, :] @ reference_dataset[j, :, :])
    return confusion_matrix


def safe_column_mean(dataset: np.ndarray) -> np.ndarray:
    dataset = np.asarray(dataset, dtype=float)
    if dataset.size == 0:
        warnings.warn("Received an empty dataset for averaging.")
        return np.array([], dtype=float)
    return dataset.mean(axis=1)


def _minmax_scale(data: np.ndarray, axis: int | None = None) -> np.ndarray:
    data = np.asarray(data, dtype=float)
    minimum = np.nanmin(data, axis=axis, keepdims=True)
    maximum = np.nanmax(data, axis=axis, keepdims=True)
    denominator = np.where((maximum - minimum) == 0, 1.0, maximum - minimum)
    scaled = (data - minimum) / denominator
    return np.nan_to_num(scaled, nan=0.0, posinf=0.0, neginf=0.0)
