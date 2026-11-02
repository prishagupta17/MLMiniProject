"""
Generates simulated student study histories using the actual seeded topics from
all four courses (CSE 3148, CSE 3129, HUM 3022, CSE 3128).

Design principles
-----------------
* Simulated records are ALWAYS flagged: User.is_simulated=True,
  LearningEvent.is_simulated=True, RecallEvent.is_simulated=True.
* Topics come exclusively from the real seeded database — no invented topics.
* RecallEvent.is_correct is derived from a documented forgetting model; it is
  NEVER read back as an input feature (zero leakage).
* Reproducibility: identical SimulationConfig -> identical output.
* Real student records are never touched.

Simulation does NOT retrain or replace the saved ML model.

See METHODOLOGY.md § Simulation for full assumptions and limitations.
"""

from __future__ import annotations

import math
import random
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from .models import (
    Assessment, Course, LearningEvent, Module, RecallEvent, Topic, User,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public constants (documented in METHODOLOGY.md)
# ---------------------------------------------------------------------------

# Per-student calendar offset distribution (inclusive bounds, in days).
# Each simulated student's "semester start" is shifted by a uniform draw from
# [STUDENT_CALENDAR_OFFSET_DAYS[0], STUDENT_CALENDAR_OFFSET_DAYS[1]].
# Range ±14 days as specified in the Step 2 methodology note.
STUDENT_CALENDAR_OFFSET_DAYS: Tuple[int, int] = (-14, 14)

# Default simulation settings (all overridable via SimulationConfig)
DEFAULT_N_STUDENTS: int = 30
DEFAULT_SEED: int = 42

# Semester anchor date — the nominal first day of term for the seeded courses.
# All assessment dates in the seed data are in the 2026 academic year.
SEMESTER_START: datetime = datetime(2026, 8, 1)
SEMESTER_END: datetime = datetime(2026, 11, 30)
SEMESTER_DAYS: int = (SEMESTER_END - SEMESTER_START).days  # ≈121


# ---------------------------------------------------------------------------
# Student behavioural profiles
# ---------------------------------------------------------------------------
# Six profiles that vary study frequency, duration, revision intervals,
# confidence calibration, and forgetting tendency.
# Each is a dict of named parameters; values are (low, high) uniform ranges
# or fixed scalars.  See METHODOLOGY.md § Behavioural Profiles.

PROFILES = {
    "consistent": {
        # Revises regularly at spaced intervals
        "topic_coverage":     (0.55, 0.80),   # fraction of course topics studied
        "n_study_sessions":   (3, 7),          # per topic
        "study_interval_days": (3, 8),         # gap between revisions
        "session_secs":        (900, 2400),    # 15–40 min per session
        "confidence_bias":     0.10,           # bias added to base confidence
        "forgetting_factor":   0.80,           # multiplier on forgetting rate (lower = remembers better)
        "pre_assessment_boost": 1,             # extra study sessions before each assessment
        "weight": 0.20,
    },
    "crammer": {
        # Studies intensively only near assessments
        "topic_coverage":     (0.50, 0.75),
        "n_study_sessions":   (1, 3),
        "study_interval_days": (1, 3),
        "session_secs":        (1200, 3600),
        "confidence_bias":     0.05,
        "forgetting_factor":   1.20,           # forgets faster (cramming is less durable)
        "pre_assessment_boost": 3,
        "weight": 0.20,
    },
    "irregular": {
        # Studies at random, unpredictable intervals
        "topic_coverage":     (0.30, 0.65),
        "n_study_sessions":   (1, 5),
        "study_interval_days": (1, 20),
        "session_secs":        (300, 2700),
        "confidence_bias":     0.00,
        "forgetting_factor":   1.05,
        "pre_assessment_boost": 0,
        "weight": 0.20,
    },
    "thorough": {
        # Spends more time on difficult topics
        "topic_coverage":     (0.65, 0.90),
        "n_study_sessions":   (4, 9),
        "study_interval_days": (2, 7),
        "session_secs":        (1500, 4500),
        "confidence_bias":     0.15,
        "forgetting_factor":   0.70,
        "pre_assessment_boost": 2,
        "weight": 0.20,
    },
    "overconfident": {
        # Reports high confidence but forgets quickly
        "topic_coverage":     (0.40, 0.70),
        "n_study_sessions":   (1, 3),
        "study_interval_days": (5, 15),
        "session_secs":        (400, 1200),
        "confidence_bias":     0.30,           # over-reports confidence
        "forgetting_factor":   1.30,
        "pre_assessment_boost": 0,
        "weight": 0.10,
    },
    "underconfident": {
        # Studies frequently but underestimates their own retention
        "topic_coverage":     (0.60, 0.85),
        "n_study_sessions":   (3, 8),
        "study_interval_days": (2, 5),
        "session_secs":        (600, 2000),
        "confidence_bias":    -0.15,
        "forgetting_factor":   0.85,
        "pre_assessment_boost": 2,
        "weight": 0.10,
    },
}

_PROFILE_NAMES = list(PROFILES.keys())
_PROFILE_WEIGHTS = [PROFILES[p]["weight"] for p in _PROFILE_NAMES]


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class SimulationConfig:
    """All simulation knobs in one place.  Defaults are documented."""
    n_students: int = DEFAULT_N_STUDENTS
    random_seed: int = DEFAULT_SEED
    # If True, deletes previously generated simulated records before regenerating.
    # Safe default is False so reruns don't silently duplicate.
    replace_existing: bool = False


# ---------------------------------------------------------------------------
# Core forgetting model (used to generate is_correct labels only)
# ---------------------------------------------------------------------------

def _recall_probability(
    *,
    days_since_last: float,
    difficulty: float,
    times_studied: int,
    prereq_ratio: float,
    confusability: int,
    concurrent_load: int,
    forgetting_factor: float,
) -> float:
    """
    Ebbinghaus-inspired forgetting curve adapted to the 13-feature set.

    strength  = 1 + (times_studied - 1) * 1.3
    decay     = forgetting_factor * (0.15 + difficulty * 0.35) / strength
    base      = exp(-decay * days_since_last)

    Penalties (each capped so total cannot push below 0.05):
      prereq_penalty    = 0.15 * (1 - prereq_ratio)
      confusion_penalty = 0.04 * confusability
      load_penalty      = 0.015 * min(concurrent_load, 8)

    Output is clamped to [0.05, 0.97].

    NOTE: This function is used ONLY to derive RecallEvent.is_correct.
    It is documented here so the label-generation process is transparent and
    inspectable.  It is NEVER called during feature engineering.
    """
    strength = 1.0 + (times_studied - 1) * 1.3
    decay_rate = forgetting_factor * (0.15 + difficulty * 0.35) / strength
    base = math.exp(-decay_rate * max(days_since_last, 0))

    prereq_penalty = 0.15 * (1.0 - prereq_ratio)
    confusion_penalty = 0.04 * confusability
    load_penalty = 0.015 * min(concurrent_load, 8)

    p = base - prereq_penalty - confusion_penalty - load_penalty
    return min(max(p, 0.05), 0.97)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _uniform(rng: random.Random, lo: float, hi: float) -> float:
    return rng.uniform(lo, hi)


def _pick_profile(rng: random.Random) -> dict:
    name = rng.choices(_PROFILE_NAMES, weights=_PROFILE_WEIGHTS, k=1)[0]
    return PROFILES[name], name


def _topics_for_course(db: Session, course: Course) -> List[Topic]:
    topics = []
    for module in course.modules:
        topics.extend(module.topics)
    return topics


def _dated_assessments(course: Course) -> List[Assessment]:
    """Return only assessments that have both start_date and end_date."""
    return [a for a in course.assessments if a.start_date and a.end_date]


def _prereq_ratio_sim(
    topic: Topic, studied_ids: Set[int]
) -> float:
    prereqs = topic.prerequisites
    if not prereqs:
        return 1.0
    n_studied = sum(1 for p in prereqs if p.id in studied_ids)
    return n_studied / len(prereqs)


def _confusability(topic: Topic) -> int:
    if not topic.confusable_topic_names:
        return 0
    return len([n for n in topic.confusable_topic_names.split(",") if n.strip()])


def _shift_date(dt: datetime, offset_days: int) -> datetime:
    return dt + timedelta(days=offset_days)


# ---------------------------------------------------------------------------
# Main simulation entry point
# ---------------------------------------------------------------------------

def simulate_students(db: Session, cfg: SimulationConfig) -> None:
    """
    Generate `cfg.n_students` simulated students, each with a full study
    history and recall-check records, using real seeded topics.

    Calling this function twice with the same `cfg` on the same DB will
    produce duplicate records unless `cfg.replace_existing=True`.  By default
    (replace_existing=False) it logs a warning and returns early if simulated
    records already exist.
    """
    existing = db.query(User).filter(User.is_simulated == True).count()
    if existing > 0:
        if cfg.replace_existing:
            logger.info(
                "replace_existing=True: removing %d existing simulated users.", existing
            )
            _delete_simulated(db)
        else:
            logger.warning(
                "Simulated records already exist (%d users).  "
                "Pass replace_existing=True to overwrite.  Skipping.", existing
            )
            return

    # Load all real courses and their topics
    courses: List[Course] = db.query(Course).filter(Course.is_simulated == False).all()
    if not courses:
        raise RuntimeError("No seeded courses found.  Run load_all_seeds() first.")

    course_topics: Dict[int, List[Topic]] = {
        c.id: _topics_for_course(db, c) for c in courses
    }
    # Filter out courses with no topics
    courses = [c for c in courses if course_topics[c.id]]

    # Root RNG — all randomness flows from this, ensuring reproducibility.
    root_rng = random.Random(cfg.random_seed)

    for student_idx in range(cfg.n_students):
        # Each student gets its own RNG child seeded deterministically
        student_seed = root_rng.randint(0, 2**31 - 1)
        rng = random.Random(student_seed)

        profile, profile_name = _pick_profile(rng)

        # Per-student calendar offset (±14 days)
        lo, hi = STUDENT_CALENDAR_OFFSET_DAYS
        cal_offset = rng.randint(lo, hi)

        user = User(
            name=f"SimStudent_{student_idx + 1:04d}_{profile_name}",
            email=f"sim_{student_seed}@sim.internal",
            is_simulated=True,
        )
        db.add(user)
        db.flush()

        _simulate_one_student(
            db=db,
            rng=rng,
            user=user,
            courses=courses,
            course_topics=course_topics,
            profile=profile,
            cal_offset=cal_offset,
        )

    db.commit()
    _log_summary(db)


def _simulate_one_student(
    *,
    db: Session,
    rng: random.Random,
    user: User,
    courses: List[Course],
    course_topics: Dict[int, List[Topic]],
    profile: dict,
    cal_offset: int,
) -> None:
    """Simulate one student's complete semester history."""

    studied_topic_ids: Set[int] = set()

    for course in courses:
        topics = course_topics[course.id]
        if not topics:
            continue

        # How many topics this student covers in this course
        cov_lo, cov_hi = profile["topic_coverage"]
        n_to_study = max(1, int(len(topics) * _uniform(rng, cov_lo, cov_hi)))
        selected_topics = rng.sample(topics, min(n_to_study, len(topics)))

        # Dated assessments for this course (with calendar shift applied)
        dated_assessments = _dated_assessments(course)

        for topic in selected_topics:
            _simulate_topic_history(
                db=db,
                rng=rng,
                user=user,
                topic=topic,
                profile=profile,
                cal_offset=cal_offset,
                dated_assessments=dated_assessments,
                studied_topic_ids=studied_topic_ids,
            )
            studied_topic_ids.add(topic.id)

        db.flush()


def _simulate_topic_history(
    *,
    db: Session,
    rng: random.Random,
    user: User,
    topic: Topic,
    profile: dict,
    cal_offset: int,
    dated_assessments: List[Assessment],
    studied_topic_ids: Set[int],
) -> None:
    """
    Generate LearningEvents and RecallEvents for one (student, topic) pair.

    Study session schedule
    ----------------------
    1. Pick a 'first learn' day within the first 70% of the semester.
    2. Schedule n_study_sessions revision sessions at profile-defined intervals.
    3. If an assessment covers this topic, optionally add pre-assessment crammer
       sessions within 7 days before the (shifted) assessment start.

    Self-check schedule
    -------------------
    After each study session (except the first), there is a probability of a
    recall check 1–7 days later.  The check outcome (is_correct) is drawn from
    _recall_probability() using only information available up to that moment
    (zero leakage by construction: the draw happens after all study-time
    features are computed from the in-memory lists, never from the DB features).
    """
    # --- 1. First learn date ---
    first_day_offset = rng.randint(0, int(SEMESTER_DAYS * 0.70))
    first_learn_dt = _shift_date(SEMESTER_START, first_day_offset + cal_offset)
    # Clamp to valid semester range
    first_learn_dt = max(first_learn_dt, SEMESTER_START + timedelta(days=0))
    first_learn_dt = min(first_learn_dt, SEMESTER_END - timedelta(days=10))

    n_lo, n_hi = profile["n_study_sessions"]
    n_sessions = rng.randint(n_lo, n_hi)

    int_lo, int_hi = profile["study_interval_days"]
    sec_lo, sec_hi = profile["session_secs"]

    study_times: List[datetime] = [first_learn_dt]
    cursor = first_learn_dt

    for _ in range(n_sessions - 1):
        gap = rng.randint(int_lo, int_hi)
        cursor = cursor + timedelta(days=gap)
        if cursor > SEMESTER_END:
            break
        study_times.append(cursor)

    # --- 2. Pre-assessment boost sessions ---
    boost_count = profile["pre_assessment_boost"]
    if boost_count > 0 and topic.lecture_num is not None:
        for assessment in dated_assessments:
            if topic.lecture_num not in assessment.covered_lectures_list:
                continue
            a_start = _shift_date(assessment.start_date, cal_offset)
            # Add sessions in the 7 days before assessment
            for b in range(boost_count):
                boost_dt = a_start - timedelta(days=rng.randint(1, 7))
                if SEMESTER_START <= boost_dt <= SEMESTER_END:
                    study_times.append(boost_dt)

    study_times.sort()

    # --- 3. Persist LearningEvents ---
    conf_bias = profile["confidence_bias"]
    for st in study_times:
        secs = rng.randint(int(sec_lo), int(sec_hi))
        # Base confidence: harder topics get lower confidence on average
        base_conf = max(0.0, min(1.0, _uniform(rng, 0.3, 0.85) + conf_bias
                                 - topic.difficulty * 0.20))
        db.add(LearningEvent(
            user_id=user.id,
            topic_id=topic.id,
            timestamp=st,
            time_spent_seconds=secs,
            self_reported_confidence=round(base_conf, 2),
            is_simulated=True,
        ))

    # --- 4. Self-checks (RecallEvents) ---
    # Only after the first study session is there a chance of a recall check.
    forgetting_factor = profile["forgetting_factor"]
    confusability_score = _confusability(topic)
    concurrent_load = min(len(studied_topic_ids), 8)

    for i, check_anchor in enumerate(study_times[1:], start=1):
        # ~65% chance of a self-check after any revision session
        if rng.random() > 0.65:
            continue

        check_gap = rng.randint(1, 7)
        check_dt = check_anchor + timedelta(days=check_gap)
        if check_dt > SEMESTER_END:
            break

        # Prior study sessions up to check_dt
        prior_studies = [t for t in study_times if t <= check_dt]
        if not prior_studies:
            continue

        times_studied_now = len(prior_studies)
        last_study = max(prior_studies)
        days_since = max((check_dt - last_study).days, 0)

        prereq_ratio = _prereq_ratio_sim(topic, studied_topic_ids)

        p_correct = _recall_probability(
            days_since_last=days_since,
            difficulty=topic.difficulty,
            times_studied=times_studied_now,
            prereq_ratio=prereq_ratio,
            confusability=confusability_score,
            concurrent_load=concurrent_load,
            forgetting_factor=forgetting_factor,
        )

        is_correct = rng.random() < p_correct

        # is_upcoming_assessment_prep: True if within 7 days of a dated assessment
        is_prep = False
        if topic.lecture_num is not None:
            for assessment in dated_assessments:
                if topic.lecture_num not in assessment.covered_lectures_list:
                    continue
                shifted_start = _shift_date(assessment.start_date, cal_offset)
                days_to_a = (shifted_start - check_dt).days
                if 0 <= days_to_a <= 7:
                    is_prep = True
                    break

        db.add(RecallEvent(
            user_id=user.id,
            topic_id=topic.id,
            timestamp=check_dt,
            is_correct=is_correct,
            time_spent_seconds=rng.randint(20, 120),
            is_upcoming_assessment_prep=is_prep,
            is_simulated=True,
        ))


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def _delete_simulated(db: Session) -> None:
    """Remove all records that have is_simulated=True, in FK-safe order."""
    sim_user_ids = [
        u.id for u in db.query(User).filter(User.is_simulated == True).all()
    ]
    if not sim_user_ids:
        return
    db.query(RecallEvent).filter(RecallEvent.user_id.in_(sim_user_ids)).delete(
        synchronize_session=False
    )
    db.query(LearningEvent).filter(LearningEvent.user_id.in_(sim_user_ids)).delete(
        synchronize_session=False
    )
    db.query(User).filter(User.id.in_(sim_user_ids)).delete(
        synchronize_session=False
    )
    db.flush()


# ---------------------------------------------------------------------------
# Logging summary
# ---------------------------------------------------------------------------

def _log_summary(db: Session) -> None:
    n_users = db.query(User).filter(User.is_simulated == True).count()
    n_les   = db.query(LearningEvent).filter(LearningEvent.is_simulated == True).count()
    n_res   = db.query(RecallEvent).filter(RecallEvent.is_simulated == True).count()
    logger.info(
        "Simulation complete: %d students, %d LearningEvents, %d RecallEvents",
        n_users, n_les, n_res,
    )


# ---------------------------------------------------------------------------
# Legacy compatibility shim
# ---------------------------------------------------------------------------
# The old API (seed_course_structure + simulate_users + generate_all) created
# fictional topics and fictional courses.  Those functions are preserved here
# as no-ops / deprecated stubs so existing import chains don't break, but they
# are NOT called by any production path.

def seed_course_structure(db: Session) -> None:  # noqa: ARG001
    """DEPRECATED: now a no-op. The seed loader (seed_loader.py) handles seeding."""
    logger.warning(
        "seed_course_structure() is deprecated and does nothing. "
        "Use backend.app.seed_loader.load_all_seeds() instead."
    )


def simulate_users(db: Session, n_users: int = 25, days_span: int = 90) -> None:
    """DEPRECATED: use simulate_students() with SimulationConfig instead."""
    logger.warning(
        "simulate_users() is deprecated. Use simulate_students() with "
        "SimulationConfig(n_students=%d) instead.", n_users
    )
    cfg = SimulationConfig(n_students=n_users)
    simulate_students(db, cfg)


def generate_all(db: Session, n_users: int = 25, days_span: int = 90) -> None:
    """DEPRECATED: use load_all_seeds() + simulate_students() instead."""
    logger.warning(
        "generate_all() is deprecated. Call load_all_seeds(db) first, "
        "then simulate_students(db, SimulationConfig(n_students=%d)).", n_users
    )
    cfg = SimulationConfig(n_students=n_users)
    simulate_students(db, cfg)
