from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal as scipy_signal

from .config import ensure_directory
from .image_io import folders_generation, read_oib_folder_image, read_oir_folder_image, save_tiff
from .reference import reference_signal2, reference_signal3
from .spectra import (
    image_normalization,
    penalty_on_shift,
    process_all_rawdata,
    rawdataprocess,
    retrieve_image,
    window_estimation,
)
from .spontaneous import read_all_data


def srs5_image_generation(
    root_folder: Path | str,
    output_folder: Path | str | None = None,
    wavenumber_samples: np.ndarray | None = None,
    potential_shift: float = 100.0,
) -> dict[str, dict[str, np.ndarray]]:
    root = Path(root_folder)
    folder_names = folders_generation(root)
    output_root = ensure_directory(output_folder or Path(f"{root}_lipid_subtype_output"))

    if wavenumber_samples is None:
        wavenumber_samples = np.linspace(2700, 3120, 62)
    window_size = window_estimation(wavenumber_samples, potential_shift)
    subtype_name, reference_spectra = reference_signal2(wavenumber_samples, window_size)

    results: dict[str, dict[str, np.ndarray]] = {}
    for folder_name in folder_names:
        images = read_oir_folder_image(folder_name)
        folder_output = ensure_directory(output_root / folder_name.name)
        score_images_by_name, shift_images_by_name = match_shifted_references(
            images,
            subtype_name,
            reference_spectra,
            window_size,
        )
        for name, image in score_images_by_name.items():
            save_tiff(folder_output / f"{name}_convolution_image.tiff", image)
        results[folder_name.name] = {
            "scores": score_images_by_name,
            "shifts": shift_images_by_name,
        }
    return results


def srs5_image_generation_copy(
    root_folder: Path | str,
    output_folder: Path | str | None = None,
    wavenumber_samples: np.ndarray | None = None,
    potential_shift: float = 100.0,
) -> dict[str, dict[str, np.ndarray]]:
    root = Path(root_folder)
    output = output_folder or Path(f"{root}_lipid subtype")
    samples = wavenumber_samples if wavenumber_samples is not None else np.linspace(2700, 3120, 51)
    return srs5_image_generation(root, output_folder=output, wavenumber_samples=samples, potential_shift=potential_shift)


