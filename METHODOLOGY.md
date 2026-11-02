# The Forgetting Engine — ML Methodology

> **Simulation vs. Real Data**: All content under §3 (Simulation) describes a *synthetic* approximation of student behaviour. Simulated data has **not** been validated against real student outcomes. It exists solely to bootstrap the ML pipeline. Replace with real student data before drawing any conclusions about actual learning behaviour or model performance.

---

## 1. Feature Engineering (13 Features)

Features represent learner state and topic characteristics strictly before a recall event:

1. `times_studied`: Count of prior study events for this user and topic.
2. `is_first_exposure`: Binary indicator ($1$ if `times_studied == 1`, else $0$).
3. `days_since_last_studied`: Elapsed whole days since the user's most recent study session on this topic.
4. `revision_frequency`: Revisions per day over the learner's entire history on the topic: $(\text{times\_studied} - 1) / \max(\text{days\_since\_first\_learned}, 1)$.
5. `self_reported_confidence`: Mean of self-reported confidence ratings ($0.0 - 1.0$) from prior study sessions (defaults to $0.5$).
6. `universal_difficulty`: Topic difficulty ($0.0 - 1.0$), blended from initial curriculum estimate and empirical recall performance across learners.
7. `topic_importance`: Exam weight normalized per course ($0.0 - 1.0$).
   - Raw importance: $\text{raw} = \frac{\text{CO Marks}}{\text{Number of Lecture Topics in CO}}$.
   - Normalization: $\text{topic\_importance} = \frac{\text{raw}}{\max_{\text{course}}(\text{raw})}$.
   - **Note on PCAP CO6**: CO6 in CSE 3129 carries 5 marks but has no lecture topics in the lesson plan. In accordance with curriculum structure rules, COs without lecture topics are ignored during topic importance calculation, so these 5 marks do not enter importance.
8. `time_spent_studying_min`: Total cumulative minutes spent studying this topic prior to the recall check.
9. `confusability_score`: Number of easily confused topics flagged for this topic.
10. `prerequisite_completion_ratio`: Proportion of prerequisite topics studied by the learner prior to the event.
11. `concurrent_topic_load`: Number of distinct other topics studied by the learner in the 7-day window preceding this check.
12. `days_to_next_assessment`: Number of days from the observation date to the start of the next dated assessment covering this topic (capped at 60). Defaults to 60 if no dated covering assessment remains.
13. `has_upcoming_assessment`: Binary indicator ($1$ if an upcoming dated covering assessment exists, $0$ otherwise).

## 2. Zero-Leakage Guarantee

- Self-check correctness (`RecallEvent.is_correct`) is **strictly never** an input feature. It is solely used as the target label (`forgot = int(not is_correct)`).
- Every feature for an event at timestamp $T$ is computed exclusively from activity strictly before $T$ ($\le T$). Adding events after $T$ or altering the target label has zero mathematical effect on the computed feature row.


---

## 3. Simulation Architecture (Step 3)

### 3.1 Purpose

Real student data does not yet exist. The simulation generates synthetic study histories using **actual seeded topics** from all four courses so that the ML pipeline (feature engineering, training, evaluation) can be exercised end-to-end.

> [!IMPORTANT]
> Every simulated record is flagged `is_simulated=True`. Simulated metrics (accuracy, recall, etc.) are **not** measures of real-world model performance. They are internal pipeline health checks only.

---

### 3.2 Entry Point

```
backend/app/synthetic_data.py — simulate_students(db, cfg)
```

- `SimulationConfig` dataclass controls all knobs (see §3.9).
- No topics, courses, modules, or assessments are invented. All foreign-key references come from the seeded DB.
- Calling `simulate_students` twice without `replace_existing=True` logs a warning and exits safely.

---

### 3.3 Student Behavioural Profiles

Six named profiles determine per-student study patterns. Each student is assigned one profile at the start of their simulation. Profiles are sampled with fixed weights (see table). Within each profile, all numeric parameters are drawn uniformly from documented ranges — students of the same profile are not identical.

| Profile | Weight | Description |
|---|---|---|
| `consistent` | 20 % | Revises at regular intervals; remembers well. |
| `crammer` | 20 % | Barely studies except in the week before assessments. |
| `irregular` | 20 % | Random interval, random coverage; no pre-assessment boost. |
| `thorough` | 20 % | High coverage, many sessions, long sessions; best retention. |
| `overconfident` | 10 % | Reports inflated confidence; forgets faster than expected. |
| `underconfident` | 10 % | Reports deflated confidence; actually retains reasonably well. |

Parameters per profile (uniform ranges):

| Parameter | consistent | crammer | irregular | thorough | overconfident | underconfident |
|---|---|---|---|---|---|---|
| Topic coverage | 55–80 % | 50–75 % | 30–65 % | 65–90 % | 40–70 % | 60–85 % |
| Study sessions per topic | 3–7 | 1–3 | 1–5 | 4–9 | 1–3 | 3–8 |
| Revision interval (days) | 3–8 | 1–3 | 1–20 | 2–7 | 5–15 | 2–5 |
| Session duration (seconds) | 900–2400 | 1200–3600 | 300–2700 | 1500–4500 | 400–1200 | 600–2000 |
| Confidence bias | +0.10 | +0.05 | 0.00 | +0.15 | +0.30 | −0.15 |
| Forgetting factor | 0.80× | 1.20× | 1.05× | 0.70× | 1.30× | 0.85× |
| Pre-assessment boost sessions | 1 | 3 | 0 | 2 | 0 | 2 |

