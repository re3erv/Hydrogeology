import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_environment.py"
SPEC = spec_from_file_location("check_environment", SCRIPT_PATH)
assert SPEC and SPEC.loader
check_environment = module_from_spec(SPEC)
sys.modules[SPEC.name] = check_environment
SPEC.loader.exec_module(check_environment)


build_install_recommendations = check_environment.build_install_recommendations
check_executables = check_environment.check_executables
check_python_packages = check_environment.check_python_packages
check_python_runtime = check_environment.check_python_runtime
build_pip_install_command = check_environment.build_pip_install_command


def test_core_python_packages_are_importable() -> None:
    results = check_python_packages(["sys", "json"])
    assert all(item.ok for item in results)


def test_missing_package_reports_install_hint() -> None:
    results = check_python_packages(["definitely_missing_package_xyz"])
    assert len(results) == 1
    assert results[0].ok is False
    assert "pip install" in results[0].detail


def test_executable_check_reports_missing_binary() -> None:
    results = check_executables(("definitely_missing_executable_xyz",))
    assert len(results) == 1
    assert results[0].ok is False


def test_recommendations_include_get_modflow() -> None:
    for os_name in ("linux", "macos", "windows"):
        recommendations = build_install_recommendations(os_name)
        assert any("flopy.utils.get_modflow" in line or "get-modflow :flopy" in line for line in recommendations)


def test_runtime_check_returns_named_result() -> None:
    result = check_python_runtime()
    assert result.name == "python"


def test_build_pip_install_command_uses_current_python() -> None:
    command = build_pip_install_command(["pytest", "flopy"])
    assert command[1:4] == ["-m", "pip", "install"]
    assert "pytest" in command and "flopy" in command
