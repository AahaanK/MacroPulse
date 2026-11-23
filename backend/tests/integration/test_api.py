"""Integration tests for FastAPI endpoints and event study execution."""

from fastapi.testclient import TestClient
import pytest

from macropulse.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True


def test_list_indicators():
    resp = client.get("/api/indicators")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 11
    cpi = next((i for i in data if i["code"] == "CPI"), None)
    assert cpi is not None
    assert cpi["fred_series_id"] == "CPIAUCSL"
    assert cpi["latest_value"] is not None


def test_list_assets():
    resp = client.get("/api/assets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 11
    symbols = [a["symbol"] for a in data]
    assert "SPY" in symbols
    assert "DGS2" in symbols
    assert "^VIX" in symbols


def test_list_events():
    resp = client.get("/api/events?event_type=CPI&page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert data["total"] > 0
    first = data["items"][0]
    assert first["event_type"] == "CPI"
    assert "release_ts" in first


def test_run_event_study_api():
    payload = {
        "event_type": "CPI",
        "asset_symbol": "SPY",
        "benchmark_symbol": "SPY",
        "event_window": [-1, 3],
        "estimation_window": [-260, -11],
        "return_method": "simple",
        "model_type": "market_adjusted",
        "use_first_release": True,
        "exclude_overlapping": False,
        "seed": 42,
    }
    resp = client.post("/api/event-studies/run", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["n_included"] > 0
    assert len(data["aar_series"]) == 5  # tau = -1, 0, 1, 2, 3
    assert len(data["per_event"]) == data["n_included"]
    assert "[+0,+1]" in data["window_stats"]
    w_stat = data["window_stats"]["[+0,+1]"]
    assert "t_stat" in w_stat
    assert "p_value_t" in w_stat
    assert "verdict" in w_stat
    assert data["study_id"] is not None

    # Test GET by study_id
    get_resp = client.get(f"/api/event-studies/{data['study_id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["study_id"] == data["study_id"]


def test_data_status_api():
    resp = client.get("/api/data-status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data_mode"] in ("LIVE", "DEMO")
    assert data["total_assets"] >= 11
    assert data["total_prices"] > 1000
