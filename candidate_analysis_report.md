# Candidate Analysis Report

Descriptive characterization of all position-matched next-doctor-turn candidates.
No instances were removed, sampled for the final experiment, or classified with an LLM.

## 1. Basic Corpus Statistics

- Total candidate instances: **13,111**
- Unique dialogues: **272**
- Candidate turns per dialogue (mean): **48.20**
- Candidate turns per dialogue (median): **48.0**
- Candidate turns per dialogue (SD): **10.14**
- Candidate turns per dialogue (min/max): **22 / 77**

### Candidate Turns by Specialty

| Specialty | Count | Percentage |
| --- | ---: | ---: |
| Cardiovascular | 229 | 1.75% |
| Dermatological | 41 | 0.31% |
| Gastrointestinal | 235 | 1.79% |
| General | 38 | 0.29% |
| Musculoskeletal | 2,467 | 18.82% |
| Respiratory | 10,101 | 77.04% |

### Target Position Distribution Within Dialogues

| Position bin | Count | Share |
| --- | ---: | ---: |
| 0.00-0.10 | 1160 | 8.85% |
| 0.10-0.20 | 1303 | 9.94% |
| 0.20-0.30 | 1319 | 10.06% |
| 0.30-0.40 | 1303 | 9.94% |
| 0.40-0.50 | 1273 | 9.71% |
| 0.50-0.60 | 1352 | 10.31% |
| 0.60-0.70 | 1322 | 10.08% |
| 0.70-0.80 | 1300 | 9.92% |
| 0.80-0.90 | 1322 | 10.08% |
| 0.90-1.01 | 1457 | 11.11% |

### Context Length

- Context words (mean / median / SD): **701.50 / 665.0 / 398.38**
- Context words (min / max): **13 / 2440**
- Context turns (mean / median / SD): **51.35 / 50.0 / 31.30**
- Context turns (min / max): **1 / 154**

### Human Target Length

- Target words (mean / median / SD): **15.23 / 11.0 / 20.96**
- Target words (min / max): **1 / 322**

## 2. Question Characteristics

Automatic question features are heuristic only, not pragmatic ground truth.

- Contains question mark: **12,041** (91.84%)
- Multiple question marks: **1,000** (7.63%)
- Starts with WH-word: **197** (1.50%)
- Appears yes/no by rule: **1,192** (9.09%)
- Mean question marks per target: **1.00**
- Mean sentences per target: **1.57**
- Mean interrogative sentences per target: **1.01**

## 3. Exploratory Target Flags

These flags are descriptive only. No instances were excluded based on them.

| Flag | Count | Percentage |
| --- | ---: | ---: |
| Question-containing (`?` present) | 12,041 | 91.84% |
| Acknowledgement-only | 280 | 2.14% |
| Greeting/opening | 71 | 0.54% |
| Closing/farewell | 168 | 1.28% |
| Examination/procedure instruction | 138 | 1.05% |
| Diagnosis/explanation | 352 | 2.68% |
| Treatment/management | 249 | 1.90% |
| Administrative | 18 | 0.14% |
| Very short (<=2 words) | 472 | 3.60% |
| Very short (<=3 words) | 854 | 6.51% |
| Very short (<=5 words) | 1,956 | 14.92% |

### Flag Rule Documentation

#### Question-containing
- True when `human_doctor_target` contains at least one `?`.

#### Acknowledgement-only
- True when there is no `?` and the full target matches:
  - regex: `^\s*(?:ok(?:ay)?|alright|right|sure|yes|yeah|yep|mm(?:-?hmm)?|uh(?:-|\s)?huh|i see|got it|understood|thank you|thanks|good|great|perfect|sounds good|no problem|of course|mhm)(?:[\s,.!?-]*(?:ok(?:ay)?|alright|right|sure|yes|yeah|yep|mm(?:-?hmm)?|uh(?:-|\s)?huh|i see|got it|understood|thank you|thanks|good|great|perfect|sounds good|no problem|of course|mhm))*[\s.!?-]*$`
- Intended for short acknowledgement/backchannel turns built from phrases such as `ok`, `alright`, `I see`, `thank you`, `got it`, `mhm`.

#### Greeting/opening
- True when target matches:
  - regex: `\b(hi|hello|hey|good morning|good afternoon|good evening|nice to meet you|welcome|my name is)\b`

#### Closing/farewell
- True when target matches:
  - regex: `\b(goodbye|bye|see you|take care|have a (?:good|nice) day|that(?:'s| is) (?:all|everything)|we(?:'re| are) (?:done|finished)|thank you for (?:coming|your time)|anything else(?:\?| before we)|do you have any (?:other )?questions)\b`

#### Examination/procedure instruction
- True when target matches:
  - regex: `\b(examine|examination|physical exam|let me (?:look|check|listen|feel|palpate|have a look|take a look)|i(?:'ll| will) (?:look|check|listen|examine|palpate|need to examine|do an exam)|listen to your|check your (?:blood pressure|vitals|pulse|heart|lungs|abdomen|back|leg|skin|reflexes)|going to (?:examine|check|look at|inspect|palpate)|move on to the physical|start the physical|during the exam|can you (?:lie down|sit up|stand up|remove|take off|lift|bend|move))\b`

