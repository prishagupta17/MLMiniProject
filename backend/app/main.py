from datetime import datetime
from typing import List
from dotenv import load_dotenv
load_dotenv()  # reads backend/.env if present — see .env.example

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import init_db, get_db
from . import models, schemas
from .predict import predict_forgetting
from .topic_enrichment import enrich_topic
from .difficulty_refine import refresh_topic_difficulty

app = FastAPI(title="The Forgetting Engine API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # demo only — tighten before real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


# ---------------------------------------------------------------- users ----
@app.post("/users", response_model=schemas.UserOut)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        return existing
    user = models.User(name=payload.name, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


# -------------------------------------------------------------- courses ----
@app.post("/courses", response_model=schemas.CourseOut)
def create_course(payload: schemas.CourseCreate, db: Session = Depends(get_db)):
    course = models.Course(name=payload.name)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@app.get("/courses", response_model=List[schemas.CourseOut])
def list_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()


@app.post("/modules", response_model=schemas.ModuleOut)
def create_module(payload: schemas.ModuleCreate, db: Session = Depends(get_db)):
    course = db.query(models.Course).get(payload.course_id)
    if not course:
        raise HTTPException(404, "Course not found")
    module = models.Module(course_id=payload.course_id, name=payload.name, order_index=payload.order_index)
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


@app.get("/courses/{course_id}/modules", response_model=List[schemas.ModuleOut])
def list_modules(course_id: int, db: Session = Depends(get_db)):
    return db.query(models.Module).filter(models.Module.course_id == course_id).all()


@app.post("/topics", response_model=schemas.TopicOut)
def create_topic(payload: schemas.TopicCreate, db: Session = Depends(get_db)):
    module = db.query(models.Module).get(payload.module_id)
    if not module:
        raise HTTPException(404, "Module not found")

    sibling_names = [t.name for t in db.query(models.Topic).filter(models.Topic.module_id == payload.module_id).all()]
    enrichment = enrich_topic(
        topic_name=payload.name,
        module_name=module.name,
        course_name=module.course.name,
        sibling_topic_names=sibling_names,
        reference_material=payload.reference_material,
    )

    topic = models.Topic(
        module_id=payload.module_id, name=payload.name,
        importance=payload.importance,
        reference_material=payload.reference_material,
        llm_difficulty=enrichment["difficulty"],
        difficulty=enrichment["difficulty"],
        confusable_note=enrichment.get("confusable_note") or None,
        confusable_topic_names=(
            ",".join(enrichment["confusable_topic_names"]) if enrichment.get("confusable_topic_names") else None
        ),
    )
    if payload.prerequisite_ids:
        prereqs = db.query(models.Topic).filter(models.Topic.id.in_(payload.prerequisite_ids)).all()
        topic.prerequisites = prereqs
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@app.get("/modules/{module_id}/topics", response_model=List[schemas.TopicOut])
def list_topics(module_id: int, db: Session = Depends(get_db)):
    return db.query(models.Topic).filter(models.Topic.module_id == module_id).all()


# ---------------------------------------------------------------- events ----
@app.post("/learning-events")
def log_learning_event(payload: schemas.LearningEventCreate, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(payload.topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    event = models.LearningEvent(
        user_id=payload.user_id, topic_id=payload.topic_id,
        time_spent_seconds=payload.time_spent_seconds,
        self_reported_confidence=payload.self_reported_confidence,
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    return {"status": "logged", "event_id": event.id}


@app.post("/self-check-events")
def log_self_check_event(payload: schemas.RecallEventCreate, db: Session = Depends(get_db)):
    """Logs a recall self-check. Used ONLY to (a) validate model accuracy over
    time and (b) refine the topic's crowd difficulty — never fed back into
    the model as an input feature."""
    topic = db.query(models.Topic).get(payload.topic_id)
    if not topic:
        raise HTTPException(404, "Topic not found")
    event = models.RecallEvent(
        user_id=payload.user_id, topic_id=payload.topic_id,
        is_correct=payload.is_correct, time_spent_seconds=payload.time_spent_seconds,
        is_upcoming_assessment_prep=payload.is_upcoming_assessment_prep,
        timestamp=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    new_difficulty = refresh_topic_difficulty(db, payload.topic_id)
    return {"status": "logged", "event_id": event.id, "updated_topic_difficulty": new_difficulty}


# ------------------------------------------------------------ dashboard ----
@app.get("/users/{user_id}/dashboard", response_model=schemas.DashboardOut)
def get_dashboard(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    studied_topic_ids = {
        row.topic_id for row in
        db.query(models.LearningEvent.topic_id).filter(models.LearningEvent.user_id == user_id).distinct()
    }

    topics_out = []
    for topic_id in studied_topic_ids:
        result = predict_forgetting(db, user_id, topic_id)
        if result is None:
            continue
        topic = db.query(models.Topic).get(topic_id)
        topics_out.append(schemas.TopicRisk(
            topic_id=topic_id,
            topic_name=topic.name,
            module_name=topic.module.name,
            forgetting_probability=result["forgetting_probability"],
            retention_status=result["retention_status"],
            top_factors=result["top_factors"],
            local_explanation=result.get("local_explanation"),
        ))

    topics_out.sort(key=lambda t: -t.forgetting_probability)
    overall = (
        1 - (sum(t.forgetting_probability for t in topics_out) / len(topics_out))
        if topics_out else 1.0
    )
    high_risk_count = sum(1 for t in topics_out if t.retention_status == "high_risk")

    return schemas.DashboardOut(
        user_id=user_id,
        generated_at=datetime.utcnow(),
        topics=topics_out,
        overall_retention_score=round(overall, 3),
        high_risk_count=high_risk_count,
    )


@app.get("/")
def root():
    return {"status": "ok", "service": "The Forgetting Engine API"}
