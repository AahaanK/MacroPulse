import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse.analytics.returns import calculate_returns
from macropulse.db.session import get_db
from macropulse.models.asset import Asset, MarketPrice

router = APIRouter(prefix="/market-data", tags=["Market Data"])


@router.get("/{symbol}/prices")
def get_asset_prices(
    symbol: str,
    start: datetime.date | None = Query(None, description="Start date (YYYY-MM-DD)"),
    end: datetime.date | None = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Get historical daily prices for a symbol."""
    asset = db.execute(select(Asset).where(Asset.symbol == symbol.upper())).scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Asset '{symbol}' not found."}},
        )

    query = select(MarketPrice).where(MarketPrice.asset_id == asset.id)
    if start:
        query = query.where(MarketPrice.trade_date >= start)
    if end:
        query = query.where(MarketPrice.trade_date <= end)
    query = query.order_by(MarketPrice.trade_date)

    rows = db.execute(query).scalars().all()
    return {
        "symbol": asset.symbol,
        "name": asset.name,
        "metric_type": asset.metric_type,
        "unit": asset.unit,
        "prices": [
            {
                "date": r.trade_date.isoformat(),
                "close": r.close,
                "adj_close": r.adj_close,
                "volume": r.volume,
            }
            for r in rows
        ],
    }


@router.get("/{symbol}/returns")
def get_asset_returns(
    symbol: str,
    method: str = Query("simple", description="'simple' or 'log'"),
    start: datetime.date | None = Query(None),
    end: datetime.date | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get calculated historical returns or level differences for a symbol."""
    asset = db.execute(select(Asset).where(Asset.symbol == symbol.upper())).scalar_one_or_none()
    if not asset:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Asset '{symbol}' not found."}},
        )

    query = select(MarketPrice.trade_date, MarketPrice.adj_close).where(MarketPrice.asset_id == asset.id)
    if start:
        query = query.where(MarketPrice.trade_date >= start)
    if end:
        query = query.where(MarketPrice.trade_date <= end)
    query = query.order_by(MarketPrice.trade_date)

    rows = db.execute(query).all()
    if not rows:
        return {"symbol": asset.symbol, "returns": []}

    s_prices = pd.Series([r.adj_close for r in rows], index=[r.trade_date for r in rows])
    s_rets = calculate_returns(s_prices, metric_type=asset.metric_type, method=method, unit=asset.unit).dropna()

    return {
        "symbol": asset.symbol,
        "metric_type": asset.metric_type,
        "unit": asset.unit,
        "returns": [{"date": dt.isoformat(), "value": round(float(val), 4)} for dt, val in s_rets.items()],
    }
