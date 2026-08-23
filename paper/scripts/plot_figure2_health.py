"""Generate Figure 2 from the archived per-agent weekly health snapshots."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


PAPER_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = PAPER_DIR.parent
DATA_DIR = PROJECT_DIR / "实验数据" / "基线"
FIGURES_DIR = PAPER_DIR / "figures"

AGENTS = (
    "Aaron Whitfield",
    "Adrian Morales",
    "Adrian Vale",
    "Alaric Voss",
    "Alessandro Vieri",
)


@dataclass(frozen=True)
class RunSpec:
    label: str
    directory: str
    weeks: int
    color: str
    linestyle: str


RUNS = (
    RunSpec("Run 1", "T6-Run1-20260709-5ag-52wk", 52, "#0072B2", "-"),
    RunSpec("Run 2", "T6-Run2-20260711-5ag-52wk", 52, "#D55E00", "--"),
    RunSpec("Run 3", "T6-Run3-20260716-5ag-52wk", 50, "#009E73", "-."),
)

EXPECTED_FINAL = {
    "Run 1": {
        "Aaron Whitfield": (100, 93),
        "Adrian Morales": (100, 97),
        "Adrian Vale": (93, 92),
        "Alaric Voss": (100, 79),
        "Alessandro Vieri": (100, 95),
    },
    "Run 2": {
        "Aaron Whitfield": (95, 70),
        "Adrian Morales": (100, 79),
        "Adrian Vale": (96, 77),
        "Alaric Voss": (100, 77),
        "Alessandro Vieri": (100, 100),
    },
    "Run 3": {
        "Aaron Whitfield": (96, 71),
        "Adrian Morales": (100, 89),
        "Adrian Vale": (100, 96),
        "Alaric Voss": (100, 99),
        "Alessandro Vieri": (100, 91),
    },
}

EXPECTED_MINIMA = {
    "Run 1": (80, 59),
    "Run 2": (80, 53),
    "Run 3": (80, 60),
}

YEAR_RE = re.compile(r"year=(\d+)$")
WEEK_RE = re.compile(r"week=(\d+)\.json$")


def load_run(spec: RunSpec) -> dict[str, dict[int, tuple[int, int]]]:
    run_dir = DATA_DIR / spec.directory
    assert run_dir.is_dir(), f"Missing run directory: {run_dir}"

    result: dict[str, dict[int, tuple[int, int]]] = {}
    total_files = 0
    expected_weeks = set(range(1, spec.weeks + 1))

    for agent in AGENTS:
        health_dir = run_dir / "persona" / agent / "memory" / "health"
        assert health_dir.is_dir(), f"Missing health directory: {health_dir}"

        by_week: dict[int, tuple[int, int]] = {}
        files = list(health_dir.glob("year=*/week=*.json"))
        total_files += len(files)

        for path in files:
            year_match = YEAR_RE.fullmatch(path.parent.name)
            week_match = WEEK_RE.fullmatch(path.name)
            assert year_match and week_match, f"Unexpected health path: {path}"

            year = int(year_match.group(1))
            week = int(week_match.group(1))
            assert year == 2020, f"Unexpected year in {path}: {year}"
            assert week not in by_week, f"Duplicate week {week}: {health_dir}"

            with path.open(encoding="utf-8") as handle:
                payload = json.load(handle)

            assert payload["year"] == year and payload["week"] == week, (
                f"Path/payload mismatch: {path}"
            )
            physical = int(payload["physical_health"])
            mental = int(payload["mental_health"])
            assert 0 <= physical <= 100 and 0 <= mental <= 100, (
                f"Out-of-range health score in {path}: {(physical, mental)}"
            )
            by_week[week] = (physical, mental)

        assert set(by_week) == expected_weeks, (
            f"{spec.label}/{agent} weeks differ: "
            f"missing={sorted(expected_weeks - set(by_week))}, "
            f"extra={sorted(set(by_week) - expected_weeks)}"
        )
        assert by_week[spec.weeks] == EXPECTED_FINAL[spec.label][agent], (
            f"Unexpected final checkpoint for {spec.label}/{agent}: "
            f"{by_week[spec.weeks]}"
        )
        result[agent] = by_week

    expected_files = len(AGENTS) * spec.weeks
    assert total_files == expected_files, (
        f"{spec.label} has {total_files} snapshots, expected {expected_files}"
    )

    all_values = [scores for agent_data in result.values() for scores in agent_data.values()]
    minima = (min(v[0] for v in all_values), min(v[1] for v in all_values))
    assert minima == EXPECTED_MINIMA[spec.label], (
        f"Unexpected all-week minima for {spec.label}: {minima}"
    )
    return result


def write_csv(data: dict[str, dict[str, dict[int, tuple[int, int]]]]) -> Path:
    output = FIGURES_DIR / "figure2_health_data.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("run", "week", "agent", "physical_health", "mental_health"))
        for spec in RUNS:
            for week in range(1, spec.weeks + 1):
                for agent in AGENTS:
                    physical, mental = data[spec.label][agent][week]
                    writer.writerow((spec.label, week, agent, physical, mental))
    return output


def plot(data: dict[str, dict[str, dict[int, tuple[int, int]]]]) -> tuple[Path, Path]:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 9.5,
            "legend.fontsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.25), sharey=True)
    panels = (
        (axes[0], 0, "(a) Physical health", 10),
        (axes[1], 1, "(b) Mental health", 20),
    )

    for axis, value_index, title, threshold in panels:
        for spec in RUNS:
            weeks = np.arange(1, spec.weeks + 1)
            values = np.array(
                [
                    [data[spec.label][agent][week][value_index] for agent in AGENTS]
                    for week in weeks
                ],
                dtype=float,
            )
            weekly_mean = values.mean(axis=1)
            axis.fill_between(
                weeks,
                values.min(axis=1),
                values.max(axis=1),
                color=spec.color,
                alpha=0.13,
                linewidth=0,
            )
            axis.plot(
                weeks,
                weekly_mean,
                color=spec.color,
                linestyle=spec.linestyle,
                linewidth=1.65,
            )

        axis.axhline(threshold, color="#8B1A1A", linestyle=":", linewidth=1.2)
        axis.text(
            51.5,
            threshold + 2.2,
            f"warning threshold = {threshold}",
            color="#8B1A1A",
            fontsize=7.2,
            ha="right",
            va="bottom",
        )
        axis.set_title(title, loc="left", fontweight="semibold")
        axis.set_xlabel("Simulation week")
        axis.set_xlim(1, 52)
        axis.set_ylim(0, 105)
        axis.set_xticks((1, 10, 20, 30, 40, 52))
        axis.set_yticks((0, 20, 40, 60, 80, 100))
        axis.grid(axis="y", color="#D9D9D9", linewidth=0.55)
        axis.set_axisbelow(True)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)

    axes[0].set_ylabel("Health score (0--100)")
    legend_handles = [
        Line2D(
            [0],
            [0],
            color=spec.color,
            linestyle=spec.linestyle,
            linewidth=1.8,
            label=f"{spec.label} ({spec.weeks} weeks)",
        )
        for spec in RUNS
    ]
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.995),
        ncol=3,
        frameon=False,
        handlelength=2.8,
        columnspacing=1.8,
    )
    fig.subplots_adjust(left=0.085, right=0.98, bottom=0.17, top=0.84, wspace=0.12)

    pdf_path = FIGURES_DIR / "figure2_health_trajectories.pdf"
    png_path = FIGURES_DIR / "figure2_health_trajectories_preview.png"
    fig.savefig(
        pdf_path,
        format="pdf",
        metadata={"Title": "Weekly physical and mental health trajectories"},
    )
    fig.savefig(png_path, dpi=240, facecolor="white")
    plt.close(fig)
    return pdf_path, png_path


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    data = {spec.label: load_run(spec) for spec in RUNS}
    csv_path = write_csv(data)
    pdf_path, png_path = plot(data)

    for spec in RUNS:
        final_values = [data[spec.label][agent][spec.weeks] for agent in AGENTS]
        all_values = [
            scores
            for agent_data in data[spec.label].values()
            for scores in agent_data.values()
        ]
        print(
            f"{spec.label}: snapshots={len(all_values)}, final_week={spec.weeks}, "
            f"final_PH={min(v[0] for v in final_values)}-{max(v[0] for v in final_values)}, "
            f"final_MH={min(v[1] for v in final_values)}-{max(v[1] for v in final_values)}, "
            f"all_week_min=({min(v[0] for v in all_values)}, "
            f"{min(v[1] for v in all_values)})"
        )
    print(f"CSV: {csv_path}")
    print(f"PDF: {pdf_path}")
    print(f"Preview: {png_path}")


if __name__ == "__main__":
    main()
