# Final Sampling Report

Frozen experimental sample constructed from `candidate_characteristics_v3.csv`.
Classification rules were not modified during sampling.

## Eligibility Criteria

1. `primary_turn_function == history_information_seeking`
2. `completed_exchanges_before_target >= 2`

No additional filters were applied.

## Pool and Sample Size

- Eligible pool before sampling: **11,573**
- Final frozen sample size: **1,500**
- Unique source dialogues represented: **272**

## Targets per Dialogue

- Mean: **5.51**
- Median: **6.0**
- SD: **0.50**
- Min / max: **5 / 6**

Allocation design:
- Base allocation for every dialogue: **2 Early + 2 Middle + 1 Late = 5 targets**
- Additional Late target added to the first **140** dialogues when sorted alphabetically by `dialogue_id`, yielding **2 Late** targets in those dialogues (**6 total** each).

## Position Category Distribution

| Category | Count | Percentage |
| --- | ---: | ---: |
| early | 544 | 36.27% |
| middle | 544 | 36.27% |
| late | 412 | 27.47% |

## Specialty Distribution

Sampling did **not** enforce equal specialty representation.

| Specialty | Count | Percentage |
| --- | ---: | ---: |
| Cardiovascular | 30 | 2.00% |
| Dermatological | 6 | 0.40% |
| Gastrointestinal | 36 | 2.40% |
| General | 6 | 0.40% |
| Musculoskeletal | 276 | 18.40% |
| Respiratory | 1,146 | 76.40% |

## Context Length (words)

- Mean / median / SD: **639.32 / 600.5 / 359.42**
- Min / max: **43 / 2036**

| Bin | Count |
| --- | ---: |
| 0-249 | 222 |
| 250-499 | 378 |
| 500-749 | 364 |
| 750-999 | 285 |
| 1000-1249 | 153 |
| 1250-1499 | 75 |
| 1500-1999 | 22 |
| 2000-100000 | 1 |

## Human Target Length (words)

- Mean / median / SD: **12.96 / 11.0 / 10.72**
- Min / max: **1 / 241**

| Bin | Count |
| --- | ---: |
| 0-4 | 113 |
| 5-9 | 529 |
| 10-14 | 402 |
| 15-19 | 223 |
| 20-29 | 180 |
| 30-49 | 39 |
| 50-100000 | 14 |

## Completed Exchange Distribution

| Completed exchanges before target | Count | Percentage |
| --- | ---: | ---: |
| 2 | 40 | 2.67% |
| 3 | 32 | 2.13% |
| 4 | 43 | 2.87% |
| 5 | 43 | 2.87% |
| 6 | 36 | 2.40% |
| 7 | 40 | 2.67% |
| 8 | 47 | 3.13% |
| 9 | 40 | 2.67% |
| 10 | 34 | 2.27% |
| 11 | 36 | 2.40% |
| 12 | 43 | 2.87% |
| 13 | 37 | 2.47% |
| 14 | 39 | 2.60% |
| 15 | 34 | 2.27% |
| 16 | 38 | 2.53% |
| 17 | 38 | 2.53% |
| 18 | 40 | 2.67% |
| 19 | 31 | 2.07% |
| 20 | 40 | 2.67% |
| 21 | 33 | 2.20% |
| 22 | 34 | 2.27% |
| 23 | 38 | 2.53% |
| 24 | 25 | 1.67% |
| 25 | 37 | 2.47% |
| 26 | 28 | 1.87% |
| 27 | 26 | 1.73% |
| 28 | 36 | 2.40% |
| 29 | 20 | 1.33% |
| 30 | 25 | 1.67% |
| 31 | 27 | 1.80% |
| 32 | 34 | 2.27% |
| 33 | 25 | 1.67% |
| 34 | 31 | 2.07% |
| 35 | 31 | 2.07% |
| 36 | 31 | 2.07% |
| 37 | 29 | 1.93% |
| 38 | 29 | 1.93% |
| 39 | 21 | 1.40% |
| 40 | 20 | 1.33% |
| 41 | 18 | 1.20% |
| 42 | 17 | 1.13% |
| 43 | 10 | 0.67% |
| 44 | 18 | 1.20% |
| 45 | 9 | 0.60% |
| 46 | 19 | 1.27% |
| 47 | 12 | 0.80% |
| 48 | 8 | 0.53% |
| 49 | 6 | 0.40% |
| 50 | 12 | 0.80% |
| 51 | 9 | 0.60% |
| 52 | 8 | 0.53% |
| 53 | 7 | 0.47% |
| 54 | 8 | 0.53% |
| 55 | 4 | 0.27% |
| 56 | 3 | 0.20% |
| 57 | 5 | 0.33% |
| 58 | 3 | 0.20% |
| 59 | 1 | 0.07% |
| 60 | 3 | 0.20% |
| 61 | 2 | 0.13% |
| 62 | 1 | 0.07% |
| 64 | 3 | 0.20% |
| 66 | 1 | 0.07% |
| 68 | 1 | 0.07% |
| 71 | 1 | 0.07% |

