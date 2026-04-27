"""Build and run B6: multilayer MF6 model with interlayer leakage diagnostics.

Usage:
  python scripts/build_mf6_06_multilayer_leakage.py
  python scripts/build_mf6_06_multilayer_leakage.py --workspace /tmp/mf6_b6
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np
from flopy.mf6.utils.postprocessing import get_structured_faceflows


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT_ROOT / "models" / "mf6" / "06_multilayer_leakage"
SIM_NAME = "mf6_06_multilayer_leakage"
GWF_NAME = "gwf"


def _build_chd_spd(nlay: int, nrow: int, ncol: int) -> list[tuple[tuple[int, int, int], float]]:
    chd_spd: list[tuple[tuple[int, int, int], float]] = []
    for k in range(nlay):
        for r in range(nrow):
            chd_spd.append(((k, r, 0), 10.0))
            chd_spd.append(((k, r, ncol - 1), 0.0))
    return chd_spd


def build_simulation(
    workspace: Path,
    sim_name: str = SIM_NAME,
    gwf_name: str = GWF_NAME,
    pumping_rate: float = -700.0,
    well_layer: int = 1,
    well_row: int = 5,
    well_col: int = 5,
) -> flopy.mf6.MFSimulation:
    """Create B6 steady-state multilayer model with vertical leakage."""
    workspace.mkdir(parents=True, exist_ok=True)

    sim = flopy.mf6.MFSimulation(sim_name=sim_name, sim_ws=str(workspace), exe_name="mf6")
    flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)], time_units="DAYS")
    flopy.mf6.ModflowIms(sim, complexity="SIMPLE", linear_acceleration="CG")

    gwf = flopy.mf6.ModflowGwf(sim, modelname=gwf_name, save_flows=True)

    nlay, nrow, ncol = 3, 10, 10
    delr = np.full(ncol, 100.0, dtype=float)
    delc = np.full(nrow, 100.0, dtype=float)
    top = np.full((nrow, ncol), 30.0, dtype=float)
    botm = np.array(
        [
            np.full((nrow, ncol), 20.0, dtype=float),
            np.full((nrow, ncol), 10.0, dtype=float),
            np.full((nrow, ncol), 0.0, dtype=float),
        ]
    )

    flopy.mf6.ModflowGwfdis(gwf, nlay=nlay, nrow=nrow, ncol=ncol, delr=delr, delc=delc, top=top, botm=botm)
    flopy.mf6.ModflowGwfic(gwf, strt=np.full((nlay, nrow, ncol), 5.0, dtype=float))

    # Upper and lower aquifers are more permeable than the middle layer.
    kh = np.array([10.0, 2.0, 10.0], dtype=float)
    kv = np.array([1.0, 0.05, 1.0], dtype=float)
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=kh, k33=kv, save_specific_discharge=True)

    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=_build_chd_spd(nlay=nlay, nrow=nrow, ncol=ncol))
    flopy.mf6.ModflowGwfrcha(gwf, recharge=1.0e-4)
    flopy.mf6.ModflowGwfwel(gwf, stress_period_data=[((well_layer, well_row, well_col), pumping_rate)])

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


def _save_maps(heads: np.ndarray, lower_face_flow: np.ndarray, heads_png: Path, leakage_png: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), dpi=120, constrained_layout=True)
    vmin = float(np.min(heads))
    vmax = float(np.max(heads))
    for k in range(3):
        im = axes[k].imshow(heads[k], origin="upper", cmap="viridis", vmin=vmin, vmax=vmax)
        axes[k].set_title(f"Head map layer {k + 1}")
        axes[k].set_xlabel("Column")
        axes[k].set_ylabel("Row")
    fig.colorbar(im, ax=axes.ravel().tolist(), label="Head")
    fig.savefig(heads_png)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), dpi=120, constrained_layout=True)
    labels = ["L1 -> L2", "L2 -> L3"]
    for i in range(2):
        flow = lower_face_flow[i]
        im = axes[i].imshow(flow, origin="upper", cmap="coolwarm")
        axes[i].set_title(f"Vertical leakage {labels[i]}")
        axes[i].set_xlabel("Column")
        axes[i].set_ylabel("Row")
        fig.colorbar(im, ax=axes[i], label="Flow")
    fig.savefig(leakage_png)
    plt.close(fig)


def run_b6_model(
    workspace: Path = WORKSPACE,
    sim_name: str = SIM_NAME,
    gwf_name: str = GWF_NAME,
    pumping_rate: float = -700.0,
    well_layer: int = 1,
    well_row: int = 5,
    well_col: int = 5,
) -> dict[str, Path | float | None]:
    workspace.mkdir(parents=True, exist_ok=True)

    sim = build_simulation(
        workspace=workspace,
        sim_name=sim_name,
        gwf_name=gwf_name,
        pumping_rate=pumping_rate,
        well_layer=well_layer,
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
    grb_path = workspace / f"{gwf_name}.dis.grb"
    lst_path = workspace / "mfsim.lst"
    gwf_lst_path = workspace / f"{gwf_name}.lst"
    sim_nam_path = workspace / "mfsim.nam"
    heads_png_path = workspace / "heads_layers_map.png"
    leakage_png_path = workspace / "vertical_leakage_map.png"
    summary_path = workspace / "run_summary.txt"

    heads = flopy.utils.HeadFile(str(hds_path)).get_data(kstpkper=(0, 0))

    cbc = flopy.utils.CellBudgetFile(str(cbc_path), precision="double")
    flow_ja = cbc.get_data(text="FLOW-JA-FACE")[-1].ravel()
    lower_face_flow = get_structured_faceflows(flow_ja, grb_file=str(grb_path))[2]

    _save_maps(heads, lower_face_flow, heads_png_path, leakage_png_path)

    l1_to_l2 = float(np.sum(lower_face_flow[0]))
    l2_to_l3 = float(np.sum(lower_face_flow[1]))
    center_heads = [float(heads[k, well_row, well_col]) for k in range(3)]
    residual_pct = _budget_residual_percent(lst_path, gwf_lst_path)

    summary_lines = [
        "B6 steady-state multilayer model with interlayer leakage (MODFLOW 6)",
        f"Workspace: {workspace}",
        f"Simulation name file: {sim_nam_path}",
        "Grid: 3 layers, 10x10 cells, top=30, botm=[20, 10, 0]",
        "Hydraulic conductivity by layer: kh=[10, 2, 10], kv=[1, 0.05, 1]",
        f"Boundary conditions: CHD left=10/right=0 on all layers, RCHA=1e-4, WEL={pumping_rate:.2f}",
        f"Well location (layer,row,col): ({well_layer}, {well_row}, {well_col})",
        f"Center heads by layer (L1,L2,L3): {center_heads[0]:.6f}, {center_heads[1]:.6f}, {center_heads[2]:.6f}",
        f"Net vertical flow L1->L2: {l1_to_l2:.6f}",
        f"Net vertical flow L2->L3: {l2_to_l3:.6f}",
        "Budget percent discrepancy (%): " + (f"{residual_pct:.6f}" if residual_pct is not None else "not parsed"),
        f"List file: {lst_path}",
        f"Head file: {hds_path}",
        f"Budget file: {cbc_path}",
        f"Heads map: {heads_png_path}",
        f"Vertical leakage map: {leakage_png_path}",
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
        "leakage_png_path": leakage_png_path,
        "summary_path": summary_path,
        "center_head_l2": center_heads[1],
        "l1_to_l2": l1_to_l2,
        "l2_to_l3": l2_to_l3,
        "residual_pct": residual_pct,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--sim-name", default=SIM_NAME)
    parser.add_argument("--gwf-name", default=GWF_NAME)
    parser.add_argument("--pumping-rate", type=float, default=-700.0)
    parser.add_argument("--well-layer", type=int, default=1)
    parser.add_argument("--well-row", type=int, default=5)
    parser.add_argument("--well-col", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_b6_model(
        workspace=args.workspace,
        sim_name=args.sim_name,
        gwf_name=args.gwf_name,
        pumping_rate=args.pumping_rate,
        well_layer=args.well_layer,
        well_row=args.well_row,
        well_col=args.well_col,
    )
    print("B6 MF6 multilayer model built and executed successfully.")
    print(f"Workspace: {result['workspace']}")
    print(f"Heads map: {result['heads_png_path']}")
    print(f"Vertical leakage map: {result['leakage_png_path']}")
    print(f"Summary: {result['summary_path']}")
