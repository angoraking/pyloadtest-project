# -*- coding: utf-8 -*-

"""
Install each library from PyPI into a brand new ``.venv``, one library at a time.

For every library picked by its probability (0-1), this script:

1. renders ``pyproject.toml`` from ``pyproject.toml.template`` with only that library
2. removes ``.venv`` and ``uv.lock``
3. ``uv venv`` a new ``.venv`` with the interpreter that runs this script
4. ``uv sync --no-cache`` so every wheel is downloaded from the index

The whole thing is repeated ``N`` times, each round rolls the dice again.
Only uses the standard library.

Usage::

    python run_load_test.py
"""

import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

dir_here = Path(__file__).absolute().parent
path_template = dir_here / "pyproject.toml.template"
path_pyproject_toml = dir_here / "pyproject.toml"
path_uv_lock = dir_here / "uv.lock"
dir_venv = dir_here / ".venv"

PLACEHOLDER = "{DEPENDENCIES}"

N = 3

LIBRARIES = [
    {"name": "vislog", "prob": 1},
    {"name": "soft-deps", "prob": 0.5},
    {"name": "boto-session-manager", "prob": 1},
    {"name": "cdk-mate", "prob": 1},
    {"name": "simple-aws-lambda", "prob": 1},
    {"name": "simple-aws-ssm-parameter-store", "prob": 1},
]

# If this script itself runs from .venv, sys.executable is deleted with it;
# use the base interpreter the venv was created from instead.
python_executable = getattr(sys, "_base_executable", sys.executable)


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(args: list[str]) -> float:
    """
    Run a command, print its output, return the elapsed time in seconds.
    """
    log(f"$ {' '.join(args)}")
    start = time.perf_counter()
    # uv writes most of its output to stderr, merge it so everything is printed in order
    result = subprocess.run(
        args,
        cwd=dir_here,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    elapsed = time.perf_counter() - start
    for line in result.stdout.splitlines():
        print(f"    {line}", flush=True)
    if result.returncode != 0:
        log(f"failed with exit code {result.returncode} in {elapsed:.2f}s")
        raise subprocess.CalledProcessError(result.returncode, args)
    log(f"done in {elapsed:.2f}s")
    return elapsed


def pick_libraries(libraries: list[dict]) -> list[str]:
    """
    Roll the dice for each library, return the names that are picked.
    """
    return [lib["name"] for lib in libraries if random.random() < lib["prob"]]


def write_pyproject_toml(name: str):
    # A bare name means "any version", the PEP 508 equivalent of ``*``.
    template = path_template.read_text(encoding="utf-8")
    path_pyproject_toml.write_text(
        template.replace(PLACEHOLDER, f'"{name}"'),
        encoding="utf-8",
    )
    log(f"wrote {path_pyproject_toml.name} with dependency {name!r}")


def install_library(name: str) -> dict[str, float]:
    """
    Install one library into a fresh .venv, return the time of each uv step.
    """
    write_pyproject_toml(name)
    # Start from an empty venv every time, and resolve again without the old lock
    log(f"remove {dir_venv.name} and {path_uv_lock.name}")
    shutil.rmtree(dir_venv, ignore_errors=True)
    path_uv_lock.unlink(missing_ok=True)
    venv_time = run(["uv", "venv", str(dir_venv), "--python", python_executable])
    # --no-cache: always download from the index, never reuse uv's cache
    sync_time = run(["uv", "sync", "--no-cache"])
    return {"venv": venv_time, "sync": sync_time}


def main():
    log(f"python: {sys.version.split()[0]} ({python_executable})")
    log(f"rounds: {N}")
    records = []  # (round, library, times)
    for i in range(1, N + 1):
        names = pick_libraries(LIBRARIES)
        log(f"===== round {i}/{N}, picked {names} =====")
        for name in names:
            log(f"----- install {name} -----")
            records.append((i, name, install_library(name)))

    log("===== summary =====")
    for i, name, times in records:
        log(
            f"round {i} {name:<32} "
            f"uv venv {times['venv']:.2f}s, uv sync {times['sync']:.2f}s"
        )
    if records:
        total_venv = sum(times["venv"] for _, _, times in records)
        total_sync = sum(times["sync"] for _, _, times in records)
        log(
            f"{len(records)} installs, "
            f"total uv venv {total_venv:.2f}s, total uv sync {total_sync:.2f}s"
        )


if __name__ == "__main__":
    main()