---

### 3.4 Study Session Generation

For each (student, course) pair:

1. Draw the fraction of course topics to study from `topic_coverage` range.
2. Sample that many topics at random (without replacement) from real seeded topics.
3. For each selected topic:
   a. Draw a first-learn date from `Uniform(0, 0.70 × SEMESTER_DAYS)`.
   b. Schedule `n_study_sessions` follow-up revisions at `study_interval_days` gaps.
   c. If the topic's `lecture_num` is covered by a dated assessment and the profile's `pre_assessment_boost > 0`, add that many extra sessions in the 7 days before each (calendar-shifted) assessment start.
4. Persist one `LearningEvent` per session with `is_simulated=True`.

Semester window: `2026-08-01` to `2026-11-30` (SEMESTER_START / SEMESTER_END constants). First-learn date is clamped so at least 10 days remain in the semester.

---

### 3.5 Self-Check (RecallEvent) Generation

After every revision session (sessions 2…N):

1. With probability **0.65**, generate a recall check.
2. Draw `check_gap ~ Uniform(1, 7)` days after the session.
3. Collect all prior `LearningEvent` timestamps ≤ `check_dt` to compute study statistics **in-memory** (not from the DB feature table — no leakage path).
4. Compute `p_correct = _recall_probability(...)` (see §3.6).
5. Draw `is_correct ~ Bernoulli(p_correct)`.
6. Persist one `RecallEvent` with `is_simulated=True`.

`is_correct` is **only** used as the training label `forgot = int(not is_correct)`. It is never read back as an input feature.

---

### 3.6 Forgetting Curve Model (Label Generation Only)

The function `_recall_probability()` is used **exclusively** to produce `RecallEvent.is_correct`. It is **never** called during feature engineering.

$$
\text{strength} = 1 + (\text{times\_studied} - 1) \times 1.3
$$

$$
\text{decay} = \frac{\text{forgetting\_factor} \times (0.15 + \text{difficulty} \times 0.35)}{\text{strength}}
$$

$$
\text{base} = e^{-\text{decay} \times \text{days\_since\_last}}
$$

$$
p_{\text{correct}} = \text{clamp}\!\left(\text{base} - 0.15(1 - \text{prereq\_ratio}) - 0.04 \times \text{confusability} - 0.015 \times \min(\text{concurrent\_load}, 8),\ 0.05,\ 0.97\right)
$$

`forgetting_factor` is drawn from the profile (e.g. 0.70 for `thorough`, 1.30 for `overconfident`). This is a simulation assumption, **not** a measured parameter.

---

### 3.7 Assessment-Aware Behaviour

- Only **dated** assessments (those with non-null `start_date` and `end_date`) affect study behaviour.
- Assessments with `null` dates (Mid-Term, End-Sem in ML; End-Sem in PCAP/EOM) are **ignored** for scheduling purposes.
- Covered lectures are read from `Assessment.covered_lectures_list` (from Step 2 seed data).
- `is_upcoming_assessment_prep=True` is set on a `RecallEvent` if the check falls within 7 days before a dated assessment that covers the topic.

---

### 3.8 Calendar-Shifting Mechanism

Each student's semester start is shifted by a per-student offset:

$$
\text{offset} \sim \text{Uniform}(\text{STUDENT\_CALENDAR\_OFFSET\_DAYS})
\quad \text{where} \quad \text{STUDENT\_CALENDAR\_OFFSET\_DAYS} = (-14, 14)
$$

The offset is added to every assessment date used for study scheduling, so relative spacing between assessments is preserved exactly. This models the fact that different student groups may have slightly different assessment windows.

---

### 3.9 Reproducibility and Configuration

All randomness flows from a single `random.Random(cfg.random_seed)` root generator. Each student gets a child seed derived deterministically from the root, so:

- Identical `SimulationConfig` → identical output (same users, events, labels).
- Different seeds → different histories.

**`SimulationConfig` fields:**

| Field | Default | Description |
|---|---|---|
| `n_students` | 30 | Number of simulated students to generate. |
| `random_seed` | 42 | Root random seed for full reproducibility. |
| `replace_existing` | `False` | If `True`, deletes existing simulated records before re-running. |

---

### 3.10 Limitations of Simulated Data

1. **No real-world validation**: The forgetting curve parameters (0.15, 0.35, 1.3, etc.) and profile weights are plausible but not fitted to any student population.
2. **Confusability scores**: Topics in the seeded courses have `confusable_topic_names=None` (LLM enrichment not yet run), so `confusability=0` for all simulated events. This underestimates confusion effects.
3. **Topic difficulty**: All seeded topics have `difficulty=0.5` (LLM enrichment not yet run). True difficulty variation is absent.
4. **No prerequisite chains**: Seeded topics have no `prerequisites` set. `prereq_ratio=1.0` for all topics.
5. **Single-semester scope**: Study histories are confined to 2026-08-01 – 2026-11-30 and do not model prior knowledge or inter-semester carry-over.
6. **Profile assignment is synthetic**: Real students do not self-identify as "crammerss" or "consistent" learners; these are modelling simplifications.
7. **Replace with real data**: Simulated data should be replaced with real `LearningEvent` and `RecallEvent` records as soon as even a small cohort of real students uses the system.
