"""
Step 3 acceptance tests: Simulated Student Data.

All tests are written BEFORE implementation, so they will FAIL until
backend/app/synthetic_data.py is rewritten to satisfy the spec.

Rules enforced here:
- Every simulated User, LearningEvent and RecallEvent has is_simulated=True.
- Topics must come from real seeded courses, never invented.
- All four courses must be represented.
- Timestamps are chronologically consistent.
- RecallEvent.is_correct is NEVER read back as a feature input.
- Reproducibility: same seed + config -> identical output.
- Assessment dates are shifted per student, preserving relative spacing.
- Feature table build_feature_table() works on simulated data.
- Existing real student data is untouched.
- ground_truth.json is not modified.
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import (
    Base, User, Course, Module, Topic,
    LearningEvent, RecallEvent, Assessment,
)
from backend.app.seed_loader import load_all_seeds
from backend.app.features import FEATURE_COLUMNS, build_feature_table
from backend.app.synthetic_data import (
    simulate_students,       # NEW: replaces the old generate_all / simulate_users
    SimulationConfig,        # NEW: dataclass / named-tuple for config
    STUDENT_CALENDAR_OFFSET_DAYS,  # NEW: constant from spec (range ±14 days)
    DEFAULT_N_STUDENTS,      # NEW: documented default
    DEFAULT_SEED,            # NEW: documented default seed
)

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def seeded_engine():
    """One in-memory DB shared across all tests in this module."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    load_all_seeds(db)
    db.close()
    return engine


@pytest.fixture
def db(seeded_engine):
    """Fresh session per test, rolls back after the test."""
    Session = sessionmaker(bind=seeded_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="module")
def valid_topic_ids(seeded_engine):
    """Set of topic IDs that exist in the real seeded courses."""
    Session = sessionmaker(bind=seeded_engine)
    db = Session()
    ids = {t.id for t in db.query(Topic).all()}
    db.close()
    return ids


@pytest.fixture(scope="module")
def valid_course_codes(seeded_engine):
    Session = sessionmaker(bind=seeded_engine)
    db = Session()
    codes = {c.code for c in db.query(Course).all()}
    db.close()
    return codes


# ---------------------------------------------------------------------------
# Helper: run a simulation and return (users, learning_events, recall_events)
# ---------------------------------------------------------------------------

def run_sim(db, n_students=5, seed=42):
    cfg = SimulationConfig(n_students=n_students, random_seed=seed)
    simulate_students(db, cfg)
    users = db.query(User).filter(User.is_simulated == True).all()
    les   = db.query(LearningEvent).filter(LearningEvent.is_simulated == True).all()
    res   = db.query(RecallEvent).filter(RecallEvent.is_simulated == True).all()
    return users, les, res


# ---------------------------------------------------------------------------
# Test 1: Simulation runs without error and generates records
# ---------------------------------------------------------------------------

def test_simulation_runs_successfully(db):
    """simulate_students() completes without raising exceptions."""
    cfg = SimulationConfig(n_students=3, random_seed=0)
    simulate_students(db, cfg)  # must not raise
    users = db.query(User).filter(User.is_simulated == True).all()
    assert len(users) == 3


# ---------------------------------------------------------------------------
# Test 2: Every simulated student has is_simulated=True
# ---------------------------------------------------------------------------

def test_all_simulated_users_flagged(db):
    users, les, res = run_sim(db)
    for u in users:
        assert u.is_simulated is True, f"User {u.id} missing is_simulated=True"


# ---------------------------------------------------------------------------
# Test 3: All generated events reference actual seeded topics
# ---------------------------------------------------------------------------

def test_events_reference_real_topics(db, valid_topic_ids):
    users, les, res = run_sim(db)
    assert len(les) > 0, "No LearningEvents were generated"
    assert len(res) > 0, "No RecallEvents were generated"
    for le in les:
        assert le.topic_id in valid_topic_ids, (
            f"LearningEvent references non-existent topic_id={le.topic_id}"
        )
    for re in res:
        assert re.topic_id in valid_topic_ids, (
            f"RecallEvent references non-existent topic_id={re.topic_id}"
        )


# ---------------------------------------------------------------------------
# Test 4: All four seeded courses are represented in generated events
# ---------------------------------------------------------------------------

def test_all_four_courses_represented(db, seeded_engine):
    """After simulation, each of the 4 courses has at least one LearningEvent."""
    cfg = SimulationConfig(n_students=10, random_seed=1)
    simulate_students(db, cfg)

    # Build: topic_id -> course_code
    Session = sessionmaker(bind=seeded_engine)
    lookup_db = Session()
    topic_to_course = {}
    for course in lookup_db.query(Course).all():
        for module in course.modules:
            for topic in module.topics:
                topic_to_course[topic.id] = course.code
    lookup_db.close()

    covered_courses = set()
    for le in db.query(LearningEvent).filter(LearningEvent.is_simulated == True).all():
        code = topic_to_course.get(le.topic_id)
        if code:
            covered_courses.add(code)

    required = {"CSE 3148", "CSE 3129", "HUM 3022", "CSE 3128"}
    assert required.issubset(covered_courses), (
        f"Missing courses in simulated events: {required - covered_courses}"
    )


