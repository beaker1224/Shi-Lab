from __future__ import annotations

from prm_srs.config import MATLAB_ROOT
from prm_srs.demo_workflows import demo_6_similarity_boxplots


if __name__ == "__main__":
    demo_6_similarity_boxplots(MATLAB_ROOT / "schizophrenia", target="nerve", bounds=(2700, 3150))
