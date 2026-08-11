# Candidate Turn Report

Generated from `parse_candidate_turns.py` using all 272 OSCE clean transcripts.

## Overview

- Dialogues parsed: **272**
- Total doctor turns: **13385**
- Candidate next-doctor-turn instances: **13111**

Candidate rule: include every doctor turn immediately preceded by a patient turn.
No LLM generation, no sampling, and no subjective turn removal were applied.

## Specialty Distribution

| Specialty | Dialogues | Candidate turns | Avg candidates / dialogue |
| --- | ---: | ---: | ---: |
| Cardiovascular | 5 | 229 | 45.80 |
| Dermatological | 1 | 41 | 41.00 |
| Gastrointestinal | 6 | 235 | 39.17 |
| General | 1 | 38 | 38.00 |
| Musculoskeletal | 46 | 2467 | 53.63 |
| Respiratory | 213 | 10101 | 47.42 |

## Candidate Turns Per Dialogue

- Minimum: **22**
- Median: **48.0**
- Mean: **48.20**
- Maximum: **77**

| Candidate turns / dialogue | Dialogue count |
| ---: | ---: |
| 22 | 1 |
| 26 | 1 |
| 27 | 5 |
| 28 | 2 |
| 29 | 1 |
| 31 | 2 |
| 32 | 3 |
| 33 | 6 |
| 34 | 4 |
| 35 | 2 |
| 36 | 5 |
| 37 | 6 |
| 38 | 5 |
| 39 | 13 |
| 40 | 8 |
| 41 | 7 |
| 42 | 8 |
| 43 | 15 |
| 44 | 10 |
| 45 | 9 |
| 46 | 8 |
| 47 | 11 |
| 48 | 8 |
| 49 | 9 |
| 50 | 11 |
| 51 | 11 |
| 52 | 9 |
| 53 | 10 |
| 54 | 8 |
| 55 | 7 |
| 56 | 7 |
| 57 | 12 |
| 58 | 5 |
| 59 | 8 |
| 60 | 5 |
| 61 | 5 |
| 62 | 3 |
| 63 | 3 |
| 64 | 2 |
| 65 | 1 |
| 66 | 7 |
| 67 | 1 |
| 68 | 1 |
| 69 | 2 |
| 70 | 1 |
| 73 | 2 |
| 74 | 1 |
| 77 | 1 |

## Target Position Distribution

Normalized target position is computed within each dialogue as `candidate_turn_number / candidate_turns_in_dialogue`.

| Position third | Candidate turns | Share |
| --- | ---: | ---: |
| early | 4286 | 32.69% |
| middle | 4369 | 33.32% |
| late | 4456 | 33.99% |

## Output Files

- CSV: `all_candidate_turns.csv`
- Report: `candidate_turn_report.md`
- Parser: `parse_candidate_turns.py`