#### Diagnosis/explanation
- True when target matches:
  - regex: `\b(i think|it (?:sounds|looks|seems) like|likely|probably|possibly|this (?:is|could be|may be|might be)|appears to be|diagnosis|based on what you(?:'ve| have) told me|from what you(?:'ve| have) said|suggest(?:s|ing)? (?:that )?you (?:have|may have|might have)|consistent with|indicative of|concerned about|worried about)\b`

#### Treatment/management
- True when target matches:
  - regex: `\b(recommend|prescribe|prescription|medication|treatment|manage(?:ment)?|you should (?:take|try|use|start|stop|avoid|rest|drink|eat)|we(?:'ll| will) (?:start|give|prescribe|order|refer|arrange|book)|follow up|follow-up|refer you|send you for|take (?:this|these|it|them)|over the counter|apply (?:this|a)|come back if|return if|go to (?:the )?(?:er|emergency))\b`

#### Administrative
- True when target matches:
  - regex: `\b(appointment|schedule|paperwork|form|insurance|billing|registration|wait here|waiting room|front desk|referral letter|fill out|sign this|contact (?:the )?clinic|book (?:you )?(?:in|an appointment))\b`

#### Very short targets
- `flag_very_short_le2`: target word count <= 2
- `flag_very_short_le3`: target word count <= 3
- `flag_very_short_le5`: target word count <= 5
- Word count uses regex `[A-Za-z0-9']+`.

#### WH-word start
- regex: `^\s*(what|when|where|why|who|which|how)\b`

#### Yes/no question heuristic
- True when target starts with auxiliary/modal/question opener regex:
  - `^\s*(do|does|did|are|is|was|were|have|has|had|can|could|will|would|should|shall|may|might|any|have you|has there|is there|are there|did you|do you|does it|can you|could you|would you|will you)\b`
- Or ends with tag-like patterns such as `, right?`, `, correct?`, `, yes?`, `, no?`, or contains `or not?`.

#### Interrogative sentence count
- A sentence is counted as interrogative if it contains `?`, starts with a WH-word, or starts with the yes/no opener regex above.
- Sentences are split on `.`, `!`, and `?`.

## 4. Dialogue Position

- `absolute_target_doctor_turn_index` = doctor turn number within the dialogue.
- `normalized_target_position` = candidate turn index / candidate turns in dialogue, in `[0, 1]`.
- `position_category`: Early = first third, Middle = second third, Late = final third.

### Position Category Counts

| Category | Count | Percentage |
| --- | ---: | ---: |
| early | 4,286 | 32.69% |
| middle | 4,369 | 33.32% |
| late | 4,456 | 33.99% |

## 5. Context Depth

- Mean preceding doctor turns: **25.66**
- Mean preceding patient turns: **25.69**
- Mean preceding total turns: **51.35**
- Mean latest patient-turn word count: **11.85**

Completed exchange count before target = number of preceding patient turns in context.

| Threshold | Count | Percentage |
| --- | ---: | ---: |
| >=1 completed exchange | 13,111 | 100.00% |
| >=2 completed exchanges | 12,839 | 97.93% |
| >=3 completed exchanges | 12,567 | 95.85% |
| >=4 completed exchanges | 12,295 | 93.78% |

## 6. Target-Type Combinations

Counts under alternative possible inclusion rules. These are not final decisions.

| Rule | Count | Percentage |
| --- | ---: | ---: |
| question and ge2 exchanges | 11,782 | 89.86% |
| question and ge3 exchanges | 11,530 | 87.94% |
| question and not ack only | 12,041 | 91.84% |
| question and not dte | 11,621 | 88.64% |
| question and ge2 and not dte | 11,366 | 86.69% |

### By Specialty

| specialty | question_and_ge2_exchanges | question_and_ge3_exchanges | question_and_not_ack_only | question_and_not_dte | question_and_ge2_and_not_dte |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cardiovascular | 216 | 211 | 221 | 213 | 208 |
| Dermatological | 37 | 36 | 37 | 35 | 35 |
| Gastrointestinal | 220 | 214 | 226 | 217 | 211 |
| General | 35 | 34 | 36 | 33 | 32 |
| Musculoskeletal | 2215 | 2174 | 2261 | 2178 | 2132 |
| Respiratory | 9059 | 8861 | 9260 | 8945 | 8748 |

### By Position Category

| position_category | question_and_ge2_exchanges | question_and_ge3_exchanges | question_and_not_ack_only | question_and_not_dte | question_and_ge2_and_not_dte |
| --- | ---: | ---: | ---: | ---: | ---: |
| early | 3820 | 3568 | 4079 | 4025 | 3770 |
| late | 3771 | 3771 | 3771 | 3516 | 3516 |
| middle | 4191 | 4191 | 4191 | 4080 | 4080 |

## 7. Random Examples for Manual Inspection

- Output file: `candidate_examples_for_review.csv`
- Random seed: **42**
- Target sample size: **100**
- Stratification buckets: specialty x Early/Middle/Late x question/non-question x short(<=5 words)/longer.
- Examples were selected automatically; no manual classification was applied.

## 8. Output Files

- `candidate_characteristics.csv`
- `candidate_analysis_report.md`
- `candidate_examples_for_review.csv`
- `analyze_candidate_turns.py`
- Source input (unchanged): `all_candidate_turns.csv`
