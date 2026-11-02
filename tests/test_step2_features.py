import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import (
    Base, User, Course, Module, Topic, CourseOutcome, Assessment,
    LearningEvent, RecallEvent
)
from backend.app.seed_loader import load_all_seeds
from backend.app.features import (
    FEATURE_COLUMNS,
    build_feature_table,
    compute_assessment_timing,
    compute_topic_importances_for_course,
)
from backend.app.predict import compute_current_features, predict_forgetting


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def seeded_db(db_session):
    load_all_seeds(db_session)
    return db_session


def test_feature_columns_list():
    expected_13 = [
        "times_studied",
        "is_first_exposure",
        "days_since_last_studied",
        "revision_frequency",
        "self_reported_confidence",
        "universal_difficulty",
        "topic_importance",
        "time_spent_studying_min",
        "confusability_score",
        "prerequisite_completion_ratio",
        "concurrent_topic_load",
        "days_to_next_assessment",
        "has_upcoming_assessment",
    ]
    assert FEATURE_COLUMNS == expected_13, f"FEATURE_COLUMNS must have exactly the 13 specified features, got {FEATURE_COLUMNS}"


def test_topic_importance_expected_values(seeded_db):
    def get_topic_importance(course_code, lecture_num):
        course = seeded_db.query(Course).filter(Course.code == course_code).first()
        assert course is not None
        topic = (
            seeded_db.query(Topic)
            .join(Module)
            .filter(Module.course_id == course.id, Topic.lecture_num == lecture_num)
            .first()
        )
        assert topic is not None, f"Topic L{lecture_num} in {course_code} not found"
        return round(topic.importance, 3)

    # ML expected values
    assert get_topic_importance("CSE 3148", 1) == 1.000
    assert get_topic_importance("CSE 3148", 36) == 0.545

    # PCAP expected values
    assert get_topic_importance("CSE 3129", 18) == 0.953

    # EOM expected values
    assert get_topic_importance("HUM 3022", 1) == 0.846
    assert get_topic_importance("HUM 3022", 24) == 1.000

    # FACD expected values
    assert get_topic_importance("CSE 3128", 38) == 1.000
    assert get_topic_importance("CSE 3128", 47) == 0.938

    # Unassociated topic without CO data keeps importance 0.5
    custom_course = Course(code="TEST101", name="Test Course")
    seeded_db.add(custom_course)
    seeded_db.flush()
    custom_module = Module(course_id=custom_course.id, name="Module 1")
    seeded_db.add(custom_module)
    seeded_db.flush()
    custom_topic = Topic(module_id=custom_module.id, name="Custom Topic Without CO")
    seeded_db.add(custom_topic)
    seeded_db.commit()
    assert custom_topic.importance == 0.5


def test_assessment_timing_features(seeded_db):
    def check_timing(course_code, lecture_num, as_of_str):
        course = seeded_db.query(Course).filter(Course.code == course_code).first()
        topic = (
            seeded_db.query(Topic)
            .join(Module)
            .filter(Module.course_id == course.id, Topic.lecture_num == lecture_num)
            .first()
        )
        as_of = datetime.strptime(as_of_str, "%Y-%m-%d")
        days, has_upcoming = compute_assessment_timing(seeded_db, topic, as_of)
        return days, has_upcoming

    # FACD tests
    # FACD L10, 2026-08-01 -> 16
    assert check_timing("CSE 3128", 10, "2026-08-01") == (16, 1)
    # FACD L10, 2026-08-20 -> 0
    assert check_timing("CSE 3128", 10, "2026-08-20") == (0, 1)
    # FACD L20, 2026-08-01 -> 37 (Assignment 2 starts 7 Sep, earlier than Mid-sem)
    assert check_timing("CSE 3128", 20, "2026-08-01") == (37, 1)
    # FACD L47, 2026-11-01 -> 13, has_upcoming 1
    assert check_timing("CSE 3128", 47, "2026-11-01") == (13, 1)
    # FACD L47, 2026-11-20 -> 0
    assert check_timing("CSE 3128", 47, "2026-11-20") == (0, 1)
    # FACD L47, 2026-11-29 -> 60, has_upcoming 0
    assert check_timing("CSE 3128", 47, "2026-11-29") == (60, 0)

    # ML tests
    # ML L1, 2026-10-01 -> 18 (IA3 starts 19 Oct)
    assert check_timing("CSE 3148", 1, "2026-10-01") == (18, 1)

    # EOM tests
    # EOM L1, 2026-08-01 -> 16 (Quiz 1 starts 17 Aug)
    assert check_timing("HUM 3022", 1, "2026-08-01") == (16, 1)
    # EOM L25, 2026-10-01 -> 3 (Term project starts 4 Oct)
    assert check_timing("HUM 3022", 25, "2026-10-01") == (3, 1)


