"""Fail when backend maintainability boundaries drift."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from radon.complexity import cc_visit

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
MAX_LINES = 500
MAX_COMPLEXITY = 10


def _module_name(path: Path) -> str:
    relative = path.relative_to(ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _modules() -> dict[str, Path]:
    return {_module_name(path): path for path in BACKEND.rglob("*.py")}


def _complexity_failures(path: Path) -> list[str]:
    failures = []
    for block in cc_visit(path.read_text(encoding="utf-8")):
        candidates = [block, *getattr(block, "methods", [])]
        for candidate in candidates:
            if candidate.complexity > MAX_COMPLEXITY:
                relative = path.relative_to(ROOT)
                failures.append(
                    f"{relative}:{candidate.lineno} {candidate.name} has complexity "
                    f"{candidate.complexity} (max {MAX_COMPLEXITY})"
                )
    return failures


def _dependency_for_import(module: str, candidate: str, known: set[str]) -> str | None:
    if not candidate.startswith("backend"):
        return None
    parts = candidate.split(".")
    while parts:
        name = ".".join(parts)
        if name in known and name != module:
            return name
        parts.pop()
    return None


def _dependencies(module: str, path: Path, known: set[str]) -> set[str]:
    dependencies: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        candidates: list[str] = []
        if isinstance(node, ast.Import):
            candidates.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            candidates.append(node.module)
            candidates.extend(f"{node.module}.{alias.name}" for alias in node.names)
        for candidate in candidates:
            dependency = _dependency_for_import(module, candidate, known)
            if dependency:
                dependencies.add(dependency)
    return dependencies


def _cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    found: set[tuple[str, ...]] = set()

    def visit(node: str, path: list[str]) -> None:
        if node in path:
            cycle = path[path.index(node) :]
            rotations = [tuple(cycle[index:] + cycle[:index]) for index in range(len(cycle))]
            found.add(min(rotations))
            return
        for dependency in graph[node]:
            visit(dependency, [*path, node])

    for module in graph:
        visit(module, [])
    return [list(cycle) for cycle in sorted(found)]


def check() -> list[str]:
    modules = _modules()
    failures: list[str] = []
    for path in modules.values():
        line_count = len(path.read_text(encoding="utf-8").splitlines())
        if line_count > MAX_LINES:
            failures.append(f"{path.relative_to(ROOT)} has {line_count} lines (max {MAX_LINES})")
        failures.extend(_complexity_failures(path))
    graph = {module: _dependencies(module, path, set(modules)) for module, path in modules.items()}
    failures.extend(f"circular dependency: {' -> '.join([*cycle, cycle[0]])}" for cycle in _cycles(graph))
    return failures


def main() -> int:
    failures = check()
    if failures:
        print("Architecture checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(
        f"Architecture checks passed: files <= {MAX_LINES} lines, "
        f"complexity <= {MAX_COMPLEXITY}, no circular backend imports."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
