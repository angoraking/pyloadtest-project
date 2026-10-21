# -*- coding: utf-8 -*-

"""
Create a fresh ``.venv`` with uv and install the libraries from ``pyproject.toml``,
repeated ``N`` times. Only uses the standard library.

Run ``gen_pyproject_toml.py`` first. The venv uses the same interpreter
that runs this script.

Usage::

    python install_libraries.py
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

dir_here = Path(__file__).absolute().parent
dir_venv = dir_here / ".venv"

N = 3

# If this script itself runs from .venv, sys.executable is deleted with it;
# use the base interpreter the venv was created from instead.
python_executable = getattr(sys, "_base_executable", sys.executable)


def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(args: list[str]):
    log(f"$ {' '.join(args)}")
    start = time.perf_counter()
    subprocess.run(args, cwd=dir_here, check=True)
    elapsed = time.perf_counter() - start
    log(f"done in {elapsed:.2f}s")
    return elapsed


def install_libraries() -> float:
    """
    Recreate .venv and install the libraries, return the ``uv sync`` time in seconds.
    """
    # Start from an empty venv every time
    log(f"remove {dir_venv}")
    shutil.rmtree(dir_venv, ignore_errors=True)
    run(["uv", "venv", str(dir_venv), "--python", python_executable])
    # --no-cache: always download from the index, never reuse uv's cache
    return run(["uv", "sync", "--no-cache"])


def main():
    log(f"python: {sys.version.split()[0]} ({python_executable})")
    log(f"rounds: {N}")
    sync_times = []
    for i in range(N):
        log(f"===== install round {i + 1}/{N} =====")
        sync_times.append(install_libraries())
    log("===== summary =====")
    for i, t in enumerate(sync_times, start=1):
        log(f"round {i}: uv sync {t:.2f}s")
    log(f"total uv sync {sum(sync_times):.2f}s, avg {sum(sync_times) / N:.2f}s")


if __name__ == "__main__":
    main()