def srs_lipid_subtype(
    root_folder: Path | str,
    output_folder: Path | str | None = None,
    wavenumber_samples: np.ndarray | None = None,
    protein_index: int = 36,
    lipid_index: int = 43,
) -> None:
    root = Path(root_folder)
    folder_names = folders_generation(root)
    output_root = ensure_directory(output_folder or Path(f"{root}_out"))

    samples = wavenumber_samples if wavenumber_samples is not None else np.linspace(2700, 3150, 76)
    subtype_name, reference_dataset = reference_signal3(samples)

    for folder_name in folder_names:
        folder_output = ensure_directory(output_root / folder_name.name)
        raw_image = read_oir_folder_image(folder_name)
        images = image_normalization(raw_image)
        images_2d = images.reshape(images.shape[0], -1)

        protein_image = retrieve_image(images[protein_index, :, :])
        lipid_image = retrieve_image(images[lipid_index, :, :])
        save_tiff(folder_output / "protein_channel.tiff", (65535 * protein_image).astype(np.uint16))
        save_tiff(folder_output / "lipid_channel.tiff", (65535 * lipid_image).astype(np.uint16))

        norms = np.linalg.norm(images_2d, axis=0, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        images_2d_norm = images_2d / norms

        for name, reference in zip(subtype_name, reference_dataset):
            correlations = np.array(
                [
                    np.max(scipy_signal.convolve(images_2d_norm[:, pixel_idx], reference, mode="full"))
                    for pixel_idx in range(images_2d_norm.shape[1])
                ],
                dtype=float,
            )
            corr_image = correlations.reshape(images.shape[1], images.shape[2])
            save_tiff(folder_output / f"{name}_convolution_image.tiff", corr_image)


def srs5_hippocampus(
    root_folder: Path | str,
    output_folder: Path | str | None = None,
    subtype_index: int = 4,
) -> dict[str, np.ndarray]:
    root = Path(root_folder)
    folder_names = folders_generation(root)
    if not folder_names:
        raise FileNotFoundError(f"No folders found under {root}")

    output_root = ensure_directory(output_folder or Path(f"{root}_out"))
    wavenumber_samples = np.linspace(2796, 3085, 82)
    window_size = window_estimation(wavenumber_samples, 100)
    subtype_name, reference_spectra = reference_signal2(wavenumber_samples, window_size)

    folder_name = folder_names[0]
    folder_output = ensure_directory(output_root / folder_name.name)
    raw_image = read_oib_folder_image(folder_name)
    score_images_by_name, shift_images_by_name = match_shifted_references(
        raw_image,
        subtype_name,
        reference_spectra,
        window_size,
        subtype_indices=[subtype_index - 1],
    )

    chosen_name = subtype_name[subtype_index - 1]
    score_images = score_images_by_name[chosen_name]
    save_tiff(folder_output / f"{chosen_name}_convolution_image.tiff", score_images)
    return {
        "raw_image": raw_image,
        "score_images": score_images,
        "shift_images": shift_images_by_name[chosen_name],
        "subtype_name": np.array(subtype_name, dtype=object),
        "reference_spectra": reference_spectra,
    }


def match_shifted_references(
    images: np.ndarray,
    subtype_names: list[str],
    reference_spectra: np.ndarray,
    window_size: int,
    subtype_indices: list[int] | None = None,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    images_2d = np.asarray(images, dtype=float).reshape(images.shape[0], -1)
    images_2d = _column_minmax_scale(images_2d)
    norms = np.linalg.norm(images_2d, axis=0, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    images_2d_norm = images_2d / norms
    images_2d_norms = np.flipud(images_2d_norm).T

    indices = subtype_indices if subtype_indices is not None else list(range(len(subtype_names)))
    score_images_by_name: dict[str, np.ndarray] = {}
    shift_images_by_name: dict[str, np.ndarray] = {}
    for idx in indices:
        reference_subtype = reference_spectra[idx, :, :]
        score_matching_value = images_2d_norms @ reference_subtype
        shift_matrix = np.argmax(score_matching_value, axis=1)
        score_matching_matrix = score_matching_value[np.arange(score_matching_value.shape[0]), shift_matrix]
        score_shift_penalty_matrix = penalty_on_shift(shift_matrix, window_size)
        score_matrix = np.maximum(score_matching_matrix + score_shift_penalty_matrix, 0)

        score_images_by_name[subtype_names[idx]] = score_matrix.reshape(images.shape[1], images.shape[2])
        shift_images_by_name[subtype_names[idx]] = shift_matrix.reshape(images.shape[1], images.shape[2])
    return score_images_by_name, shift_images_by_name


def load_spontaneous_window(
    dataset_folder: Path | str,
    lb: float,
    ub: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    raw_wavenumber, raw_control_nerve_dataset, raw_control_neuron_dataset, raw_mutant_nerve_dataset, raw_mutant_neuron_dataset = read_all_data(
        dataset_folder
    )
    idx = (raw_wavenumber > lb) & (raw_wavenumber < ub)
    return process_all_rawdata(
        raw_wavenumber,
        raw_control_nerve_dataset,
        raw_control_neuron_dataset,
        raw_mutant_nerve_dataset,
        raw_mutant_neuron_dataset,
        idx,
    )


def simple_rawdataprocess(
    raw_wavenumber: np.ndarray,
    raw_dataset: np.ndarray,
    lb: float,
    ub: float,
) -> tuple[np.ndarray, np.ndarray]:
    idx = (raw_wavenumber > lb) & (raw_wavenumber < ub)
    return rawdataprocess(raw_wavenumber, raw_dataset, idx)


def _column_minmax_scale(data: np.ndarray) -> np.ndarray:
    minimum = data.min(axis=0, keepdims=True)
    maximum = data.max(axis=0, keepdims=True)
    denominator = np.where((maximum - minimum) == 0, 1.0, maximum - minimum)
    return (data - minimum) / denominator
