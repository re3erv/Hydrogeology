"""Build and run B2: steady-state confined MODFLOW 6 model with heterogeneous K.

Usage:
  python scripts/build_mf6_02_heterogeneous_k.py
  python scripts/build_mf6_02_heterogeneous_k.py --workspace /tmp/mf6_b2
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import flopy
import matplotlib.pyplot as plt
import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = PROJECT_ROOT / "models" / "mf6" / "02_heterogeneous_k"
SIM_NAME = "mf6_02_heterogeneous_k"
GWF_NAME = "gwf"


def _build_k_field(nrow: int, ncol: int, k_background: float = 10.0, k_lens: float = 1.0) -> np.ndarray:
    """Create a simple heterogeneous K field with a low-K lens in the center."""
    k = np.full((1, nrow, ncol), k_background, dtype=float)
    row_slice = slice(3, 7)
    col_slice = slice(3, 7)
    k[0, row_slice, col_slice] = k_lens
    return k


def build_simulation(workspace: Path, sim_name: str = SIM_NAME, gwf_name: str = GWF_NAME) -> flopy.mf6.MFSimulation:
    """Create the MF6 steady-state confined flow simulation for stage B2."""
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
    k_field = _build_k_field(nrow=nrow, ncol=ncol)
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=k_field)

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


def _save_maps(heads: np.ndarray, k_field: np.ndarray, out_heads_png: Path, out_k_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    im = ax.imshow(heads[0], origin="upper", cmap="viridis")
    ax.set_title("B2 heterogeneous K: heads (MF6)")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.colorbar(im, ax=ax, label="Head")
    fig.tight_layout()
    fig.savefig(out_heads_png)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 5), dpi=120)
    im = ax.imshow(k_field[0], origin="upper", cmap="plasma")
    ax.set_title("B2 hydraulic conductivity field K")
    ax.set_xlabel("Column")
    ax.set_ylabel("Row")
    fig.colorbar(im, ax=ax, label="K")
    fig.tight_layout()
    fig.savefig(out_k_png)
    plt.close(fig)


def _budget_residual_percent(list_file: Path) -> float | None:
    """Parse percent discrepancy from MF6 list file in a format-tolerant way."""
    lines = list_file.read_text(encoding="utf-8", errors="ignore").splitlines()
    marker = "PERCENT DISCREPANCY"
    float_pattern = re.compile(r"[-+]?\d*\.?\d+(?:[Ee][-+]?\d+)?")

    for idx, line in enumerate(lines):
        if marker not in line.upper():
            continue

        # Case 1: value appears on the same line as the marker.
        same_line_matches = float_pattern.findall(line)
        if same_line_matches:
            try:
                return float(same_line_matches[-1])
            except ValueError:
                pass

        # Case 2: value appears in nearby following lines (varies by MF6 output format).
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


def _cross_row_deviation(heads: np.ndarray) -> tuple[int, float]:
    """Return row index with strongest centerline deviation and its magnitude."""
    row_profiles = heads[0]
    expected = np.linspace(row_profiles[:, 0], row_profiles[:, -1], row_profiles.shape[1]).T
    deviations = np.max(np.abs(row_profiles - expected), axis=1)
    row_idx = int(np.argmax(deviations))
    return row_idx, float(deviations[row_idx])


def run_b2_model(workspace: Path = WORKSPACE, sim_name: str = SIM_NAME, gwf_name: str = GWF_NAME) -> dict[str, Path | float | int | None]:
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
    heads_png_path = workspace / "heads_map.png"
    k_png_path = workspace / "k_field_map.png"
    summary_path = workspace / "run_summary.txt"

    heads = flopy.utils.HeadFile(str(hds_path)).get_data(kstpkper=(0, 0))
    k_field = _build_k_field(nrow=heads.shape[1], ncol=heads.shape[2])
    _save_maps(heads, k_field, heads_png_path, k_png_path)

    left_mean = float(np.mean(heads[0, :, 0]))
    right_mean = float(np.mean(heads[0, :, -1]))
    residual_pct = _budget_residual_percent(lst_path)
    max_grad_row, max_dev = _cross_row_deviation(heads)

    summary_lines = [
        "B2 steady-state confined model with heterogeneous K (MODFLOW 6)",
        f"Workspace: {workspace}",
        f"Simulation name file: {sim_nam_path}",
        "K field: background K=10, central low-K lens (rows 3-6, cols 3-6) with K=1",
        f"Head left boundary mean: {left_mean:.4f}",
        f"Head right boundary mean: {right_mean:.4f}",
        "Budget percent discrepancy (%): " + (f"{residual_pct:.6f}" if residual_pct is not None else "not parsed"),
        f"Row with max nonlinearity: {max_grad_row}",
        f"Max row-profile abs deviation from linear trend: {max_dev:.6f}",
        f"List file: {lst_path}",
        f"Head file: {hds_path}",
        f"Budget file: {cbc_path}",
        f"Head map: {heads_png_path}",
        f"K field map: {k_png_path}",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "workspace": workspace,
        "sim_nam_path": sim_nam_path,
        "hds_path": hds_path,
        "cbc_path": cbc_path,
        "lst_path": lst_path,
        "heads_png_path": heads_png_path,
        "k_png_path": k_png_path,
        "summary_path": summary_path,
        "residual_pct": residual_pct,
        "max_grad_row": max_grad_row,
        "max_dev": max_dev,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    parser.add_argument("--sim-name", default=SIM_NAME)
    parser.add_argument("--gwf-name", default=GWF_NAME)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_b2_model(workspace=args.workspace, sim_name=args.sim_name, gwf_name=args.gwf_name)
    print("B2 MF6 model (heterogeneous K) built and executed successfully.")
    print(f"Workspace: {result['workspace']}")
    print(f"Simulation name file: {result['sim_nam_path']}")
    if result["residual_pct"] is None:
        print("Budget residual (%): not parsed from list file")
    else:
        print(f"Budget residual (%): {result['residual_pct']:.6f}")
    print(f"Row with max nonlinearity: {result['max_grad_row']}")
    print(f"Max row-profile abs deviation: {result['max_dev']:.6f}")
