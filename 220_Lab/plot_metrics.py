#!/usr/bin/env python3
import argparse
import json
import os
from typing import Dict, List, Optional, Tuple

import matplotlib

# Use a non-interactive backend so this works over SSH.
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def read_descriptor(path: str) -> Dict:
    with open(path, "r") as f:
        return json.load(f)


def read_stat_value(stat_path: str, key: str) -> Optional[float]:
    """
    Read the numeric value for a given key from a Scarab *.stat.*.csv file.
    Returns None if the file or key is missing.
    """
    try:
        with open(stat_path, "r") as f:
            for line in f:
                parts = [p.strip() for p in line.split(",")]
                if not parts:
                    continue
                if parts[0] == key and len(parts) >= 2:
                    # Use the last numeric field; some rows have an extra index column.
                    try:
                        return float(parts[-1])
                    except ValueError:
                        return None
    except FileNotFoundError:
        return None
    return None


def compute_metrics(
    descriptor: Dict, sim_path: str, metric: str
) -> Tuple[List[str], Dict[str, List[float]], str, Optional[Tuple[float, float]]]:
    """
    Compute the requested metric across all benchmarks/configs.
    Returns: (benchmarks_with_avg, data_by_config, ylabel, ylim)
    """
    benches = [b.split("/")[-1] for b in descriptor["workloads_list"]]
    configs = list(descriptor["configurations"].keys())
    exp = descriptor["experiment"]

    data: Dict[str, List[float]] = {}
    ylabel = ""
    ylim = None

    for cfg in configs:
        values: List[float] = []
        for bench in benches:
            bench_dir = os.path.join(sim_path, bench, exp, cfg)
            mem_stat = os.path.join(bench_dir, "memory.stat.0.csv")
            bp_stat = os.path.join(bench_dir, "bp.stat.0.csv")

            if metric == "ipc":
                ylabel = "IPC"
                cycles = read_stat_value(mem_stat, "Periodic_Cycles")
                insts = read_stat_value(mem_stat, "Periodic_Instructions")
                if cycles is not None and insts is not None and cycles != 0:
                    val = insts / cycles
                else:
                    fallback = read_stat_value(mem_stat, "Periodic IPC")
                    val = fallback if fallback is not None else 0.0
            elif metric == "branch_mispred":
                ylabel = "Branch Misprediction Ratio"
                correct = read_stat_value(bp_stat, "CBR_CORRECT_count") or 0.0
                mispred = read_stat_value(bp_stat, "CBR_RECOVER_MISPREDICT_count") or 0.0
                total = correct + mispred
                val = (mispred / total) if total > 0 else 0.0
                ylim = (0, 0.25)
            elif metric == "dcache_miss":
                ylabel = "D-Cache Miss Ratio"
                miss = read_stat_value(mem_stat, "DCACHE_MISS_ONPATH_count") or 0.0
                hit = read_stat_value(mem_stat, "DCACHE_HIT_ONPATH_count") or 0.0
                total = hit + miss
                val = (miss / total) if total > 0 else 0.0
                ylim = (0, 0.25)
            elif metric == "icache_miss":
                ylabel = "I-Cache Miss Ratio"
                miss = read_stat_value(mem_stat, "ICACHE_MISS_ONPATH_count") or 0.0
                hit = read_stat_value(mem_stat, "ICACHE_HIT_ONPATH_count") or 0.0
                total = hit + miss
                val = (miss / total) if total > 0 else 0.0
                ylim = (0, 0.25)
            else:
                raise ValueError(f"Unknown metric '{metric}'")

            if val is None:
                val = 0.0
            values.append(val)

        avg = sum(values) / len(values) if values else 0.0
        values.append(avg)
        data[cfg] = values

    benches_with_avg = benches + ["Avg"]
    return benches_with_avg, data, ylabel, ylim


def plot_data(
    benchmarks: List[str],
    data: Dict[str, List[float]],
    ylabel_name: str,
    fig_name: str,
    ylim: Optional[Tuple[float, float]] = None,
) -> None:
    colors = [
        "#800000",
        "#911eb4",
        "#4363d8",
        "#f58231",
        "#3cb44b",
        "#46f0f0",
        "#f032e6",
        "#bcf60c",
        "#fabebe",
        "#e6beff",
        "#e6194b",
        "#000075",
        "#800000",
        "#9a6324",
        "#808080",
        "#ffffff",
        "#000000",
    ]
    ind = np.arange(len(benchmarks))
    width = 0.18
    fig, ax = plt.subplots(figsize=(14, 4.4), dpi=80)
    num_keys = len(data.keys())

    idx = 0
    start_id = -int(num_keys / 2)
    for key in data.keys():
        hatch = "\\\\\\" if idx % 2 else "///"
        ax.bar(
            ind + (start_id + idx) * width,
            data[key],
            width=width,
            fill=False,
            hatch=hatch,
            color=colors[idx],
            edgecolor=colors[idx],
            label=key,
        )
        idx += 1
    ax.set_xlabel("Benchmarks")
    ax.set_ylabel(ylabel_name)
    ax.set_xticks(ind)
    ax.set_xticklabels(benchmarks, rotation=27, ha="right")
    ax.grid("x")
    if ylim is not None:
        ax.set_ylim(ylim)
    ax.legend(loc="upper left", ncols=2)
    fig.tight_layout()
    plt.savefig(fig_name, format="png", bbox_inches="tight")


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot CSE220 lab metrics")
    parser.add_argument(
        "-o", "--output_dir", required=True, help="Output directory for plots"
    )
    parser.add_argument(
        "-d",
        "--descriptor",
        required=True,
        help="Experiment descriptor JSON (e.g., /home/ubuntu/lab1.json)",
    )
    parser.add_argument(
        "-s",
        "--simulation_path",
        required=True,
        help="Path to simulations (e.g., /home/ubuntu/exp/simulations)",
    )
    parser.add_argument(
        "-m",
        "--metrics",
        nargs="+",
        default=["ipc", "branch_mispred", "dcache_miss", "icache_miss"],
        choices=["ipc", "branch_mispred", "dcache_miss", "icache_miss"],
        help="Metrics to plot",
    )
    args = parser.parse_args()

    desc = read_descriptor(args.descriptor)
    os.makedirs(args.output_dir, exist_ok=True)

    file_suffix = {
        "ipc": "ipc.png",
        "branch_mispred": "branch_mispred.png",
        "dcache_miss": "dcache_miss.png",
        "icache_miss": "icache_miss.png",
    }

    for metric in args.metrics:
        benchmarks, data, ylabel, ylim = compute_metrics(
            desc, args.simulation_path, metric
        )
        out_path = os.path.join(args.output_dir, file_suffix[metric])
        plot_data(benchmarks, data, ylabel, out_path, ylim=ylim)


if __name__ == "__main__":
    main()