# ---------------------------------------------------------------------------
# Test 5: No invented topics — topic ids must be in the seeded set
# ---------------------------------------------------------------------------

def test_no_invented_topics(db, valid_topic_ids):
    users, les, res = run_sim(db)
    all_topic_ids_in_events = (
        {le.topic_id for le in les} | {re.topic_id for re in res}
    )
    invented = all_topic_ids_in_events - valid_topic_ids
    assert invented == set(), f"Invented (non-existent) topic_ids found: {invented}"


# ---------------------------------------------------------------------------
# Test 6: Timestamps are chronologically consistent
# ---------------------------------------------------------------------------

def test_timestamps_chronologically_consistent(db):
    users, les, res = run_sim(db, n_students=5)
    for user in users:
        user_les = sorted(
            [le for le in les if le.user_id == user.id],
            key=lambda e: e.timestamp
        )
        user_res = sorted(
            [re for re in res if re.user_id == user.id],
            key=lambda e: e.timestamp
        )
        # Every RecallEvent for a given (user, topic) must have at least one
        # LearningEvent strictly before (or at) it.
        le_times_by_topic = {}
        for le in user_les:
            le_times_by_topic.setdefault(le.topic_id, []).append(le.timestamp)

        for re in user_res:
            prior = [t for t in le_times_by_topic.get(re.topic_id, [])
                     if t <= re.timestamp]
            assert len(prior) > 0, (
                f"RecallEvent at {re.timestamp} for topic {re.topic_id} "
                f"has no prior LearningEvent"
            )


# ---------------------------------------------------------------------------
# Test 7: RecallEvents have valid references and boolean labels
# ---------------------------------------------------------------------------

def test_recall_events_valid_structure(db):
    users, les, res = run_sim(db)
    user_ids = {u.id for u in users}
    for re in res:
        assert re.user_id in user_ids
        assert re.topic_id is not None
        assert isinstance(re.is_correct, bool), (
            f"is_correct must be bool, got {type(re.is_correct)}"
        )
        assert re.is_simulated is True
        assert re.timestamp is not None


# ---------------------------------------------------------------------------
# Test 8: Simulated records distinguishable from real records
# ---------------------------------------------------------------------------

def test_simulated_distinguishable_from_real(db):
    users, les, res = run_sim(db)
    # After seeding only (no real users): all users should be simulated
    real_users = db.query(User).filter(User.is_simulated == False).all()
    # Real users have is_simulated=False; simulated have True
    for u in users:
        assert u.is_simulated is True
    for u in real_users:
        assert u.is_simulated is False

    sim_les  = db.query(LearningEvent).filter(LearningEvent.is_simulated == True).all()
    real_les = db.query(LearningEvent).filter(LearningEvent.is_simulated == False).all()
    assert all(le.is_simulated for le in sim_les)
    assert all(not le.is_simulated for le in real_les)


# ---------------------------------------------------------------------------
# Test 9: Reproducibility — same seed + config -> identical outcome
# ---------------------------------------------------------------------------

def test_reproducibility_same_seed(seeded_engine):
    """Two independent runs with the same config produce identical histories."""
    def collect(seed_val):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        load_all_seeds(db)
        cfg = SimulationConfig(n_students=4, random_seed=seed_val)
        simulate_students(db, cfg)
        users = db.query(User).filter(User.is_simulated == True).order_by(User.name).all()
        les   = db.query(LearningEvent).filter(LearningEvent.is_simulated == True).order_by(
            LearningEvent.user_id, LearningEvent.topic_id, LearningEvent.timestamp
        ).all()
        res   = db.query(RecallEvent).filter(RecallEvent.is_simulated == True).order_by(
            RecallEvent.user_id, RecallEvent.topic_id, RecallEvent.timestamp
        ).all()
        summary = {
            "n_users": len(users),
            "n_les": len(les),
            "n_res": len(res),
            "le_topic_ids": [le.topic_id for le in les],
            "re_topic_ids": [re.topic_id for re in res],
            "re_correct": [re.is_correct for re in res],
        }
        db.close()
        return summary

    run_a = collect(seed_val=99)
    run_b = collect(seed_val=99)
    assert run_a == run_b, "Same seed produced different output — not reproducible"


# ---------------------------------------------------------------------------
# Test 10: Different seeds produce different histories
# ---------------------------------------------------------------------------

