#!/usr/bin/env python3
"""Create the official frozen 100-context multi-model pilot set."""

from __future__ import annotations

import csv
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INPUT_FROZEN = ROOT / "final_1500_TRULY_FROZEN.csv"
OUTPUT_PILOT = ROOT / "pilot_100_FROZEN.csv"
OUTPUT_IDS = ROOT / "pilot_100_context_ids.csv"

RANDOM_SEED = 42
PILOT_SIZE = 100
POSITION_TARGETS = {"early": 36, "middle": 36, "late": 28}

PILOT_COLUMNS = [
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
    "context_word_count",
    "target_word_count",
]

ID_COLUMNS = [
    "context_id",
    "dialogue_id",
    "target_turn_id",
    "position_category",
]


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def select_pilot_contexts(
    rows: list[dict[str, str]], seed: int = RANDOM_SEED
) -> list[dict[str, str]]:
    """Select 100 contexts with maximal dialogue coverage and position stratification."""
    rng = random.Random(seed)

    by_position: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_position[row["position_category"].strip().lower()].append(row)

    for position, target in POSITION_TARGETS.items():
        if len(by_position[position]) < target:
            raise ValueError(
                f"Not enough {position} contexts: need {target}, have {len(by_position[position])}"
            )

    dialogues = sorted({row["dialogue_id"] for row in rows})
    rng.shuffle(dialogues)
    if len(dialogues) < PILOT_SIZE:
        raise ValueError(
            f"Need at least {PILOT_SIZE} dialogues for one-context-per-dialogue sampling."
        )

    assignments: list[tuple[str, str]] = []
    offset = 0
    for position, count in POSITION_TARGETS.items():
        for dialogue_id in dialogues[offset : offset + count]:
            assignments.append((position, dialogue_id))
        offset += count

    selected: list[dict[str, str]] = []
    used_context_ids: set[str] = set()
    used_target_ids: set[str] = set()
    used_dialogues: set[str] = set()

    for position, dialogue_id in assignments:
        if dialogue_id in used_dialogues:
            raise ValueError(f"Dialogue reused in assignment plan: {dialogue_id}")

        candidates = [
            row
            for row in by_position[position]
            if row["dialogue_id"] == dialogue_id and row["context_id"] not in used_context_ids
        ]
        if not candidates:
            raise ValueError(
                f"No context available for dialogue={dialogue_id}, position={position}"
            )

        rng.shuffle(candidates)
        pick = None
        for candidate in candidates:
            if candidate["target_turn_id"] not in used_target_ids:
                pick = candidate
                break
        if pick is None:
            raise ValueError(
                f"No unused target_turn_id for dialogue={dialogue_id}, position={position}"
            )

        selected.append(pick)
        used_context_ids.add(pick["context_id"])
        used_target_ids.add(pick["target_turn_id"])
        used_dialogues.add(dialogue_id)

    selected.sort(key=lambda row: row["context_id"])
    return selected


def validate_pilot(
    pilot_rows: list[dict[str, str]], source_rows: list[dict[str, str]]
) -> dict[str, object]:
    source_context_ids = {row["context_id"] for row in source_rows}
    source_target_ids = {row["target_turn_id"] for row in source_rows}

    context_ids = [row["context_id"] for row in pilot_rows]
    target_ids = [row["target_turn_id"] for row in pilot_rows]
    dialogue_ids = [row["dialogue_id"] for row in pilot_rows]
    position_counts = Counter(row["position_category"] for row in pilot_rows)

    if len(pilot_rows) != PILOT_SIZE:
        raise ValueError(f"Expected {PILOT_SIZE} rows, found {len(pilot_rows)}.")
    if len(set(context_ids)) != PILOT_SIZE:
        raise ValueError("Duplicate context_id values in pilot set.")
    if len(set(target_ids)) != PILOT_SIZE:
        raise ValueError("Duplicate target_turn_id values in pilot set.")
    if any(context_id not in source_context_ids for context_id in context_ids):
        raise ValueError("Pilot contains context_id values outside the frozen source.")
    if any(target_id not in source_target_ids for target_id in target_ids):
        raise ValueError("Pilot contains target_turn_id values outside the frozen source.")
    if position_counts != Counter(POSITION_TARGETS):
        raise ValueError(
            f"Position distribution mismatch. Expected {dict(POSITION_TARGETS)}, "
            f"found {dict(position_counts)}."
        )

    return {
        "row_count": len(pilot_rows),
        "unique_context_ids": len(set(context_ids)),
        "unique_target_ids": len(set(target_ids)),
        "unique_dialogues": len(set(dialogue_ids)),
        "position_counts": dict(position_counts),
    }


def main() -> None:
    if not INPUT_FROZEN.exists():
        raise FileNotFoundError(f"Missing input dataset: {INPUT_FROZEN}")

    source_rows = load_csv(INPUT_FROZEN)
    pilot_rows = select_pilot_contexts(source_rows)
    validation = validate_pilot(pilot_rows, source_rows)

    write_csv(OUTPUT_PILOT, PILOT_COLUMNS, pilot_rows)
    write_csv(
        OUTPUT_IDS,
        ID_COLUMNS,
        [{column: row[column] for column in ID_COLUMNS} for row in pilot_rows],
    )

    print("Official multi-model pilot set created.")
    print(f"Wrote {OUTPUT_PILOT.name}")
    print(f"Wrote {OUTPUT_IDS.name}")
    print("Validation:")
    print(f"  - rows: {validation['row_count']}")
    print(f"  - unique context IDs: {validation['unique_context_ids']}")
    print(f"  - unique target IDs: {validation['unique_target_ids']}")
    print(f"  - unique dialogues: {validation['unique_dialogues']}")
    print(f"  - position counts: {validation['position_counts']}")
    print(f"  - random seed: {RANDOM_SEED}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
