/** Formatting helpers shared across the app. */

export const EVENT_TYPES: Array<{ value: string; label: string; short: string; plural: string; about: string }> = [
  {
    value: "CPI",
    label: "Inflation report (CPI)",
    short: "CPI",
    plural: "inflation reports",
    about: "Monthly change in consumer prices, published by the Bureau of Labor Statistics.",
  },
  {
    value: "CORE_CPI",
    label: "Core inflation (Core CPI)",
    short: "Core CPI",
    plural: "core inflation reports",
    about: "Consumer prices excluding food and energy, which swing a lot from month to month.",
  },
  {
    value: "NFP",
    label: "Jobs report (Nonfarm payrolls)",
    short: "Jobs report",
    plural: "jobs reports",
    about: "Number of jobs added or lost in the US economy last month.",
  },
  {
    value: "FOMC",
    label: "Fed rate decision (FOMC)",
    short: "Fed decision",
    plural: "Fed rate decisions",
    about: "Interest-rate decision from the Federal Reserve's policy committee.",
  },
];

export function eventLabel(code: string | undefined | null): string {
  if (!code) return "";
  return EVENT_TYPES.find((e) => e.value === code)?.label ?? code;
}

export function eventPlural(code: string | undefined | null): string {
  if (!code) return "releases";
  return EVENT_TYPES.find((e) => e.value === code)?.plural ?? `${code} releases`;
}

export function eventShort(code: string | undefined | null): string {
  if (!code) return "";
  return EVENT_TYPES.find((e) => e.value === code)?.short ?? code;
}

/** Format a number with an explicit sign so direction never relies on colour alone. */
export function signed(value: number | null | undefined, digits = 2, unit = ""): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const rounded = Number(value.toFixed(digits));
  const sign = rounded > 0 ? "+" : rounded < 0 ? "−" : "";
  return `${sign}${Math.abs(rounded).toFixed(digits)}${formatUnit(unit)}`;
}

export function num(value: number | null | undefined, digits = 2, unit = ""): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const s = value < 0 ? `−${Math.abs(value).toFixed(digits)}` : value.toFixed(digits);
  return `${s}${formatUnit(unit)}`;
}

export function formatUnit(unit: string): string {
  if (!unit) return "";
  if (unit === "%") return "%";
  return ` ${unit}`;
}

/** Tailwind classes for positive / negative values, with AA contrast in both themes. */
export function signClass(value: number | null | undefined): string {
  if (value === null || value === undefined || value === 0) return "text-abyssal dark:text-palladian";
  return value > 0
    ? "text-blue-fantastic dark:text-burning-flame"
    : "text-truffle dark:text-truffle-soft";
}

/** p-value in plain form: "0.032", or "< 0.001". */
export function pval(p: number | null | undefined): string {
  if (p === null || p === undefined || Number.isNaN(p)) return "—";
  if (p < 0.001) return "< 0.001";
  return p.toFixed(3);
}

/**
 * The API returns release timestamps in UTC without a zone marker ("2023-07-12T12:30:00").
 * `new Date()` would read those as local time, so mark them as UTC explicitly.
 */
export function parseUtc(ts: string): Date {
  const hasZone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(ts);
  return new Date(hasZone ? ts : `${ts}Z`);
}

