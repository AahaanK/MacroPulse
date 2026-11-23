"""Pure alignment module for mapping macroeconomic announcement timestamps to trading sessions.

Rules (Section 4):
1. Convert release_ts to America/New_York.
2. Check NYSE calendar using pandas_market_calendars, accounting for weekends, holidays, and early closes.
3. Day 0 rule:
   - Release before 09:30 ET on a trading day -> Day 0 is that session (close(t-1) -> close(t) contains release).
   - Release during session (e.g. FOMC 14:00) -> Day 0 is that session, flagged intraday_release_daily_measure.
   - Release after close (>= 16:00 ET or early close time) or on a non-trading day -> Day 0 is next trading session.
4. Event windows (tau in [-k, +m]) and estimation windows ([-260, -11]) use trading-day offsets.
5. Missing prices are never filled across holidays.
"""

from dataclasses import dataclass
import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import pandas_market_calendars as mcal


@dataclass(frozen=True)
class AlignedEventWindow:
    """Trading-day calendar alignment for a single macroeconomic event."""

    event_id: int | str
    event_type: str
    period_date: datetime.date
    release_ts: datetime.datetime
    day_0_date: datetime.date
    is_intraday_release: bool
    event_window_tau_dates: dict[int, datetime.date]  # tau -> trading date
    estimation_dates: list[datetime.date]
    is_overlapping: bool = False


@dataclass(frozen=True)
class ExcludedEvent:
    """Record of an event excluded from analysis with an explicit methodological reason."""

    event_id: int | str
    event_type: str
    period_date: datetime.date
    release_ts: datetime.datetime
    reason: str


