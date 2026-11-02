# The Forgetting Engine — ML Methodology

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
