from __future__ import annotations

import csv
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
    raman_shift_start: float | None = None,
    raman_shift_end: float | None = None,
    image_count: int | None = None,
) -> dict[str, dict[str, np.ndarray]]:
    root = Path(root_folder)
    folder_names = folders_generation(root)
    output_root = ensure_directory(
        output_folder or (root.parent / f"{root.name}_lipid_subtype_output")
    )

    if wavenumber_samples is None:
        wavenumber_samples = build_wavenumber_samples(
            raman_shift_start=raman_shift_start,
            raman_shift_end=raman_shift_end,
            image_count=image_count,
        )
    window_size = window_estimation(wavenumber_samples, potential_shift)
    subtype_name, reference_spectra = reference_signal2(wavenumber_samples, window_size)

    results: dict[str, dict[str, np.ndarray]] = {}
    for folder_name in folder_names:
        images = read_oir_folder_image(folder_name)
        _validate_stack_size(images, wavenumber_samples, folder_name)
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
    output = output_folder or (root.parent / f"{root.name}_lipid subtype")
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
    output_root = ensure_directory(output_folder or (root.parent / f"{root.name}_out"))

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

    output_root = ensure_directory(output_folder or (root.parent / f"{root.name}_out"))
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


def score_spectrum_subtypes(
    spectrum: np.ndarray,
    reference_dir: Path | str | None = None,
) -> list[dict[str, float | int | str]]:
    prepared_spectrum = _prepare_spectrum(spectrum)
    wavenumber_samples = prepared_spectrum[:, 0]
    normalized_intensity = _normalize_spectrum_values(prepared_spectrum[:, 1])
    subtype_names, reference_dataset = reference_signal3(
        wavenumber_samples,
        reference_dir=reference_dir,
    )

    gap = float(np.median(np.diff(wavenumber_samples)))
    scores: list[dict[str, float | int | str]] = []
    for subtype_name, reference_spectrum in zip(subtype_names, reference_dataset):
        # Mirror the original one-pixel scoring in srs_lipid_subtype.m.
        convolution_scores = scipy_signal.convolve(normalized_intensity, reference_spectrum, mode="full")
        peak_index = int(np.argmax(convolution_scores))
        lag_index = peak_index - (reference_spectrum.size - 1)
        relative_shift = float(lag_index * gap)
        scores.append(
            {
                "subtype_name": subtype_name,
                "score": float(convolution_scores[peak_index]),
                "peak_index": peak_index,
                "lag_index": lag_index,
                "relative_shift_cm_1": relative_shift,
            }
        )

    scores.sort(key=lambda item: float(item["score"]), reverse=True)
    return scores


