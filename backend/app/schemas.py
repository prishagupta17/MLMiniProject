from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str


class CourseCreate(BaseModel):
    name: str


class CourseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class ModuleCreate(BaseModel):
    course_id: int
    name: str
    order_index: int = 0


class ModuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    name: str
    order_index: int


class TopicCreate(BaseModel):
    module_id: int
    name: str
    importance: float = 0.5
    reference_material: Optional[str] = None
    prerequisite_ids: List[int] = []


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    module_id: int
    name: str
    difficulty: float
    llm_difficulty: float
    crowd_difficulty: Optional[float] = None
    importance: float
    reference_material: Optional[str] = None
    confusable_note: Optional[str] = None
    confusable_topic_names: Optional[str] = None


class LearningEventCreate(BaseModel):
    user_id: int
    topic_id: int
    time_spent_seconds: int
    self_reported_confidence: Optional[float] = None


class RecallEventCreate(BaseModel):
    user_id: int
    topic_id: int
    is_correct: bool
    time_spent_seconds: int
    is_upcoming_assessment_prep: bool = False


class FactorExplanation(BaseModel):
    factor: str
    value: Any
    contribution: float
    direction: str
    explanation: str
    model_weight: Optional[float] = None


class LocalExplanation(BaseModel):
    explanation_space: str = "log_odds"
    intercept: float
    predicted_log_odds: float
    reconstructed_probability: float
    summary: Optional[str] = None
    positive_factors: List[FactorExplanation] = []
    negative_factors: List[FactorExplanation] = []
    top_factors: List[FactorExplanation] = []
    all_factors: List[FactorExplanation] = []


class TopicRisk(BaseModel):
    topic_id: int
    topic_name: str
    module_name: str
    forgetting_probability: float
    retention_status: str
    top_factors: List[Any] = []
    local_explanation: Optional[LocalExplanation] = None


class DashboardOut(BaseModel):
    user_id: int
    generated_at: datetime
    topics: List[TopicRisk]
    overall_retention_score: float
    high_risk_count: int
