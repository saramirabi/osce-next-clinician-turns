#!/usr/bin/env python3
"""Construct the frozen 1,500-target experimental sample from v3 characteristics."""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median, pstdev

ROOT = Path(__file__).resolve().parent
INPUT_CSV = ROOT / "candidate_characteristics_v3.csv"
OUTPUT_SAMPLE = ROOT / "final_1500_contexts.csv"
OUTPUT_REPORT = ROOT / "final_sampling_report.md"
OUTPUT_AUDIT = ROOT / "final_sampling_audit.csv"
OUTPUT_REVIEW = ROOT / "final_sample_review.csv"

RANDOM_SEED = 42
REVIEW_RANDOM_SEED = 42
TARGET_SIZE = 1500
DIALOGUE_COUNT = 272
BASE_TARGETS_PER_DIALOGUE = 5
PREFERRED_ALLOCATION = {"early": 2, "middle": 2, "late": 1}
EXTRA_LATE_ALLOCATION = 2

SAMPLE_COLUMNS = [
    "context_id",
    "dialogue_id",
    "specialty",
    "target_turn_id",
    "context",
    "latest_patient_turn",
    "human_doctor_target",
    "completed_exchanges_before_target",
    "normalized_target_position",
    "position_category",
    "primary_turn_function",
    "target_word_count",
    "context_word_count",
]

AUDIT_COLUMNS = [
    "context_id",
    "dialogue_id",
    "target_turn_id",
    "position_category",
    "selection_stratum",
    "selection_reason",
    "normalized_target_position",
    "completed_exchanges_before_target",
]


def load_rows() -> list[dict[str, str]]:
    with INPUT_CSV.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def eligible_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        row
        for row in rows
        if row["primary_turn_function"] == "history_information_seeking"
        and int(row["completed_exchanges_before_target"]) >= 2
    ]


def pct(part: int, whole: int) -> float:
    return (part / whole * 100) if whole else 0.0


def histogram(values: list[int], edges: list[int]) -> list[tuple[str, int]]:
    counts: list[tuple[str, int]] = []
    for index, edge in enumerate(edges[:-1]):
        low = edge
        high = edges[index + 1]
        if index == len(edges) - 2:
            count = sum(1 for value in values if low <= value <= high)
            label = f"{low}-{high}"
        else:
            count = sum(1 for value in values if low <= value < high)
            label = f"{low}-{high - 1}"
        counts.append((label, count))
    return counts


