# Final Sampling Report v2

Frozen experimental sample reconstructed with random extra-late dialogue allocation.
V3 classification rules were not modified.

## Eligibility Criteria

1. `primary_turn_function == history_information_seeking`
2. `completed_exchanges_before_target >= 2`

## Pool and Sample Size

- Eligible pool before sampling: **11,573**
- Final frozen sample size: **1,500**
- Unique source dialogues represented: **272**

## Targets per Dialogue

- Mean: **5.51**
- Median: **6.0**
- SD: **0.50**
- Min / max: **5 / 6**

## Allocation Design

- Base allocation for every dialogue: **2 Early + 2 Middle + 1 Late = 5**
- Additional Late target added to **140** dialogues randomly selected among dialogues with at least **2** eligible Late targets.
- Random seed for extra-late dialogue selection and within-stratum sampling: **42**

## Position Category Distribution

| Category | Count | Percentage |
| --- | ---: | ---: |
| early | 544 | 36.27% |
| middle | 544 | 36.27% |
| late | 412 | 27.47% |

## Specialty Distribution

| Specialty | Count | Percentage |
| --- | ---: | ---: |
| Cardiovascular | 26 | 1.73% |
| Dermatological | 5 | 0.33% |
| Gastrointestinal | 32 | 2.13% |
| General | 6 | 0.40% |
| Musculoskeletal | 259 | 17.27% |
| Respiratory | 1,172 | 78.13% |

## Context and Target Length

- Context words mean / median / SD: **641.28 / 603.0 / 360.90**
- Target words mean / median / SD: **13.00 / 11.0 / 9.45**

## Completed Exchange Distribution

- Mean completed exchanges before target: **22.96**

## Sampling Algorithm

1. Filter eligible rows from `candidate_characteristics_v3.csv`.
2. Group by `dialogue_id` and `position_category`.
3. Randomly choose 140 dialogues with at least 2 eligible Late targets for the extra Late slot.
4. For each dialogue, allocate 2 Early, 2 Middle, and 1 or 2 Late targets.
5. Randomly sample within each dialogue-position stratum without replacement using seed 42.
6. Assign `context_id` values in selection order.

## Pre-Generation Eligibility Audit

- Flagged targets for manual review: **61**
- Output file: `final_eligibility_audit_for_review.csv`
- Flagged rows were **not** automatically removed.

## Extra-Late Dialogues (Random Selection)

CAR0002, GAS0003, GAS0007, GEN0001, MSK0001, MSK0003, MSK0004, MSK0005, MSK0006, MSK0007, MSK0009, MSK0012, MSK0013, MSK0014, MSK0015, MSK0017, MSK0020, MSK0024, MSK0025, MSK0028, MSK0029, MSK0031, MSK0033, MSK0034, MSK0037, MSK0039, MSK0042, MSK0043, MSK0044, MSK0045, MSK0046, MSK0049, MSK0050, RES0001, RES0004, RES0005, RES0006, RES0009, RES0010, RES0011, RES0013, RES0016, RES0017, RES0022, RES0025, RES0028, RES0029, RES0030, RES0032, RES0033, RES0034, RES0035, RES0036, RES0038, RES0039, RES0042, RES0045, RES0046, RES0052, RES0053, RES0055, RES0058, RES0060, RES0061, RES0062, RES0063, RES0069, RES0070, RES0071, RES0074, RES0080, RES0081, RES0084, RES0085, RES0086, RES0087, RES0089, RES0091, RES0093, RES0094, RES0095, RES0098, RES0099, RES0100, RES0101, RES0102, RES0104, RES0106, RES0107, RES0109, RES0110, RES0112, RES0113, RES0116, RES0119, RES0121, RES0123, RES0124, RES0125, RES0131, RES0133, RES0134, RES0135, RES0136, RES0139, RES0140, RES0141, RES0142, RES0143, RES0146, RES0151, RES0152, RES0153, RES0158, RES0160, RES0162, RES0166, RES0168, RES0169, RES0170, RES0172, RES0174, RES0180, RES0181, RES0186, RES0187, RES0189, RES0191, RES0192, RES0196, RES0197, RES0200, RES0201, RES0202, RES0204, RES0208, RES0209, RES0212, RES0213, RES0216

## Output Files

- `final_1500_contexts_v2.csv`
- `final_sampling_report_v2.md`
- `final_sampling_audit_v2.csv`
- `final_eligibility_audit_for_review.csv`
- `sample_final_1500_v2.py`
