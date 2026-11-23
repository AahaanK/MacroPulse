import datetime
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from macropulse.db.base import Base


class ResearchProject(Base):
    """Container for organizing related event studies and quant hypotheses."""

    __tablename__ = "research_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    studies = relationship("ProjectStudy", back_populates="project", cascade="all, delete-orphan")
    notes = relationship("ResearchNote", back_populates="project", cascade="all, delete-orphan")


class ProjectStudy(Base):
    """Many-to-many relationship between research projects and event study results."""

    __tablename__ = "project_studies"
    __table_args__ = (
        UniqueConstraint("project_id", "result_id", name="uq_project_result"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("research_projects.id"), nullable=False)
    result_id: Mapped[int] = mapped_column(Integer, ForeignKey("study_results.id"), nullable=False)

    project = relationship("ResearchProject", back_populates="studies")
    result = relationship("StudyResult", back_populates="project_associations")


class ResearchNote(Base):
    """Markdown research notes linked to a project and optionally to a specific study result."""

    __tablename__ = "research_notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("research_projects.id"), nullable=False)
    result_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("study_results.id"), nullable=True)
    body_md: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    project = relationship("ResearchProject", back_populates="notes")
    result = relationship("StudyResult", back_populates="notes")
