"""
Blends the LLM's initial difficulty estimate with real observed outcomes
from self-check RecallEvents, as more learners study a topic.

blended_difficulty = (1 - w) * llm_difficulty + w * observed_difficulty
where w grows from 0 -> up to 0.7 as more samples accumulate (crowd signal
gets more weight once there's enough data to trust it), and
observed_difficulty is derived from how often people forget it despite
"normal" study effort (more forgetting -> higher observed difficulty).

Call refresh_topic_difficulty(db, topic_id) periodically (e.g. after each
new self-check, or on a schedule) to keep it current.
"""
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Topic, RecallEvent

MIN_SAMPLES_FOR_TRUST = 5
MAX_CROWD_WEIGHT = 0.7


def refresh_topic_difficulty(db: Session, topic_id: int):
    topic = db.query(Topic).get(topic_id)
    if topic is None:
        return None

    checks = db.query(RecallEvent).filter(RecallEvent.topic_id == topic_id).all()
    n = len(checks)
    if n == 0:
        topic.difficulty = topic.llm_difficulty
        db.commit()
        return topic.difficulty

    forget_rate = sum(1 for c in checks if not c.is_correct) / n
    # forget_rate is already a reasonable proxy for "observed difficulty" in [0,1]
    observed_difficulty = forget_rate

    crowd_weight = min(MAX_CROWD_WEIGHT, n / (n + MIN_SAMPLES_FOR_TRUST) * MAX_CROWD_WEIGHT)
    blended = (1 - crowd_weight) * topic.llm_difficulty + crowd_weight * observed_difficulty

    topic.crowd_difficulty = round(observed_difficulty, 3)
    topic.difficulty = round(blended, 3)
    topic.num_crowd_samples = n
    topic.difficulty_last_updated = datetime.utcnow()
    db.commit()
    return topic.difficulty
