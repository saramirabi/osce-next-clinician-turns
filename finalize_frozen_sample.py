#!/usr/bin/env python3
"""Finalize frozen 1,500 sample using manual eligibility audit decisions."""

from __future__ import annotations

import csv
import random
from collections import Counter
from pathlib import Path
from statistics import mean, median, pstdev

import sample_final_1500_v2 as qc

ROOT = Path(__file__).resolve().parent
REVIEWED_AUDIT = ROOT / "final_eligibility_audit_for_review.csv"
INPUT_SAMPLE = ROOT / "final_1500_contexts_v2.csv"
INPUT_CHARACTERISTICS = ROOT / "candidate_characteristics_v3.csv"
OUTPUT_FROZEN = ROOT / "final_1500_FROZEN.csv"
OUTPUT_REPLACEMENT_AUDIT = ROOT / "final_replacement_audit.csv"
OUTPUT_REPORT = ROOT / "final_frozen_sample_report.md"

RANDOM_SEED = 42
DECISION_COLUMNS = ("manual_decision", "manual_reason")
DECISION_ALIASES = ("manual_decision", "decision", "review_decision", "manual review")
REASON_ALIASES = ("manual_reason", "reason", "review_reason", "manual review reason")
SAMPLE_COLUMNS = qc.SAMPLE_COLUMNS
REPLACEMENT_AUDIT_COLUMNS = [
    "original_context_id",
    "removed_target_turn_id",
    "manual_reason",
    "replacement_target_turn_id",
    "replacement_context_id",
    "dialogue_id",
    "position_category",
    "replacement_selection_reason",
]


def normalize_decision(value: str) -> str:
    return value.strip().upper()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def resolve_column(fieldnames: list[str], aliases: tuple[str, ...]) -> str | None:
    normalized = {name.strip().lower(): name for name in fieldnames}
    for alias in aliases:
        if alias in normalized:
            return normalized[alias]
    return None


def load_manual_decisions() -> tuple[list[dict[str, str]], list[dict[str, str]], str]:
    rows = load_csv(REVIEWED_AUDIT)
    fieldnames = list(rows[0].keys()) if rows else []
    decision_col = resolve_column(fieldnames, DECISION_ALIASES)
    reason_col = resolve_column(fieldnames, REASON_ALIASES)

    keep_rows: list[dict[str, str]] = []
    exclude_rows: list[dict[str, str]] = []
    mode = "explicit_manual_decisions"

    if decision_col is None:
        mode = "default_keep_no_manual_decision_column"
        for row in rows:
            keep_rows.append(row)
        return keep_rows, exclude_rows, mode

    for row in rows:
        decision = normalize_decision(row.get(decision_col, ""))
        if decision in ("", "KEEP"):
            keep_rows.append(row)
        elif decision == "EXCLUDE":
            exclude_rows.append(row)
        else:
            raise ValueError(
                f"Unsupported {decision_col} `{row.get(decision_col)}` "
                f"for {row.get('context_id')}."
            )
        if reason_col:
            row["_manual_reason"] = row.get(reason_col, "")
        else:
            row["_manual_reason"] = ""
    return keep_rows, exclude_rows, mode


def build_eligible_pool(characteristics: list[dict[str, str]]) -> dict[tuple[str, str], list[dict[str, str]]]:
    pool: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in qc.eligible_rows(characteristics):
        key = (row["dialogue_id"], row["position_category"])
        pool.setdefault(key, []).append(row)
    return pool


def choose_replacement(
    rng: random.Random,
    dialogue_id: str,
    position_category: str,
    selected_target_ids: set[str],
    eligible_pool: dict[tuple[str, str], list[dict[str, str]]],
) -> tuple[dict[str, str], str]:
    candidates = [
        row
        for row in eligible_pool.get((dialogue_id, position_category), [])
        if row["target_turn_id"] not in selected_target_ids
    ]
    if not candidates:
        raise ValueError(
            f"No replacement available for dialogue={dialogue_id}, position={position_category}."
        )

    clean = [row for row in candidates if not qc.audit_flags_for_row(row)]
    pool = clean if clean else candidates
    selection_reason = (
        "unflagged_replacement" if clean else "flagged_replacement_fallback"
    )
    rng.shuffle(pool)
    return pool[0], selection_reason


