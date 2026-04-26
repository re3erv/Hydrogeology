"""Build and run B5: compare RIV / DRN / GHB in a steady-state MF6 model.

Usage:
  python scripts/build_mf6_05_riv_drn_ghb.py
  python scripts/build_mf6_05_riv_drn_ghb.py --workspace /tmp/mf6_b5
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
WORKSPACE = PROJECT_ROOT / "models" / "mf6" / "05_riv_drn_ghb"
GWF_NAME = "gwf"


def _build_chd_spd(nrow: int, ncol: int) -> list[tuple[tuple[int, int, int], float]]:
    chd_spd: list[tuple[tuple[int, int, int], float]] = []
    for r in range(nrow):
        chd_spd.append(((0, r, 0), 10.0))
        chd_spd.append(((0, r, ncol - 1), 0.0))
    return chd_spd


def build_simulation(workspace: Path, sim_name: str, boundary_package: str) -> flopy.mf6.MFSimulation:
    """Create one MF6 simulation for a selected package: RIV, DRN, or GHB."""
    workspace.mkdir(parents=True, exist_ok=True)

    sim = flopy.mf6.MFSimulation(sim_name=sim_name, sim_ws=str(workspace), exe_name="mf6")
    flopy.mf6.ModflowTdis(sim, nper=1, perioddata=[(1.0, 1, 1.0)], time_units="DAYS")
    flopy.mf6.ModflowIms(sim, complexity="SIMPLE", linear_acceleration="CG")

    gwf = flopy.mf6.ModflowGwf(sim, modelname=GWF_NAME, save_flows=True)

    nlay, nrow, ncol = 1, 10, 10
    delr = np.full(ncol, 100.0, dtype=float)
    delc = np.full(nrow, 100.0, dtype=float)
    top = np.full((nrow, ncol), 10.0, dtype=float)
    botm = np.full((nlay, nrow, ncol), 0.0, dtype=float)

    flopy.mf6.ModflowGwfdis(gwf, nlay=nlay, nrow=nrow, ncol=ncol, delr=delr, delc=delc, top=top, botm=botm)
    flopy.mf6.ModflowGwfic(gwf, strt=np.full((nlay, nrow, ncol), 5.0, dtype=float))
    flopy.mf6.ModflowGwfnpf(gwf, icelltype=0, k=10.0)
    flopy.mf6.ModflowGwfchd(gwf, stress_period_data=_build_chd_spd(nrow=nrow, ncol=ncol))

    # Third boundary is applied along top row (except CHD corners).
    package = boundary_package.upper()
    cond = 20.0
    stage_like_head = 7.0
    bottom = 5.0
    records = []
    for c in range(1, ncol - 1):
        cellid = (0, 0, c)
        if package == "RIV":
            records.append((cellid, stage_like_head, cond, bottom))
        elif package == "DRN":
            records.append((cellid, stage_like_head, cond))
        elif package == "GHB":
            records.append((cellid, stage_like_head, cond))
        else:
            raise ValueError(f"Unsupported package: {boundary_package}")

    if package == "RIV":
        flopy.mf6.ModflowGwfriv(gwf, stress_period_data=records)
    elif package == "DRN":
        flopy.mf6.ModflowGwfdrn(gwf, stress_period_data=records)
    else:
        flopy.mf6.ModflowGwfghb(gwf, stress_period_data=records)

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


def _package_exchange(cbc_path: Path, package: str) -> float:
    cbc = flopy.utils.CellBudgetFile(str(cbc_path))
    text = package.upper()
    data = cbc.get_data(text=text)
    if not data:
        return 0.0
    arr = data[-1]
    total = 0.0
    if isinstance(arr, np.recarray):
        if "q" in arr.dtype.names:
            total = float(np.sum(arr["q"]))
    else:
        total = float(np.sum(arr))
    return total


def _save_compare_plot(labels: list[str], center_heads: list[float], exchanges: list[float], out_png: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), dpi=120)

    axes[0].bar(labels, center_heads, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    axes[0].set_title("Center head by boundary package")
    axes[0].set_ylabel("Head")

    axes[1].bar(labels, exchanges, color=["#1f77b4", "#ff7f0e", "#2ca02c"])
    axes[1].set_title("Net package exchange (q)")
    axes[1].set_ylabel("Flow rate")

    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)


def run_b5_model(workspace: Path = WORKSPACE) -> dict[str, Path]:
    workspace.mkdir(parents=True, exist_ok=True)

    packages = ["RIV", "DRN", "GHB"]
    rows: list[dict[str, float | str | None]] = []
    center_heads: list[float] = []
    exchanges: list[float] = []

    for package in packages:
        run_ws = workspace / package.lower()
        sim_name = f"mf6_05_{package.lower()}"
        sim = build_simulation(workspace=run_ws, sim_name=sim_name, boundary_package=package)
        sim.write_simulation()

        success, output = sim.run_simulation(silent=True, report=True)
        if not success:
            tail = "\n".join(output[-20:])
            raise RuntimeError(f"MODFLOW 6 run failed for {package}. Output tail:\n{tail}")

        hds_path = run_ws / f"{sim_name}.hds"
        cbc_path = run_ws / f"{sim_name}.cbc"
        lst_path = run_ws / "mfsim.lst"
        gwf_lst_path = run_ws / f"{GWF_NAME}.lst"

        heads = flopy.utils.HeadFile(str(hds_path)).get_data(kstpkper=(0, 0))
        center_head = float(heads[0, 5, 5])
        top_mid_head = float(heads[0, 0, 5])
        residual_pct = _budget_residual_percent(lst_path, gwf_lst_path)
        exchange = _package_exchange(cbc_path, package)

        rows.append(
            {
                "package": package,
                "center_head": center_head,
                "top_mid_head": top_mid_head,
                "package_exchange_q": exchange,
                "budget_percent_discrepancy": residual_pct,
            }
        )
        center_heads.append(center_head)
        exchanges.append(exchange)

    csv_path = workspace / "comparison_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "package",
                "center_head",
                "top_mid_head",
                "package_exchange_q",
                "budget_percent_discrepancy",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    plot_path = workspace / "comparison_plot.png"
    _save_compare_plot(packages, center_heads, exchanges, plot_path)

    summary_lines = [
        "B5 steady-state MF6 comparison: RIV vs DRN vs GHB",
        f"Workspace: {workspace}",
        "Configuration: B1 grid + CHD left/right + top-row boundary package (cols 1..8)",
        "Shared boundary params: stage/head=7.0, cond=20.0, RIV bottom=5.0",
        "",
        "Results:",
    ]
    for row in rows:
        discrepancy = row["budget_percent_discrepancy"]
        discrepancy_text = "not parsed" if discrepancy is None else f"{float(discrepancy):.6f}"
        summary_lines.append(
            f"- {row['package']}: center_head={float(row['center_head']):.6f}, "
            f"top_mid_head={float(row['top_mid_head']):.6f}, "
            f"package_exchange_q={float(row['package_exchange_q']):.6f}, "
            f"budget_discrepancy={discrepancy_text}%"
        )

    summary_lines.extend(["", f"CSV: {csv_path}", f"Plot: {plot_path}"])
    summary_path = workspace / "run_summary.txt"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "workspace": workspace,
        "csv_path": csv_path,
        "plot_path": plot_path,
        "summary_path": summary_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, default=WORKSPACE)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = run_b5_model(workspace=args.workspace)
    print("B5 MF6 comparison (RIV/DRN/GHB) built and executed successfully.")
    print(f"Workspace: {result['workspace']}")
    print(f"CSV metrics: {result['csv_path']}")
    print(f"Comparison plot: {result['plot_path']}")
    print(f"Summary: {result['summary_path']}")
