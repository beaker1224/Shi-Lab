from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import mannwhitneyu

from .config import DEFAULT_OUTPUT_DIR, MATLAB_ROOT, SUBTYPE_REFERENCE_DIR, ensure_directory
from .plotting import boxplot_with_scatter, heatmap, save_figure, style_axes
from .reference import cardiolipin_signal, reference_signal2, reference_signal3
from .spectra import cutoff_matrix, retrieve_image, safe_column_mean, signal_normalization, window_estimation
from .workflows import load_spontaneous_window, srs5_hippocampus


def demo_1_1_hippocampus_lipid_channels(
    root_folder: Path | str = MATLAB_ROOT / "hippocampus_dataset",
    output_path: Path | str | None = None,
) -> Path:
    result = srs5_hippocampus(root_folder)
    images = result["raw_image"]
    score_images = result["score_images"]
    max_score_loc = np.argmax(score_images)
    row_idx, col_idx = np.unravel_index(max_score_loc, score_images.shape)
    pixel_spectra = images[:, row_idx, col_idx]

    wavenumber_samples = np.arange(2596, 3286, 4, dtype=float)
    wavenumber_pixel = np.linspace(3085, 2796, images.shape[0])
    vis_pixel_spectra = signal_normalization(
        np.column_stack([wavenumber_pixel, pixel_spectra]),
        wavenumber_pixel,
    )
    vis_cardiolipin_spectra = cardiolipin_signal(wavenumber_samples)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(wavenumber_samples, vis_cardiolipin_spectra, linewidth=2, label="Cardiolipin Reference Spectra")
    ax.plot(wavenumber_pixel, vis_pixel_spectra, linewidth=2, label="Spectra on a Single Pixel")
    ax.set_xlim([2596, 3285])
    ax.set_xlabel("Wavenumber (cm^-1)")
    ax.set_ylabel("Intensity (au)")
    ax.legend()
    style_axes(ax)
    output = Path(output_path or (DEFAULT_OUTPUT_DIR / "demo_1_1_hippocampus_lipid_channels.png"))
    save_figure(fig, output)
    plt.close(fig)
    return output


def demo_1_2_shift_matching(output_dir: Path | str | None = None) -> list[Path]:
    root_output = ensure_directory(output_dir or DEFAULT_OUTPUT_DIR / "demo_1_2")
    result = srs5_hippocampus(MATLAB_ROOT / "hippocampus_dataset")
    raw_image = result["raw_image"]
    score_images = result["score_images"]

    wavenumber_samples = np.linspace(2796, 3085, 82)
    window_size = window_estimation(wavenumber_samples, 100)
    subtype_name, reference_spectra = reference_signal2(wavenumber_samples, window_size)
    cardiolipin_reference_spectra = reference_spectra[subtype_name.index("Cardiolipin"), :, :]

    row_idx, col_idx = np.unravel_index(np.argmax(score_images), score_images.shape)
    pixel_spectra = np.flipud(raw_image[:, row_idx, col_idx])
    pixel_spectra = pixel_spectra - pixel_spectra.min()
    pixel_spectra = pixel_spectra / max(pixel_spectra.max(), 1.0)
    pixel_spectra = pixel_spectra / max(np.linalg.norm(pixel_spectra), 1.0)

    gap = wavenumber_samples[1] - wavenumber_samples[0]
    relative_shift = gap * np.arange(-window_size, window_size + 1)
    matching_score = cardiolipin_reference_spectra.T @ pixel_spectra
    penalty_score = (1.0 / 10000.0) * relative_shift**2
    score = np.maximum(matching_score - penalty_score, 0)

    outputs: list[Path] = []
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(relative_shift, matching_score, linewidth=2, label="matching score")
    ax.plot(relative_shift, penalty_score, linewidth=2, label="penalty score")
    ax.plot(relative_shift, score, linewidth=2, label="score")
    ax.set_xlim([-100, 100])
    ax.set_ylim([0, 1])
    ax.set_xlabel("Relative Shift Compared to Experiment Measurement (cm^-1)")
    ax.set_ylabel("Scores")
    ax.legend()
    style_axes(ax)
    output = root_output / "demo_1_2_shift_matching.png"
    save_figure(fig, output)
    plt.close(fig)
    outputs.append(output)

    center_index = window_size + 1
    for matlab_idx, suffix in [(24, "left"), (28, "best"), (36, "right")]:
        python_idx = matlab_idx - 1
        shift_offset = center_index - matlab_idx
        shifted_reference = cardiolipin_reference_spectra[:, python_idx]
        fig, ax = plt.subplots(figsize=(2, 4))
        ax.plot(wavenumber_samples - shift_offset * gap, shifted_reference, linewidth=2)
        ax.plot(wavenumber_samples - shift_offset * gap, pixel_spectra, linewidth=2)
        ax.set_xticks([2800, 2900, 3000])
        style_axes(ax)
        output = root_output / f"demo_1_2_{suffix}_shift.png"
        save_figure(fig, output)
        plt.close(fig)
        outputs.append(output)
    return outputs


