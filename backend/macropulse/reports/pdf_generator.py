"""Deterministic PDF report generator for MacroPulse event study findings.

Strictly uses the six approved design tokens:
- palladian: #EEE9DF
- oatmeal: #C9C1B1
- blue-fantastic: #2C3B4D
- burning-flame: #FFB162
- truffle: #A35139
- abyssal: #1B2632
"""

import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Approved Design Palette Colors
C_PALLADIAN = colors.HexColor("#EEE9DF")
C_OATMEAL = colors.HexColor("#C9C1B1")
C_BLUE_FANTASTIC = colors.HexColor("#2C3B4D")
C_BURNING_FLAME = colors.HexColor("#FFB162")
C_TRUFFLE = colors.HexColor("#A35139")
C_ABYSSAL = colors.HexColor("#1B2632")


def generate_study_pdf(study_data: dict) -> bytes:
    """Generate professional quantitative event-study research PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=C_BLUE_FANTASTIC,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13,
        textColor=C_TRUFFLE,
    )

    h2_style = ParagraphStyle(
        "H2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=C_BLUE_FANTASTIC,
        spaceBefore=10,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=C_ABYSSAL,
    )

    mono_style = ParagraphStyle(
        "Mono",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=C_ABYSSAL,
    )

    verdict_style = ParagraphStyle(
        "Verdict",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=C_BLUE_FANTASTIC,
    )

    elements = []

    # Title & Metadata
    event_type = study_data.get("event_type", "CPI")
    asset_sym = study_data.get("asset_symbol", "SPY")
    unit = study_data.get("unit", "%")
    cfg = study_data.get("config", {})

    elements.append(Paragraph(f"MacroPulse Quantitative Research Report", title_style))
    elements.append(Paragraph(f"Macroeconomic Announcement Study: {event_type} Releases & {asset_sym} Response", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=C_BURNING_FLAME, spaceBefore=2, spaceAfter=12))

    # Section 1: Executive Summary & Verdict
    elements.append(Paragraph("1. Executive Summary & Verdict", h2_style))
    verdict_text = study_data.get("primary_verdict", "No verdict recorded.")
    elements.append(Paragraph(verdict_text, verdict_style))
    elements.append(Spacer(1, 8))

    # Section 2: Research Specification
    elements.append(Paragraph("2. Empirical Specification", h2_style))
    spec_data = [
        ["Event Type", event_type, "Model Type", str(cfg.get("model_type", "market_adjusted"))],
        ["Target Asset", asset_sym, "Benchmark", str(cfg.get("benchmark_symbol", "SPY"))],
        ["Event Window", f"[{cfg.get('event_window', [-1, 3])[0]}, {cfg.get('event_window', [-1, 3])[1]}]", "Estimation Window", f"[{cfg.get('estimation_window', [-260, -11])[0]}, {cfg.get('estimation_window', [-260, -11])[1]}]"],
        ["Return Method", str(cfg.get("return_method", "simple")), "Revision Guard", "First-Release Vintages (ALFRED)" if cfg.get("use_first_release") else "Revised Values"],
    ]

    t_spec = Table(spec_data, colWidths=[100, 160, 110, 160])
    t_spec.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), C_PALLADIAN),
        ("TEXTCOLOR", (0, 0), (-1, -1), C_ABYSSAL),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, C_OATMEAL),
    ]))
    elements.append(t_spec)
    elements.append(Spacer(1, 10))

    # Section 3: Statistical Windows Summary Table
    elements.append(Paragraph("3. Window Cumulative Abnormal Returns (CAR) & Statistical Inference", h2_style))
    stats_map = study_data.get("window_stats", {})

    table_rows = [
        ["Window", "Events", f"Mean CAR ({unit})", "Median", "t-stat", "p-value (t)", "BMP Stat", "Sign Test", "95% Bootstrap CI"]
    ]

    for w_key, s in stats_map.items():
        bmp_str = f"{s['bmp_stat']:.2f}" if s.get("bmp_stat") is not None else "N/A"
        sign_str = f"{s['sign_stat_positive']}+/{s['sign_stat_negative']}-"
        ci_str = f"[{s['bootstrap_ci_lower']:.2f}, {s['bootstrap_ci_upper']:.2f}]"
        table_rows.append([
            w_key,
            str(s["n_events"]),
            f"{s['mean_car']:+.3f}",
            f"{s['median_car']:+.3f}",
            f"{s['t_stat']:.2f}",
            f"{s['p_value_t']:.3f}",
            bmp_str,
            sign_str,
            ci_str,
        ])

    t_stats = Table(table_rows, colWidths=[55, 45, 75, 55, 45, 60, 55, 55, 90])
    t_stats.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), C_BLUE_FANTASTIC),
        ("TEXTCOLOR", (0, 0), (-1, 0), C_PALLADIAN),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, C_PALLADIAN]),
        ("TEXTCOLOR", (0, 1), (-1, -1), C_ABYSSAL),
        ("FONTNAME", (0, 1), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 1), (-1, -1), 7.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.5, C_OATMEAL),
    ]))
    elements.append(t_stats)
    elements.append(Spacer(1, 10))

    # Section 4: Methodological Caveats
    elements.append(Paragraph("4. Methodological Limitations & Integrity Caveats", h2_style))
    sample_stats = list(stats_map.values())[0] if stats_map else {}
    caveats = sample_stats.get("caveats", [])
    for c in caveats:
        elements.append(Paragraph(f"• {c}", body_style))
        elements.append(Spacer(1, 2))

    elements.append(Spacer(1, 8))

    # Section 5: Provenance & Audit Trail
    elements.append(Paragraph("5. Provenance & Reproducibility Audit", h2_style))
    prov_text = (
        f"Generated by: MacroPulse v{study_data.get('app_version', '1.0.0')} | "
        f"Input Fingerprint: {study_data.get('input_fingerprint', 'N/A')} | "
        f"Random Seed: {study_data.get('seed', 42)} | "
        f"Data Mode: {'DEMO' if study_data.get('is_demo') else 'LIVE'}"
    )
    elements.append(Paragraph(prov_text, mono_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