## Sampling Algorithm

1. Load all rows from `candidate_characteristics_v3.csv`.
2. Keep rows with `primary_turn_function == history_information_seeking` and `completed_exchanges_before_target >= 2`.
3. Group eligible rows by `dialogue_id` and `position_category`.
4. For each dialogue in alphabetical order:
   - Allocate 2 Early, 2 Middle, and 1 Late target by default.
   - Add a second Late target for the first 140 dialogues alphabetically to reach exactly 1,500.
5. Within each dialogue-position stratum with more eligible rows than required, randomly sample without replacement using seed **42**.
6. Assign unique `context_id` values in selection order (`CTX_0001` … `CTX_1500`).
7. Write audit records documenting dialogue-position stratum and allocation reason.
8. Create a 100-row review subset from the final 1,500 using seed **42** with coverage across position categories, specialties, and source dialogues.

## Random Seeds

- Primary sampling seed: **42**
- Review subset seed: **42**

## Extra-Late Dialogues

The following dialogues received 6 targets (2 Early / 2 Middle / 2 Late):

CAR0001, CAR0002, CAR0003, CAR0004, CAR0005, DER0001, GAS0001, GAS0002, GAS0003, GAS0004, GAS0005, GAS0007, GEN0001, MSK0001, MSK0003, MSK0004, MSK0005, MSK0006, MSK0007, MSK0008, MSK0009, MSK0010, MSK0011, MSK0012, MSK0013, MSK0014, MSK0015, MSK0016, MSK0017, MSK0018, MSK0019, MSK0020, MSK0021, MSK0022, MSK0023, MSK0024, MSK0025, MSK0026, MSK0027, MSK0028, MSK0029, MSK0031, MSK0032, MSK0033, MSK0034, MSK0035, MSK0036, MSK0037, MSK0038, MSK0039, MSK0040, MSK0041, MSK0042, MSK0043, MSK0044, MSK0045, MSK0046, MSK0049, MSK0050, RES0001, RES0002, RES0003, RES0004, RES0005, RES0006, RES0007, RES0008, RES0009, RES0010, RES0011, RES0012, RES0013, RES0014, RES0015, RES0016, RES0017, RES0018, RES0019, RES0020, RES0021, RES0022, RES0023, RES0024, RES0025, RES0026, RES0027, RES0028, RES0029, RES0030, RES0031, RES0032, RES0033, RES0034, RES0035, RES0036, RES0037, RES0038, RES0039, RES0042, RES0043, RES0044, RES0045, RES0046, RES0047, RES0048, RES0049, RES0050, RES0051, RES0052, RES0053, RES0054, RES0055, RES0056, RES0057, RES0058, RES0059, RES0060, RES0061, RES0062, RES0063, RES0064, RES0065, RES0066, RES0067, RES0068, RES0069, RES0070, RES0071, RES0072, RES0073, RES0074, RES0075, RES0076, RES0077, RES0078, RES0079, RES0080, RES0081, RES0082, RES0083

## Output Files

- `final_1500_contexts.csv`
- `final_sampling_report.md`
- `final_sampling_audit.csv`
- `final_sample_review.csv`
- `sample_final_1500.py`