def select_primary_sample(
    eligible: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rng = random.Random(RANDOM_SEED)
    by_dialogue: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for row in eligible:
        by_dialogue[row["dialogue_id"]][row["position_category"]].append(row)

    dialogue_ids = sorted(by_dialogue)
    extra_needed = TARGET_SIZE - (DIALOGUE_COUNT * BASE_TARGETS_PER_DIALOGUE)
    if extra_needed < 0:
        raise ValueError("Target size is smaller than base allocation per dialogue.")

    extra_dialogues = set(dialogue_ids[:extra_needed])

    selected: list[dict[str, str]] = []
    audit_rows: list[dict[str, str]] = []
    selected_ids: set[str] = set()

    for dialogue_id in dialogue_ids:
        allocation = dict(PREFERRED_ALLOCATION)
        if dialogue_id in extra_dialogues:
            allocation["late"] = EXTRA_LATE_ALLOCATION

        for position_category in ("early", "middle", "late"):
            quota = allocation[position_category]
            pool = by_dialogue[dialogue_id][position_category][:]
            rng.shuffle(pool)
            if len(pool) < quota:
                raise ValueError(
                    f"Dialogue {dialogue_id} lacks {quota} eligible {position_category} targets."
                )
            for row in pool[:quota]:
                if row["target_turn_id"] in selected_ids:
                    raise ValueError(f"Duplicate target selected: {row['target_turn_id']}")
                selected_ids.add(row["target_turn_id"])
                context_id = f"CTX_{len(selected):04d}"
                row = dict(row)
                row["context_id"] = context_id
                selected.append(row)
                audit_rows.append(
                    {
                        "context_id": context_id,
                        "dialogue_id": dialogue_id,
                        "target_turn_id": row["target_turn_id"],
                        "position_category": position_category,
                        "selection_stratum": f"{dialogue_id}:{position_category}",
                        "selection_reason": (
                            f"primary_allocation {quota} {position_category} "
                            f"(dialogue_total={sum(allocation.values())})"
                        ),
                        "normalized_target_position": row["normalized_target_position"],
                        "completed_exchanges_before_target": row[
                            "completed_exchanges_before_target"
                        ],
                    }
                )

    if len(selected) != TARGET_SIZE:
        raise ValueError(f"Expected {TARGET_SIZE} selections, got {len(selected)}.")

    return selected, audit_rows


def select_review_sample(
    selected: list[dict[str, str]], target_count: int = 100
) -> list[dict[str, str]]:
    rng = random.Random(REVIEW_RANDOM_SEED)
    chosen: list[dict[str, str]] = []
    chosen_ids: set[str] = set()

    for position in ("early", "middle", "late"):
        pool = [
            row
            for row in selected
            if row["position_category"] == position and row["context_id"] not in chosen_ids
        ]
        rng.shuffle(pool)
        for row in pool[: max(1, target_count // 3)]:
            chosen.append(row)
            chosen_ids.add(row["context_id"])

    for specialty in sorted(set(row["specialty"] for row in selected)):
        pool = [
            row
            for row in selected
            if row["specialty"] == specialty and row["context_id"] not in chosen_ids
        ]
        rng.shuffle(pool)
        if pool:
            chosen.append(pool[0])
            chosen_ids.add(pool[0]["context_id"])

    dialogue_seen = {row["dialogue_id"] for row in chosen}
    for row in sorted(selected, key=lambda item: item["dialogue_id"]):
        if row["dialogue_id"] not in dialogue_seen and row["context_id"] not in chosen_ids:
            chosen.append(row)
            chosen_ids.add(row["context_id"])
            dialogue_seen.add(row["dialogue_id"])

    remaining = [row for row in selected if row["context_id"] not in chosen_ids]
    rng.shuffle(remaining)
    for row in remaining:
        chosen.append(row)
        chosen_ids.add(row["context_id"])
        if len(chosen) >= target_count:
            break

    return chosen[:target_count]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def write_report(
    eligible: list[dict[str, str]],
    selected: list[dict[str, str]],
    audit_rows: list[dict[str, str]],
) -> None:
    per_dialogue = Counter(row["dialogue_id"] for row in selected)
    per_dialogue_values = list(per_dialogue.values())
    position_counts = Counter(row["position_category"] for row in selected)
    specialty_counts = Counter(row["specialty"] for row in selected)
    context_words = [int(row["context_word_count"]) for row in selected]
    target_words = [int(row["target_word_count"]) for row in selected]
    exchanges = [int(row["completed_exchanges_before_target"]) for row in selected]

    context_bins = histogram(
        context_words,
        [0, 250, 500, 750, 1000, 1250, 1500, 2000, 100000],
    )
    target_bins = histogram(target_words, [0, 5, 10, 15, 20, 30, 50, 100000])
    exchange_counts = Counter(exchanges)

    extra_needed = TARGET_SIZE - (DIALOGUE_COUNT * BASE_TARGETS_PER_DIALOGUE)
    dialogue_ids = sorted(set(row["dialogue_id"] for row in eligible))
    extra_dialogues = dialogue_ids[:extra_needed]

    lines = [
        "# Final Sampling Report",
        "",
        "Frozen experimental sample constructed from `candidate_characteristics_v3.csv`.",
        "Classification rules were not modified during sampling.",
        "",
        "## Eligibility Criteria",
        "",
        "1. `primary_turn_function == history_information_seeking`",
        "2. `completed_exchanges_before_target >= 2`",
        "",
        "No additional filters were applied.",
        "",
        "## Pool and Sample Size",
        "",
        f"- Eligible pool before sampling: **{len(eligible):,}**",
        f"- Final frozen sample size: **{len(selected):,}**",
        f"- Unique source dialogues represented: **{len(per_dialogue):,}**",
        "",
        "## Targets per Dialogue",
        "",
        f"- Mean: **{mean(per_dialogue_values):.2f}**",
        f"- Median: **{median(per_dialogue_values):.1f}**",
        f"- SD: **{pstdev(per_dialogue_values):.2f}**",
        f"- Min / max: **{min(per_dialogue_values)} / {max(per_dialogue_values)}**",
        "",
        "Allocation design:",
        f"- Base allocation for every dialogue: **{PREFERRED_ALLOCATION['early']} Early + "
        f"{PREFERRED_ALLOCATION['middle']} Middle + {PREFERRED_ALLOCATION['late']} Late = "
        f"{BASE_TARGETS_PER_DIALOGUE} targets**",
        f"- Additional Late target added to the first **{extra_needed}** dialogues when sorted "
        f"alphabetically by `dialogue_id`, yielding **{EXTRA_LATE_ALLOCATION} Late** targets "
        f"in those dialogues (**6 total** each).",
        "",
        "## Position Category Distribution",
        "",
        "| Category | Count | Percentage |",
        "| --- | ---: | ---: |",
    ]

    for category in ("early", "middle", "late"):
        count = position_counts[category]
        lines.append(f"| {category} | {count:,} | {pct(count, len(selected)):.2f}% |")

    lines.extend(
        [
            "",
            "## Specialty Distribution",
            "",
            "Sampling did **not** enforce equal specialty representation.",
            "",
            "| Specialty | Count | Percentage |",
            "| --- | ---: | ---: |",
        ]
    )

    for specialty in sorted(specialty_counts):
        count = specialty_counts[specialty]
        lines.append(f"| {specialty} | {count:,} | {pct(count, len(selected)):.2f}% |")

    lines.extend(
        [
            "",
            "## Context Length (words)",
            "",
            f"- Mean / median / SD: **{mean(context_words):.2f} / {median(context_words):.1f} / {pstdev(context_words):.2f}**",
            f"- Min / max: **{min(context_words)} / {max(context_words)}**",
            "",
            "| Bin | Count |",
            "| --- | ---: |",
        ]
    )
    for label, count in context_bins:
        lines.append(f"| {label} | {count} |")

    lines.extend(
        [
            "",
            "## Human Target Length (words)",
            "",
            f"- Mean / median / SD: **{mean(target_words):.2f} / {median(target_words):.1f} / {pstdev(target_words):.2f}**",
            f"- Min / max: **{min(target_words)} / {max(target_words)}**",
            "",
            "| Bin | Count |",
            "| --- | ---: |",
        ]
    )
    for label, count in target_bins:
        lines.append(f"| {label} | {count} |")

    lines.extend(
        [
            "",
            "## Completed Exchange Distribution",
            "",
            "| Completed exchanges before target | Count | Percentage |",
            "| --- | ---: | ---: |",
        ]
    )
    for exchange_count in sorted(exchange_counts):
        count = exchange_counts[exchange_count]
        lines.append(
            f"| {exchange_count} | {count:,} | {pct(count, len(selected)):.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Sampling Algorithm",
            "",
            "1. Load all rows from `candidate_characteristics_v3.csv`.",
            "2. Keep rows with `primary_turn_function == history_information_seeking` and "
            "`completed_exchanges_before_target >= 2`.",
            "3. Group eligible rows by `dialogue_id` and `position_category`.",
            "4. For each dialogue in alphabetical order:",
            "   - Allocate 2 Early, 2 Middle, and 1 Late target by default.",
            "   - Add a second Late target for the first 140 dialogues alphabetically to reach exactly 1,500.",
            "5. Within each dialogue-position stratum with more eligible rows than required, "
            f"randomly sample without replacement using seed **{RANDOM_SEED}**.",
            "6. Assign unique `context_id` values in selection order (`CTX_0001` … `CTX_1500`).",
            "7. Write audit records documenting dialogue-position stratum and allocation reason.",
            "8. Create a 100-row review subset from the final 1,500 using seed "
            f"**{REVIEW_RANDOM_SEED}** with coverage across position categories, specialties, "
            "and source dialogues.",
            "",
            "## Random Seeds",
            "",
            f"- Primary sampling seed: **{RANDOM_SEED}**",
            f"- Review subset seed: **{REVIEW_RANDOM_SEED}**",
            "",
            "## Extra-Late Dialogues",
            "",
            "The following dialogues received 6 targets (2 Early / 2 Middle / 2 Late):",
            "",
            ", ".join(extra_dialogues),
            "",
            "## Output Files",
            "",
            f"- `{OUTPUT_SAMPLE.name}`",
            f"- `{OUTPUT_REPORT.name}`",
            f"- `{OUTPUT_AUDIT.name}`",
            f"- `{OUTPUT_REVIEW.name}`",
            f"- `{Path(__file__).name}`",
        ]
    )

    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    eligible = eligible_rows(rows)
    selected, audit_rows = select_primary_sample(eligible)
    review = select_review_sample(selected)

    write_csv(OUTPUT_SAMPLE, SAMPLE_COLUMNS, selected)
    write_csv(OUTPUT_AUDIT, AUDIT_COLUMNS, audit_rows)
    write_csv(OUTPUT_REVIEW, SAMPLE_COLUMNS, review)
    write_report(eligible, selected, audit_rows)

    print(f"Eligible pool: {len(eligible):,}")
    print(f"Wrote {len(selected):,} contexts to {OUTPUT_SAMPLE}")
    print(f"Wrote audit to {OUTPUT_AUDIT}")
    print(f"Wrote {len(review)} review rows to {OUTPUT_REVIEW}")
    print(f"Wrote report to {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