def score_spectrum_files(
    input_path: Path | str,
    output_csv: Path | str | None = None,
    top_n: int | None = None,
    reference_dir: Path | str | None = None,
) -> Path:
    root = Path(input_path)
    if top_n is not None and top_n <= 0:
        raise ValueError(f"`top_n` must be positive when provided, got {top_n}.")

    output_path = Path(output_csv) if output_csv is not None else _default_spectrum_output_csv(root)
    spectrum_files = _collect_spectrum_files(root)
    output_path_resolved = output_path.resolve()
    spectrum_files = [path for path in spectrum_files if path.resolve() != output_path_resolved]
    if not spectrum_files:
        raise FileNotFoundError("No input spectra files remain after excluding the output CSV path.")
    rows: list[dict[str, float | int | str]] = []

    for spectrum_file in spectrum_files:
        spectrum = _read_spectrum_file(spectrum_file)
        ranked_scores = score_spectrum_subtypes(
            spectrum,
            reference_dir=reference_dir,
        )
        if top_n is not None:
            ranked_scores = ranked_scores[:top_n]

        for rank, result in enumerate(ranked_scores, start=1):
            rows.append(
                {
                    "file_name": spectrum_file.name,
                    "file_path": str(spectrum_file.resolve()),
                    "rank": rank,
                    "lipid_subtype": result["subtype_name"],
                    "score": result["score"],
                    "peak_index": result["peak_index"],
                    "lag_index": result["lag_index"],
                    "relative_shift_cm_1": result["relative_shift_cm_1"],
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "file_name",
        "file_path",
        "rank",
        "lipid_subtype",
        "score",
        "peak_index",
        "lag_index",
        "relative_shift_cm_1",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


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


def build_wavenumber_samples(
    raman_shift_start: float | None,
    raman_shift_end: float | None,
    image_count: int | None,
) -> np.ndarray:
    if raman_shift_start is None or raman_shift_end is None or image_count is None:
        raise ValueError(
            "srs5_image_generation requires either `wavenumber_samples` or all of "
            "`raman_shift_start`, `raman_shift_end`, and `image_count`."
        )
    if image_count <= 0:
        raise ValueError(f"`image_count` must be positive, got {image_count}.")
    return np.linspace(float(raman_shift_start), float(raman_shift_end), int(image_count))


def _validate_stack_size(images: np.ndarray, wavenumber_samples: np.ndarray, folder_name: Path) -> None:
    stack_size = int(images.shape[0])
    expected_size = int(len(wavenumber_samples))
    if stack_size != expected_size:
        raise ValueError(
            f"Image-count mismatch for {folder_name}: loaded {stack_size} images, "
            f"but the Raman-shift inputs describe {expected_size} positions."
        )


def _collect_spectrum_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() not in {".csv", ".txt"}:
            raise ValueError(f"Unsupported spectrum file type: {path.suffix}")
        return [path]
    if not path.is_dir():
        raise FileNotFoundError(f"Input path does not exist: {path}")

    files = sorted(
        candidate
        for candidate in path.iterdir()
        if candidate.is_file() and candidate.suffix.lower() in {".csv", ".txt"}
    )
    if not files:
        raise FileNotFoundError(f"No .csv or .txt spectra files found in {path}")
    return files


def _default_spectrum_output_csv(path: Path) -> Path:
    if path.is_dir():
        return path / "lipid_subtype_possibilities.csv"
    return path.with_name(f"{path.stem}_lipid_subtype_possibilities.csv")


def _read_spectrum_file(path: Path) -> np.ndarray:
    import pandas as pd

    read_attempts = [
        {"sep": None, "engine": "python", "header": None, "comment": "#"},
        {"sep": r"\s+", "engine": "python", "header": None, "comment": "#"},
        {"sep": ",", "engine": "python", "header": None, "comment": "#"},
        {"sep": "\t", "engine": "python", "header": None, "comment": "#"},
    ]
    errors: list[str] = []
    for kwargs in read_attempts:
        try:
            dataframe = pd.read_csv(path, **kwargs)
            spectrum = _extract_numeric_spectrum(dataframe)
            return spectrum
        except Exception as exc:
            errors.append(f"{kwargs}: {exc}")
    joined_errors = "\n".join(errors)
    raise ValueError(f"Unable to parse spectrum file {path}\n{joined_errors}")


def _extract_numeric_spectrum(dataframe) -> np.ndarray:
    import pandas as pd

    numeric_columns = []
    for column in dataframe.columns:
        numeric = pd.to_numeric(dataframe[column], errors="coerce")
        if int(numeric.notna().sum()) >= 2:
            numeric_columns.append(numeric)
        if len(numeric_columns) == 2:
            break

    if len(numeric_columns) < 2:
        raise ValueError("Could not find two numeric columns for Raman shift and intensity.")

    valid_rows = numeric_columns[0].notna() & numeric_columns[1].notna()
    if int(valid_rows.sum()) < 2:
        raise ValueError("Spectrum file must contain at least two valid Raman-shift/intensity pairs.")

    return np.column_stack(
        [
            numeric_columns[0][valid_rows].to_numpy(dtype=float),
            numeric_columns[1][valid_rows].to_numpy(dtype=float),
        ]
    )


def _prepare_spectrum(spectrum: np.ndarray) -> np.ndarray:
    spectrum = np.asarray(spectrum, dtype=float)
    if spectrum.ndim != 2 or spectrum.shape[1] < 2:
        raise ValueError(
            "Spectrum input must be a 2-column matrix with Raman shift in the first column "
            "and intensity in the second column."
        )

    prepared = spectrum[:, :2]
    valid_rows = np.isfinite(prepared[:, 0]) & np.isfinite(prepared[:, 1])
    prepared = prepared[valid_rows]
    if prepared.shape[0] < 2:
        raise ValueError("Spectrum input must contain at least two valid data points.")

    prepared = prepared[np.argsort(prepared[:, 0])]
    unique_shift, inverse = np.unique(prepared[:, 0], return_inverse=True)
    if unique_shift.size < 2:
        raise ValueError("Spectrum input must contain at least two distinct Raman shifts.")
    if unique_shift.size != prepared.shape[0]:
        averaged_intensity = np.zeros(unique_shift.shape, dtype=float)
        counts = np.zeros(unique_shift.shape, dtype=float)
        np.add.at(averaged_intensity, inverse, prepared[:, 1])
        np.add.at(counts, inverse, 1.0)
        prepared = np.column_stack([unique_shift, averaged_intensity / counts])

    return prepared


def _normalize_spectrum_values(intensity: np.ndarray) -> np.ndarray:
    intensity = np.asarray(intensity, dtype=float)
    minimum = float(np.min(intensity))
    maximum = float(np.max(intensity))
    normalized = (intensity - minimum) / (maximum - minimum + 0.01)
    norm = float(np.linalg.norm(normalized))
    if norm == 0:
        return normalized
    return normalized / norm
