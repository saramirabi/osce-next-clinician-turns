# Candidate Analysis Report v3

Deterministic primary turn-function classification with sentence-level precedence.
All v2 descriptive flags are preserved. No final sampling or LLM calls were performed.

## Primary Turn Function Distribution

| Primary function | Count | Percentage |
| --- | ---: | ---: |
| `history_information_seeking` | 11,826 | 90.20% |
| `acknowledgement_only` | 311 | 2.37% |
| `greeting_opening` | 38 | 0.29% |
| `closing_farewell` | 217 | 1.66% |
| `conversational_transition` | 54 | 0.41% |
| `examination_procedure` | 87 | 0.66% |
| `diagnosis_explanation` | 330 | 2.52% |
| `treatment_management` | 27 | 0.21% |
| `administrative` | 18 | 0.14% |
| `other_unclassified` | 203 | 1.55% |

## Corpus Summary

- Total candidates: **13,111**
- Unique dialogues: **272**
- Candidates per dialogue (mean / median / SD): **48.20 / 48.0 / 10.14**
- History-information-seeking primary function: **11,826** (90.20%)

## Precedence Logic

Each turn is split into sentences. Each sentence receives an independent function label.
Brief acknowledgement-only sentences are ignored when selecting the dominant substantive function.
The turn-level primary function is the highest-precedence substantive sentence function.

Precedence order (highest to lowest):
1. `examination_procedure`
2. `diagnosis_explanation`
3. `treatment_management`
4. `administrative`
5. `closing_farewell`
6. `conversational_transition`
7. `greeting_opening`
8. `history_information_seeking`
9. `other_unclassified`

If every sentence is acknowledgement-only, primary function = `acknowledgement_only`.

## Sentence-Level Rules

### History information seeking
- Assigned when the substantive sentence elicits patient history.
- Includes medication-history questions such as `do you take`, `any medications`, and `allergies`.
- Includes social/family/history patterns via `HISTORY_SOCIAL_RE`.
- Uses v2 hybrid interrogative detection only after ruling out incidental closing, treatment, and diagnosis patterns.
- Brief acknowledgement prefixes do not prevent history classification of the substantive sentence.

### Treatment/management
- Requires directive language via `TREATMENT_DIRECTIVE_RE`.
- Medication-history questions are explicitly routed to history first.

### Diagnosis/explanation
- Requires declarative diagnosis/explanation patterns via `DIAGNOSIS_STATEMENT_RE`.
- Interrogative history-taking sentences are excluded.

### Incidental closing interrogatives
- Sentences such as `Do you have any questions?` are classified as `closing_farewell`, not history.
- Regex: `^\s*(?:and\s+)?(?:do you have any (?:other )?questions(?: for me)?|any questions(?: for me)?|anything else(?: you(?:'d| would) like to (?:ask|know|discuss|add))?|does that (?:make )?sense|is that (?:ok|okay|clear|alright|fine)|do you understand|are you (?:ok|okay) with that|how does that sound|did you have any questions)\??\s*$`

## Descriptive Flags Preserved

All v2 flags remain available in the CSV, including `flag_information_seeking` and the exploratory exclusion flags.
These are not identical to `primary_turn_function`; use primary function for inclusion decisions.

## Review Sample

- Output file: `candidate_examples_for_review_v3.csv`
- Random seed: **42**
- Target size: **175**
- Minimum history-information-seeking examples: **30**
- Coverage includes every primary function category and all specialties where available.

## Output Files

- `candidate_characteristics_v3.csv`
- `candidate_analysis_report_v3.md`
- `candidate_examples_for_review_v3.csv`
- `analyze_candidate_turns_v3.py`
- Source input (unchanged): `all_candidate_turns.csv`
