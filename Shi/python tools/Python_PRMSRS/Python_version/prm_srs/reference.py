from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import SUBTYPE_REFERENCE_DIR
from .excel_io import read_excel_numeric
from .spectra import eliminate_nan, signal_normalization


def reference_signal3(
    wavenumber_samples: np.ndarray,
    reference_dir: Path | str | None = None,
) -> tuple[list[str], list[np.ndarray]]:
    reference_path = Path(reference_dir) if reference_dir is not None else SUBTYPE_REFERENCE_DIR
    lipid_subtype_signal = read_excel_numeric(reference_path / "lipid_subtype.xlsx")
    rna_signal = read_excel_numeric(reference_path / "RNA Data.xlsx")

    names: list[str] = []
    dataset: list[np.ndarray] = []

    def add_from_matrix(name: str, matrix: np.ndarray) -> None:
        names.append(name)
        dataset.append(signal_normalization(matrix, wavenumber_samples))

    add_from_matrix("PE", eliminate_nan(lipid_subtype_signal[:, 0:2]))
    add_from_matrix("PLS", eliminate_nan(lipid_subtype_signal[:, 3:5]))
    add_from_matrix("Cholesterol", _read_matrix(reference_path / "Cholesterol.txt"))
    add_from_matrix("Cholesterol_ester", _read_matrix(reference_path / "Cholesterol ester.txt"))
    add_from_matrix("Cardiolipin", eliminate_nan(lipid_subtype_signal[:, 9:11]))
    add_from_matrix("Sphingosine", eliminate_nan(lipid_subtype_signal[:, 12:14]))
    add_from_matrix("WT", eliminate_nan(rna_signal[:, [0, 1]]))
    add_from_matrix("MUT", eliminate_nan(rna_signal[:, [0, 2]]))
    add_from_matrix("PC", _read_matrix(reference_path / "PC.txt"))
    add_from_matrix("PS", _read_matrix(reference_path / "PS.txt"))
    add_from_matrix("CDP_DG", _read_matrix(reference_path / "CDP DG.txt"))
    add_from_matrix("Lyso_PA", _read_matrix(reference_path / "LysoPA.txt"))
    add_from_matrix("Lysyl_DG", _read_matrix(reference_path / "Lysyl DG.txt"))

    bg_sub_dir = reference_path / "2021-02-17 LIPID grating2400 Int100 Amp100 Acq30 Acc2 slit100 hole300 (bg sub)"
    add_from_matrix(
        "dsgPI",
        _read_matrix(bg_sub_dir / "1,2-Diacyl-sn-glycero-3-phospho-L-serine-sub bg.txt"),
    )
    add_from_matrix("LaPI", _read_matrix(bg_sub_dir / "L-a-phosphatidyl  inositol-sub bg.txt"))
    add_from_matrix("LaPG", _read_matrix(bg_sub_dir / "L-a-phosphatidyl-DL-glycerol sodium salt-sub bg.txt"))
    add_from_matrix("LPA", _read_matrix(bg_sub_dir / "Oleoyl-L-a-lysophosphatidic acid-sub bg.txt"))
    add_from_matrix("Phosphatidylcholine", _read_matrix(bg_sub_dir / "Phosphatidylcholine-sub bg.txt"))
    add_from_matrix("TAG", _read_matrix(bg_sub_dir / "TAG mix-sub bg.txt"))

    add_from_matrix("lipid_16_0", _read_matrix(reference_path / "lipid_16_0.txt"))
    add_from_matrix("lipid_18_0", _read_matrix(reference_path / "lipid_18_0.txt"))
    add_from_matrix("lipid_24_5", _read_matrix(reference_path / "lipid_24_5.txt"))
    add_from_matrix("DHA_omega_3_22_6", _read_matrix(reference_path / "DHA_omega_3_22_6.txt"))
    add_from_matrix("omega_3_24_5", _read_matrix(reference_path / "omega_3_24_5.txt"))
    add_from_matrix("C24_1_cera3", _read_matrix(reference_path / "C24_1_cera3.txt"))
    add_from_matrix("C24_cera2", _read_matrix(reference_path / "C24_cera2.txt"))
    add_from_matrix("C22_cera1", _read_matrix(reference_path / "C22_cera1.txt"))
    add_from_matrix("PC-18-1", _read_matrix(reference_path / "PC 18-1.txt"))
    add_from_matrix("PE-18-1", _read_matrix(reference_path / "PE 18-1.txt"))
    add_from_matrix("Ceramide-18-1-12-0", _read_matrix(reference_path / "Ceramide 18-1&12-0.txt"))
    add_from_matrix("deoxycer 18,1_24,1", _read_matrix(reference_path / "deoxycer 18,1_24,1.txt"))
    add_from_matrix("deoxycer 18,1_16,0", _read_matrix(reference_path / "deoxycer 18,1_16,0.txt"))
    add_from_matrix(
        "deoxy dihydro cer 18,0_14,0",
        _read_matrix(reference_path / "deoxy dihydro cer 18,0_14,0.txt"),
    )
    add_from_matrix(
        "deoxy dihydro cer 18,0_24,1",
        _read_matrix(reference_path / "deoxy dihydro cer 18,0_24,1.txt"),
    )
    add_from_matrix("L_Dopamine", _read_matrix(reference_path / "L Dopamine Raw.txt"))
    add_from_matrix(
        "DL_Norepinephrine_hcl",
        _read_matrix(reference_path / "DL Norepinephrine hcl Raw.txt"),
    )
    return names, dataset


def reference_signal2(
    wavenumber_samples: np.ndarray,
    window_size: int,
    reference_dir: Path | str | None = None,
) -> tuple[list[str], np.ndarray]:
    wavenumber_samples = np.asarray(wavenumber_samples, dtype=float)
    gap = wavenumber_samples[1] - wavenumber_samples[0]
    stack_size = wavenumber_samples.size
    scan_size = window_size * 2 + 1

    first_serial_start = wavenumber_samples[0] - window_size * gap
    first_serial_stop = first_serial_start + wavenumber_samples[-1] - wavenumber_samples[0]

    dataset_by_shift: list[list[np.ndarray]] = []
    subtype_name: list[str] = []
    for shift_idx in range(scan_size):
        serial_start = first_serial_start + shift_idx * gap
        serial_stop = first_serial_stop + shift_idx * gap
        serial_wavenumber_samples = np.linspace(serial_start, serial_stop, stack_size)
        subtype_name, shifted_dataset = reference_signal3(
            serial_wavenumber_samples,
            reference_dir=reference_dir,
        )
        dataset_by_shift.append(shifted_dataset)

    subtype_size = len(subtype_name)
    reference_spectra = np.zeros((subtype_size, stack_size, scan_size), dtype=float)
    for shift_idx, shifted_dataset in enumerate(dataset_by_shift):
        for subtype_idx, spectrum in enumerate(shifted_dataset):
            reference_spectra[subtype_idx, :, shift_idx] = spectrum
    return subtype_name, reference_spectra


def cardiolipin_signal(
    wavenumber_samples: np.ndarray,
    reference_dir: Path | str | None = None,
) -> np.ndarray:
    subtype_names, reference_dataset = reference_signal3(wavenumber_samples, reference_dir=reference_dir)
    cardiolipin_idx = subtype_names.index("Cardiolipin")
    return reference_dataset[cardiolipin_idx]


def _read_matrix(path: Path) -> np.ndarray:
    suffix = path.suffix.lower()
    if suffix == ".xlsx":
        return read_excel_numeric(path)
    return np.genfromtxt(path, dtype=float)
