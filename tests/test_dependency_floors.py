"""pyproject.toml and backend/requirements.txt must declare identical floors.

The runtime dependency list deliberately lives in two places: pyproject.toml
feeds the hash-checked lock compilation (see the lock-file headers), while
backend/requirements.txt drives ``make setup`` on a judge's machine. Each
security floor (Pillow, python-multipart, setuptools) is therefore spelled
twice, and the 2026-07-16 audit found the copies already disagreeing —
python-multipart's <1.0 cap was missing from pyproject and openai's floor was
spelled differently. This gate makes any future drift fail the suite, the same
way scripts/check_claim_counts.py guards the published test counts.
"""

import tomllib
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]


def _floors(lines):
    floors = {}
    for line in lines:
        spec = line.split("#")[0].strip()
        if not spec:
            continue
        requirement = Requirement(spec)
        floors[requirement.name.lower()] = (
            sorted(str(s) for s in requirement.specifier),
            tuple(sorted(requirement.extras)),
        )
    return floors


def test_pyproject_and_requirements_declare_identical_runtime_floors():
    with (ROOT / "pyproject.toml").open("rb") as fh:
        declared = tomllib.load(fh)["project"]["dependencies"]
    requirements = (ROOT / "backend" / "requirements.txt").read_text(
        encoding="utf-8"
    ).splitlines()

    assert _floors(declared) == _floors(requirements)
