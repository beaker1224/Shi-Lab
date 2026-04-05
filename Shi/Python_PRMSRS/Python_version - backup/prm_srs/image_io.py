from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import tifffile


def folders_generation(root_folder: Path | str) -> list[Path]:
    root = Path(root_folder)
    directories = [path for path in root.rglob("*") if path.is_dir()]
    if not directories:
        return [root]
    leaf_directories = [path for path in directories if not any(child.is_dir() for child in path.iterdir())]
    return sorted(leaf_directories)


def read_oir_folder_image(path: Path | str) -> np.ndarray:
    return _read_folder_image(path, "*.oir")


def read_oib_folder_image(path: Path | str) -> np.ndarray:
    return _read_folder_image(path, "*.oib")


def read_image(file_name: Path | str) -> np.ndarray:
    image_path = Path(file_name)
    errors: list[str] = []

    for loader in (_load_with_tifffile, _load_with_aicsimageio, _load_with_bioio):
        try:
            data = loader(image_path)
            return _coerce_image_stack(data)
        except Exception as exc:
            errors.append(f"{loader.__name__}: {exc}")

    error_message = "\n".join(errors)
    raise RuntimeError(
        f"Unable to read image file: {image_path}\n"
        "Install an optional OIR/OIB reader such as `aicsimageio`, or export the data to TIFF.\n"
        f"Reader attempts:\n{error_message}"
    )


def _read_folder_image(path: Path | str, pattern: str) -> np.ndarray:
    folder = Path(path)
    file_list = sorted(folder.glob(pattern))
    if not file_list:
        raise FileNotFoundError(f"No files matching {pattern} found in {folder}")

    collected = []
    shape = None
    for file_name in file_list:
        image = read_image(file_name)
        frame = _single_frame(image, file_name)
        if shape is None:
            shape = frame.shape
        if frame.shape != shape:
            raise ValueError(
                f"Image stack size mismatch in {folder}: expected {shape}, got {frame.shape} from {file_name}"
            )
        collected.append(frame)
    return np.stack(collected, axis=0).astype(float)


def _coerce_image_stack(data: np.ndarray) -> np.ndarray:
    array = np.asarray(data)
    if array.ndim == 2:
        return array[np.newaxis, ...].astype(float)

    if array.ndim == 3:
        if array.shape[-1] <= 4 and array.shape[0] > 4:
            return array[..., 0][np.newaxis, ...].astype(float)
        return array.astype(float)

    if array.ndim > 3:
        squeezed = np.squeeze(array)
        if squeezed.ndim == 2:
            return squeezed[np.newaxis, ...].astype(float)
        if squeezed.ndim == 3:
            if squeezed.shape[-1] <= 4 and squeezed.shape[0] > 4:
                return squeezed[..., 0][np.newaxis, ...].astype(float)
            return squeezed.astype(float)
    raise ValueError(f"Unsupported image dimensionality: {array.shape}")


def _single_frame(image: np.ndarray, source: Path) -> np.ndarray:
    if image.ndim != 3:
        raise ValueError(f"Expected a 3D stack from {source}, got shape {image.shape}")
    if image.shape[0] == 1:
        return image[0]
    raise ValueError(
        f"Expected a single frame per file in {source}, got stack shape {image.shape}. "
        "If your files contain multi-frame data, adapt the loader for your acquisition format."
    )


def _load_with_tifffile(path: Path) -> np.ndarray:
    return tifffile.imread(path)


def _load_with_aicsimageio(path: Path) -> np.ndarray:
    from aicsimageio import AICSImage

    image = AICSImage(path)
    data = image.get_image_data()
    return np.asarray(data)


def _load_with_bioio(path: Path) -> np.ndarray:
    from bioio import BioImage

    image = BioImage(path)
    data = image.get_image_data()
    return np.asarray(data)


def save_tiff(path: Path | str, image: np.ndarray) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    array = np.asarray(image)
    if array.dtype == np.float64:
        array = array.astype(np.float32)
    tifffile.imwrite(output_path, array)
