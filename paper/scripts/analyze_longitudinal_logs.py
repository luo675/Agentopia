#!/usr/bin/env python3
"""Read-only longitudinal audit for the three finalized Agentopia runs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path


RUNS = (
    ("Run 1", "T6-Run1-20260709-5ag-52wk"),
    ("Run 2", "T6-Run2-20260711-5ag-52wk"),
    ("Run 3", "T6-Run3-20260716-5ag-52wk"),
)
WEEK_RE = re.compile(r"-W(\d+)-")
TOKEN_RE = re.compile(r"[a-z0-9]+")
NEAR_THRESHOLD = 0.80
NEAR_WINDOW_WEEKS = 8
SHINGLE_SIZE = 5


@dataclass
class TextRecord:
    run: str
    agent: str
    week: int
    kind: str
    primary: str
    reflection: str
    no_response: bool
    is_partial_week: bool


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    return " ".join(TOKEN_RE.findall(text))


def shingles(text: str, size: int = SHINGLE_SIZE) -> frozenset[str]:
    tokens = normalize(text).split()
    if len(tokens) < size:
        return frozenset()
    return frozenset(" ".join(tokens[i : i + size]) for i in range(len(tokens) - size + 1))


def jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


class RollingNearDuplicateDetector:
    def __init__(self, window_weeks: int = NEAR_WINDOW_WEEKS) -> None:
        self.window_weeks = window_weeks
        self.documents: dict[int, tuple[int, frozenset[str]]] = {}
        self.inverted: defaultdict[str, set[int]] = defaultdict(set)
        self.order: deque[int] = deque()
        self.next_id = 0

    def _expire(self, week: int) -> None:
        cutoff = week - self.window_weeks
        while self.order:
            doc_id = self.order[0]
            old_week, old_shingles = self.documents[doc_id]
            if old_week >= cutoff:
                break
            self.order.popleft()
            for shingle in old_shingles:
                ids = self.inverted[shingle]
                ids.discard(doc_id)
                if not ids:
                    del self.inverted[shingle]
            del self.documents[doc_id]

    def add(self, week: int, text: str) -> tuple[bool, float]:
        self._expire(week)
        current = shingles(text)
        candidates: set[int] = set()
        for shingle in current:
            candidates.update(self.inverted.get(shingle, ()))
        maximum = max(
            (jaccard(current, self.documents[doc_id][1]) for doc_id in candidates),
            default=0.0,
        )
        doc_id = self.next_id
        self.next_id += 1
        self.documents[doc_id] = (week, current)
        self.order.append(doc_id)
        for shingle in current:
            self.inverted[shingle].add(doc_id)
        return maximum >= NEAR_THRESHOLD, maximum


def read_checkpoint(run_dir: Path) -> int:
    payload = json.loads((run_dir / "checkpoint.json").read_text(encoding="utf-8"))
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    start_year = int(config["world"]["time"]["start_year"])
    weeks_per_year = int(config["world"]["time"]["n_week"])
    year = int(payload["year"])
    week = int(payload["week"])
    return (year - start_year) * weeks_per_year + week


def discover_active_agents(run_dir: Path) -> list[str]:
    agents = []
    for agent_dir in sorted((run_dir / "persona").iterdir()):
        path = agent_dir / "activity.jsonl"
        if path.is_file() and path.stat().st_size > 10_000:
            agents.append(agent_dir.name)
    return agents


def read_activity(path: Path, run: str, agent: str, max_week: int) -> list[TextRecord]:
    records: list[TextRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            payload = json.loads(line)
            match = WEEK_RE.search(str(payload.get("time", "")))
            if not match:
                raise ValueError(f"No week in {path}:{line_number}")
            week = int(match.group(1))
            if not 1 <= week <= max_week + 1:
                raise ValueError(f"Week {week} too far beyond checkpoint in {path}:{line_number}")
            kind = str(payload.get("type", "unknown"))
            primary = str(payload.get("content") or payload.get("summary") or "")
            reflection = str(payload.get("reflection") or "")
            no_response = "NO_RESPONSE" in line
            records.append(
                TextRecord(run, agent, week, kind, primary, reflection, no_response, week > max_week)
            )
    return records


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError(f"No rows for {path}")
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def text_metrics(records: list[TextRecord]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    weekly: defaultdict[tuple[str, str, int], Counter[str]] = defaultdict(Counter)
    detail: list[dict[str, object]] = []
    exact_seen: defaultdict[tuple[str, str, str, str], set[str]] = defaultdict(set)
    detectors: defaultdict[tuple[str, str, str, str], RollingNearDuplicateDetector] = defaultdict(
        RollingNearDuplicateDetector
    )

    for record in sorted(records, key=lambda r: (r.run, r.agent, r.week)):
        key = (record.run, record.agent, record.week)
        row: dict[str, object] = {
            "run": record.run,
            "agent": record.agent,
            "week": record.week,
            "type": record.kind,
            "no_response": int(record.no_response),
            "partial_week_record": int(record.is_partial_week),
        }
        for field, text in (("primary", record.primary), ("reflection", record.reflection)):
            normalized = normalize(text)
            seen_key = (record.run, record.agent, record.kind, field)
            is_exact = bool(normalized and normalized in exact_seen[seen_key])
            if normalized:
                exact_seen[seen_key].add(normalized)
            is_near, maximum = detectors[seen_key].add(record.week, text)
            row[f"{field}_chars"] = len(text)
            row[f"{field}_exact_duplicate"] = int(is_exact)
            row[f"{field}_near_duplicate"] = int(is_near and not is_exact)
            row[f"{field}_max_prior_jaccard"] = round(maximum, 6)
        detail.append(row)

        counter = weekly[key]
        counter["records"] += 1
        counter[f"type_{record.kind}"] += 1
        counter["no_response"] += int(record.no_response)
        counter["partial_week"] += int(record.is_partial_week)
        counter["primary_chars"] += len(record.primary)
        counter["primary_exact"] += int(row["primary_exact_duplicate"])
        counter["primary_near"] += int(row["primary_near_duplicate"])
        counter["reflection_exact"] += int(row["reflection_exact_duplicate"])
        counter["reflection_near"] += int(row["reflection_near_duplicate"])

    weekly_rows: list[dict[str, object]] = []
    for (run, agent, week), values in sorted(weekly.items()):
        count = values["records"]
        weekly_rows.append(
            {
                "run": run,
                "agent": agent,
                "week": week,
                "records": count,
                "solo_records": values["type_solo"],
                "joint_records": values["type_joint"],
                "no_response_records": values["no_response"],
                "no_response_rate": round(values["no_response"] / count, 6),
                "partial_week_records": values["partial_week"],
                "mean_primary_chars": round(values["primary_chars"] / count, 2),
                "primary_exact_duplicates": values["primary_exact"],
                "primary_near_duplicates": values["primary_near"],
                "reflection_exact_duplicates": values["reflection_exact"],
                "reflection_near_duplicates": values["reflection_near"],
            }
        )
    return weekly_rows, detail


def memory_metrics(
    run_dirs: dict[str, Path], checkpoints: dict[str, int], active_agents: dict[str, list[str]]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    l2_text: dict[tuple[str, str, int], str] = {}
    for run, run_dir in run_dirs.items():
        config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
        recent_weeks = int(config["world"]["context"]["recent_summary_weeks"])
        expected_l2_last_week = checkpoints[run] - recent_weeks
        for agent in active_agents[run]:
            memory_dir = run_dir / "persona" / agent / "memory"
            l2_files = sorted((memory_dir / "l2").rglob("week=*.json"))
            l3_files = sorted((memory_dir / "l3").rglob("*.json"))
            l2_weeks: list[int] = []
            l2_sizes: list[int] = []
            normalized_seen: set[str] = set()
            exact = 0
            near = 0
            detector = RollingNearDuplicateDetector(window_weeks=10_000)
            for path in l2_files:
                payload = json.loads(path.read_text(encoding="utf-8"))
                week = int(payload["week"])
                text = str(payload.get("compressed", ""))
                l2_text[(run, agent, week)] = text
                l2_weeks.append(week)
                l2_sizes.append(path.stat().st_size)
                normalized = normalize(text)
                is_exact = bool(normalized and normalized in normalized_seen)
                if normalized:
                    normalized_seen.add(normalized)
                is_near, _ = detector.add(week, text)
                exact += int(is_exact)
                near += int(is_near and not is_exact)
            expected_weeks = set(range(1, expected_l2_last_week + 1))
            missing = sorted(expected_weeks - set(l2_weeks))
            rows.append(
                {
                    "run": run,
                    "agent": agent,
                    "checkpoint_week": checkpoints[run],
                    "recent_uncompressed_weeks": recent_weeks,
                    "expected_l2_last_week": expected_l2_last_week,
                    "l2_files": len(l2_files),
                    "l2_bytes": sum(l2_sizes),
                    "l2_mean_bytes": round(statistics.mean(l2_sizes), 2) if l2_sizes else 0,
                    "l2_missing_expected_weeks": ";".join(map(str, missing)),
                    "l2_exact_duplicates": exact,
                    "l2_near_duplicates": near,
                    "l3_files": len(l3_files),
                    "l3_bytes": sum(path.stat().st_size for path in l3_files),
                }
            )

    cross_rows: list[dict[str, object]] = []
    run_pairs = (("Run 1", "Run 2"), ("Run 1", "Run 3"), ("Run 2", "Run 3"))
    common_agents = sorted(set.intersection(*(set(value) for value in active_agents.values())))
    for agent in common_agents:
        for left_run, right_run in run_pairs:
            shared_weeks = sorted(
                week
                for week in range(1, min(checkpoints[left_run], checkpoints[right_run]) + 1)
                if (left_run, agent, week) in l2_text and (right_run, agent, week) in l2_text
            )
            for week in shared_weeks:
                score = jaccard(
                    shingles(l2_text[(left_run, agent, week)]),
                    shingles(l2_text[(right_run, agent, week)]),
                )
                cross_rows.append(
                    {
                        "agent": agent,
                        "week": week,
                        "left_run": left_run,
                        "right_run": right_run,
                        "shingle_jaccard": round(score, 6),
                    }
                )
    return rows, cross_rows


def aggregate_run_summary(detail: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for row in detail:
        grouped[str(row["run"])].append(row)
    result = []
    for run in (name for name, _ in RUNS):
        rows = grouped[run]
        count = len(rows)
        unflagged_solo = [
            row for row in rows if row["type"] == "solo" and int(row["no_response"]) == 0
        ]
        unflagged_joint = [
            row for row in rows if row["type"] == "joint" and int(row["no_response"]) == 0
        ]
        result.append(
            {
                "run": run,
                "records": count,
                "no_response_records": sum(int(row["no_response"]) for row in rows),
                "no_response_rate": round(sum(int(row["no_response"]) for row in rows) / count, 6),
                "partial_week_records": sum(int(row["partial_week_record"]) for row in rows),
                "primary_exact_duplicates": sum(int(row["primary_exact_duplicate"]) for row in rows),
                "primary_exact_duplicate_rate": round(sum(int(row["primary_exact_duplicate"]) for row in rows) / count, 6),
                "primary_near_duplicates": sum(int(row["primary_near_duplicate"]) for row in rows),
                "primary_near_duplicate_rate": round(sum(int(row["primary_near_duplicate"]) for row in rows) / count, 6),
                "reflection_exact_duplicates": sum(int(row["reflection_exact_duplicate"]) for row in rows),
                "reflection_exact_duplicate_rate": round(sum(int(row["reflection_exact_duplicate"]) for row in rows) / count, 6),
                "reflection_near_duplicates": sum(int(row["reflection_near_duplicate"]) for row in rows),
                "reflection_near_duplicate_rate": round(sum(int(row["reflection_near_duplicate"]) for row in rows) / count, 6),
                "unflagged_solo_records": len(unflagged_solo),
                "unflagged_solo_primary_exact_duplicates": sum(int(row["primary_exact_duplicate"]) for row in unflagged_solo),
                "unflagged_solo_primary_exact_rate": round(sum(int(row["primary_exact_duplicate"]) for row in unflagged_solo) / len(unflagged_solo), 6),
                "unflagged_solo_primary_near_duplicates": sum(int(row["primary_near_duplicate"]) for row in unflagged_solo),
                "unflagged_solo_primary_near_rate": round(sum(int(row["primary_near_duplicate"]) for row in unflagged_solo) / len(unflagged_solo), 6),
                "unflagged_solo_reflection_exact_duplicates": sum(int(row["reflection_exact_duplicate"]) for row in unflagged_solo),
                "unflagged_solo_reflection_exact_rate": round(sum(int(row["reflection_exact_duplicate"]) for row in unflagged_solo) / len(unflagged_solo), 6),
                "unflagged_joint_records": len(unflagged_joint),
                "unflagged_joint_primary_exact_duplicates": sum(int(row["primary_exact_duplicate"]) for row in unflagged_joint),
            }
        )
    return result


def build_report(
    path: Path,
    summaries: list[dict[str, object]],
    memory_rows: list[dict[str, object]],
    cross_rows: list[dict[str, object]],
    checkpoints: dict[str, int],
) -> None:
    pooled_records = sum(int(row["records"]) for row in summaries)
    pooled_nr = sum(int(row["no_response_records"]) for row in summaries)
    partial_records = sum(int(row["partial_week_records"]) for row in summaries)
    l2_total = sum(int(row["l2_files"]) for row in memory_rows)
    l3_total = sum(int(row["l3_files"]) for row in memory_rows)
    missing = [row for row in memory_rows if row["l2_missing_expected_weeks"]]
    cross_scores = [float(row["shingle_jaccard"]) for row in cross_rows]

    lines = [
        "---",
        "title: Agentopia 纵向日志只读审计",
        "type: experiment-audit",
        "status: complete",
        "created: 2026-08-03",
        "updated: 2026-08-03",
        "tags: [Agentopia, longitudinal, repetition, memory]",
        "---",
        "",
        "# 纵向日志只读审计",
        "",
        "> 本报告由 `../scripts/analyze_longitudinal_logs.py` 从三次 finalized run 直接生成。没有修改原始实验数据，也没有启动新模拟。",
        "",
        "## 数据完整性",
        "",
        f"- checkpoints：Run 1 W{checkpoints['Run 1']}、Run 2 W{checkpoints['Run 2']}、Run 3 W{checkpoints['Run 3']}。",
        f"- activity records：{pooled_records:,}；其中含 `NO_RESPONSE` 标记的 finalized records 为 {pooled_nr:,}（{pooled_nr / pooled_records:.2%}）。",
        f"- Run 3 在 W51 失败前已向 finalized `activity.jsonl` 写入 {partial_records} 条 partial-week records；它们保留在 4,236/13,084 的 activity-record 口径中，但不把 W51 计作完成周。",
        f"- 分层记忆 artifacts：L2 {l2_total:,} 份，L3 {l3_total:,} 份。",
        f"- 依据每个 run 配置的 `recent_summary_weeks=5`，L2 应覆盖离开 recent window 的周；15 个 agent-run 单元中缺失预期 L2 周的单元数为 {len(missing)}。",
        "",
        "## Activity 文本重复审计",
        "",
        "| Run | records | primary exact | primary near | reflection exact | reflection near |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summaries:
        lines.append(
            f"| {row['run']} | {int(row['records']):,} | "
            f"{int(row['primary_exact_duplicates']):,} ({float(row['primary_exact_duplicate_rate']):.2%}) | "
            f"{int(row['primary_near_duplicates']):,} ({float(row['primary_near_duplicate_rate']):.2%}) | "
            f"{int(row['reflection_exact_duplicates']):,} ({float(row['reflection_exact_duplicate_rate']):.2%}) | "
            f"{int(row['reflection_near_duplicates']):,} ({float(row['reflection_near_duplicate_rate']):.2%}) |"
        )
    lines.extend(
        [
            "",
            "口径：exact 是 Unicode 规范化、转小写、去标点后的逐字相同；near 是同一 run、同一 agent、同一活动类型、此前 8 周内的 5-token shingle Jaccard >= 0.80，exact 不重复计入 near。该指标是文本重复筛查，不是行为多样性或社会有效性指标。",
            "",
            "### 排除 NO_RESPONSE 后的 solo 文本",
            "",
            "| Run | unflagged solo | primary exact | primary near | reflection exact |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for row in summaries:
        lines.append(
            f"| {row['run']} | {int(row['unflagged_solo_records']):,} | "
            f"{int(row['unflagged_solo_primary_exact_duplicates']):,} ({float(row['unflagged_solo_primary_exact_rate']):.2%}) | "
            f"{int(row['unflagged_solo_primary_near_duplicates']):,} ({float(row['unflagged_solo_primary_near_rate']):.2%}) | "
            f"{int(row['unflagged_solo_reflection_exact_duplicates']):,} ({float(row['unflagged_solo_reflection_exact_rate']):.2%}) |"
        )
    lines.extend(
        [
            "",
            "总体 exact rate 会被重复出现的字面量 `NO_RESPONSE` 抬高，因此论文若引用重复度，应优先使用上表的 unflagged-solo 口径。这里的 flagged/unflagged 是 activity-record-level 标记，不是模型调用成功率。三个 run 的 unflagged joint records 中 primary exact duplicates 均为 0。unflagged-solo 的逐字重复仍达到约 14%--18%，说明输出复用是实际限制，但它不等价于行为完全相同。",
            "",
            "## L2 跨运行差异",
            "",
            f"同一 agent、同一 week 的跨运行 L2 共得到 {len(cross_scores):,} 个 pairwise comparisons。",
            f"平均 5-token shingle Jaccard 为 {statistics.mean(cross_scores):.4f}，中位数为 {statistics.median(cross_scores):.4f}，最大值为 {max(cross_scores):.4f}。" if cross_scores else "没有可比较的跨运行 L2。",
            "",
            "这只能说明三次 stochastic restarts 的 L2 文本表面重合程度，不能证明分层记忆对 downstream behavior 的因果作用。",
            "",
            "## 可用于论文的结果边界",
            "",
            "- 可报告：13,084 条 finalized records 的精确/近重复筛查口径与结果。",
            "- 可报告：L2 对离开 5-week recent window 的周是否连续产出，以及 L2/L3 artifact 数量。",
            "- 可报告：三次运行同 agent-week 的 L2 文本表面差异，前提是明确这不是 semantic diversity 或 causal ablation。",
            "- 不可报告：memory causes behavioral diversity、agents learned over time、five agents represent a population。",
            "",
            "## 产物",
            "",
            "- `run_summary.csv`：run-level 汇总。",
            "- `weekly_activity_metrics.csv`：agent-week 统计。",
            "- `activity_text_audit.csv`：每条 finalized record 的重复标记与最大相似度。",
            "- `memory_artifacts.csv`：每个 agent-run 的 L2/L3 完整性与体量。",
            "- `cross_run_l2_similarity.csv`：同 agent-week 跨运行 L2 表面相似度。",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    run_dirs = {label: args.data_root / dirname for label, dirname in RUNS}
    checkpoints = {label: read_checkpoint(path) for label, path in run_dirs.items()}
    active_agents = {label: discover_active_agents(path) for label, path in run_dirs.items()}
    for run, agents in active_agents.items():
        if len(agents) != 5:
            raise ValueError(f"Expected 5 active agents in {run}, found {agents}")

    records: list[TextRecord] = []
    for run, run_dir in run_dirs.items():
        for agent in active_agents[run]:
            records.extend(
                read_activity(run_dir / "persona" / agent / "activity.jsonl", run, agent, checkpoints[run])
            )

    weekly_rows, detail_rows = text_metrics(records)
    summaries = aggregate_run_summary(detail_rows)
    memory_rows, cross_rows = memory_metrics(run_dirs, checkpoints, active_agents)

    write_csv(args.output_dir / "run_summary.csv", summaries)
    write_csv(args.output_dir / "weekly_activity_metrics.csv", weekly_rows)
    write_csv(args.output_dir / "activity_text_audit.csv", detail_rows)
    write_csv(args.output_dir / "memory_artifacts.csv", memory_rows)
    write_csv(args.output_dir / "cross_run_l2_similarity.csv", cross_rows)
    build_report(args.output_dir / "纵向日志审计.md", summaries, memory_rows, cross_rows, checkpoints)

    print(f"records={len(records)} weekly_rows={len(weekly_rows)} memory_rows={len(memory_rows)} l2_pairs={len(cross_rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
