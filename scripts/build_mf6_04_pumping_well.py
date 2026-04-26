"""Build and run B4: steady-state confined MODFLOW 6 model with pumping well (WEL).

Usage:
  python scripts/build_mf6_04_pumping_well.py
  python scripts/build_mf6_04_pumping_well.py --workspace /tmp/mf6_b4
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT_ROOT / "models" / "mf6" / "04_pumping_well"
SIM_NAME = "mf6_04_pumping_well"
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
    """Create the MF6 steady-state confined flow simulation for stage B4."""
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

    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=_build_chd_spd(nrow=nrow, ncol=ncol))
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data=[((0, well_row, well_col), pumping_rate)])

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
                if not matches:
                    continue
                for token in reversed(matches):
                    try:
                        return float(token)
                    except ValueError:
                        continue

    return None


def _save_maps(heads: np.ndarray, drawdown: np.ndarray, out_heads_png: Path, out_drawdown_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    im = ax.imshow(heads[0], origin="upper", cmap="viridis")
    ax.set_title("B4 pumping well (WEL): heads (MF6)")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.colorbar(im, ax=ax, label="Head")
    fig.tight_layout()
    fig.savefig(out_heads_png)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    im = ax.imshow(drawdown[0], origin="upper", cmap="magma")
    ax.set_title("B4 drawdown map: baseline - pumped")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.colorbar(im, ax=ax, label="Drawdown")
    fig.tight_layout()
    fig.savefig(out_drawdown_png)
    plt.close(fig)


def _run_single(
    workspace: Path,
    sim_name: str,
    gwf_name: str,
    pumping_rate: float,
    well_row: int,
    well_col: int,
) -> np.ndarray:
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
        raise RuntimeError(f"MODFLOW 6 run failed for {sim_name}. Output tail:\n{tail}")

    hds_path = workspace / f"{sim_name}.hds"
    return flopy.utils.HeadFile(str(hds_path)).get_data(kstpkper=(0, 0))


def run_b4_model(
    workspace: Path = WORKSPACE,
    sim_name: str = SIM_NAME,
    gwf_name: str = GWF_NAME,
    pumping_rate: float = -500.0,
    well_row: int = 5,
    well_col: int = 5,
) -> dict[str, Path | float | int | None]:
    workspace.mkdir(parents=True, exist_ok=True)

    baseline_name = f"{sim_name}_baseline"
    pumped_name = sim_name

    baseline_heads = _run_single(
        workspace=workspace,
        sim_name=baseline_name,
        gwf_name=gwf_name,
        pumping_rate=0.0,
        well_row=well_row,
        well_col=well_col,
    )
    pumped_heads = _run_single(
        workspace=workspace,
        sim_name=pumped_name,
        gwf_name=gwf_name,
        pumping_rate=pumping_rate,
        well_row=well_row,
        well_col=well_col,
    )

    drawdown = baseline_heads - pumped_heads

    hds_path = workspace / f"{pumped_name}.hds"
    cbc_path = workspace / f"{pumped_name}.cbc"
    lst_path = workspace / "mfsim.lst"
    gwf_lst_path = workspace / f"{gwf_name}.lst"
    sim_nam_path = workspace / "mfsim.nam"
    heads_png_path = workspace / "heads_map.png"
    drawdown_png_path = workspace / "drawdown_map.png"
    summary_path = workspace / "run_summary.txt"

    _save_maps(pumped_heads, drawdown, heads_png_path, drawdown_png_path)

    residual_pct = _budget_residual_percent(lst_path, gwf_lst_path)
    left_mean = float(np.mean(pumped_heads[0, :, 0]))
    right_mean = float(np.mean(pumped_heads[0, :, -1]))
    well_head = float(pumped_heads[0, well_row, well_col])
    max_dd_idx = np.unravel_index(np.argmax(drawdown[0]), drawdown[0].shape)
    max_drawdown = float(drawdown[0][max_dd_idx])

    summary_lines = [
        "B4 steady-state confined model with pumping well WEL and drawdown (MODFLOW 6)",
        f"Workspace: {workspace}",
        f"Simulation name file: {sim_nam_path}",
        f"Pumping rate (WEL): {pumping_rate:.6f}",
        f"Well cell (row, col): ({well_row}, {well_col})",
        f"Pumped run left boundary mean head: {left_mean:.4f}",
        f"Pumped run right boundary mean head: {right_mean:.4f}",
        f"Pumped run well-cell head: {well_head:.6f}",
        f"Max drawdown (baseline - pumped): {max_drawdown:.6f}",
        f"Max drawdown cell (row, col): ({int(max_dd_idx[0])}, {int(max_dd_idx[1])})",
        "Budget percent discrepancy (%): " + (f"{residual_pct:.6f}" if residual_pct is not None else "not parsed"),
        f"List file: {lst_path}",
        f"Head file: {hds_path}",
        f"Budget file: {cbc_path}",
        f"Head map: {heads_png_path}",
        f"Drawdown map: {drawdown_png_path}",
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
        "drawdown_png_path": drawdown_png_path,
        "summary_path": summary_path,
        "residual_pct": residual_pct,
        "max_drawdown": max_drawdown,
        "max_drawdown_row": int(max_dd_idx[0]),
        "max_drawdown_col": int(max_dd_idx[1]),
        "well_head": well_head,
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
    result = run_b4_model(
        workspace=args.workspace,
        sim_name=args.sim_name,
        gwf_name=args.gwf_name,
        pumping_rate=args.pumping_rate,
        well_row=args.well_row,
        well_col=args.well_col,
    )
    print("B4 MF6 model (pumping well + drawdown) built and executed successfully.")
    print(f"Workspace: {result['workspace']}")
    print(f"Simulation name file: {result['sim_nam_path']}")
    if result["residual_pct"] is None:
        print("Budget residual (%): not parsed from list file")
    else:
        print(f"Budget residual (%): {result['residual_pct']:.6f}")
    print(f"Well-cell head: {result['well_head']:.6f}")
    print(f"Max drawdown: {result['max_drawdown']:.6f} at ({result['max_drawdown_row']}, {result['max_drawdown_col']})")