def finalize_sample() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], list[dict[str, str]], str]:
    keep_rows, exclude_rows, mode = load_manual_decisions()
    sample_rows = load_csv(INPUT_SAMPLE)
    characteristics = load_csv(INPUT_CHARACTERISTICS)
    characteristics_by_target = {row["target_turn_id"]: row for row in characteristics}
    eligible_pool = build_eligible_pool(characteristics)

    sample_by_context = {row["context_id"]: dict(row) for row in sample_rows}
    exclude_context_ids = {row["context_id"] for row in exclude_rows}
    if not exclude_context_ids:
        return [dict(row) for row in sample_rows], [], keep_rows, exclude_rows, mode

    rng = random.Random(RANDOM_SEED)
    replacement_audit: list[dict[str, str]] = []
    selected_target_ids = {
        row["target_turn_id"]
        for context_id, row in sample_by_context.items()
        if context_id not in exclude_context_ids
    }

    for exclude_row in exclude_rows:
        context_id = exclude_row["context_id"]
        if context_id not in sample_by_context:
            raise ValueError(f"Excluded context_id not found in sample: {context_id}")

        original = sample_by_context[context_id]
        replacement, selection_reason = choose_replacement(
            rng,
            original["dialogue_id"],
            original["position_category"],
            selected_target_ids,
            eligible_pool,
        )
        selected_target_ids.add(replacement["target_turn_id"])

        enriched = {**replacement}
        enriched["context_id"] = context_id
        sample_by_context[context_id] = enriched

        replacement_audit.append(
            {
                "original_context_id": context_id,
                "removed_target_turn_id": original["target_turn_id"],
                "manual_reason": exclude_row.get("_manual_reason")
                or exclude_row.get("manual_reason", ""),
                "replacement_target_turn_id": replacement["target_turn_id"],
                "replacement_context_id": context_id,
                "dialogue_id": original["dialogue_id"],
                "position_category": original["position_category"],
                "replacement_selection_reason": selection_reason,
            }
        )

    frozen = [sample_by_context[row["context_id"]] for row in sample_rows]
    return frozen, replacement_audit, keep_rows, exclude_rows, mode


def verify_frozen_sample(rows: list[dict[str, str]]) -> None:
    if len(rows) != 1500:
        raise ValueError(f"Expected 1500 rows, found {len(rows)}.")

    target_ids = [row["target_turn_id"] for row in rows]
    if len(set(target_ids)) != 1500:
        raise ValueError("Duplicate target_turn_id values found in frozen sample.")

    per_dialogue = Counter(row["dialogue_id"] for row in rows)
    if len(per_dialogue) != 272:
        raise ValueError(f"Expected 272 dialogues, found {len(per_dialogue)}.")

    per_dialogue_values = set(per_dialogue.values())
    if per_dialogue_values - {5, 6}:
        raise ValueError(f"Unexpected targets-per-dialogue values: {sorted(per_dialogue_values)}")

    position_counts = Counter(row["position_category"] for row in rows)
    expected_position = Counter({"early": 544, "middle": 544, "late": 412})
    if position_counts != expected_position:
        raise ValueError(
            "Position allocation mismatch. "
            f"Expected {dict(expected_position)}, found {dict(position_counts)}."
        )


