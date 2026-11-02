"""
Database schema for The Forgetting Engine.

Hierarchy: Course -> Module -> Topic (a "concept" the learner can forget)
Topics can map to CourseOutcomes (many-to-many) and to prerequisite Topics.

Two kinds of learner activity are logged:
  - LearningEvent: the learner studied a topic (with time spent, self-reported confidence)
  - RecallEvent: the learner attempted a quiz/recall check on a topic (with correctness, time spent)

Everything else (days_since_last_revision, revision_count, etc.) is DERIVED
from these two event tables at feature-engineering time, not stored directly.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Table, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# ---- many-to-many: Topic <-> CourseOutcome -------------------------------
topic_co_association = Table(
    "topic_co_association",
    Base.metadata,
    Column("topic_id", ForeignKey("topics.id"), primary_key=True),
    Column("co_id", ForeignKey("course_outcomes.id"), primary_key=True),
)

# ---- many-to-many: Topic <-> Topic (prerequisites) ------------------------
topic_prereq_association = Table(
    "topic_prereq_association",
    Base.metadata,
    Column("topic_id", ForeignKey("topics.id"), primary_key=True),
    Column("prerequisite_id", ForeignKey("topics.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    is_simulated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    learning_events = relationship("LearningEvent", back_populates="user", cascade="all, delete-orphan")
    recall_events = relationship("RecallEvent", back_populates="user", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=True)
    name = Column(String, nullable=False)
    is_simulated = Column(Boolean, default=False, nullable=False)

    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    course_outcomes = relationship("CourseOutcome", back_populates="course", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="course", cascade="all, delete-orphan")
    sdl_items = relationship("SDLItem", back_populates="course", cascade="all, delete-orphan")


class CourseOutcome(Base):
    __tablename__ = "course_outcomes"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    code = Column(String, nullable=False)          # e.g. "CO1"
    description = Column(String, nullable=True)
    hours = Column(Float, nullable=True)
    marks = Column(Float, nullable=True)

    course = relationship("Course", back_populates="course_outcomes")
    topics = relationship("Topic", secondary=topic_co_association, back_populates="course_outcomes")


class Assessment(Base):
    """Assessment event with schedule date ranges and covered lectures."""
    __tablename__ = "assessments"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String, nullable=False)
    assessment_type = Column(String, nullable=True)
    marks = Column(Float, nullable=True)
    schedule = Column(String, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    covered_lectures = Column(String, nullable=True)   # e.g. "1-15" or comma separated
    covered_chapters = Column(String, nullable=True)

    course = relationship("Course", back_populates="assessments")


class SDLItem(Base):
    """Self Directed Learning (SDL) item."""
    __tablename__ = "sdl_items"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    sl_no = Column(Integer, nullable=True)
    topic = Column(String, nullable=False)
    hours = Column(Float, nullable=True)
    co_code = Column(String, nullable=True)

    course = relationship("Course", back_populates="sdl_items")


class Module(Base):
    __tablename__ = "modules"
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(String, nullable=False)
    order_index = Column(Integer, default=0)

    course = relationship("Course", back_populates="modules")
    topics = relationship("Topic", back_populates="module", cascade="all, delete-orphan")


class Topic(Base):
    """A single 'concept' — the atomic unit the model predicts forgetting for."""
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    lecture_num = Column(Integer, nullable=True)
    name = Column(String, nullable=False)
    importance = Column(Float, default=0.5)          # 0-1, weight toward exam/CO relevance
    reference_material = Column(String, nullable=True)  # notes text, or a link to material

    # --- universal difficulty: LLM-seeded, then crowd-refined over time ---
    llm_difficulty = Column(Float, default=0.5)       # initial LLM estimate, fixed once set
    crowd_difficulty = Column(Float, nullable=True)    # observed-outcome estimate, updated periodically
    difficulty = Column(Float, default=0.5)            # blended value actually used by the model
    difficulty_last_updated = Column(DateTime, nullable=True)
    num_crowd_samples = Column(Integer, default=0)     # how many self-checks fed into crowd_difficulty

    # --- LLM-generated "confusable topics" note ---
    confusable_note = Column(String, nullable=True)    # human-readable disambiguation text
    confusable_topic_names = Column(String, nullable=True)  # comma-separated names (simple storage)

    module = relationship("Module", back_populates="topics")
    course_outcomes = relationship("CourseOutcome", secondary=topic_co_association, back_populates="topics")
    prerequisites = relationship(
        "Topic",
        secondary=topic_prereq_association,
        primaryjoin=id == topic_prereq_association.c.topic_id,
        secondaryjoin=id == topic_prereq_association.c.prerequisite_id,
    )
    learning_events = relationship("LearningEvent", back_populates="topic")
    recall_events = relationship("RecallEvent", back_populates="topic")


class LearningEvent(Base):
    """A study session on a topic."""
    __tablename__ = "learning_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    time_spent_seconds = Column(Integer, default=0)
    self_reported_confidence = Column(Float)   # 0-1, learner's own rating after studying
    is_simulated = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="learning_events")
    topic = relationship("Topic", back_populates="learning_events")


class RecallEvent(Base):
    """A quiz / recall check attempt on a topic — this is what we predict."""
    __tablename__ = "recall_events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_correct = Column(Boolean, nullable=False)
    time_spent_seconds = Column(Integer, default=0)
    is_upcoming_assessment_prep = Column(Boolean, default=False)
    is_simulated = Column(Boolean, default=False, nullable=False)

    user = relationship("User", back_populates="recall_events")
    topic = relationship("Topic", back_populates="recall_events")
