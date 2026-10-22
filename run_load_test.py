# -*- coding: utf-8 -*-

"""
Install each library from PyPI into a brand new ``.venv``, one library at a time.

For every library picked by its probability (0-1), this script quietly:

1. removes ``.venv``
2. ``uv venv`` a new ``.venv`` with the interpreter that runs this script
3. ``uv pip install --no-deps --no-cache`` the library only, without its
   dependencies, always downloaded from the index

The whole thing is repeated ``N`` times, each round rolls the dice again.
Only a short line per install is printed, a failed command also prints its output.
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
dir_venv = dir_here / ".venv"

N = 3

LIBRARIES = [
    # --- high-traffic libraries
    # {"name": "boto-session-manager", "prob": 0.0},
    # {"name": "s3pathlib", "prob": 0.0},
    # {"name": "uszipcode", "prob": 0.0},
    # {"name": "sqlalchemy-mate", "prob": 0.0},
    # {"name": "func-args", "prob": 0.0},
    # {"name": "iterproxy", "prob": 0.0},
    # {"name": "pathlib-mate", "prob": 0.0},
    # --- medium-traffic libraries
    {"name": "pynamodb-mate", "prob": 1.0},
    {"name": "pynamodb-session-manager", "prob": 1.0},
    {"name": "atlas-doc-parser", "prob": 1.0},
    {"name": "aws-lbd-art-builder-core", "prob": 1.0},
    {"name": "aws-lbd-art-builder-uv", "prob": 1.0},
    {"name": "cdk-mate", "prob": 1.0},
    {"name": "cookiecutter-maker", "prob": 1.0},
    {"name": "home-secret-toml", "prob": 1.0},
    {"name": "s3vectorm", "prob": 1.0},
    {"name": "sqlalchemy-upsert-kit", "prob": 1.0},
    {"name": "sayt2", "prob": 1.0},
    {"name": "windtalker", "prob": 1.0},
    # --- low-traffic libraries
    {"name": "aws-sdk-polars", "prob": 0.5},
    {"name": "configcraft", "prob": 0.5},
    {"name": "polars-writer", "prob": 0.5},
    {"name": "s3manifesto", "prob": 0.5},
    {"name": "simple-aws-lambda", "prob": 0.5},
    {"name": "simple-aws-ssm-parameter-store", "prob": 0.5},
    {"name": "soft-deps", "prob": 0.5},
    {"name": "vislog", "prob": 0.5},
]

# If this script itself runs from .venv, sys.executable is deleted with it;
# use the base interpreter the venv was created from instead.
python_executable = getattr(sys, "_base_executable", sys.executable)


def run(args: list[str]):
    """
    Run a command quietly; only print its output if it fails.
    """
    # uv writes most of its output to stderr, merge it so it is printed in order
    result = subprocess.run(
        args,
        cwd=dir_here,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        for line in result.stdout.splitlines():
            print(f"    {line}", flush=True)
        raise subprocess.CalledProcessError(result.returncode, args)


def install_library(name: str):
    """
    Install one library into a fresh .venv.
    """
    # Start from an empty venv every time
    shutil.rmtree(dir_venv, ignore_errors=True)
    run(["uv", "venv", str(dir_venv), "--python", python_executable])
    # --no-deps: only the library itself, not its dependencies
    # --no-cache: always download from the index, never reuse uv's cache
    run(
        [
            "uv", "pip", "install",
            "--no-deps", "--no-cache",
            "--python", str(dir_venv),
            name,
        ]
    )


def main():
    # Windows runners default to a legacy code page that cannot print emoji
    sys.stdout.reconfigure(encoding="utf-8")

    n_libs = len(LIBRARIES)
    n_total = N * n_libs
    print(f"python {sys.version.split()[0]}, {N} rounds x {n_libs} libraries", flush=True)

    n_ok, n_failed = 0, 0
    start = time.perf_counter()
    for i in range(1, N + 1):
        print(f"\n{'=' * 20} round {i}/{N} {'=' * 20}", flush=True)
        for j, lib in enumerate(LIBRARIES, start=1):
            # Skipped libraries print nothing, but still count towards j and k
            if random.random() >= lib["prob"]:
                continue
            k = (i - 1) * n_libs + j
            name = lib["name"]
            print(f"{'-' * 8} {j}/{n_libs} | {k}/{n_total} | {name}", flush=True)
            t = time.perf_counter()
            try:
                install_library(name)
            except subprocess.CalledProcessError:
                n_failed += 1
                print(f"❌ {name} failed ({time.perf_counter() - t:.2f}s)", flush=True)
            else:
                n_ok += 1
                print(f"✅ {name} ({time.perf_counter() - t:.2f}s)", flush=True)

    elapsed = time.perf_counter() - start
    print(f"\n{'=' * 20} summary {'=' * 20}", flush=True)
    print(
        f"✅ {n_ok} ok, ❌ {n_failed} failed, "
        f"⏭️ {n_total - n_ok - n_failed} skipped, {elapsed:.2f}s",
        flush=True,
    )
    if n_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
