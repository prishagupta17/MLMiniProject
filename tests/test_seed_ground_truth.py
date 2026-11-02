import os
import json
import logging
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.models import Base, Course, Module, Topic, CourseOutcome, Assessment, SDLItem
from backend.app.seed_loader import load_all_seeds, load_seed_file

GROUND_TRUTH_PATH = os.path.join(os.path.dirname(__file__), "ground_truth.json")
SEED_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "seed")


@pytest.fixture(scope="session")
def ground_truth():
    assert os.path.exists(GROUND_TRUTH_PATH), f"Ground truth not found at {GROUND_TRUTH_PATH}"
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        return json.load(f)["courses"]


@pytest.fixture(scope="session")
def seed_data():
    seeds = {}
    for fname in os.listdir(SEED_DIR):
        if fname.endswith(".json"):
            with open(os.path.join(SEED_DIR, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
                c_code = data["course_info"]["code"]
                seeds[c_code] = data
    return seeds


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_seed_files_exist(ground_truth, seed_data):
    for key, expected in ground_truth.items():
        code = expected["code"]
        assert code in seed_data, f"Seed data for course code {code} ({key}) missing"


def test_outcomes_and_marks(ground_truth, seed_data):
    for key, expected in ground_truth.items():
        code = expected["code"]
        data = seed_data[code]
        outcomes = data["outcomes"]

        # Number of COs
        assert len(outcomes) == expected["num_outcomes"], (
            f"{key} expected {expected['num_outcomes']} outcomes, got {len(outcomes)}"
        )

        # Marks list and sum
        marks = [co["marks"] for co in outcomes]
        assert marks == expected["outcome_marks"], (
            f"{key} marks {marks} != expected {expected['outcome_marks']}"
        )
        assert sum(marks) == 100, f"{key} marks must sum to 100, got {sum(marks)}"

        # Contact hours if specified in ground truth
        if "contact_hours" in expected:
            hours = [co.get("hours") for co in outcomes]
            assert hours == expected["contact_hours"], (
                f"{key} hours {hours} != expected {expected['contact_hours']}"
            )


def test_lecture_topics_and_co_ranges(ground_truth, seed_data):
    for key, expected in ground_truth.items():
        code = expected["code"]
        data = seed_data[code]
        lessons = data["lesson_plan"]

        # Lecture topics = lesson-plan rows excluding lecture 0, with CONTINUED rows kept
        assert len(lessons) == expected["num_lectures"], (
            f"{key} expected {expected['num_lectures']} lectures, got {len(lessons)}"
        )
        assert all(l["lecture_num"] != 0 for l in lessons), f"{key} contains lecture 0"

        # Check CO ranges
        ranges = expected["lecture_co_ranges"]
        lec_map = {l["lecture_num"]: l["co_code"] for l in lessons}

        for r_name, (start_l, end_l) in ranges.items():
            expected_co = r_name.split("_")[0]  # handles CO5_part1 -> CO5
            for lec in range(start_l, end_l + 1):
                actual_co = lec_map.get(lec)
                assert actual_co == expected_co, (
                    f"{key} L{lec} expected {expected_co}, got {actual_co}"
                )


def test_sdl_rows_and_hours(ground_truth, seed_data, caplog):
    for key, expected in ground_truth.items():
        code = expected["code"]
        data = seed_data[code]
        sdl_items = data.get("sdl_items", [])

        # SDL row count
        assert len(sdl_items) == expected["num_sdl_rows"], (
            f"{key} expected {expected['num_sdl_rows']} SDL rows, got {len(sdl_items)}"
        )

        # Total hours
        if "sdl_hours_total" in expected:
            total_hours = sum(item["hours"] for item in sdl_items)
            assert total_hours == expected["sdl_hours_total"], (
                f"{key} SDL hours sum {total_hours} != {expected['sdl_hours_total']}"
            )
        elif "sdl_hours_printed_total" in expected:
            assert data.get("sdl_hours_printed_total") == expected["sdl_hours_printed_total"]

        # EOM specific check: rows [32, 16, 8] sum to 56 while printed is 54
        if key == "EOM":
            row_hours = [item["hours"] for item in sdl_items]
            assert row_hours == expected["sdl_row_hours"]
            assert sum(row_hours) == expected["sdl_rows_sum"]
            assert data["sdl_hours_printed_total"] == expected["sdl_hours_printed_total"]


def test_spot_checks(ground_truth, seed_data):
    for key, expected in ground_truth.items():
        code = expected["code"]
        data = seed_data[code]
        lessons = {l["lecture_num"]: l for l in data["lesson_plan"]}

        for spot in expected.get("spot_checks", []):
            lec_num = spot["lecture"]
            assert lec_num in lessons, f"{key} missing lecture {lec_num}"
            topic_entry = lessons[lec_num]
            assert topic_entry["co_code"] == spot["co"], (
                f"{key} L{lec_num} CO {topic_entry['co_code']} != expected {spot['co']}"
            )
            needle = spot["contains"].lower().replace("naive", "naïve")
            topic_name_lower = topic_entry["name"].lower().replace("naive", "naïve")
            assert needle in topic_name_lower, (
                f"{key} L{lec_num} '{topic_entry['name']}' does not contain '{spot['contains']}'"
            )


def test_assessments(ground_truth, seed_data):
    # ML assessments: IA1, IA2, IA3, Mid-Term (dates null), End-Sem (dates null)
    ml = seed_data["CSE 3148"]
    ml_assessments = {a["name"]: a for a in ml["assessments"]}
    assert "IA1" in ml_assessments
    assert "17-29 Aug 2026" in ml_assessments["IA1"]["schedule"]
    assert "IA2" in ml_assessments
    assert "7-21 Sep 2026" in ml_assessments["IA2"]["schedule"]
    assert "IA3" in ml_assessments
    assert "19-31 Oct 2026" in ml_assessments["IA3"]["schedule"]
    assert ml_assessments["Mid-Term"]["marks"] == 30.0
    assert ml_assessments["Mid-Term"]["start_date"] is None
    assert ml_assessments["End-Sem"]["marks"] == 50.0
    assert ml_assessments["End-Sem"]["start_date"] is None

    # PCAP assessments
    pcap = seed_data["CSE 3129"]
    pcap_assessments = {a["name"]: a for a in pcap["assessments"]}
    assert pcap_assessments["Mid-Term"]["marks"] == 30.0
    assert "25 Sep to 1 Oct 2026" in pcap_assessments["Mid-Term"]["schedule"]
    assert pcap_assessments["End-Sem"]["marks"] == 50.0

    # FACD assessments
    facd = seed_data["CSE 3128"]
    facd_assessments = {a["name"]: a for a in facd["assessments"]}
    assert facd_assessments["Assignment 1"]["marks"] == 10.0
    cov1 = facd_assessments["Assignment 1"]["covered_lectures"]
    assert set(range(1, 16)).issubset(set(cov1)) if isinstance(cov1, list) else "L1 - L15" in cov1

    assert facd_assessments["Assignment 2"]["marks"] == 5.0
    cov2 = facd_assessments["Assignment 2"]["covered_lectures"]
    assert set(range(16, 25)).issubset(set(cov2)) if isinstance(cov2, list) else "L16 - L24" in cov2

    assert facd_assessments["Mid-Sem"]["marks"] == 30.0
    cov_mid = facd_assessments["Mid-Sem"]["covered_lectures"]
    assert set(range(1, 30)).issubset(set(cov_mid)) if isinstance(cov_mid, list) else "L1 - L29" in cov_mid

    assert facd_assessments["Assignment 3"]["marks"] == 5.0
    cov3 = facd_assessments["Assignment 3"]["covered_lectures"]
    assert set(range(30, 43)).issubset(set(cov3)) if isinstance(cov3, list) else "L30 - L42" in cov3

    assert facd_assessments["End-Sem"]["marks"] == 50.0
    cov_end = facd_assessments["End-Sem"]["covered_lectures"]
    assert set(range(1, 49)).issubset(set(cov_end)) if isinstance(cov_end, list) else "L1 - L48" in cov_end


def test_seed_loader_db(db_session, ground_truth):
    courses = load_all_seeds(db_session)
    assert len(courses) == 4

    for key, expected in ground_truth.items():
        code = expected["code"]
        course = db_session.query(Course).filter(Course.code == code).first()
        assert course is not None, f"Course {code} not loaded in DB"

        # Check outcomes count and marks
        assert len(course.course_outcomes) == expected["num_outcomes"]
        marks = [co.marks for co in course.course_outcomes]
        assert marks == expected["outcome_marks"]

        # Check topics count
        topics = (
            db_session.query(Topic)
            .join(Module)
            .filter(Module.course_id == course.id)
            .all()
        )
        assert len(topics) == expected["num_lectures"], (
            f"{key} DB has {len(topics)} topics, expected {expected['num_lectures']}"
        )

        # Check SDL count
        sdl_items = db_session.query(SDLItem).filter(SDLItem.course_id == course.id).all()
        assert len(sdl_items) == expected["num_sdl_rows"]
