from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from .database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(String, unique=True, index=True)
    sender = Column(String)
    title = Column(String)
    body = Column(String)
    cleaned_body = Column(String)
    received_at = Column(DateTime)
    language = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    classification = relationship("Classification", back_populates="email", uselist=False)

class Classification(Base):
    __tablename__ = "classifications"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    category = Column(String)
    priority = Column(String)
    confidence = Column(Float)
    summary = Column(String)
    suggested_action = Column(String)
    estimated_response_time_hours = Column(Integer)
    tags = Column(JSON)
    routed_to = Column(String)
    sla_deadline = Column(DateTime)
    status = Column(String, default="classified")
    auto_responded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    model_version = Column(String, default="gpt-4o-mini-v1")
    needs_human_review = Column(Boolean, default=False)

    email = relationship("Email", back_populates="classification")
    feedbacks = relationship("Feedback", back_populates="classification")

class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    classification_id = Column(Integer, ForeignKey("classifications.id"))
    corrected_category = Column(String, nullable=True)
    corrected_priority = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    agent_id = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    classification = relationship("Classification", back_populates="feedbacks")
