# Candidate Analysis Report v2

Refined descriptive characterization with hybrid information-seeking detection.
No final sampling, no LLM classification, and no candidate deletion were performed.

## 1. Basic Corpus Statistics

- Total candidate instances: **13,111**
- Unique dialogues: **272**
- Candidate turns per dialogue (mean / median / SD / min / max): **48.20 / 48.0 / 10.14 / 22 / 77**

### Candidate Turns by Specialty

| Specialty | Count | Percentage |
| --- | ---: | ---: |
| Cardiovascular | 229 | 1.75% |
| Dermatological | 41 | 0.31% |
| Gastrointestinal | 235 | 1.79% |
| General | 38 | 0.29% |
| Musculoskeletal | 2,467 | 18.82% |
| Respiratory | 10,101 | 77.04% |

### Target Position Distribution

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

## 2. Question vs Information-Seeking

- Question mark present: **12,041** (91.84%)
- Information-seeking by hybrid rules: **12,485** (95.23%)
- Information-seeking without question mark: **444** (3.39%)
- Question mark but not information-seeking: **0**
- Disagreement between old and new flags: **444**

### Information-Seeking Rule Hits

| Rule | Count |
| --- | ---: |
| `question_mark` | 12,041 |
| `auxiliary_led` | 8,490 |
| `elliptical_request` | 6,924 |
| `wh_construction` | 3,031 |
| `spacy_wh` | 2,724 |
| `spacy_aux_inversion` | 1,623 |
| `request_verb` | 275 |
| `spacy_conditional_request` | 259 |
| `tag_question` | 104 |
| `spacy_request_verb` | 70 |

## 3. Exploratory Exclusion Flags

| Flag | Count | Percentage |
| --- | ---: | ---: |
| Question-containing (`?` present) | 12,041 | 91.84% |
| Information-seeking (hybrid rules) | 12,485 | 95.23% |
| Disagreement: question mark vs information-seeking | 444 | 3.39% |
| Acknowledgement-only | 303 | 2.31% |
| Greeting/opening | 71 | 0.54% |
| Closing/farewell | 277 | 2.11% |
| Conversational transition | 124 | 0.95% |
| Examination/procedure instruction | 159 | 1.21% |
| Diagnosis/explanation | 354 | 2.70% |
| Treatment/management | 255 | 1.94% |
| Administrative | 18 | 0.14% |
| Very short (<=2 words) | 472 | 3.60% |
| Very short (<=3 words) | 854 | 6.51% |
| Very short (<=5 words) | 1,956 | 14.92% |

## 4. Rule Documentation

### `flag_information_seeking`
True when any hybrid rule matches on `human_doctor_target`.

1. **Question punctuation**: at least one `?`.
2. **WH interrogatives**: regex `(?:^|\b)(what|when|where|why|who|which|how)\b` on full text or discourse-stripped text.
3. **Auxiliary-led interrogatives**: regex `(?:^|\b)(?:do|does|did|have|has|had|is|are|was|were|can|could|will|would|shall|should|may|might|must|am)\b(?:\s+\w+){0,4}\s+(?:you|your|there|it|this|that|he|she|they|we|the|any|anything|anyone|ever|either|one|she's|he's|it's|they're|we're|i|u)\b` or `^\s*(?:do|does|did|have|has|had|is|are|was|were|can|could|will|would|shall|should|may|might|must|am)\b`.
4. **Elliptical clinical requests**: regex `(?:^|\b)(?:any(?:thing|one|body)?|ever|either)\b` on full text or discourse-stripped text.
5. **Explicit request verbs**: regex `\b(tell me|let me know|describe|explain|clarify|walk me through|can you tell me|could you tell me|can you describe|could you describe|can you explain|could you explain|would you mind telling me)\b`.
6. **Tag-like prompts**: regex `(?:,|\b)(?:right|correct|yes|no|or not)\s*[.?!]?\s*$`.
7. **spaCy syntactic cues** on any sentence:
   - WH token with dependency in `{advmod, attr, dobj, pobj, nsubj, ROOT}`
   - sentence-initial auxiliary with subject (`nsubj`, `nsubjpass`, or `expl`)
   - root lemma in `{tell, describe, explain, clarify, list, mention, note}`
   - conditional request with `if` mark plus auxiliary

Discourse prefixes stripped before several regex checks:
`^(?:(?:ok(?:ay)?|alright|right|sure|and|so|well|now|um+|uh+|hmm+|great|good|perfect|awesome|excellent|wonderful|thanks|thank you|all right)[,.\s-]*)+`

Word count is **not** used as an exclusion criterion.

### Exclusion flags

#### Acknowledgement-only
- Entire turn must contain only acknowledgement vocabulary tokens after lowercasing and removing final punctuation.
- Allowed token set: `['all', 'alright', 'awesome', 'course', 'excellent', 'good', 'got', 'great', 'hmm', 'huh', 'i', 'it', 'mhm', 'mm', 'my', 'no', 'of', 'ok', 'okay', 'perfect', 'pleasure', 'problem', 'right', 'see', 'sounds', 'sure', 'thank', 'thanks', 'uh', 'understood', 'wonderful', 'worries', 'yeah', 'yep', 'yes', 'you']`
- Allowed multiword phrases: `thank you`, `no problem`, `i see`, `got it`, `sounds good`, `all right`.
- Rejected if `?` is present or if information-request keywords such as `any`, `what`, `how`, or `do you` appear.

#### Greeting/opening
- `\b(hi|hello|hey|good morning|good afternoon|good evening|nice to meet you|welcome(?: to)?|my name is|i(?:'m| am)\s+(?:dr|doctor))\b`

