"""Environment diagnostics for FloPy and MODFLOW executables.

This script checks:
1) Python runtime and core scientific packages.
2) Availability of MODFLOW executables (mf6, mf2005, mfnwt).
3) Suggested installation commands for the current OS.

It can optionally try to install MODFLOW executables via FloPy's get-modflow.
"""

from __future__ import annotations

import argparse
import importlib
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass


PACKAGE_HINTS = {
    "flopy": "pip install flopy",
    "numpy": "pip install numpy",
    "pandas": "pip install pandas",
    "matplotlib": "pip install matplotlib",
    "pytest": "pip install pytest",
}

EXECUTABLES = ("mf6", "mf2005", "mfnwt")

DOWNLOAD_LINKS = {
    "mf6": "https://water.usgs.gov/water-resources/software/MODFLOW-6/",
    "mf2005": "https://www.usgs.gov/software/modflow-2005-usgs-three-dimensional-finite-difference-ground-water-model",
    "mfnwt": "https://water.usgs.gov/ogw/modflow-nwt/",
    "flopy_get_modflow": "https://flopy.readthedocs.io/en/latest/md/get_modflow.html",
}


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


def detect_os_family() -> str:
    system = platform.system().lower()
    if "windows" in system:
        return "windows"
    if "darwin" in system:
        return "macos"
    return "linux"


def check_python_runtime() -> CheckResult:
    major, minor = sys.version_info.major, sys.version_info.minor
    if major == 3 and minor in (11, 12, 13):
        return CheckResult("python", True, f"supported runtime detected: {major}.{minor}")
    return CheckResult(
        "python",
        False,
        (
            f"detected {major}.{minor}; recommended 3.11-3.13 for stable scientific stack. "
            "If installs fail, create a 3.11 environment."
        ),
    )