def demo_2_subtype_lipid_signal(output_path: Path | str | None = None) -> Path:
    wavenumber_samples = np.arange(400, 3151, 4, dtype=float)
    subtype_name, reference_dataset = reference_signal3(wavenumber_samples)

    cmaps = np.array(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 1.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 0.0],
            [0.61, 0.4, 0.12],
            [1.0, 0.5, 0.31],
            [0.7, 0.13, 0.13],
            [0.69, 0.19, 0.38],
            [1.0, 0.75, 0.8],
            [0.53, 0.15, 0.34],
            [0.98, 0.5, 0.45],
            [1.0, 0.27, 0.0],
            [1.0, 0.6, 0.07],
            [0.92, 0.56, 0.33],
            [1.0, 0.89, 0.52],
            [0.85, 0.65, 0.41],
            [1.0, 0.38, 0.0],
            [0.96, 0.87, 0.7],
            [0.04, 0.09, 0.27],
            [0.01, 0.66, 0.62],
            [0.5, 1.0, 0.83],
            [0.5, 0.16, 0.16],
            [0.5, 1.0, 1.0],
            [0.18, 0.3, 0.3],
            [0.41, 0.41, 0.41],
            [0.44, 0.5, 0.56],
            [0.83, 0.83, 0.83],
            [0.25, 0.41, 0.88],
            [0.52, 0.8, 0.98],
            [0.68, 0.93, 0.93],
            [0.25, 0.25, 0.7],
            [0.8, 0.4, 0.2],
            [0.2, 0.6, 0.2],
        ],
        dtype=float,
    )

    fig, ax = plt.subplots(figsize=(3, 3))
    offsets = np.arange(len(reference_dataset)) * 0.2
    for idx, reference in enumerate(reference_dataset):
        ax.plot(wavenumber_samples, reference + offsets[idx], linewidth=2, color=cmaps[idx % len(cmaps)])
    ax.set_xlabel("Wavenumber (cm^-1)")
    ax.set_ylabel("Intensity (au)")
    style_axes(ax)
    output = Path(output_path or (DEFAULT_OUTPUT_DIR / "demo_2_subtype_lipid_signal.png"))
    save_figure(fig, output)
    plt.close(fig)
    return output


def demo_3_signal_score_between_subtype(output_path: Path | str | None = None) -> Path:
    wavenumber_samples = np.linspace(2796, 3085, 82)
    window_size = window_estimation(wavenumber_samples, 100)
    subtype_name, reference_spectra = reference_signal2(wavenumber_samples, window_size)
    confusion = cutoff_matrix(reference_spectra)
    output = Path(output_path or (DEFAULT_OUTPUT_DIR / "demo_3_signal_score_between_subtype.png"))
    heatmap(
        confusion,
        subtype_name,
        subtype_name,
        output,
        figsize=(12, 12),
        xlabel="unknown signal",
        ylabel="ground truth reference",
    )
    return output


def demo_5_spontaneous_plot(
    dataset_folder: Path | str,
    target: str,
    bounds: tuple[float, float],
    output_path: Path | str | None = None,
) -> Path:
    lb, ub = bounds
    wavenumber, control_nerve_dataset, control_neuron_dataset, mutant_nerve_dataset, mutant_neuron_dataset = load_spontaneous_window(
        dataset_folder,
        lb,
        ub,
    )
    if target == "neuron":
        control = control_neuron_dataset
        mutant = mutant_neuron_dataset
    else:
        control = control_nerve_dataset
        mutant = mutant_nerve_dataset

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(wavenumber, safe_column_mean(control), linewidth=2, label="control")
    ax.plot(wavenumber, safe_column_mean(mutant), linewidth=2, label="FTLD")
    ax.set_xlim([lb, ub])
    ax.set_xlabel("Wavenumber (cm^-1)")
    ax.set_ylabel("Intensity (au)")
    ax.legend()
    style_axes(ax)
    output = Path(output_path or (DEFAULT_OUTPUT_DIR / f"demo_5_spontaneous_plot_{target}.png"))
    save_figure(fig, output)
    plt.close(fig)
    return output


