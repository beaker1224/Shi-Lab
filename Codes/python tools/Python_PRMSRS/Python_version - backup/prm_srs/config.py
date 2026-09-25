from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PYTHON_VERSION_ROOT = PACKAGE_ROOT.parent
PROJECT_ROOT = PYTHON_VERSION_ROOT.parent
MATLAB_ROOT = PROJECT_ROOT / "PRM_SRS_Matlab_version"
SUBTYPE_REFERENCE_DIR = MATLAB_ROOT / "subtype_reference"
DEFAULT_OUTPUT_DIR = PYTHON_VERSION_ROOT / "outputs"


def ensure_directory(path: Path | str) -> Path:
    output_path = Path(path)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path