def check_python_packages(package_names: list[str]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for package_name in package_names:
        try:
            module = importlib.import_module(package_name)
            version = getattr(module, "__version__", "version unknown")
            results.append(CheckResult(package_name, True, f"installed ({version})"))
        except Exception:
            hint = PACKAGE_HINTS.get(package_name, f"pip install {package_name}")
            results.append(CheckResult(package_name, False, f"not installed; try: {hint}"))
    return results


def check_executables(names: tuple[str, ...]) -> list[CheckResult]:
    results: list[CheckResult] = []
    for executable_name in names:
        path = shutil.which(executable_name)
        if path:
            results.append(CheckResult(executable_name, True, f"found at {path}"))
        else:
            results.append(CheckResult(executable_name, False, "not found in PATH"))
    return results


def build_install_recommendations(os_family: str) -> list[str]:
    common = [
        "Python package for installer helper: pip install flopy",
        "Install USGS binaries via FloPy CLI: python -m flopy.utils.get_modflow :flopy",
        "Alternative entry point (if installed to PATH): get-modflow :flopy",
        "By default this script auto-installs missing Python packages; use --diagnose-only to disable.",
        f"Guide: {DOWNLOAD_LINKS['flopy_get_modflow']}",
    ]

    if os_family == "windows":
        return common + [
            "If command-line install is blocked, use official downloads:",
            f"- MF6: {DOWNLOAD_LINKS['mf6']}",
            f"- MF2005: {DOWNLOAD_LINKS['mf2005']}",
            f"- MF-NWT: {DOWNLOAD_LINKS['mfnwt']}",
            "Install Python deps in current interpreter: python -m pip install -U pip pytest flopy numpy pandas matplotlib",
            "Run tests reliably from this interpreter: python -m pytest -q",
        ]

    if os_family == "macos":
        return common + [
            "Install deps: python -m pip install -U pip pytest flopy numpy pandas matplotlib",
            f"Official downloads if needed: {DOWNLOAD_LINKS['mf6']}",
        ]

    return common + [
        "Install deps: python -m pip install -U pip pytest flopy numpy pandas matplotlib",
        "APT example (Debian/Ubuntu): sudo apt-get update && sudo apt-get install -y python3 python3-pip",
        f"Official downloads if needed: {DOWNLOAD_LINKS['mf6']}",
    ]


def try_install_modflow_binaries() -> CheckResult:
    try:
        command = [sys.executable, "-m", "flopy.utils.get_modflow", ":flopy"]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode == 0:
            return CheckResult(
                "get-modflow",
                True,
                "installation completed successfully via flopy.utils.get_modflow",
            )
        stderr = completed.stderr.strip() or "unknown error"
        return CheckResult("get-modflow", False, f"installation failed: {stderr}")
    except Exception as exc:
        return CheckResult("get-modflow", False, f"installation failed: {exc}")


def build_pip_install_command(package_names: list[str]) -> list[str]:
    return [sys.executable, "-m", "pip", "install", "-U", *package_names]


def install_missing_python_packages(package_names: list[str]) -> list[CheckResult]:
    if not package_names:
        return []
    command = build_pip_install_command(package_names)
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode == 0:
            return [CheckResult("pip", True, f"installed: {', '.join(package_names)}")]
        stderr = completed.stderr.strip() or "unknown error"
        return [CheckResult("pip", False, f"install failed: {stderr}")]
    except Exception as exc:
        return [CheckResult("pip", False, f"install failed: {exc}")]


def print_results(title: str, results: list[CheckResult]) -> None:
    print(f"\n{title}")
    for result in results:
        status = "OK" if result.ok else "MISS"
        print(f"- [{status}] {result.name}: {result.detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose environment for FloPy + MODFLOW workflow")
    parser.add_argument(
        "--install-modflow",
        action="store_true",
        help="Attempt immediate MODFLOW executable installation via FloPy get-modflow",
    )
    parser.add_argument(
        "--diagnose-only",
        action="store_true",
        help="Run checks only, without auto-installing missing Python packages.",
    )
    args = parser.parse_args()

    os_family = detect_os_family()
    print("=== Hydrogeology environment diagnostics (A1) ===")
    print(f"Python: {sys.version.split()[0]}")
    print(f"OS: {platform.platform()}")
    print(f"Detected OS family: {os_family}")

    runtime_result = check_python_runtime()
    package_results = check_python_packages(["pytest", "flopy", "numpy", "pandas", "matplotlib"])
    executable_results = check_executables(EXECUTABLES)

    print_results("Python runtime", [runtime_result])
    print_results("Python packages", package_results)
    print_results("MODFLOW executables", executable_results)

    auto_install_enabled = not args.diagnose_only
    if auto_install_enabled:
        missing_python_packages = [item.name for item in package_results if not item.ok]
        install_results = install_missing_python_packages(missing_python_packages)
        if install_results:
            print_results("Auto-install Python packages", install_results)
            package_results = check_python_packages(["pytest", "flopy", "numpy", "pandas", "matplotlib"])
            print_results("Python packages (after auto-install)", package_results)

    if args.install_modflow:
        install_result = try_install_modflow_binaries()
        print_results("Immediate install attempt", [install_result])
        executable_results = check_executables(EXECUTABLES)
        print_results("MODFLOW executables (after install attempt)", executable_results)
    elif auto_install_enabled:
        flopy_ok = any(item.name == "flopy" and item.ok for item in package_results)
        missing_exes_now = [item.name for item in executable_results if not item.ok]
        if flopy_ok and missing_exes_now:
            install_result = try_install_modflow_binaries()
            print_results("Auto-install MODFLOW executables", [install_result])
            executable_results = check_executables(EXECUTABLES)
            print_results("MODFLOW executables (after auto-install)", executable_results)

    print("\nRecommended install commands and links")
    for line in build_install_recommendations(os_family):
        print(f"- {line}")

    missing_packages = [item.name for item in package_results if not item.ok]
    missing_exes = [item.name for item in executable_results if not item.ok]

    if runtime_result.ok and not missing_packages and not missing_exes:
        print("\nEnvironment looks ready for B1/C1 model work.")
        return 0

    print("\nEnvironment is not fully ready yet.")
    if missing_packages:
        print(f"Missing Python packages: {', '.join(missing_packages)}")
    if missing_exes:
        print(f"Missing MODFLOW executables in PATH: {', '.join(missing_exes)}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