def test_leakage_guarantee(seeded_db):
    # Rule 1: No column derived from RecallEvent.is_correct is in FEATURE_COLUMNS
    for feat in FEATURE_COLUMNS:
        assert "correct" not in feat.lower()
        assert "recall" not in feat.lower() or feat == "universal_difficulty"
        assert feat != "forgot"

    # Rule 2: Features for a row use ONLY events strictly before that self-check
    user = User(name="Leakage Test User", email="leakage@test.edu")
    seeded_db.add(user)
    seeded_db.flush()

    topic = seeded_db.query(Topic).first()
    t0 = datetime(2026, 8, 10, 10, 0, 0)
    t1 = datetime(2026, 8, 15, 10, 0, 0)
    t_recall = datetime(2026, 8, 20, 10, 0, 0)
    t_future = datetime(2026, 8, 25, 10, 0, 0)

    # Past study events
    seeded_db.add(LearningEvent(user_id=user.id, topic_id=topic.id, timestamp=t0, time_spent_seconds=600, self_reported_confidence=0.8))
    seeded_db.add(LearningEvent(user_id=user.id, topic_id=topic.id, timestamp=t1, time_spent_seconds=1200, self_reported_confidence=0.9))

    # The recall event being evaluated
    re = RecallEvent(user_id=user.id, topic_id=topic.id, timestamp=t_recall, is_correct=True)
    seeded_db.add(re)
    seeded_db.commit()

    df_before = build_feature_table(seeded_db)
    row_before = df_before[df_before["recall_event_id"] == re.id].iloc[0][FEATURE_COLUMNS].to_dict()

    # Now add FUTURE study events and FUTURE recall events
    seeded_db.add(LearningEvent(user_id=user.id, topic_id=topic.id, timestamp=t_future, time_spent_seconds=3600, self_reported_confidence=0.2))
    seeded_db.add(RecallEvent(user_id=user.id, topic_id=topic.id, timestamp=t_future, is_correct=False))

    # Flip the recall event's own is_correct label
    re.is_correct = False
    seeded_db.commit()

    df_after = build_feature_table(seeded_db)
    row_after = df_after[df_after["recall_event_id"] == re.id].iloc[0][FEATURE_COLUMNS].to_dict()

    # Features must be 100% identical
    for col in FEATURE_COLUMNS:
        assert row_before[col] == pytest.approx(row_after[col]), f"Feature leakage on {col}: {row_before[col]} vs {row_after[col]}"


def test_feature_consistency_predict_vs_table(seeded_db):
    user = User(name="Consistency Test User", email="consistency@test.edu")
    seeded_db.add(user)
    seeded_db.flush()

    topic = seeded_db.query(Topic).first()
    t_study = datetime(2026, 8, 10, 10, 0, 0)
    t_check = datetime(2026, 8, 20, 10, 0, 0)

    seeded_db.add(LearningEvent(user_id=user.id, topic_id=topic.id, timestamp=t_study, time_spent_seconds=900, self_reported_confidence=0.7))
    re = RecallEvent(user_id=user.id, topic_id=topic.id, timestamp=t_check, is_correct=True)
    seeded_db.add(re)
    seeded_db.commit()

    df = build_feature_table(seeded_db)
    table_features = df[df["recall_event_id"] == re.id].iloc[0][FEATURE_COLUMNS].to_dict()

    predict_features = compute_current_features(seeded_db, user.id, topic.id, as_of=t_check)

    for feat in FEATURE_COLUMNS:
        assert table_features[feat] == pytest.approx(predict_features[feat]), (
            f"Mismatch on {feat}: table={table_features[feat]} vs predict={predict_features[feat]}"
        )


def test_model_feature_version_mismatch(seeded_db):
    user = User(name="Test Model User", email="model_test@test.edu")
    seeded_db.add(user)
    seeded_db.flush()
    topic = seeded_db.query(Topic).first()

    # Because the existing model on disk has 11 features and FEATURE_COLUMNS now has 13 features,
    # predict_forgetting must raise a clear RuntimeError requiring retraining
    with pytest.raises(RuntimeError) as exc_info:
        predict_forgetting(seeded_db, user.id, topic.id)
    assert "retrain required" in str(exc_info.value).lower()
