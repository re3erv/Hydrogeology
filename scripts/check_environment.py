"""Hydrogeology environment diagnostics for plan phase A1.

Usage:
  python scripts/check_environment.py
  python scripts/check_environment.py --diagnose-only
"""

from __future__ import annotations

import argparse
import importlib
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

REQUIRED_PACKAGES = ("pytest", "flopy", "numpy", "pandas", "matplotlib")
REQUIRED_EXES = ("mf6", "mf2005", "mfnwt")


@dataclass
class CheckResult:
    name: str
    ok: bool
    details: str


def _print_header() -> None:
    print("=== Hydrogeology environment diagnostics (A1) ===")
    print(f"Python: {platform.python_version()}")
    print(f"OS: {platform.platform()}")
    print(f"Detected OS family: {platform.system().lower()}")
    print()


def check_python_runtime() -> list[CheckResult]:
    major, minor = sys.version_info[:2]
    stable = major == 3 and 11 <= minor <= 13
    details = (
        f"detected {major}.{minor}; recommended 3.11-3.13 for stable scientific stack. "
        "If installs fail, create a 3.11 environment."
    )
    return [CheckResult(name="python", ok=stable, details=details)]


def check_python_packages() -> list[CheckResult]:
    results: list[CheckResult] = []
    for pkg in REQUIRED_PACKAGES:
        try:
            mod = importlib.import_module(pkg)
            version = getattr(mod, "__version__", "unknown")
            results.append(CheckResult(pkg, True, f"installed ({version})"))
        except Exception:
            results.append(CheckResult(pkg, False, f"not installed; try: pip install {pkg}"))
    return results


def _pip_install(packages: Iterable[str]) -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "pip", "install", *packages]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 0:
        return True, f"pip: installed: {', '.join(packages)}"
    tail = (proc.stderr or proc.stdout).strip().splitlines()[-1:]
    extra = tail[0] if tail else "pip install failed"
    return False, f"pip failed: {extra}"


def _which_candidates(name: str) -> list[str]:
    candidates = [name]
    if os.name == "nt":
        candidates += [f"{name}.exe", f"{name.upper()}.EXE"]
    return candidates


def find_executable(name: str) -> str | None:
    for cand in _which_candidates(name):
        found = shutil.which(cand)
        if found:
            return found
    return None


def check_modflow_executables() -> list[CheckResult]:
    results: list[CheckResult] = []
    for exe in REQUIRED_EXES:
        path = find_executable(exe)
        if path:
            results.append(CheckResult(exe, True, f"found at {path}"))
        else:
            results.append(CheckResult(exe, False, "not found in PATH"))
    return results


def install_modflow() -> tuple[bool, str]:
    try:
        import flopy

        flopy.utils.get_modflow(bindir=":flopy")
        return True, "get-modflow: installation completed successfully via flopy.utils.get_modflow"
    except Exception as exc:
        return False, f"get-modflow failed: {exc}"


def print_section(title: str, results: list[CheckResult]) -> None:
    print(title)
    for r in results:
        state = "OK" if r.ok else "MISS"
        print(f"- [{state}] {r.name}: {r.details}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diagnose-only", action="store_true")
    args = parser.parse_args()

    _print_header()

    runtime = check_python_runtime()
    print_section("Python runtime", runtime)

    packages_before = check_python_packages()
    print_section("Python packages", packages_before)

    if not args.diagnose_only:
        missing_packages = [r.name for r in packages_before if not r.ok]
        if missing_packages:
            ok, msg = _pip_install(missing_packages)
            print("Auto-install Python packages")
            print(f"- [{'OK' if ok else 'MISS'}] {msg}")
            print()

            packages_after = check_python_packages()
            print_section("Python packages (after auto-install)", packages_after)
        else:
            packages_after = packages_before
    else:
        packages_after = packages_before

    exes_before = check_modflow_executables()
    print_section("MODFLOW executables", exes_before)

    if not args.diagnose_only:
        if any(not r.ok for r in exes_before):
            ok, msg = install_modflow()
            print("Auto-install MODFLOW executables")
            print(f"- [{'OK' if ok else 'MISS'}] {msg}")
            print()

            exes_after = check_modflow_executables()
            print_section("MODFLOW executables (after auto-install)", exes_after)
        else:
            exes_after = exes_before
    else:
        exes_after = exes_before

    print("Recommended install commands and links")
    print("- Python package for installer helper: pip install flopy")
    print("- Install USGS binaries via FloPy CLI: python -m flopy.utils.get_modflow :flopy")
    print("- Alternative entry point (if installed to PATH): get-modflow :flopy")
    print("- By default this script auto-installs missing Python packages; use --diagnose-only to disable.")
    print("- Guide: https://flopy.readthedocs.io/en/latest/md/get_modflow.html")
    print("- If command-line install is blocked, use official downloads:")
    print("- - MF6: https://water.usgs.gov/water-resources/software/MODFLOW-6/")
    print("- - MF2005: https://www.usgs.gov/software/modflow-2005-usgs-three-dimensional-finite-difference-ground-water-model")
    print("- - MF-NWT: https://water.usgs.gov/ogw/modflow-nwt/")
    print(
        "- Install Python deps in current interpreter: "
        "python -m pip install -U pip pytest flopy numpy pandas matplotlib"
    )
    print("- Run tests reliably from this interpreter: python -m pytest -q")
    print()

    ready = all(r.ok for r in runtime) and all(r.ok for r in packages_after) and all(r.ok for r in exes_after)
    if ready:
        print("Environment looks ready.")
        return 0
    print("Environment is not fully ready yet.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
