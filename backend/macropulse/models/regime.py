import datetime
from sqlalchemy import (
    Date,
    Float,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from macropulse.db.base import Base


class RegimeClassification(Base):
    """Historical market regime classification (e.g. High Vol, Risk-Off)."""

    __tablename__ = "regime_classifications"
    __table_args__ = (
        UniqueConstraint("method", "params_hash", "trade_date", name="uq_regime_method_params_date"),
        Index("idx_regime_method_date", "method", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    method: Mapped[str] = mapped_column(String(32), nullable=False)  # 'rules_based', 'kmeans'
    params_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    params_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    trade_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    label: Mapped[str] = mapped_column(String(32), nullable=False)  # 'High Vol', 'Low Vol', 'Transitional / unclassified'
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    feature_json: Mapped[dict] = mapped_column(JSON, nullable=False)
