"""Single source of truth for project data paths."""

import pathlib

_ROOT = pathlib.Path(__file__).parent.parent

CORPUS = _ROOT / "data" / "corpus"
PROJECTS_DIR = _ROOT / "data" / "projects"
