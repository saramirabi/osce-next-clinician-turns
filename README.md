# OSCE Next-Clinician-Turn Dataset

Position-matched next-doctor-turn prediction dataset and multi-model pilot outputs
from OSCE clinical consultation dialogues (Fareez et al. corpus).

## Frozen experimental sample

- `final_1500_TRULY_FROZEN.csv` — 1,500 eligible history-taking targets (272 dialogues)
- `pilot_100_FROZEN.csv` — official 100-context multi-model pilot set

## Multi-model pilot outputs (NEXT_TURN_V1)

| Model | Output CSV | Config |
| --- | --- | --- |
| GPT (`gpt-5.6-sol`) | `pilot_GPT_100_NEXT_TURN_V1.csv` | `GPT_NEXT_TURN_V1_config.json` |
| Gemini (`gemini-2.5-flash`) | `pilot_Gemini_100_NEXT_TURN_V1.csv` | `Gemini_NEXT_TURN_V1_config.json` |
| Claude (`claude-sonnet-4-6`) | `pilot_Claude_100_NEXT_TURN_V1.csv` | `Claude_NEXT_TURN_V1_config.json` |

Raw API responses are stored in matching `*_raw.jsonl` files. Pilot reports are in `*_report.md`.

## Pipeline scripts

- Parsing and classification: `parse_candidate_turns.py`, `analyze_candidate_turns_v3.py`
- Sampling: `sample_final_1500_v2.py`, `finalize_truly_frozen_sample.py`, `create_pilot_100_frozen.py`
- Generation: `generate_gpt_next_turn_v1.py`, `generate_gemini_next_turn_v1.py`, `generate_claude_next_turn_v1.py`
