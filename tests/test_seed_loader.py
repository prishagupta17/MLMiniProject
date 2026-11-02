import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import Base, Course, Module, Topic, CourseOutcome, Assessment
from backend.app.pdf_extractor import (
    clean_text_markers,
    merge_continued_rows,
    extract_pdf_course_plan,
)
from backend.app.seed_loader import load_all_seeds, load_seed_file


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_clean_text_markers():
    sample1 = "4(T1) Problems on Deterministic Finite Accepter"
    sample2 = "23 *ID3,  *C4.5 [Ref Text Book 1] (Theory)"
    sample3 = "Support Vector Classifiers [Ref Text Book 1] *Numerical examples (Theory)"

    assert clean_text_markers(sample1) == "4 Problems on Deterministic Finite Accepter"
    assert clean_text_markers(sample2) == "23 ID3, C4.5"
    assert clean_text_markers(sample3) == "Support Vector Classifiers Numerical examples"


def test_merge_continued_rows_and_skip_l0():
    raw_topics = [
        {"lecture_num": 0, "name": "To address OBE philosophy... L0"},
        {"lecture_num": 4, "name": "14 Principles of Management by Henri Fayol"},
        {"lecture_num": 5, "name": "14 Principles of Management by Henri Fayol - CONTINUED"},
        {"lecture_num": 6, "name": "Mintzberg's 10 roles"},
    ]

    merged = merge_continued_rows(raw_topics)
    # Lecture 0 should be skipped
    assert all(t["lecture_num"] != 0 for t in merged)
    # L4 and L5 should be merged into 1 topic
    assert len(merged) == 2
    assert "14 Principles of Management" in merged[0]["name"]
    assert merged[0].get("continued") is True


def test_scanned_pdf_graceful_error():
    # PCAP or CSE course plan have 0 text layer
    with pytest.raises(RuntimeError) as exc_info:
        extract_pdf_course_plan("samples/Course Plan-CSE-3129-PCAP_26_8_2026_NE.pdf")
    assert "Scanned PDF without text layer detected" in str(exc_info.value)
    assert "OCR" in str(exc_info.value)


def test_load_all_seeds(db_session):
    courses = load_all_seeds(db_session)
    assert len(courses) >= 4

    course_codes = {c.code for c in courses}
    assert "HUM 3022" in course_codes
    assert "CSE 3148" in course_codes
    assert "CSE 3129" in course_codes
    assert "CSE 3128" in course_codes

    # Check HUM 3022 specific outcomes and assessments
    hum = db_session.query(Course).filter(Course.code == "HUM 3022").first()
    assert hum is not None
    assert len(hum.course_outcomes) == 5
    co1 = next(co for co in hum.course_outcomes if co.code == "CO1")
    assert co1.hours == 8
    assert co1.marks == 23

    # Ensure no lecture 0 topic exists in topics
    l0_topics = db_session.query(Topic).filter(Topic.lecture_num == 0).all()
    assert len(l0_topics) == 0

    # Check assessments are loaded with dates and covered lectures
    assessments = db_session.query(Assessment).filter(Assessment.course_id == hum.id).all()
    assert len(assessments) >= 4
    quiz = next(a for a in assessments if "Quiz" in a.name)
    assert quiz.marks == 5.0
    assert quiz.start_date is not None
    assert quiz.covered_lectures is not None

    # Check CSE 3128 topics have stripped (T1) etc
    cse3128 = db_session.query(Course).filter(Course.code == "CSE 3128").first()
    all_topics = (
        db_session.query(Topic)
        .join(Module)
        .filter(Module.course_id == cse3128.id)
        .all()
    )
    for topic in all_topics:
        assert "(T" not in topic.name
        assert "[Ref" not in topic.name
