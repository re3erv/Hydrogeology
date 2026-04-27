"""Build and run B7: transient MF6 model with STO package.

Usage:
  python scripts/build_mf6_07_transient_sto.py
  python scripts/build_mf6_07_transient_sto.py --workspace /tmp/mf6_b7
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT_ROOT / "models" / "mf6" / "07_transient_sto"
SIM_NAME = "mf6_07_transient_sto"
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
    """Create B7 transient model with storage and pumping/recovery phases."""
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

    # Keep B7 as a confined transient storage exercise (introductory STO setup).
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


def _save_plots(
    times: np.ndarray,
    center_heads: np.ndarray,
    heads_p1_end: np.ndarray,
    heads_p2_end: np.ndarray,
    heads_p3_end: np.ndarray,
    ts_png: Path,
    dd_png: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4), dpi=120, constrained_layout=True)
    ax.plot(times, center_heads, color="tab:blue", linewidth=2)
    ax.axvline(1.0, color="gray", linestyle="--", linewidth=1)
    ax.axvline(31.0, color="gray", linestyle="--", linewidth=1)
    ax.set_title("Center head transient response (STO)")
    ax.set_xlabel("Time (days)")
    ax.set_ylabel("Head")
    ax.grid(alpha=0.25)
    fig.savefig(ts_png)
    plt.close(fig)

    baseline = heads_p1_end
    dd_p2 = baseline - heads_p2_end
    dd_p3 = baseline - heads_p3_end
    vmax = max(float(np.max(dd_p2)), float(np.max(dd_p3)))

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), dpi=120, constrained_layout=True)
    im1 = axes[0].imshow(dd_p2, origin="upper", cmap="magma", vmin=0.0, vmax=vmax)
    axes[0].set_title("Drawdown at end of pumping (SP2)")
    axes[0].set_xlabel("Column")
    axes[0].set_ylabel("Row")

    im2 = axes[1].imshow(dd_p3, origin="upper", cmap="magma", vmin=0.0, vmax=vmax)
    axes[1].set_title("Residual drawdown after recovery (SP3)")
    axes[1].set_xlabel("Column")
    axes[1].set_ylabel("Row")

    fig.colorbar(im1, ax=axes.ravel().tolist(), label="Drawdown")
    fig.savefig(dd_png)
    plt.close(fig)


def _period_end_indices(hds: flopy.utils.HeadFile) -> dict[int, int]:
    """Return {kper: last_output_index_for_period} from HeadFile records."""
    period_to_last_idx: dict[int, int] = {}
    for idx, (_kstp, kper) in enumerate(hds.get_kstpkper()):
        period_to_last_idx[int(kper)] = idx
    return period_to_last_idx


def run_b7_model(
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
    ts_png_path = workspace / "heads_timeseries.png"
    dd_png_path = workspace / "drawdown_transient_maps.png"
    summary_path = workspace / "run_summary.txt"

    hds = flopy.utils.HeadFile(str(hds_path))
    times = np.asarray(hds.get_times(), dtype=float)
    heads_all = hds.get_alldata()[:, 0, :, :]
    period_last = _period_end_indices(hds)
    required_periods = (0, 1, 2)
    missing_periods = [kper for kper in required_periods if kper not in period_last]
    if missing_periods:
        raise RuntimeError(f"Could not find output snapshots for periods: {missing_periods}")

    center_heads = heads_all[:, well_row, well_col]
    heads_p1_end = heads_all[period_last[0]]
    heads_p2_end = heads_all[period_last[1]]
    heads_p3_end = heads_all[period_last[2]]

    _save_plots(
        times=times,
        center_heads=center_heads,
        heads_p1_end=heads_p1_end,
        heads_p2_end=heads_p2_end,
        heads_p3_end=heads_p3_end,
        ts_png=ts_png_path,
        dd_png=dd_png_path,
    )

    max_dd_p2 = float(np.max(heads_p1_end - heads_p2_end))
    max_dd_p3 = float(np.max(heads_p1_end - heads_p3_end))
    center_min_head = float(np.min(center_heads))
    center_recovered_head = float(center_heads[-1])
    residual_pct = _budget_residual_percent(lst_path, gwf_lst_path)

    summary_lines = [
        "B7 transient model with storage package STO (MODFLOW 6)",
        f"Workspace: {workspace}",
        f"Simulation name file: {sim_nam_path}",
        "Grid: 1 layer, 10x10 cells, top=10, botm=0, delr=delc=100",
        "Hydraulic properties: K=10, icelltype=0, SS=1e-5, SY=0.15, iconvert=0",
        "Stress periods: SP1 steady (1 day), SP2 transient pumping (30 days), SP3 transient recovery (30 days)",
        f"Boundary conditions: CHD left=10/right=0; WEL(center) SP2={pumping_rate:.2f}",
        f"Well location (layer,row,col): (0, {well_row}, {well_col})",
        f"Center head min during pumping/recovery: {center_min_head:.6f}",
        f"Center head at end of recovery: {center_recovered_head:.6f}",
        f"Max drawdown at SP2 end: {max_dd_p2:.6f}",
        f"Residual max drawdown at SP3 end: {max_dd_p3:.6f}",
        "Budget percent discrepancy (%): " + (f"{residual_pct:.6f}" if residual_pct is not None else "not parsed"),
        f"List file: {lst_path}",
        f"Head file: {hds_path}",
        f"Budget file: {cbc_path}",
        f"Heads time-series plot: {ts_png_path}",
        f"Transient drawdown maps: {dd_png_path}",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "workspace": workspace,
        "sim_nam_path": sim_nam_path,
        "hds_path": hds_path,
        "cbc_path": cbc_path,
        "lst_path": lst_path,
        "gwf_lst_path": gwf_lst_path,
        "timeseries_png_path": ts_png_path,
        "drawdown_png_path": dd_png_path,
        "summary_path": summary_path,
        "center_min_head": center_min_head,
        "center_recovered_head": center_recovered_head,
        "max_dd_p2": max_dd_p2,
        "max_dd_p3": max_dd_p3,
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
    result = run_b7_model(
        workspace=args.workspace,
        sim_name=args.sim_name,
        gwf_name=args.gwf_name,
        pumping_rate=args.pumping_rate,
        well_row=args.well_row,
        well_col=args.well_col,
    )
    print("B7 MF6 transient STO model built and executed successfully.")
    print(f"Workspace: {result['workspace']}")
    print(f"Head time-series: {result['timeseries_png_path']}")
    print(f"Transient drawdown maps: {result['drawdown_png_path']}")
    print(f"Summary: {result['summary_path']}")
