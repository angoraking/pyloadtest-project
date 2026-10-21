# -*- coding: utf-8 -*-

"""
Generate ``pyproject.toml`` from ``pyproject.toml.template``.

Each library is included as a dependency with its own probability (0-1),
rolled independently. Only uses the standard library.

Usage::

    python gen_pyproject_toml.py
"""

import random
from pathlib import Path

dir_here = Path(__file__).absolute().parent
path_template = dir_here / "pyproject.toml.template"
path_pyproject_toml = dir_here / "pyproject.toml"

PLACEHOLDER = "{DEPENDENCIES}"

LIBRARIES = [
    {"name": "vislog", "prob": 1},
    {"name": "soft-deps", "prob": 0.5},
]


def pick_libraries(libraries: list[dict]) -> list[str]:
    """
    Roll the dice for each library, return the names that are picked.
    """
    return [lib["name"] for lib in libraries if random.random() < lib["prob"]]


def render(names: list[str]) -> str:
    # A bare name means "any version", the PEP 508 equivalent of ``*``.
    dependencies = ",\n    ".join(f'"{name}"' for name in names)
    template = path_template.read_text(encoding="utf-8")
    return template.replace(PLACEHOLDER, dependencies)


def main():
    names = pick_libraries(LIBRARIES)
    path_pyproject_toml.write_text(render(names), encoding="utf-8")
    print(f"picked libraries: {names}")
    print(f"wrote {path_pyproject_toml}")


if __name__ == "__main__":
    main()
