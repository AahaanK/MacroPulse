import datetime
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from macropulse.db.base import Base


class StudyConfig(Base):
    """Event study specification and parameter configuration."""

    __tablename__ = "study_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    results = relationship("StudyResult", back_populates="config", cascade="all, delete-orphan")


class StudyResult(Base):
    """Computed outputs, statistics, and per-event AR/CAR series."""

    __tablename__ = "study_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_id: Mapped[int] = mapped_column(Integer, ForeignKey("study_configs.id"), nullable=False)
    summary_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    per_event_json: Mapped[list] = mapped_column(JSON, nullable=False)
    aar_json: Mapped[list] = mapped_column(JSON, nullable=False)
    stats_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    excluded_json: Mapped[list] = mapped_column(JSON, nullable=False)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    app_version: Mapped[str] = mapped_column(String(32), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    config = relationship("StudyConfig", back_populates="results")
    project_associations = relationship("ProjectStudy", back_populates="result")
    notes = relationship("ResearchNote", back_populates="result")
