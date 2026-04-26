"""Build and run B3: steady-state confined MODFLOW 6 model with recharge (RCHA).

Usage:
  python scripts/build_mf6_03_recharge.py
  python scripts/build_mf6_03_recharge.py --workspace /tmp/mf6_b3
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT_ROOT / "models" / "mf6" / "03_recharge"
SIM_NAME = "mf6_03_recharge"
GWF_NAME = "gwf"


def build_simulation(
    workspace: Path,
    sim_name: str = SIM_NAME,
    gwf_name: str = GWF_NAME,
    recharge_rate: float = 1.0e-4,
) -> flopy.mf6.MFSimulation:
    """Create the MF6 steady-state confined flow simulation for stage B3."""
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

    recharge_array = np.full((nrow, ncol), recharge_rate, dtype=float)
    flopy.mf6.ModflowGwfrcha(gwf, recharge=recharge_array)

    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=f"{sim_name}.hds",
        budget_filerecord=f"{sim_name}.cbc",
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
        printrecord=[("BUDGET", "LAST")],
    )

    return sim


def _save_maps(heads: np.ndarray, recharge_rate: float, out_heads_png: Path, out_recharge_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    im = ax.imshow(heads[0], origin="upper", cmap="viridis")
    ax.set_title("B3 recharge (RCHA): heads (MF6)")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.colorbar(im, ax=ax, label="Head")
    fig.tight_layout()
    fig.savefig(out_heads_png)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    recharge_plot = np.full(heads.shape[1:], recharge_rate, dtype=float)
    im = ax.imshow(recharge_plot, origin="upper", cmap="Blues")
    ax.set_title("B3 recharge field RCHA")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.colorbar(im, ax=ax, label="Recharge")
    fig.tight_layout()
    fig.savefig(out_recharge_png)
    plt.close(fig)


def _budget_residual_percent(*list_files: Path) -> float | None:
    """Parse percent discrepancy from one or more MF6 list files."""
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
                if not matches:
                    continue
                for token in reversed(matches):
                    try:
                        return float(token)
                    except ValueError:
                        continue

    return None


def _recharge_mound_metrics(heads: np.ndarray) -> tuple[float, int, int]:
    """Return max interior head rise above a no-recharge linear baseline."""
    head2d = heads[0]

    left = head2d[:, [0]]
    right = head2d[:, [-1]]
    ncol = head2d.shape[1]
    linear_baseline = np.linspace(0.0, 1.0, ncol)[None, :] * (right - left) + left

    deviation = head2d - linear_baseline
    if ncol > 2:
        deviation[:, 0] = -np.inf
        deviation[:, -1] = -np.inf

    peak_idx = np.unravel_index(np.argmax(deviation), deviation.shape)
    peak_rise = float(deviation[peak_idx])
    return peak_rise, int(peak_idx[0]), int(peak_idx[1])


def run_b3_model(
    workspace: Path = WORKSPACE,
    sim_name: str = SIM_NAME,
    gwf_name: str = GWF_NAME,
    recharge_rate: float = 1.0e-4,
) -> dict[str, Path | float | int | None]:
    sim = build_simulation(workspace=workspace, sim_name=sim_name, gwf_name=gwf_name, recharge_rate=recharge_rate)
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
    heads_png_path = workspace / "heads_map.png"
    recharge_png_path = workspace / "recharge_map.png"
    summary_path = workspace / "run_summary.txt"

    heads = flopy.utils.HeadFile(str(hds_path)).get_data(kstpkper=(0, 0))
    _save_maps(heads, recharge_rate, heads_png_path, recharge_png_path)

    left_mean = float(np.mean(heads[0, :, 0]))
    right_mean = float(np.mean(heads[0, :, -1]))
    residual_pct = _budget_residual_percent(lst_path, gwf_lst_path)
    center_rise, peak_row, peak_col = _recharge_mound_metrics(heads)

    summary_lines = [
        "B3 steady-state confined model with areal recharge (MODFLOW 6)",
        f"Workspace: {workspace}",
        f"Simulation name file: {sim_nam_path}",
        f"Recharge rate (RCHA): {recharge_rate:.6e}",
        f"Head left boundary mean: {left_mean:.4f}",
        f"Head right boundary mean: {right_mean:.4f}",
        "Budget percent discrepancy (%): " + (f"{residual_pct:.6f}" if residual_pct is not None else "not parsed"),
        f"Peak recharge-mound cell (row, col): ({peak_row}, {peak_col})",
        f"Max interior rise above no-recharge linear baseline: {center_rise:.6f}",
        f"List file: {lst_path}",
        f"Head file: {hds_path}",
        f"Budget file: {cbc_path}",
        f"Head map: {heads_png_path}",
        f"Recharge map: {recharge_png_path}",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "workspace": workspace,
        "sim_nam_path": sim_nam_path,
        "hds_path": hds_path,
        "cbc_path": cbc_path,
        "lst_path": lst_path,
        "gwf_lst_path": gwf_lst_path,
        "heads_png_path": heads_png_path,
        "recharge_png_path": recharge_png_path,
        "summary_path": summary_path,
        "residual_pct": residual_pct,
        "center_rise": center_rise,
        "peak_row": peak_row,
        "peak_col": peak_col,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--sim-name", default=SIM_NAME)
    parser.add_argument("--gwf-name", default=GWF_NAME)
    parser.add_argument("--recharge-rate", type=float, default=1.0e-4)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_b3_model(
        workspace=args.workspace,
        sim_name=args.sim_name,
        gwf_name=args.gwf_name,
        recharge_rate=args.recharge_rate,
    )
    print("B3 MF6 model (recharge RCHA) built and executed successfully.")
    print(f"Workspace: {result['workspace']}")
    print(f"Simulation name file: {result['sim_nam_path']}")
    if result["residual_pct"] is None:
        print("Budget residual (%): not parsed from list file")
    else:
        print(f"Budget residual (%): {result['residual_pct']:.6f}")
    print(f"Peak recharge-mound cell: ({result['peak_row']}, {result['peak_col']})")
    print(f"Max interior rise above no-recharge baseline: {result['center_rise']:.6f}")