def write_report(
    frozen: list[dict[str, str]],
    replacement_audit: list[dict[str, str]],
    keep_rows: list[dict[str, str]],
    exclude_rows: list[dict[str, str]],
    decision_mode: str,
) -> None:
    per_dialogue = Counter(row["dialogue_id"] for row in frozen)
    per_dialogue_values = list(per_dialogue.values())
    position_counts = Counter(row["position_category"] for row in frozen)
    specialty_counts = Counter(row["specialty"] for row in frozen)
    context_words = [int(row["context_word_count"]) for row in frozen]
    target_words = [int(row["target_word_count"]) for row in frozen]
    exchanges = [int(row["completed_exchanges_before_target"]) for row in frozen]

    lines = [
        "# Final Frozen Sample Report",
        "",
        "The experimental sample is finalized and should be treated as immutable before LLM generation.",
        "",
        "## Manual Review Applied",
        "",
        f"- Audit rows reviewed: **{len(keep_rows) + len(exclude_rows)}**",
        f"- Rows marked KEEP: **{len(keep_rows)}**",
        f"- Rows marked EXCLUDE: **{len(exclude_rows)}**",
        f"- Replacements made: **{len(replacement_audit)}**",
        f"- Decision source mode: **{decision_mode}**",
        "",
        "## Final Sample Checks",
        "",
        f"- Final sample size: **{len(frozen):,}**",
        f"- Unique target IDs: **{len(set(row['target_turn_id'] for row in frozen)):,}**",
        f"- Unique dialogues: **{len(per_dialogue):,}**",
        f"- Targets per dialogue mean / median / SD: "
        f"**{mean(per_dialogue_values):.2f} / {median(per_dialogue_values):.1f} / "
        f"{pstdev(per_dialogue_values):.2f}**",
        f"- Targets per dialogue min / max: **{min(per_dialogue_values)} / {max(per_dialogue_values)}**",
        "",
        "### Position Category Distribution",
        "",
        "| Category | Count | Percentage |",
        "| --- | ---: | ---: |",
    ]

    for category in ("early", "middle", "late"):
        count = position_counts[category]
        lines.append(f"| {category} | {count:,} | {count / len(frozen) * 100:.2f}% |")

    lines.extend(
        [
            "",
            "### Specialty Distribution",
            "",
            "| Specialty | Count | Percentage |",
            "| --- | ---: | ---: |",
        ]
    )
    for specialty in sorted(specialty_counts):
        count = specialty_counts[specialty]
        lines.append(f"| {specialty} | {count:,} | {count / len(frozen) * 100:.2f}% |")

    lines.extend(
        [
            "",
            "### Context and Target Length",
            "",
            f"- Context words mean / median / SD: **{mean(context_words):.2f} / {median(context_words):.1f} / {pstdev(context_words):.2f}**",
            f"- Target words mean / median / SD: **{mean(target_words):.2f} / {median(target_words):.1f} / {pstdev(target_words):.2f}**",
            "",
            "### Completed Exchanges Before Target",
            "",
            f"- Mean: **{mean(exchanges):.2f}**",
            f"- Min / max: **{min(exchanges)} / {max(exchanges)}**",
            "",
            "## Replacement Policy",
            "",
            "For each manually excluded target:",
            "- Removed from `final_1500_contexts_v2.csv` by `context_id`.",
            "- Replaced from the same `dialogue_id` and `position_category` stratum.",
            "- Replacement candidates required `primary_turn_function == history_information_seeking` "
            "and `completed_exchanges_before_target >= 2`.",
            "- Unflagged eligible replacements were preferred; otherwise deterministic fallback among remaining eligible targets.",
            f"- Random seed: **{RANDOM_SEED}**",
            "",
            "## Output Files",
            "",
            f"- `{OUTPUT_FROZEN.name}`",
            f"- `{OUTPUT_REPLACEMENT_AUDIT.name}`",
            f"- `{OUTPUT_REPORT.name}`",
            f"- `{Path(__file__).name}`",
        ]
    )

    OUTPUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    frozen, replacement_audit, keep_rows, exclude_rows, decision_mode = finalize_sample()
    verify_frozen_sample(frozen)

    write_csv(OUTPUT_FROZEN, SAMPLE_COLUMNS, frozen)
    write_csv(OUTPUT_REPLACEMENT_AUDIT, REPLACEMENT_AUDIT_COLUMNS, replacement_audit)
    write_report(frozen, replacement_audit, keep_rows, exclude_rows, decision_mode)

    print(f"Decision mode: {decision_mode}")
    print(f"Manual EXCLUDE rows: {len(exclude_rows)}")
    print(f"Replacements made: {len(replacement_audit)}")
    print(f"Wrote frozen sample to {OUTPUT_FROZEN}")
    print(f"Wrote replacement audit to {OUTPUT_REPLACEMENT_AUDIT}")
    print(f"Wrote report to {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
