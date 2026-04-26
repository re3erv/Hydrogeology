"""Build and run B1: first steady-state confined MODFLOW 6 model.

Usage:
  python scripts/build_mf6_01_confined.py
  python scripts/build_mf6_01_confined.py --workspace /tmp/mf6_b1
"""

from __future__ import annotations

import argparse
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT_ROOT / "models" / "mf6" / "01_confined_steady"
SIM_NAME = "mf6_01_confined"
GWF_NAME = "gwf"


def build_simulation(workspace: Path, sim_name: str = SIM_NAME, gwf_name: str = GWF_NAME) -> flopy.mf6.MFSimulation:
    """Create the MF6 steady-state confined flow simulation for stage B1."""
    workspace.mkdir(parents=True, exist_ok=True)

    sim = flopy.mf6.MFSimulation(sim_name=sim_name, sim_ws=str(workspace), exe_name="mf6")

    flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)], time_units="DAYS")
    flopy.mf6.ModflowIms(sim, complexity="SIMPLE", linear_acceleration="CG")

    gwf = flopy.mf6.ModflowGwf(sim, modelname=gwf_name, save_flows=True)

    nlay, nrow, ncol = 1, 10, 10
    delr = np.full(ncol, 100.0, dtype=float)
    delc = np.full(nrow, 100.0, dtype=float)
    top = np.full((nrow, ncol), 10.0, dtype=float)
    botm = np.full((nlay, nrow, ncol), 0.0, dtype=float)

    flopy.mf6.ModflowGwfdis(
        gwf,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
    )

    flopy.mf6.ModflowGwfic(gwf, strt=np.full((nlay, nrow, ncol), 5.0, dtype=float))
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=10.0)

    chd_spd = []
    for r in range(nrow):
        chd_spd.append(((0, r, 0), 10.0))
        chd_spd.append(((0, r, ncol - 1), 0.0))
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chd_spd)

    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=f"{sim_name}.hds",
        budget_filerecord=f"{sim_name}.cbc",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
        printrecord=[("BUDGET", "LAST")],
    )

    return sim


def _save_head_map(heads: np.ndarray, out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    im = ax.imshow(heads[0], origin="upper", cmap="viridis")
    ax.set_title("B1 confined steady-state heads (MF6)")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.colorbar(im, ax=ax, label="Head")
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def _budget_residual_percent(list_file: Path) -> float | None:
    lines = list_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    marker = "PERCENT DISCREPANCY"
    for idx, line in enumerate(lines):
        if marker in line:
            for next_line in lines[idx + 1 : idx + 5]:
                chunks = next_line.split()
                if chunks:
                    for token in reversed(chunks):
                        try:
                            return float(token)
                        except ValueError:
                            continue
    return None


def _linearity_metrics(heads: np.ndarray) -> tuple[float, float]:
    row_profile = np.mean(heads[0], axis=0)
    expected = np.linspace(row_profile[0], row_profile[-1], row_profile.size)
    max_abs_deviation = float(np.max(np.abs(row_profile - expected)))
    rmse = float(np.sqrt(np.mean((row_profile - expected) ** 2)))
    return max_abs_deviation, rmse


def run_b1_model(workspace: Path = WORKSPACE, sim_name: str = SIM_NAME, gwf_name: str = GWF_NAME) -> dict[str, Path | float | None]:
    sim = build_simulation(workspace=workspace, sim_name=sim_name, gwf_name=gwf_name)
    sim.write_simulation()

    success, output = sim.run_simulation(silent=True, report=True)
    if not success:
        tail = "\n".join(output[-20:])
        raise RuntimeError(f"MODFLOW 6 run failed. Output tail:\n{tail}")

    hds_path = workspace / f"{sim_name}.hds"
    cbc_path = workspace / f"{sim_name}.cbc"
    lst_path = workspace / "mfsim.lst"
    sim_nam_path = workspace / "mfsim.nam"
    png_path = workspace / "heads_map.png"
    summary_path = workspace / "run_summary.txt"

    heads = flopy.utils.HeadFile(str(hds_path)).get_data(kstpkper=(0, 0))
    _save_head_map(heads, png_path)

    left_mean = float(np.mean(heads[0, :, 0]))
    right_mean = float(np.mean(heads[0, :, -1]))
    residual_pct = _budget_residual_percent(lst_path)
    linearity_max_dev, linearity_rmse = _linearity_metrics(heads)

    summary_lines = [
        "B1 first steady-state confined model (MODFLOW 6)",
        f"Workspace: {workspace}",
        f"Simulation name file: {sim_nam_path}",
        f"Head left boundary mean: {left_mean:.4f}",
        f"Head right boundary mean: {right_mean:.4f}",
        "Budget percent discrepancy (%): " + (f"{residual_pct:.6f}" if residual_pct is not None else "not parsed"),
        f"Linearity max abs deviation: {linearity_max_dev:.6f}",
        f"Linearity RMSE: {linearity_rmse:.6f}",
        f"List file: {lst_path}",
        f"Head file: {hds_path}",
        f"Budget file: {cbc_path}",
        f"Head map: {png_path}",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "workspace": workspace,
        "sim_nam_path": sim_nam_path,
        "hds_path": hds_path,
        "cbc_path": cbc_path,
        "lst_path": lst_path,
        "png_path": png_path,
        "summary_path": summary_path,
        "residual_pct": residual_pct,
        "linearity_max_dev": linearity_max_dev,
        "linearity_rmse": linearity_rmse,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--sim-name", default=SIM_NAME)
    parser.add_argument("--gwf-name", default=GWF_NAME)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_b1_model(workspace=args.workspace, sim_name=args.sim_name, gwf_name=args.gwf_name)
    print("B1 MF6 model built and executed successfully.")
    print(f"Workspace: {result['workspace']}")
    print(f"Simulation name file: {result['sim_nam_path']}")
    if result["residual_pct"] is None:
        print("Budget residual (%): not parsed from list file")
    else:
        print(f"Budget residual (%): {result['residual_pct']:.6f}")
    print(f"Linearity max abs deviation: {result['linearity_max_dev']:.6f}")
    print(f"Linearity RMSE: {result['linearity_rmse']:.6f}")
