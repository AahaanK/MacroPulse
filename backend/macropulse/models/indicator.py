import datetime
from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from macropulse.db.base import Base


class Indicator(Base):
    """Macroeconomic indicator metadata (e.g. CPI, Nonfarm Payrolls)."""

    __tablename__ = "indicators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    fred_series_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    units: Mapped[str] = mapped_column(String(64), nullable=False)
    frequency: Mapped[str] = mapped_column(String(32), nullable=False)  # Monthly, Quarterly, Daily
    transform: Mapped[str | None] = mapped_column(String(32), nullable=True)  # lin, chg, ch1, pc1, pca, cch
    release_time_et: Mapped[str] = mapped_column(String(16), nullable=False, default="08:30")
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("data_sources.id"), nullable=False)

    source = relationship("DataSource", back_populates="indicators")
    observations = relationship("IndicatorObservation", back_populates="indicator", cascade="all, delete-orphan")
    vintages = relationship("IndicatorVintage", back_populates="indicator", cascade="all, delete-orphan")
    events = relationship("EconomicEvent", back_populates="indicator")


class IndicatorObservation(Base):
    """Time-series observation of an indicator."""

    __tablename__ = "indicator_observations"
    __table_args__ = (
        UniqueConstraint("indicator_id", "period_date", name="uq_indicator_period"),
        Index("idx_indicator_period", "indicator_id", "period_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[int] = mapped_column(Integer, ForeignKey("indicators.id"), nullable=False)
    period_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    indicator = relationship("Indicator", back_populates="observations")


class IndicatorVintage(Base):
    """ALFRED vintages tracking revisions across publication dates."""

    __tablename__ = "indicator_vintages"
    __table_args__ = (
        UniqueConstraint("indicator_id", "period_date", "realtime_start", name="uq_indicator_period_vintage"),
        Index("idx_indicator_vintage_lookup", "indicator_id", "period_date", "realtime_start"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    indicator_id: Mapped[int] = mapped_column(Integer, ForeignKey("indicators.id"), nullable=False)
    period_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    realtime_start: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    realtime_end: Mapped[datetime.date] = mapped_column(Date, nullable=False)

    indicator = relationship("Indicator", back_populates="vintages")