def demo_6_similarity_boxplots(
    dataset_folder: Path | str,
    target: str,
    bounds: tuple[float, float],
    output_dir: Path | str | None = None,
) -> list[Path]:
    lb, ub = bounds
    output_root = ensure_directory(output_dir or DEFAULT_OUTPUT_DIR / f"demo_6_{target}")
    wavenumber, control_nerve_dataset, control_neuron_dataset, mutant_nerve_dataset, mutant_neuron_dataset = load_spontaneous_window(
        dataset_folder,
        lb,
        ub,
    )
    subtype_name, reference_spectra = reference_signal2(wavenumber, window_estimation(wavenumber, 100))
    control_dataset = control_neuron_dataset if target == "neuron" else control_nerve_dataset
    mutant_dataset = mutant_neuron_dataset if target == "neuron" else mutant_nerve_dataset

    outputs: list[Path] = []
    for idx, name in enumerate(subtype_name):
        subtype_reference_spectra = reference_spectra[idx, :, :]
        control_similarity = np.max(control_dataset.T @ subtype_reference_spectra, axis=1)
        mutant_similarity = np.max(mutant_dataset.T @ subtype_reference_spectra, axis=1)
        pvalue = mannwhitneyu(control_similarity, mutant_similarity, alternative="two-sided").pvalue
        output = output_root / f"{name}_p_{pvalue:.6g}.png"
        boxplot_with_scatter(
            control_similarity,
            mutant_similarity,
            ["control", "FTLD"],
            f"treatment in brain {target}",
            "similarity score",
            output,
        )
        outputs.append(output)
    return outputs


def demo_7(
    dataset_folder: Path | str = MATLAB_ROOT / "brain_dataset",
    output_path: Path | str | None = None,
) -> Path:
    lb, ub = 600.0, 3150.0
    wavenumber, control_nerve_dataset, _, mutant_nerve_dataset, _ = load_spontaneous_window(dataset_folder, lb, ub)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(wavenumber, safe_column_mean(control_nerve_dataset), linewidth=2, label="control")
    ax.plot(wavenumber, safe_column_mean(mutant_nerve_dataset), linewidth=2, label="mutant")
    ax.set_xlim([lb, ub])
    ax.set_ylim([0, 0.25])
    ax.set_xlabel("Wavenumber (cm^-1)")
    ax.set_ylabel("Intensity (au)")
    ax.legend()
    style_axes(ax)
    output = Path(output_path or (DEFAULT_OUTPUT_DIR / "demo_7.png"))
    save_figure(fig, output)
    plt.close(fig)
    return output


def demo_8(
    dataset_folder: Path | str = MATLAB_ROOT / "schizophrenia",
    output_path: Path | str | None = None,
) -> Path:
    lb, ub = 700.0, 1700.0
    wavenumber, control_nerve_dataset, _, mutant_nerve_dataset, _ = load_spontaneous_window(dataset_folder, lb, ub)
    subtype_name, reference_spectra = reference_signal2(wavenumber, window_estimation(wavenumber, 100))
    cardiolipin_reference_spectra = reference_spectra[subtype_name.index("Cardiolipin"), :, :]

    control_similarity = np.max(control_nerve_dataset.T @ cardiolipin_reference_spectra, axis=1)
    mutant_similarity = np.max(mutant_nerve_dataset.T @ cardiolipin_reference_spectra, axis=1)
    output = Path(output_path or (DEFAULT_OUTPUT_DIR / "demo_8.png"))
    boxplot_with_scatter(
        control_similarity,
        mutant_similarity,
        ["control", "mutant"],
        "treatment in brain nerve",
        "similarity score",
        output,
    )
    return output


def demo_figure3(output_path: Path | str | None = None) -> Path:
    wavenumber = np.arange(2796, 3086, dtype=float)
    signal = cardiolipin_signal(wavenumber)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot(wavenumber, signal, linewidth=2)
    ax.set_xlabel("Raman Shift (cm^-1)")
    ax.set_ylabel("Intensity (au)")
    style_axes(ax)
    output = Path(output_path or (DEFAULT_OUTPUT_DIR / "demo_figure3.png"))
    save_figure(fig, output)
    plt.close(fig)
    return output


def figure2_cardiolipin(output_path: Path | str | None = None) -> Path:
    wavenumber = np.arange(700, 1701, dtype=float)
    cardiolipin = cardiolipin_signal(wavenumber)
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(wavenumber, cardiolipin, linewidth=2, color="black")
    ax.set_xlim([700, 1700])
    ax.set_xticks(np.arange(700, 1701, 200))
    ax.set_ylim([0, 0.2])
    ax.set_yticks(np.arange(0, 0.201, 0.05))
    ax.set_xlabel("Wavenumber (cm^-1)")
    ax.set_ylabel("Intensity (au)")
    ax.set_title("Cardiolipin")
    style_axes(ax, fontsize=16)
    output = Path(output_path or (DEFAULT_OUTPUT_DIR / "figure2_cardiolipin.png"))
    save_figure(fig, output)
    plt.close(fig)
    return output
