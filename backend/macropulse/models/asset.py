import datetime
from sqlalchemy import (
    BigInteger,
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


class Asset(Base):
    """Market financial instrument or rate benchmark."""

    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False)  # Equity, Bond ETF, FX, Commodity, Rate, Volatility
    metric_type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'return' or 'level_change'
    unit: Mapped[str] = mapped_column(String(32), nullable=False)  # '%', 'bp', 'points'
    provider: Mapped[str] = mapped_column(String(32), nullable=False)  # 'yfinance', 'fred', 'demo'
    proxy_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    prices = relationship("MarketPrice", back_populates="asset", cascade="all, delete-orphan")


class MarketPrice(Base):
    """Daily market bar or rate observation."""

    __tablename__ = "market_prices"
    __table_args__ = (
        UniqueConstraint("asset_id", "trade_date", name="uq_asset_trade_date"),
        Index("idx_asset_trade_date", "asset_id", "trade_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.id"), nullable=False)
    trade_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    adj_close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    source_id: Mapped[int] = mapped_column(Integer, ForeignKey("data_sources.id"), nullable=False)

    asset = relationship("Asset", back_populates="prices")
    source = relationship("DataSource", back_populates="prices")
