from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from macropulse.db.base import Base


class DataSource(Base):
    """Catalog of market and macroeconomic data providers."""

    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)  # 'fred', 'yfinance', 'demo'
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    license_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    indicators = relationship("Indicator", back_populates="source")
    events = relationship("EconomicEvent", back_populates="source")
    prices = relationship("MarketPrice", back_populates="source")
    ingestion_logs = relationship("IngestionLog", back_populates="source")