#### Closing/farewell
- `\b(goodbye|bye|see you|take care|have a (?:good|nice)(?: day| one)|that(?:'s| is) (?:all|everything)(?: my questions(?: for now)?)?|those are (?:all|all of) my questions|all my questions(?: for now)?|we(?:'re| are) (?:done|finished|all set)|thank you for (?:coming|your time)|do you have any (?:other )?questions(?: for me)?|anything else(?: you(?:'d| would) like to (?:ask|know|discuss))?|nice (?:meeting|talking to) you|we will (?:definitely )?(?:do that|take care of that) for you)\b`

#### Conversational transition
- `\b(i(?:'ll| will)|let me|give me a (?:moment|minute|sec)|bear with me|be right back|step out(?:side)?|go talk to|talk to the doctor|discuss this with|grab the doctor|get the doctor|consult with|come back (?:in|with)|back with you in a moment|move on to|moving on to|let's move on|let us move on|just going to get (?:the )?(?:patient'?s )?(?:vitals|nurse|doctor)|get the (?:patient'?s )?vitals|before we move forward to the physical|we(?:'ll| will) (?:go|move) (?:ahead )?(?:with|to)|that sounds good\??$)\b`

#### Examination/procedure instruction
- `\b(examine|examination|physical exam|let me (?:look|check|listen|feel|palpate|have a look|take a look|inspect)|i(?:'ll| will) (?:look|check|listen|examine|palpate|need to examine|do an exam|have a look|take a look)|listen to your|auscult|palpate|inspect|check your (?:blood pressure|vitals|pulse|heart|lungs|abdomen|back|leg|skin|reflexes|throat|ears|eyes)|going to (?:examine|check|look at|inspect|palpate)|move on to the physical|start the physical|during the exam|on physical exam|perform an exam|can you (?:lie down|sit up|stand up|remove|take off|lift|bend|move|show me|pull up|pull down))\b`

#### Diagnosis/explanation
- `\b(i think|it (?:sounds|looks|seems) like|likely|probably|possibly|this (?:is|could be|may be|might be)|appears to be|diagnosis|based on what you(?:'ve| have) told me|from what you(?:'ve| have) said|suggest(?:s|ing)? (?:that )?you (?:have|may have|might have)|consistent with|indicative of|concerned about|worried about|what(?:'s| is) (?:most )?likely going on|working diagnosis|differential (?:includes|is)|doesn't sound like|does not sound like)\b`

#### Treatment/management
- `\b(recommend|prescribe|prescription|medication|treatment|manage(?:ment)?|you should (?:take|try|use|start|stop|avoid|rest|drink|eat)|we(?:'ll| will) (?:start|give|prescribe|order|refer|arrange|book|send you for)|follow up|follow-up|refer you|send you for|take (?:this|these|it|them)|over the counter|apply (?:this|a)|come back if|return if|go to (?:the )?(?:er|emergency)|start you on|put you on|trial of|make sure you (?:take|use|continue|keep))\b`

#### Administrative
- `\b(appointment|schedule|paperwork|form|insurance|billing|registration|wait here|waiting room|front desk|referral letter|fill out|sign this|contact (?:the )?clinic|book (?:you )?(?:in|an appointment)|medical record number|health card|identification)\b`

## 5. Alternative Inclusion-Rule Counts

| Rule | Count | Percentage |
| --- | ---: | ---: |
| info seeking and ge2 exchanges | 12,222 | 93.22% |
| info seeking and ge3 exchanges | 11,966 | 91.27% |
| info seeking and not excluded | 11,662 | 88.95% |
| info seeking and ge2 and not excluded | 11,409 | 87.02% |
| question only and ge2 exchanges | 11,782 | 89.86% |
| info seeking not question mark | 444 | 3.39% |

### By Specialty

| specialty | info_seeking_and_ge2_exchanges | info_seeking_and_ge3_exchanges | info_seeking_and_not_excluded | info_seeking_and_ge2_and_not_excluded | question_only_and_ge2_exchanges | info_seeking_not_question_mark |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Cardiovascular | 220 | 215 | 212 | 207 | 216 | 4 |
| Dermatological | 37 | 36 | 32 | 32 | 37 | 1 |
| Gastrointestinal | 223 | 217 | 213 | 207 | 220 | 3 |
| General | 35 | 34 | 31 | 30 | 35 | 0 |
| Musculoskeletal | 2326 | 2285 | 2192 | 2146 | 2215 | 111 |
| Respiratory | 9381 | 9179 | 8982 | 8787 | 9059 | 325 |

### By Position Category

| position_category | info_seeking_and_ge2_exchanges | info_seeking_and_ge3_exchanges | info_seeking_and_not_excluded | info_seeking_and_ge2_and_not_excluded | question_only_and_ge2_exchanges | info_seeking_not_question_mark |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| early | 3874 | 3618 | 4044 | 3791 | 3820 | 58 |
| late | 4090 | 4090 | 3514 | 3514 | 3771 | 319 |
| middle | 4258 | 4258 | 4104 | 4104 | 4191 | 67 |

## 6. Review Sample

- Output file: `candidate_examples_for_review_v2.csv`
- Random seed: **42**
- Target sample size: **150**
- Coverage targets: information-seeking true/false, old/new disagreement, each exclusion category, all specialties, and all position categories.

## 7. Output Files

- `candidate_characteristics_v2.csv`
- `candidate_analysis_report_v2.md`
- `candidate_examples_for_review_v2.csv`
- `analyze_candidate_turns_v2.py`
- Source input (unchanged): `all_candidate_turns.csv`
