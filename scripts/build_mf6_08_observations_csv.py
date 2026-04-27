"""Build and run B8: MF6 observations/time series and CSV diagnostics.

Usage:
  python scripts/build_mf6_08_observations_csv.py
  python scripts/build_mf6_08_observations_csv.py --workspace /tmp/mf6_b8
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT_ROOT / "models" / "mf6" / "08_observations_csv"
SIM_NAME = "mf6_08_observations_csv"
GWF_NAME = "gwf"


def _build_chd_spd(nrow: int, ncol: int) -> list[tuple[tuple[int, int, int], float]]:
    chd_spd: list[tuple[tuple[int, int, int], float]] = []
    for r in range(nrow):
        chd_spd.append(((0, r, 0), 10.0))
        chd_spd.append(((0, r, ncol - 1), 0.0))
    return chd_spd


def build_simulation(
    workspace: Path,
    sim_name: str = SIM_NAME,
    gwf_name: str = GWF_NAME,
    pumping_rate: float = -500.0,
    well_row: int = 5,
    well_col: int = 5,
) -> flopy.mf6.MFSimulation:
    """Create B8 transient model with head observations exported to CSV."""
    workspace.mkdir(parents=True, exist_ok=True)

    sim = flopy.mf6.MFSimulation(sim_name=sim_name, sim_ws=str(workspace), exe_name="mf6")

    perioddata = [
        (1.0, 1, 1.0),
        (30.0, 30, 1.0),
        (30.0, 30, 1.0),
    ]
    flopy.mf6.ModflowTdis(sim, nper=3, perioddata=perioddata, time_units="DAYS")
    flopy.mf6.ModflowIms(sim, complexity="SIMPLE", linear_acceleration="CG")

    gwf = flopy.mf6.ModflowGwf(sim, modelname=gwf_name, save_flows=True)

    nlay, nrow, ncol = 1, 10, 10
    flopy.mf6.ModflowGwfdis(
        gwf,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=100.0,
        delc=100.0,
        top=10.0,
        botm=0.0,
    )
    flopy.mf6.ModflowGwfic(gwf, strt=np.full((nlay, nrow, ncol), 5.0, dtype=float))
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=10.0, save_specific_discharge=True)
    flopy.mf6.ModflowGwfsto(
        gwf,
        iconvert=0,
        ss=1.0e-5,
        sy=0.15,
        steady_state={0: True},
        transient={1: True, 2: True},
    )

    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=_build_chd_spd(nrow=nrow, ncol=ncol))

    wel_spd = {
        0: [((0, well_row, well_col), 0.0)],
        1: [((0, well_row, well_col), pumping_rate)],
        2: [((0, well_row, well_col), 0.0)],
    }
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data=wel_spd)

    obs_records = [
        ("h_center", "HEAD", (0, well_row, well_col)),
        ("h_upgradient", "HEAD", (0, 5, 2)),
        ("h_downgradient", "HEAD", (0, 5, 8)),
    ]
    flopy.mf6.ModflowUtlobs(
        gwf,
        pname="obs",
        filename=f"{gwf_name}.obs",
        print_input=True,
        continuous={"head_observations.csv": obs_records},
    )

    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=f"{sim_name}.hds",
        budget_filerecord=f"{sim_name}.cbc",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
        printrecord=[("BUDGET", "LAST")],
    )

    return sim


def _budget_residual_percent(*list_files: Path) -> float | None:
    marker = "PERCENT DISCREPANCY"
    float_pattern = re.compile(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?")

    for list_file in list_files:
        if not list_file.exists():
            continue
        lines = list_file.read_text(encoding="utf-8", errors="ignore").splitlines()
        for idx, line in enumerate(lines):
            if marker not in line.upper():
                continue
            same_line_matches = float_pattern.findall(line)
            if same_line_matches:
                for token in reversed(same_line_matches):
                    try:
                        return float(token)
                    except ValueError:
                        continue
            for next_line in lines[idx + 1 : idx + 8]:
                matches = float_pattern.findall(next_line)
                if matches:
                    for token in reversed(matches):
                        try:
                            return float(token)
                        except ValueError:
                            continue
    return None


def _load_obs_csv(obs_csv_path: Path) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    data = np.genfromtxt(obs_csv_path, delimiter=",", names=True, dtype=float, encoding="utf-8")
    if data.dtype.names is None or len(data.dtype.names) < 2:
        raise RuntimeError(f"Could not parse observations CSV: {obs_csv_path}")

    names = list(data.dtype.names)
    time = np.asarray(data[names[0]], dtype=float)
    series = {name: np.asarray(data[name], dtype=float) for name in names[1:]}
    return time, series


def _closest_value_at_time(time: np.ndarray, values: np.ndarray, target: float) -> float:
    idx = int(np.argmin(np.abs(time - target)))
    return float(values[idx])


def _compute_diagnostics(time: np.ndarray, center: np.ndarray) -> list[dict[str, str]]:
    h_start = float(center[0])
    h_end_pumping = _closest_value_at_time(time, center, 31.0)
    h_end_recovery = float(center[-1])

    drawdown_end_pumping = h_start - h_end_pumping
    residual_drawdown = h_start - h_end_recovery

    pumping_mask = (time > 1.0) & (time <= 31.0)
    recovery_mask = time > 31.0

    pumping_diffs = np.diff(center[pumping_mask]) if np.count_nonzero(pumping_mask) > 1 else np.array([], dtype=float)
    recovery_diffs = np.diff(center[recovery_mask]) if np.count_nonzero(recovery_mask) > 1 else np.array([], dtype=float)

    pumping_nonincreasing_share = float(np.mean(pumping_diffs <= 1.0e-10)) if pumping_diffs.size else float("nan")
    recovery_nondecreasing_share = float(np.mean(recovery_diffs >= -1.0e-10)) if recovery_diffs.size else float("nan")

    min_idx = int(np.argmin(center))
    return [
        {
            "metric": "start_head",
            "value": f"{h_start:.6f}",
            "unit": "m",
            "description": "Center head at first output time.",
        },
        {
            "metric": "head_end_pumping",
            "value": f"{h_end_pumping:.6f}",
            "unit": "m",
            "description": "Center head near end of SP2 (t≈31 days).",
        },
        {
            "metric": "head_end_recovery",
            "value": f"{h_end_recovery:.6f}",
            "unit": "m",
            "description": "Center head at final output time.",
        },
        {
            "metric": "drawdown_end_pumping",
            "value": f"{drawdown_end_pumping:.6f}",
            "unit": "m",
            "description": "Drawdown at end of pumping relative to start head.",
        },
        {
            "metric": "residual_drawdown_end_recovery",
            "value": f"{residual_drawdown:.6f}",
            "unit": "m",
            "description": "Residual drawdown at simulation end relative to start head.",
        },
        {
            "metric": "min_center_head",
            "value": f"{float(np.min(center)):.6f}",
            "unit": "m",
            "description": f"Minimum center head over full transient at t={float(time[min_idx]):.2f} days.",
        },
        {
            "metric": "pumping_nonincreasing_share",
            "value": f"{pumping_nonincreasing_share:.6f}",
            "unit": "fraction",
            "description": "Share of pumping interval steps with non-increasing center head.",
        },
        {
            "metric": "recovery_nondecreasing_share",
            "value": f"{recovery_nondecreasing_share:.6f}",
            "unit": "fraction",
            "description": "Share of recovery interval steps with non-decreasing center head.",
        },
    ]


def _save_obs_plot(time: np.ndarray, series: dict[str, np.ndarray], plot_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 4.5), dpi=120, constrained_layout=True)
    for name, values in series.items():
        ax.plot(time, values, linewidth=2, label=name)

    ax.axvline(1.0, color="gray", linestyle="--", linewidth=1)
    ax.axvline(31.0, color="gray", linestyle="--", linewidth=1)
    ax.set_title("Head observations time series")
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Head")
    ax.grid(alpha=0.25)
    ax.legend(loc="best")
    fig.savefig(plot_path)
    plt.close(fig)


def run_b8_model(
    workspace: Path = WORKSPACE,
    sim_name: str = SIM_NAME,
    gwf_name: str = GWF_NAME,
    pumping_rate: float = -500.0,
    well_row: int = 5,
    well_col: int = 5,
) -> dict[str, Path | float | None]:
    workspace.mkdir(parents=True, exist_ok=True)

    sim = build_simulation(
        workspace=workspace,
        sim_name=sim_name,
        gwf_name=gwf_name,
        pumping_rate=pumping_rate,
        well_row=well_row,
        well_col=well_col,
    )
    sim.write_simulation()

    success, output = sim.run_simulation(silent=True, report=True)
    if not success:
        tail = "\n".join(output[-20:])
        raise RuntimeError(f"MODFLOW 6 run failed. Output tail:\n{tail}")

    hds_path = workspace / f"{sim_name}.hds"
    cbc_path = workspace / f"{sim_name}.cbc"
    lst_path = workspace / "mfsim.lst"
    gwf_lst_path = workspace / f"{gwf_name}.lst"
    sim_nam_path = workspace / "mfsim.nam"
    obs_csv_path = workspace / "head_observations.csv"
    diagnostics_csv_path = workspace / "observations_diagnostics.csv"
    obs_plot_path = workspace / "observations_timeseries.png"
    summary_path = workspace / "run_summary.txt"

    if not obs_csv_path.exists():
        raise RuntimeError(f"Observation CSV was not produced: {obs_csv_path}")

    time, series = _load_obs_csv(obs_csv_path)
    center_key = next((k for k in series if k.upper() == "H_CENTER"), None)
    if center_key is None:
        raise RuntimeError("Could not locate H_CENTER series in observation CSV.")

    diagnostics = _compute_diagnostics(time=time, center=series[center_key])
    with diagnostics_csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["metric", "value", "unit", "description"])
        writer.writeheader()
        writer.writerows(diagnostics)

    _save_obs_plot(time=time, series=series, plot_path=obs_plot_path)

    residual_pct = _budget_residual_percent(lst_path, gwf_lst_path)

    summary_lines = [
        "B8 transient model with UTL-OBS observations and CSV diagnostics (MODFLOW 6)",
        f"Workspace: {workspace}",
        f"Simulation name file: {sim_nam_path}",
        "Observation points: center, upgradient, downgradient (row 5)",
        "Stress periods: SP1 steady (1 day), SP2 pumping (30 days), SP3 recovery (30 days)",
        f"Boundary conditions: CHD left=10/right=0; WEL(center) SP2={pumping_rate:.2f}",
        f"Well location (layer,row,col): (0, {well_row}, {well_col})",
        "Budget percent discrepancy (%): " + (f"{residual_pct:.6f}" if residual_pct is not None else "not parsed"),
        f"Observation CSV: {obs_csv_path}",
        f"Diagnostics CSV: {diagnostics_csv_path}",
        f"Observation plot: {obs_plot_path}",
        f"List file: {lst_path}",
        f"Head file: {hds_path}",
        f"Budget file: {cbc_path}",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "workspace": workspace,
        "sim_nam_path": sim_nam_path,
        "hds_path": hds_path,
        "cbc_path": cbc_path,
        "lst_path": lst_path,
        "gwf_lst_path": gwf_lst_path,
        "obs_csv_path": obs_csv_path,
        "diagnostics_csv_path": diagnostics_csv_path,
        "obs_plot_path": obs_plot_path,
        "summary_path": summary_path,
        "residual_pct": residual_pct,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--sim-name", default=SIM_NAME)
    parser.add_argument("--gwf-name", default=GWF_NAME)
    parser.add_argument("--pumping-rate", type=float, default=-500.0)
    parser.add_argument("--well-row", type=int, default=5)
    parser.add_argument("--well-col", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_b8_model(
        workspace=args.workspace,
        sim_name=args.sim_name,
        gwf_name=args.gwf_name,
        pumping_rate=args.pumping_rate,
        well_row=args.well_row,
        well_col=args.well_col,
    )
    print("B8 MF6 observations/time-series model built and executed successfully.")
    print(f"Workspace: {result['workspace']}")
    print(f"Observation CSV: {result['obs_csv_path']}")
    print(f"Diagnostics CSV: {result['diagnostics_csv_path']}")
    print(f"Observation plot: {result['obs_plot_path']}")
    print(f"Summary: {result['summary_path']}")