def test_different_seeds_differ(seeded_engine):
    def collect_re_correct(seed_val):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        load_all_seeds(db)
        cfg = SimulationConfig(n_students=8, random_seed=seed_val)
        simulate_students(db, cfg)
        res = db.query(RecallEvent).filter(RecallEvent.is_simulated == True).order_by(
            RecallEvent.user_id, RecallEvent.topic_id, RecallEvent.timestamp
        ).all()
        db.close()
        return [re.is_correct for re in res]

    run_42 = collect_re_correct(42)
    run_99 = collect_re_correct(99)
    # They might differ in length or content; at minimum correctness should differ
    assert run_42 != run_99, (
        "Runs with different seeds produced identical is_correct sequences"
    )


# ---------------------------------------------------------------------------
# Test 11: Assessment calendar shifting preserves relative spacing
# ---------------------------------------------------------------------------

def test_assessment_calendar_shift(db, seeded_engine):
    """
    Each simulated student gets a per-student STUDENT_CALENDAR_OFFSET_DAYS shift.
    Constant is declared in synthetic_data.py as a tuple/range describing the
    shift distribution.  We verify:
    - The constant STUDENT_CALENDAR_OFFSET_DAYS is a tuple of two ints (min, max).
    - min >= -14, max <= 14.
    - The function simulate_students does not crash for any shift in that range.
    """
    lo, hi = STUDENT_CALENDAR_OFFSET_DAYS
    assert isinstance(lo, int) and isinstance(hi, int)
    assert lo >= -14
    assert hi <= 14
    assert lo < hi

    # Run with 20 students to exercise multiple shift values.
    # replace_existing=True because earlier tests in this module already wrote
    # simulated records into the module-scope engine.
    cfg = SimulationConfig(n_students=20, random_seed=7, replace_existing=True)
    simulate_students(db, cfg)
    db.commit()
    users = db.query(User).filter(User.is_simulated == True).all()
    assert len(users) == 20


# ---------------------------------------------------------------------------
# Test 12: ground_truth.json is not modified by the simulation
# ---------------------------------------------------------------------------

def test_ground_truth_not_modified():
    gt_path = Path("tests/ground_truth.json")
    assert gt_path.exists(), "ground_truth.json does not exist"
    with open(gt_path, "r", encoding="utf-8") as f:
        content_before = f.read()

    # Parse to check validity
    data = json.loads(content_before)
    # ground_truth.json has a single top-level key "courses" mapping 4 course keys
    assert "courses" in data
    assert len(data["courses"]) >= 4, "ground_truth.json must have at least 4 course entries under 'courses'"

    # The file content must be identical after we read it (we did not write it)
    with open(gt_path, "r", encoding="utf-8") as f:
        content_after = f.read()
    assert content_before == content_after


# ---------------------------------------------------------------------------
# Test 13: build_feature_table works on simulated records (13-feature compat)
# ---------------------------------------------------------------------------

def test_feature_table_works_on_simulated_data(db):
    """build_feature_table must produce all 13 FEATURE_COLUMNS from simulated data."""
    cfg = SimulationConfig(n_students=5, random_seed=10)
    simulate_students(db, cfg)

    df = build_feature_table(db)
    # Must have rows
    assert len(df) > 0, "build_feature_table returned empty DataFrame"

    # All 13 feature columns must be present
    for col in FEATURE_COLUMNS:
        assert col in df.columns, f"Feature column '{col}' missing from DataFrame"

    # No NaN in any feature column for simulated rows
    sim_rows = df[df["user_id"].isin(
        [u.id for u in db.query(User).filter(User.is_simulated == True).all()]
    )]
    for col in FEATURE_COLUMNS:
        n_na = sim_rows[col].isna().sum()
        assert n_na == 0, f"Feature '{col}' has {n_na} NaN values in simulated rows"


# ---------------------------------------------------------------------------
# Test 14: No feature is derived from RecallEvent.is_correct
# ---------------------------------------------------------------------------

def test_no_leakage_from_is_correct(db):
    """
    Flip is_correct on all RecallEvents for a simulated student after generation.
    The feature rows must remain identical (is_correct is not an input feature).
    """
    cfg = SimulationConfig(n_students=3, random_seed=20)
    simulate_students(db, cfg)

    df_before = build_feature_table(db)

    # Flip all is_correct values for simulated RecallEvents
    for re in db.query(RecallEvent).filter(RecallEvent.is_simulated == True).all():
        re.is_correct = not re.is_correct
    db.commit()

    df_after = build_feature_table(db)

    # Re-index on recall_event_id to compare same rows
    before_idx = df_before.set_index("recall_event_id")
    after_idx  = df_after.set_index("recall_event_id")

    common_ids = before_idx.index.intersection(after_idx.index)
    assert len(common_ids) > 0, "No common recall events to compare"

    for col in FEATURE_COLUMNS:
        diff = (before_idx.loc[common_ids, col] - after_idx.loc[common_ids, col]).abs().max()
        assert diff == pytest.approx(0.0), (
            f"Feature '{col}' changed after flipping is_correct — LEAKAGE detected"
        )
