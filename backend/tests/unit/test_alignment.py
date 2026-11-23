"""Unit tests for NYSE market calendar alignment rules."""

import datetime
from zoneinfo import ZoneInfo
import pytest

from macropulse.analytics.alignment import NYSECalendarAligner


@pytest.fixture
def aligner():
    return NYSECalendarAligner(start_date="2023-01-01", end_date="2024-12-31")


def test_pre_open_release(aligner):
    """08:30 ET release on a trading day (e.g. Wednesday 2023-05-10 CPI).

    Session contains close(t-1) -> close(t).
    Day 0 is that day (2023-05-10), not flagged intraday.
    """
    ts = datetime.datetime(2023, 5, 10, 8, 30, tzinfo=ZoneInfo("America/New_York"))
    day_0, is_intraday = aligner.get_day_0(ts)

    assert day_0 == datetime.date(2023, 5, 10)
    assert is_intraday is False


def test_session_release_fomc(aligner):
    """14:00 ET release on a trading day (e.g. Wednesday 2023-05-03 FOMC).

    Day 0 is that day (2023-05-03), flagged intraday_release_daily_measure = True.
    """
    ts = datetime.datetime(2023, 5, 3, 14, 0, tzinfo=ZoneInfo("America/New_York"))
    day_0, is_intraday = aligner.get_day_0(ts)

    assert day_0 == datetime.date(2023, 5, 3)
    assert is_intraday is True


def test_after_close_release(aligner):
    """After-close release (e.g. Thursday 2023-05-04 at 16:30 ET).

    Market closed at 16:00 ET. Next session is Friday 2023-05-05.
    """
    ts = datetime.datetime(2023, 5, 4, 16, 30, tzinfo=ZoneInfo("America/New_York"))
    day_0, is_intraday = aligner.get_day_0(ts)

    assert day_0 == datetime.date(2023, 5, 5)
    assert is_intraday is False


def test_friday_after_close_to_monday(aligner):
    """Friday after-close release (e.g. Friday 2023-05-05 at 17:00 ET).

    Next session must be Monday 2023-05-08.
    """
    ts = datetime.datetime(2023, 5, 5, 17, 0, tzinfo=ZoneInfo("America/New_York"))
    day_0, is_intraday = aligner.get_day_0(ts)

    assert day_0 == datetime.date(2023, 5, 8)
    assert is_intraday is False


def test_holiday_release_july_4(aligner):
    """Release on US Independence Day (Tuesday 2023-07-04).

    Market is closed. Next session must be Wednesday 2023-07-05.
    """
    ts = datetime.datetime(2023, 7, 4, 10, 0, tzinfo=ZoneInfo("America/New_York"))
    day_0, is_intraday = aligner.get_day_0(ts)

    assert day_0 == datetime.date(2023, 7, 5)
    assert is_intraday is False


def test_missing_price_dates_excluded(aligner):
    """If price data is missing on event window date, event must be excluded with reason."""
    events = [
        {
            "id": 1,
            "event_type": "CPI",
            "period_date": datetime.date(2023, 5, 1),
            "release_ts": datetime.datetime(2023, 5, 10, 8, 30, tzinfo=ZoneInfo("America/New_York")),
        }
    ]
    # Simulate available dates missing 2023-05-10
    all_trading_dates = set(aligner.trading_days)
    all_trading_dates.remove(datetime.date(2023, 5, 10))

    included, excluded = aligner.build_event_windows(
        events=events,
        available_price_dates=all_trading_dates,
        event_window=(-1, 1),
        min_estimation_obs=10,
    )

    assert len(included) == 0
    assert len(excluded) == 1
    assert "missing_price_data_in_event_window" in excluded[0].reason
