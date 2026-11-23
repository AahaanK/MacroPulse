"""Unit tests for deterministic PDF report generation."""

from macropulse.reports.pdf_generator import generate_study_pdf


def test_pdf_report_generation():
    mock_study = {
        "event_type": "CPI",
        "asset_symbol": "SPY",
        "unit": "%",
        "primary_verdict": "Across 50 CPI releases, SPY mean CAR was -0.15% (p = 0.32). Not statistically distinguishable from zero.",
        "input_fingerprint": "a1b2c3d4e5f6",
        "app_version": "1.0.0",
        "seed": 42,
        "is_demo": True,
        "config": {
            "model_type": "market_adjusted",
            "benchmark_symbol": "SPY",
            "event_window": [-1, 3],
            "estimation_window": [-260, -11],
            "return_method": "simple",
            "use_first_release": True,
        },
        "window_stats": {
            "[+0,+1]": {
                "window": [0, 1],
                "n_events": 50,
                "mean_car": -0.152,
                "median_car": -0.110,
                "t_stat": -1.02,
                "p_value_t": 0.312,
                "bmp_stat": -0.98,
                "sign_stat_positive": 23,
                "sign_stat_negative": 27,
                "bootstrap_ci_lower": -0.42,
                "bootstrap_ci_upper": 0.12,
                "caveats": ["Small sample size warning: n = 50."],
            }
        },
    }

    pdf_bytes = generate_study_pdf(mock_study)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")
