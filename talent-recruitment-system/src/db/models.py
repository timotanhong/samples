"""SQLAlchemy models for the talent recruitment system."""

import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

from src.config import settings


class Base(DeclarativeBase):
    pass


class JobPosting(Base):
    __tablename__ = "job_postings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255), unique=True, nullable=True)
    title = Column(String(500), nullable=False)
    department = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String(1000), nullable=True)
    status = Column(Enum("active", "closed", name="job_status"), default="active")
    content_hash = Column(String(64), nullable=True)

    # Extracted requirements (JSON-like text for SQLite compatibility)
    required_skills = Column(Text, nullable=True)
    preferred_skills = Column(Text, nullable=True)
    min_experience_years = Column(Integer, nullable=True)
    seniority_level = Column(String(100), nullable=True)
    domain_keywords = Column(Text, nullable=True)

    first_seen_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    matches = relationship("MatchResult", back_populates="job_posting", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<JobPosting(id={self.id}, title='{self.title}')>"


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    headline = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    profile_url = Column(String(1000), nullable=True)
    email = Column(String(255), nullable=True)

    # Aggregated skills and experience
    skills = Column(Text, nullable=True)  # JSON string
    experience_summary = Column(Text, nullable=True)
    education = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    sources = relationship("CandidateSource", back_populates="candidate", cascade="all, delete-orphan")
    matches = relationship("MatchResult", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CandidateProfile(id={self.id}, name='{self.name}')>"


class CandidateSource(Base):
    __tablename__ = "candidate_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    source_type = Column(
        Enum("github", "semantic_scholar", "stackoverflow", "kaggle", "patent", "manual", name="source_type"),
        nullable=False,
    )
    source_id = Column(String(255), nullable=True)
    source_url = Column(String(1000), nullable=True)
    raw_data = Column(Text, nullable=True)  # JSON string
    ingested_at = Column(DateTime, default=datetime.datetime.utcnow)

    candidate = relationship("CandidateProfile", back_populates="sources")

    __table_args__ = (
        UniqueConstraint("source_type", "source_id", name="uq_source_type_id"),
    )

    def __repr__(self):
        return f"<CandidateSource(id={self.id}, type='{self.source_type}')>"


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_posting_id = Column(Integer, ForeignKey("job_postings.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidate_profiles.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    skill_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    domain_score = Column(Float, nullable=True)
    rationale = Column(Text, nullable=True)
    confidence = Column(Enum("high", "medium", "low", name="confidence_level"), nullable=True)

    # Recruiter feedback
    feedback = Column(
        Enum("pending", "contacted", "interviewed", "hired", "rejected", name="feedback_status"),
        default="pending",
    )
    feedback_notes = Column(Text, nullable=True)

    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    job_posting = relationship("JobPosting", back_populates="matches")
    candidate = relationship("CandidateProfile", back_populates="matches")

    __table_args__ = (
        UniqueConstraint("job_posting_id", "candidate_id", name="uq_job_candidate"),
    )

    def __repr__(self):
        return f"<MatchResult(job={self.job_posting_id}, candidate={self.candidate_id}, score={self.overall_score})>"


# Database setup
engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(engine)


def get_session() -> Session:
    """Get a new database session."""
    return SessionLocal()
