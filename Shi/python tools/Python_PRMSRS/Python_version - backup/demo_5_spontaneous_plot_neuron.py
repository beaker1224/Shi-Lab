from __future__ import annotations

from prm_srs.config import MATLAB_ROOT
from prm_srs.demo_workflows import demo_5_spontaneous_plot


if __name__ == "__main__":
    demo_5_spontaneous_plot(MATLAB_ROOT / "brain_dataset", target="neuron", bounds=(700, 1700))
