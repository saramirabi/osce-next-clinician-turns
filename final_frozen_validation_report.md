# Final Frozen Validation Report

Dataset correction applied after GPT pilot review. Manual eligibility decisions were applied to flagged audit rows, excluded non-history targets were replaced within dialogue/position strata, and the corrected sample was frozen as `final_1500_TRULY_FROZEN.csv`.

## Manual Review

- Flagged audit rows reviewed: **61**
- Rows marked KEEP: **37**
- Rows marked EXCLUDE: **24**
- Replacements made: **24**
- Required exclusions confirmed: **CTX_0154**, **CTX_1368**

## Automatic Validation

- Row count: **1,500**
- Unique target IDs: **1,500**
- Unique dialogues: **272**
- Targets per dialogue values: **[5, 6]**
- Position counts: **{'early': 544, 'middle': 544, 'late': 412}**
- Excluded targets replaced: **24**

## Final Sample Checks

- Targets per dialogue mean / median / SD: **5.51 / 6.0 / 0.50**
- Targets per dialogue min / max: **5 / 6**

### Position Category Distribution

| Category | Count | Percentage |
| --- | ---: | ---: |
| early | 544 | 36.27% |
| middle | 544 | 36.27% |
| late | 412 | 27.47% |

### Specialty Distribution

| Specialty | Count | Percentage |
| --- | ---: | ---: |
| Cardiovascular | 26 | 1.73% |
| Dermatological | 5 | 0.33% |
| Gastrointestinal | 32 | 2.13% |
| General | 6 | 0.40% |
| Musculoskeletal | 259 | 17.27% |
| Respiratory | 1,172 | 78.13% |

### Context and Target Length

- Context words mean / median / SD: **638.25 / 601.5 / 355.11**
- Target words mean / median / SD: **12.37 / 11.0 / 7.35**

### Completed Exchanges Before Target

- Mean: **22.87**
- Min / max: **2 / 67**

## Replacement Policy

- Source sample: `final_1500_FROZEN.csv`
- For each manually excluded target, replacement selected from same `dialogue_id` and `position_category`.
- Replacement candidates required `primary_turn_function == history_information_seeking` and `completed_exchanges_before_target >= 2`.
- Unflagged eligible replacements preferred; deterministic fallback otherwise.
- Random seed: **42**

## Output Files

- `final_1500_TRULY_FROZEN.csv`
- `final_replacement_audit_completed.csv`
- `final_eligibility_audit_for_review.csv` (updated with manual decisions)
- `final_frozen_validation_report.md`
- `finalize_truly_frozen_sample.py`
