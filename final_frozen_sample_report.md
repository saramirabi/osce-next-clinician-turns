# Final Frozen Sample Report

The experimental sample is finalized and should be treated as immutable before LLM generation.

## Manual Review Applied

- Audit rows reviewed: **61**
- Rows marked KEEP: **61**
- Rows marked EXCLUDE: **0**
- Replacements made: **0**
- Decision source mode: **default_keep_no_manual_decision_column**

## Final Sample Checks

- Final sample size: **1,500**
- Unique target IDs: **1,500**
- Unique dialogues: **272**
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

- Context words mean / median / SD: **641.28 / 603.0 / 360.90**
- Target words mean / median / SD: **13.00 / 11.0 / 9.45**

### Completed Exchanges Before Target

- Mean: **22.96**
- Min / max: **2 / 67**

## Replacement Policy

For each manually excluded target:
- Removed from `final_1500_contexts_v2.csv` by `context_id`.
- Replaced from the same `dialogue_id` and `position_category` stratum.
- Replacement candidates required `primary_turn_function == history_information_seeking` and `completed_exchanges_before_target >= 2`.
- Unflagged eligible replacements were preferred; otherwise deterministic fallback among remaining eligible targets.
- Random seed: **42**

## Output Files

- `final_1500_FROZEN.csv`
- `final_replacement_audit.csv`
- `final_frozen_sample_report.md`
- `finalize_frozen_sample.py`