class NYSECalendarAligner:
    """Aligns timestamps to NYSE trading sessions and builds trading-day windows."""

    def __init__(self, start_date: str = "2015-01-01", end_date: str = "2030-12-31"):
        self.nyse = mcal.get_calendar("NYSE")
        self.schedule = self.nyse.schedule(start_date=start_date, end_date=end_date)
        # Convert index to localized dates
        self.trading_days = [d.date() for d in self.schedule.index]
        self._date_to_index = {d: i for i, d in enumerate(self.trading_days)}
        self._ny_tz = ZoneInfo("America/New_York")

    def get_day_0(self, release_ts: datetime.datetime) -> tuple[datetime.date, bool]:
        """Determine trading session Day 0 for an announcement timestamp.

        Returns:
            (day_0_date, is_intraday_release)
        """
        # Ensure timestamp is tz-aware in America/New_York
        if release_ts.tzinfo is None:
            ts_ny = release_ts.replace(tzinfo=ZoneInfo("UTC")).astimezone(self._ny_tz)
        else:
            ts_ny = release_ts.astimezone(self._ny_tz)

        cal_date = ts_ny.date()
        release_time = ts_ny.time()

        # Check if cal_date is a trading day
        is_trading_day = cal_date in self._date_to_index

        if is_trading_day:
            day_schedule = self.schedule.loc[str(cal_date)]
            # Convert market open/close to America/New_York
            open_dt = day_schedule["market_open"].tz_convert(self._ny_tz)
            close_dt = day_schedule["market_close"].tz_convert(self._ny_tz)
            open_time = open_dt.time()
            close_time = close_dt.time()

            if release_time < open_time:
                # Pre-open release (e.g. CPI 08:30 ET) -> current trading day session
                return cal_date, False
            elif release_time < close_time:
                # During trading session (e.g. FOMC 14:00 ET) -> current trading day session, flagged intraday
                return cal_date, True
            else:
                # After market close -> next trading session
                idx = self._date_to_index[cal_date]
                if idx + 1 < len(self.trading_days):
                    return self.trading_days[idx + 1], False
                raise IndexError(f"No next trading day available after {cal_date}")
        else:
            # Weekend or market holiday (e.g. July 4, Good Friday) -> next trading session
            # Find first trading day strictly after cal_date
            for td in self.trading_days:
                if td > cal_date:
                    return td, False
            raise IndexError(f"No subsequent trading day found after holiday/weekend {cal_date}")

    def build_event_windows(
        self,
        events: list[dict],
        available_price_dates: set[datetime.date],
        event_window: tuple[int, int] = (-1, 3),
        estimation_window: tuple[int, int] = (-260, -11),
        min_estimation_obs: int = 120,
        exclude_overlapping: bool = False,
    ) -> tuple[list[AlignedEventWindow], list[ExcludedEvent]]:
        """Align all events, check data availability in trading days, and detect window overlaps.

        Args:
            events: List of event dicts containing at least 'id', 'event_type', 'period_date', 'release_ts'.
            available_price_dates: Set of dates where asset and benchmark prices actually exist.
            event_window: (tau_start, tau_end), e.g. (-1, 3).
            estimation_window: (est_start, est_end), e.g. (-260, -11).
            min_estimation_obs: Minimum required valid trading observations in estimation window.
            exclude_overlapping: If True, exclude events whose event windows overlap an adjacent event.

        Returns:
            (included_aligned_windows, excluded_events)
        """
        tau_start, tau_end = event_window
        est_start, est_end = estimation_window

        aligned_candidates: list[dict] = []
        excluded: list[ExcludedEvent] = []

        for ev in events:
            ev_id = ev["id"]
            ev_type = ev["event_type"]
            p_date = ev["period_date"]
            if isinstance(p_date, str):
                p_date = datetime.date.fromisoformat(p_date)
            rel_ts = ev["release_ts"]
            if isinstance(rel_ts, str):
                rel_ts = datetime.datetime.fromisoformat(rel_ts)

            try:
                day_0, is_intraday = self.get_day_0(rel_ts)
            except Exception as e:
                excluded.append(ExcludedEvent(ev_id, ev_type, p_date, rel_ts, f"calendar_error: {e}"))
                continue

            day_0_idx = self._date_to_index.get(day_0)
            if day_0_idx is None:
                excluded.append(ExcludedEvent(ev_id, ev_type, p_date, rel_ts, "day_0_not_in_trading_calendar"))
                continue

            # Event window trading dates
            ev_start_idx = day_0_idx + tau_start
            ev_end_idx = day_0_idx + tau_end

            if ev_start_idx < 0 or ev_end_idx >= len(self.trading_days):
                excluded.append(ExcludedEvent(ev_id, ev_type, p_date, rel_ts, "event_window_out_of_calendar_bounds"))
                continue

            # Verify every date in event window has actual price data
            event_window_dates: dict[int, datetime.date] = {}
            missing_event_date = False
            for tau in range(tau_start, tau_end + 1):
                idx = day_0_idx + tau
                t_date = self.trading_days[idx]
                if t_date not in available_price_dates:
                    missing_event_date = True
                    break
                event_window_dates[tau] = t_date

            if missing_event_date:
                excluded.append(ExcludedEvent(ev_id, ev_type, p_date, rel_ts, "missing_price_data_in_event_window"))
                continue

            # Estimation window trading dates
            e_start_idx = day_0_idx + est_start
            e_end_idx = day_0_idx + est_end

            if e_start_idx < 0 or e_end_idx >= len(self.trading_days):
                excluded.append(ExcludedEvent(ev_id, ev_type, p_date, rel_ts, "insufficient_calendar_history_for_estimation"))
                continue

            valid_est_dates: list[datetime.date] = []
            for idx in range(e_start_idx, e_end_idx + 1):
                t_date = self.trading_days[idx]
                if t_date in available_price_dates:
                    valid_est_dates.append(t_date)

            if len(valid_est_dates) < min_estimation_obs:
                excluded.append(
                    ExcludedEvent(
                        ev_id,
                        ev_type,
                        p_date,
                        rel_ts,
                        f"insufficient_estimation_data: {len(valid_est_dates)} < {min_estimation_obs}",
                    )
                )
                continue

            aligned_candidates.append({
                "event_id": ev_id,
                "event_type": ev_type,
                "period_date": p_date,
                "release_ts": rel_ts,
                "day_0_date": day_0,
                "day_0_idx": day_0_idx,
                "is_intraday_release": is_intraday,
                "event_window_tau_dates": event_window_dates,
                "estimation_dates": valid_est_dates,
                "ev_start_idx": ev_start_idx,
                "ev_end_idx": ev_end_idx,
            })

        # Overlap guard: Check overlap between consecutive events of the same event_type
        aligned_candidates.sort(key=lambda x: (x["event_type"], x["day_0_idx"]))
        included_windows: list[AlignedEventWindow] = []

        for i, cand in enumerate(aligned_candidates):
            is_overlap = False
            # Check previous candidate
            if i > 0 and aligned_candidates[i - 1]["event_type"] == cand["event_type"]:
                if aligned_candidates[i - 1]["ev_end_idx"] >= cand["ev_start_idx"]:
                    is_overlap = True
            # Check next candidate
            if i < len(aligned_candidates) - 1 and aligned_candidates[i + 1]["event_type"] == cand["event_type"]:
                if cand["ev_end_idx"] >= aligned_candidates[i + 1]["ev_start_idx"]:
                    is_overlap = True

            if is_overlap and exclude_overlapping:
                excluded.append(
                    ExcludedEvent(
                        cand["event_id"],
                        cand["event_type"],
                        cand["period_date"],
                        cand["release_ts"],
                        "overlapping_event_window_excluded",
                    )
                )
            else:
                included_windows.append(
                    AlignedEventWindow(
                        event_id=cand["event_id"],
                        event_type=cand["event_type"],
                        period_date=cand["period_date"],
                        release_ts=cand["release_ts"],
                        day_0_date=cand["day_0_date"],
                        is_intraday_release=cand["is_intraday_release"],
                        event_window_tau_dates=cand["event_window_tau_dates"],
                        estimation_dates=cand["estimation_dates"],
                        is_overlapping=is_overlap,
                    )
                )

        return included_windows, excluded
