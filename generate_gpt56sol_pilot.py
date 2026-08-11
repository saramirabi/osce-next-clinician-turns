#!/usr/bin/env python3
"""Generate GPT-5.6 Sol pilot responses for 100 position-matched OSCE contexts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from typing import Any

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)

PROJECT_DIR = Path(__file__).resolve().parent

PROMPT_VERSION = "PILOT_V1"
MODEL_ID = "gpt-5.6-sol"
MODEL_PROVIDER = "openai"
RANDOM_SEED = 42
PILOT_SIZE = 100
MAX_OUTPUT_TOKENS = 150
REQUESTED_TEMPERATURE = 0.0
REQUESTED_REASONING_EFFORT = "none"

INSTRUCTIONS = (
    "You are the clinician conducting a simulated medical history-taking interview.\n\n"
    "Based only on the conversation so far, produce the single next clinician turn "
    "that you would naturally say at this point.\n\n"
    "Continue the history-taking process. Do not provide a diagnosis, treatment "
    "recommendation, summary, explanation, or multiple alternative responses.\n\n"
    "Output only the next clinician utterance.\n\n"
    "Do not mention that you are an AI."
)

CONVERSATION_HEADER = "CONVERSATION:\n\n{context}"

PROMPT_TEMPLATE = (
    f"{INSTRUCTIONS}\n\n"
    f"{CONVERSATION_HEADER}"
)

INPUT_FROZEN = PROJECT_DIR / "final_1500_FROZEN.csv"
INPUT_V2 = PROJECT_DIR / "final_1500_contexts_v2.csv"
PILOT_IDS_FILE = PROJECT_DIR / "pilot_100_context_ids.csv"
OUTPUT_CSV = PROJECT_DIR / "pilot_gpt56sol_100.csv"
RAW_JSONL = PROJECT_DIR / "pilot_gpt56sol_raw.jsonl"
REPORT_MD = PROJECT_DIR / "pilot_gpt56sol_report.md"
CONFIG_JSON = PROJECT_DIR / "pilot_generation_config.json"

POSITION_TARGETS = {"early": 34, "middle": 33, "late": 33}

OUTPUT_COLUMNS = [
    "context_id",
    "dialogue_id",
    "specialty",
    "target_turn_id",
    "position_category",
    "normalized_target_position",
    "context",
    "latest_patient_turn",
    "human_doctor_target",
    "model_provider",
    "model_id",
    "prompt_version",
    "run_timestamp_utc",
    "requested_temperature",
    "actual_temperature_if_known",
    "requested_reasoning_effort",
    "actual_reasoning_effort_if_known",
    "max_output_tokens",
    "generated_doctor_turn",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "api_request_status",
    "retry_count",
    "error_message",
]

META_LANGUAGE_PATTERN = re.compile(r"\bas an ai\b", re.IGNORECASE)


def resolve_input_file() -> Path:
    if INPUT_FROZEN.exists():
        return INPUT_FROZEN
    if INPUT_V2.exists():
        print(
            "WARNING: final_1500_FROZEN.csv not found; using final_1500_contexts_v2.csv "
            "(PILOT ONLY — not final experimental results).",
            file=sys.stderr,
        )
        return INPUT_V2
    raise FileNotFoundError(
        "Neither final_1500_FROZEN.csv nor final_1500_contexts_v2.csv was found."
    )


def load_dataset(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"No rows found in {path}")
    return rows


def select_pilot_contexts(rows: list[dict[str, str]], seed: int = RANDOM_SEED) -> list[dict[str, str]]:
    """Select 100 contexts stratified by position with maximal dialogue coverage."""
    rng = random.Random(seed)

    by_position: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_position[row["position_category"].strip().lower()].append(row)

    for pos, target in POSITION_TARGETS.items():
        if pos not in by_position:
            raise ValueError(f"Missing position category: {pos}")
        if len(by_position[pos]) < target:
            raise ValueError(
                f"Not enough contexts for {pos}: need {target}, have {len(by_position[pos])}"
            )

    dialogues = sorted({row["dialogue_id"] for row in rows})
    rng.shuffle(dialogues)
    if len(dialogues) < PILOT_SIZE:
        raise ValueError(f"Need at least {PILOT_SIZE} dialogues, found {len(dialogues)}")

    assignments: list[tuple[str, str]] = []
    offset = 0
    for pos, count in POSITION_TARGETS.items():
        for dialogue_id in dialogues[offset : offset + count]:
            assignments.append((pos, dialogue_id))
        offset += count

    selected: list[dict[str, str]] = []
    used_context_ids: set[str] = set()
    used_target_ids: set[str] = set()

    for pos, dialogue_id in assignments:
        candidates = [
            row
            for row in by_position[pos]
            if row["dialogue_id"] == dialogue_id and row["context_id"] not in used_context_ids
        ]
        if not candidates:
            raise ValueError(
                f"No unused context for dialogue {dialogue_id} in position {pos}"
            )
        rng.shuffle(candidates)
        pick = candidates[0]
        if pick["target_turn_id"] in used_target_ids:
            for alt in candidates[1:]:
                if alt["target_turn_id"] not in used_target_ids:
                    pick = alt
                    break
            else:
                raise ValueError(
                    f"All candidates for {dialogue_id}/{pos} have duplicate target_turn_id"
                )
        selected.append(pick)
        used_context_ids.add(pick["context_id"])
        used_target_ids.add(pick["target_turn_id"])

    selected.sort(key=lambda row: row["context_id"])
    return selected


def save_pilot_ids(selected: list[dict[str, str]], path: Path) -> None:
    fieldnames = [
        "context_id",
        "dialogue_id",
        "specialty",
        "target_turn_id",
        "position_category",
        "normalized_target_position",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in selected:
            writer.writerow({key: row[key] for key in fieldnames})


def load_or_create_pilot_ids(
    rows: list[dict[str, str]], force_resample: bool = False
) -> list[dict[str, str]]:
    if PILOT_IDS_FILE.exists() and not force_resample:
        with PILOT_IDS_FILE.open(newline="", encoding="utf-8") as handle:
            id_rows = list(csv.DictReader(handle))
        id_set = {row["context_id"] for row in id_rows}
        selected = [row for row in rows if row["context_id"] in id_set]
        if len(selected) != PILOT_SIZE:
            raise ValueError(
                f"{PILOT_IDS_FILE} contains {len(id_set)} IDs but matched "
                f"{len(selected)} rows in the input dataset."
            )
        selected.sort(key=lambda row: row["context_id"])
        return selected

    if PILOT_IDS_FILE.exists() and force_resample:
        raise RuntimeError(
            f"{PILOT_IDS_FILE} already exists; refusing to resample without manual deletion."
        )

    selected = select_pilot_contexts(rows)
    save_pilot_ids(selected, PILOT_IDS_FILE)
    return selected


def build_user_input(context: str) -> str:
    """User input sent to the API (context only; instructions are separate)."""
    return CONVERSATION_HEADER.format(context=context)


def build_full_prompt_preview(context: str) -> str:
    """Full prompt text for validation previews (instructions + conversation)."""
    return PROMPT_TEMPLATE.format(context=context)


def validate_before_run(selected: list[dict[str, str]]) -> None:
    context_ids = [row["context_id"] for row in selected]
    target_ids = [row["target_turn_id"] for row in selected]

    if len(context_ids) != PILOT_SIZE:
        raise RuntimeError(f"Expected {PILOT_SIZE} contexts, got {len(context_ids)}")
    if len(set(context_ids)) != len(context_ids):
        raise RuntimeError("Duplicate context_id values in pilot sample.")
    if len(set(target_ids)) != len(target_ids):
        raise RuntimeError("Duplicate target_turn_id values in pilot sample.")

    for row in selected:
        user_input = build_user_input(row["context"])
        full_prompt = build_full_prompt_preview(row["context"])
        if not row["context"].strip():
            raise RuntimeError(f"Empty context for {row['context_id']}")
        if row["context"] not in user_input:
            raise RuntimeError(f"API input missing context for {row['context_id']}")
        if row["context"] not in full_prompt:
            raise RuntimeError(f"Prompt preview missing context for {row['context_id']}")
        if "human_doctor_target" in user_input.lower() or "human_doctor_target" in INSTRUCTIONS.lower():
            raise RuntimeError(
                f"human_doctor_target field label leaked into prompt for {row['context_id']}"
            )

    print("Validation passed:")
    print(f"  - {len(context_ids)} unique pilot context IDs")
    print(f"  - {len(set(target_ids))} unique target_turn_id values")
    print("  - Every prompt contains its context")
    print("  - Zero prompts contain the human_doctor_target field label")
    print("\nPrompt preview (3 examples):\n")
    preview_rows = selected[:3]
    for index, row in enumerate(preview_rows, start=1):
        print(f"--- Preview {index}: {row['context_id']} ({row['position_category']}) ---")
        print(build_full_prompt_preview(row["context"]))
        print()


def load_completed_context_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row.get("api_request_status") == "success":
                completed.add(row["context_id"])
    return completed


def append_csv_row(path: Path, row: dict[str, Any]) -> None:
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerow({col: row.get(col, "") for col in OUTPUT_COLUMNS})


def append_raw_jsonl(record: dict[str, Any]) -> None:
    with RAW_JSONL.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def response_to_dict(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")
    if hasattr(response, "to_dict"):
        return response.to_dict()
    return dict(response)


def extract_actual_reasoning_effort(response: Any) -> str | None:
    reasoning = getattr(response, "reasoning", None)
    if reasoning is None:
        return None
    effort = getattr(reasoning, "effort", None)
    return str(effort) if effort is not None else None


def call_model_with_retries(
    client: OpenAI,
    *,
    context_id: str,
    user_input: str,
    generation_settings: dict[str, Any],
    max_retries: int = 6,
) -> tuple[Any | None, int, str | None, dict[str, Any]]:
    retry_count = 0
    last_error: str | None = None
    request_kwargs = dict(generation_settings["request_kwargs"])
    parameter_log: list[str] = list(generation_settings.get("parameter_log", []))

    while retry_count <= max_retries:
        try:
            response = client.responses.create(**request_kwargs)
            metadata = {
                "parameter_log": parameter_log,
                "request_kwargs_keys": sorted(request_kwargs.keys()),
            }
            return response, retry_count, None, metadata
        except TypeError as exc:
            message = str(exc)
            handled = False
            if "temperature" in message and "temperature" in request_kwargs:
                parameter_log.append(
                    f"temperature={request_kwargs['temperature']} unsupported; using API default"
                )
                request_kwargs.pop("temperature", None)
                handled = True
            if "reasoning" in message and "reasoning" in request_kwargs:
                parameter_log.append(
                    f"reasoning={request_kwargs['reasoning']} unsupported; using API default"
                )
                request_kwargs.pop("reasoning", None)
                handled = True
            if handled:
                continue
            return None, retry_count, message, {"parameter_log": parameter_log}
        except (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError) as exc:
            last_error = str(exc)
            if retry_count >= max_retries:
                break
            sleep_seconds = min(60, 2**retry_count)
            time.sleep(sleep_seconds)
            retry_count += 1
        except Exception as exc:  # noqa: BLE001 - preserve API errors for output row
            return None, retry_count, str(exc), {"parameter_log": parameter_log}

    return None, retry_count, last_error, {"parameter_log": parameter_log}


def build_generation_settings() -> dict[str, Any]:
    request_kwargs: dict[str, Any] = {
        "model": MODEL_ID,
        "instructions": INSTRUCTIONS,
        "input": "{context_placeholder}",
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "temperature": REQUESTED_TEMPERATURE,
        "reasoning": {"effort": REQUESTED_REASONING_EFFORT},
        "store": False,
    }
    return {
        "request_kwargs_template": {
            key: value for key, value in request_kwargs.items() if key != "input"
        },
        "request_kwargs": request_kwargs,
        "parameter_log": [],
    }


def save_config(input_filename: str) -> None:
    config = {
        "model_id": MODEL_ID,
        "model_provider": MODEL_PROVIDER,
        "prompt_version": PROMPT_VERSION,
        "prompt_template": PROMPT_TEMPLATE,
        "instructions": INSTRUCTIONS,
        "generation_settings": {
            "temperature": REQUESTED_TEMPERATURE,
            "reasoning_effort": REQUESTED_REASONING_EFFORT,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "tools": None,
            "web_search": False,
            "text_output_only": True,
        },
        "random_seed": RANDOM_SEED,
        "pilot_size": PILOT_SIZE,
        "position_targets": POSITION_TARGETS,
        "input_filename": input_filename,
        "pilot_id_filename": PILOT_IDS_FILE.name,
        "output_csv": OUTPUT_CSV.name,
        "raw_jsonl": RAW_JSONL.name,
        "run_date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    CONFIG_JSON.write_text(json.dumps(config, indent=2), encoding="utf-8")


def count_words(text: str) -> int:
    return len(text.split())


def write_report(rows: list[dict[str, Any]], total_retries: int, input_filename: str) -> None:
    successes = [row for row in rows if row.get("api_request_status") == "success"]
    failures = [row for row in rows if row.get("api_request_status") != "success"]

    input_tokens = [int(row["input_tokens"]) for row in successes if row.get("input_tokens")]
    output_tokens = [int(row["output_tokens"]) for row in successes if row.get("output_tokens")]

    empty_responses = sum(
        1 for row in successes if not str(row.get("generated_doctor_turn", "")).strip()
    )
    over_100_words = sum(
        1
        for row in successes
        if count_words(str(row.get("generated_doctor_turn", ""))) > 100
    )
    meta_language = sum(
        1
        for row in successes
        if META_LANGUAGE_PATTERN.search(str(row.get("generated_doctor_turn", "")))
    )
    multi_paragraph = sum(
        1
        for row in successes
        if len(re.split(r"\n\s*\n", str(row.get("generated_doctor_turn", "")).strip())) > 1
    )

    position_counts = Counter(row.get("position_category", "") for row in successes)
    dialogue_coverage = len({row.get("dialogue_id") for row in successes})

    lines = [
        "# GPT-5.6 Sol Pilot Generation Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Run configuration",
        "",
        f"- Input dataset: `{input_filename}`",
        f"- Pilot ID file: `{PILOT_IDS_FILE.name}`",
        f"- Model: `{MODEL_ID}`",
        f"- Prompt version: `{PROMPT_VERSION}`",
        f"- Random seed: `{RANDOM_SEED}`",
        "",
        "## Completion summary",
        "",
        f"- Requested contexts: {PILOT_SIZE}",
        f"- Successfully generated: {len(successes)}",
        f"- Failed: {len(failures)}",
        f"- Total retries across requests: {total_retries}",
        "",
        "## Pilot sample coverage",
        "",
        f"- Unique dialogues represented: {dialogue_coverage}",
        f"- Position counts (successful rows): early={position_counts.get('early', 0)}, "
        f"middle={position_counts.get('middle', 0)}, late={position_counts.get('late', 0)}",
        "",
        "## Token usage",
        "",
    ]

    if input_tokens:
        lines.extend(
            [
                f"- Mean input tokens: {mean(input_tokens):.1f}",
                f"- Median input tokens: {median(input_tokens):.1f}",
                f"- Mean output tokens: {mean(output_tokens):.1f}",
                f"- Median output tokens: {median(output_tokens):.1f}",
                f"- Total input tokens: {sum(input_tokens)}",
                f"- Total output tokens: {sum(output_tokens)}",
                "",
            ]
        )
    else:
        lines.append("- No successful token usage recorded.\n")

    lines.extend(
        [
            "## Estimated API cost",
            "",
            "Pricing constants were not supplied separately; cost estimate not computed.",
            "",
            "## Response shape checks",
            "",
            f"- Empty responses: {empty_responses}",
            f"- Responses exceeding 100 words: {over_100_words}",
            f"- Responses containing obvious meta-language ('As an AI'): {meta_language}",
            f"- Responses containing more than one paragraph: {multi_paragraph}",
            "",
        ]
    )

    if failures:
        lines.extend(["## Failures", ""])
        for row in failures:
            lines.append(
                f"- `{row.get('context_id')}`: {row.get('error_message', 'unknown error')}"
            )
        lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def run_generation(selected: list[dict[str, str]], input_filename: str) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is not set. Export it before using --run."
        )

    client = OpenAI(api_key=api_key)
    generation_settings = build_generation_settings()
    completed = load_completed_context_ids(OUTPUT_CSV)
    total_retries = 0
    all_rows: list[dict[str, Any]] = []

    if OUTPUT_CSV.exists():
        with OUTPUT_CSV.open(newline="", encoding="utf-8") as handle:
            all_rows = list(csv.DictReader(handle))

    pending = [row for row in selected if row["context_id"] not in completed]
    print(f"Resume state: {len(completed)} completed, {len(pending)} pending.")

    for index, row in enumerate(pending, start=1):
        context_id = row["context_id"]
        user_input = build_user_input(row["context"])
        timestamp = datetime.now(timezone.utc).isoformat()

        request_kwargs = dict(generation_settings["request_kwargs_template"])
        request_kwargs["input"] = user_input

        response, retry_count, error_message, call_metadata = call_model_with_retries(
            client,
            context_id=context_id,
            user_input=user_input,
            generation_settings={
                "request_kwargs": request_kwargs,
                "parameter_log": generation_settings["parameter_log"],
            },
        )
        total_retries += retry_count

        output_row: dict[str, Any] = {
            "context_id": context_id,
            "dialogue_id": row["dialogue_id"],
            "specialty": row["specialty"],
            "target_turn_id": row["target_turn_id"],
            "position_category": row["position_category"],
            "normalized_target_position": row["normalized_target_position"],
            "context": row["context"],
            "latest_patient_turn": row["latest_patient_turn"],
            "human_doctor_target": row["human_doctor_target"],
            "model_provider": MODEL_PROVIDER,
            "model_id": MODEL_ID,
            "prompt_version": PROMPT_VERSION,
            "run_timestamp_utc": timestamp,
            "requested_temperature": REQUESTED_TEMPERATURE,
            "actual_temperature_if_known": "",
            "requested_reasoning_effort": REQUESTED_REASONING_EFFORT,
            "actual_reasoning_effort_if_known": "",
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            "generated_doctor_turn": "",
            "input_tokens": "",
            "output_tokens": "",
            "total_tokens": "",
            "api_request_status": "failed",
            "retry_count": retry_count,
            "error_message": error_message or "",
        }

        raw_record: dict[str, Any] = {
            "context_id": context_id,
            "timestamp_utc": timestamp,
            "model_id": MODEL_ID,
            "prompt_version": PROMPT_VERSION,
            "request_metadata": {
                "requested_temperature": REQUESTED_TEMPERATURE,
                "requested_reasoning_effort": REQUESTED_REASONING_EFFORT,
                "max_output_tokens": MAX_OUTPUT_TOKENS,
                "retry_count": retry_count,
                "parameter_log": call_metadata.get("parameter_log", []),
            },
            "status": "failed",
            "error_message": error_message,
            "raw_text_response": "",
            "usage_metadata": {},
        }

        if response is not None:
            generated_text = response.output_text
            usage = getattr(response, "usage", None)
            output_row["generated_doctor_turn"] = generated_text
            output_row["actual_temperature_if_known"] = (
                "" if response.temperature is None else str(response.temperature)
            )
            actual_effort = extract_actual_reasoning_effort(response)
            output_row["actual_reasoning_effort_if_known"] = actual_effort or ""
            if usage is not None:
                output_row["input_tokens"] = usage.input_tokens
                output_row["output_tokens"] = usage.output_tokens
                output_row["total_tokens"] = usage.total_tokens
            output_row["api_request_status"] = "success"
            output_row["error_message"] = ""

            raw_record["status"] = "success"
            raw_record["raw_text_response"] = generated_text
            raw_record["usage_metadata"] = (
                usage.model_dump(mode="json") if hasattr(usage, "model_dump") else {}
            )
            raw_record["response_object"] = response_to_dict(response)
            raw_record["request_metadata"]["response_model"] = str(response.model)

        append_csv_row(OUTPUT_CSV, output_row)
        append_raw_jsonl(raw_record)
        all_rows = [existing for existing in all_rows if existing.get("context_id") != context_id]
        all_rows.append(output_row)

        status = output_row["api_request_status"]
        print(f"[{index}/{len(pending)}] {context_id}: {status}")

    write_report(all_rows, total_retries, input_filename)

    success_count = sum(1 for row in all_rows if row.get("api_request_status") == "success")
    if success_count == PILOT_SIZE:
        print(f"Pilot complete: {success_count}/{PILOT_SIZE} successful responses.")
    else:
        print(
            f"Pilot incomplete: {success_count}/{PILOT_SIZE} successful responses. "
            "Re-run with --run to resume."
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate GPT-5.6 Sol pilot responses.")
    parser.add_argument(
        "--run",
        action="store_true",
        help="Perform real OpenAI API calls after validation.",
    )
    args = parser.parse_args()

    input_path = resolve_input_file()
    rows = load_dataset(input_path)
    selected = load_or_create_pilot_ids(rows)
    save_config(input_path.name)

    validate_before_run(selected)

    if not args.run:
        print("Validation complete. No API calls made.")
        print("Re-run with --run to execute the pilot generation.")
        return

    run_generation(selected, input_path.name)


if __name__ == "__main__":
    main()
