import datetime
from sqlalchemy import (
    DateTime,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from macropulse.db.base import Base


class EconomicEvent(Base):
    """Derived or verified macroeconomic announcement events."""

    __tablename__ = "economic_events"
    __table_args__ = (
        UniqueConstraint("event_type", "period_date", name="uq_event_period"),
        Index("idx_event_type_release_ts", "event_type", "release_ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    indicator_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("indicators.id"), nullable=True)
    country: Mapped[str] = mapped_column(String(8), nullable=False, default="US")
    period_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    release_ts: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timestamp_source: Mapped[str] = mapped_column(String(64), nullable=False)
    actual_first_release: Mapped[float] = mapped_column(Float, nullable=False)
    previous_first_release: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_latest: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_std: Mapped[float | None] = mapped_column(Float, nullable=True)
    data_quality: Mapped[str] = mapped_column(String(32), nullable=False)  # VERIFIED_TIMESTAMP, DERIVED_TIMESTAMP, DATE_ONLY, DEMO
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("data_sources.id"), nullable=False)

    source = relationship("DataSource", back_populates="events")
    indicator = relationship("Indicator", back_populates="events")
    consensus = relationship("ConsensusForecast", back_populates="event", uselist=False, cascade="all, delete-orphan")


class ConsensusForecast(Base):
    """Optional analyst consensus forecast for an economic event (empty by default)."""

    __tablename__ = "consensus_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("economic_events.id"), unique=True, nullable=False)
    consensus_value: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    license_note: Mapped[str] = mapped_column(Text, nullable=False)
    imported_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=datetime.datetime.now(datetime.timezone.utc), nullable=False)

    event = relationship("EconomicEvent", back_populates="consensus")