export function fmtReleaseET(ts: string, style: "short" | "long" = "short"): string {
  const d = parseUtc(ts);
  if (style === "long") {
    return d.toLocaleString("en-US", {
      timeZone: "America/New_York",
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  }
  return d.toLocaleString("en-US", {
    timeZone: "America/New_York",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** "2024-06-01" → "Jun 2024" (the reference month of a release). */
export function fmtPeriod(period: string): string {
  const [y, m] = period.split("-").map(Number);
  if (!y || !m) return period;
  return new Date(Date.UTC(y, m - 1, 1)).toLocaleString("en-US", {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}

export function fmtDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = iso.length <= 10 ? new Date(`${iso}T00:00:00Z`) : parseUtc(iso);
  return d.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: iso.length <= 10 ? "UTC" : undefined,
  });
}

/** "[+0,+1]" → [0, 1] */
export function parseWindow(key: string): [number, number] | null {
  const m = key.match(/\[\s*([+-]?\d+)\s*,\s*([+-]?\d+)\s*\]/);
  if (!m) return null;
  return [Number(m[1]), Number(m[2])];
}

function dayWord(n: number): string {
  const a = Math.abs(n);
  return `${a} day${a === 1 ? "" : "s"}`;
}

/** Plain-English description of an event window. */
export function windowLabel(key: string): string {
  const w = parseWindow(key);
  if (!w) return key;
  const [a, b] = w;
  if (a === 0 && b === 0) return "Release day only";
  if (a === 0 && b === 1) return "Release day and the next day";
  if (a === 0) return `Release day and the next ${dayWord(b)}`;
  if (a < 0 && b === 0) return `${dayWord(a)} before through release day`;
  if (a === -1 && b === 1) return "Day before to day after";
  if (a < 0 && b > 0) return `${dayWord(a)} before to ${dayWord(b)} after`;
  return key;
}

/** Compact window label, e.g. "Day 0 to +1". */
export function windowShort(key: string): string {
  const w = parseWindow(key);
  if (!w) return key;
  const f = (n: number) => (n === 0 ? "0" : n > 0 ? `+${n}` : `−${Math.abs(n)}`);
  return w[0] === w[1] ? `Day ${f(w[0])}` : `Day ${f(w[0])} to ${f(w[1])}`;
}

export function tauLabel(tau: number): string {
  if (tau === 0) return "Release";
  return tau > 0 ? `+${tau}` : `−${Math.abs(tau)}`;
}

export const MODEL_LABELS: Record<string, string> = {
  mean_adjusted: "Compared with its own average",
  market_adjusted: "Compared with the market",
  market_model: "Compared with the market, adjusted for sensitivity",
};

export function modelLabel(m: string | undefined | null): string {
  if (!m) return "";
  return MODEL_LABELS[m] ?? m;
}

export function regimeLabel(raw: string): string {
  if (raw.startsWith("High Vol")) return "Nervous market";
  if (raw.startsWith("Low Vol")) return "Calm market";
  if (raw.toLowerCase().startsWith("transitional")) return "Mixed signals";
  return raw;
}

export function regimeDetail(raw: string): string {
  if (raw.startsWith("High Vol")) return "High volatility, risk-off";
  if (raw.startsWith("Low Vol")) return "Low volatility, risk-on";
  if (raw.toLowerCase().startsWith("transitional")) return "Transitional or unclassified";
  return raw;
}

export function effectLabel(band: string): string {
  const b = band.toLowerCase();
  if (b.includes("negligible")) return "Negligible";
  if (b.includes("small")) return "Small";
  if (b.includes("medium")) return "Medium";
  if (b.includes("large")) return "Large";
  return band;
}

export function downloadCsv(filename: string, rows: Array<Array<string | number>>): void {
  const escape = (v: string | number) => {
    const s = String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const blob = new Blob([rows.map((r) => r.map(escape).join(",")).join("\n")], {
    type: "text/csv;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Value of an economic indicator: thousands separators for large numbers (payrolls). */
export function fmtValue(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  if (Math.abs(v) >= 1000) return v.toLocaleString("en-US", { maximumFractionDigits: 0 });
  return v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

/** Signed change of an indicator, scaled like fmtValue. */
export function fmtChange(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  const a = Math.abs(v);
  const body = a >= 1000 ? fmtValue(a) : a.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
  return `${v > 0 ? "+" : v < 0 ? "−" : ""}${body}`;
}

/** Plain names for the indicator series. */
export const INDICATOR_NAMES: Record<string, { name: string; unit: string }> = {
  CPI: { name: "Consumer prices (CPI)", unit: "Index, 1982–84 = 100" },
  CORE_CPI: { name: "Core consumer prices", unit: "Index, 1982–84 = 100" },
  NFP: { name: "Jobs (nonfarm payrolls)", unit: "Thousands of jobs" },
  UNEMPLOYMENT: { name: "Unemployment rate", unit: "Percent" },
  GDP: { name: "Economic output (real GDP)", unit: "Billions of 2017 dollars" },
  PCE: { name: "PCE prices (Fed's preferred)", unit: "Index, 2017 = 100" },
  RETAIL_SALES: { name: "Retail sales", unit: "Millions of dollars" },
  FOMC: { name: "Fed funds rate (upper limit)", unit: "Percent" },
  DGS2: { name: "2-year Treasury yield", unit: "Percent" },
  DGS10: { name: "10-year Treasury yield", unit: "Percent" },
  VIXCLS: { name: "VIX (expected volatility)", unit: "Index" },
};

export function indicatorName(code: string, fallback?: string): string {
  return INDICATOR_NAMES[code]?.name ?? fallback ?? code;
}

export function indicatorUnit(code: string, fallback?: string): string {
  return INDICATOR_NAMES[code]?.unit ?? fallback ?? "";
}

/** Short plain-English names for the asset tickers. */
export const ASSET_NAMES: Record<string, string> = {
  SPY: "S&P 500",
  QQQ: "Nasdaq-100",
  DIA: "Dow Jones",
  SHY: "Short-term Treasuries",
  TLT: "Long-term Treasuries",
  UUP: "US dollar",
  GLD: "Gold",
  USO: "Oil",
  DGS2: "2-year yield",
  DGS10: "10-year yield",
  "^VIX": "VIX",
};

export function assetName(symbol: string, fallback?: string): string {
  return ASSET_NAMES[symbol] ?? fallback ?? symbol;
}

/** Change formatted to match the size of the series it belongs to (no decimals for payrolls). */
export function fmtChangeFor(change: number | null | undefined, reference: number | null | undefined): string {
  return fmtChange(change, Math.abs(reference ?? 0) >= 1000 ? 0 : 2);
}
