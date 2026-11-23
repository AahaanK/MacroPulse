import React, { useMemo, useState } from "react";

import { HERO_STUDY } from "../data/heroStudy";

const W = 640;
const H = 380;
const M = { top: 28, right: 92, bottom: 48, left: 44 };
const Y_MIN = -4;
const Y_MAX = 4;

/**
 * Editorial chart for the homepage: every CPI release's cumulative reaction (thin lines),
 * the average across releases (orange) and its 95% bootstrap range (band).
 */
export const HeroFigure: React.FC = () => {
  const { taus, caar, lower, upper, events, n } = HERO_STUDY;
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const x = (tau: number) => M.left + ((tau - taus[0]) / (taus[taus.length - 1] - taus[0])) * (W - M.left - M.right);
  const y = (v: number) => M.top + ((Y_MAX - v) / (Y_MAX - Y_MIN)) * (H - M.top - M.bottom);
  const line = (vals: number[]) => vals.map((v, i) => `${i === 0 ? "M" : "L"}${x(taus[i]).toFixed(1)},${y(v).toFixed(1)}`).join("");

  const band = useMemo(() => {
    const top = upper.map((v, i) => `${i === 0 ? "M" : "L"}${x(taus[i]).toFixed(1)},${y(v).toFixed(1)}`).join("");
    const bottom = lower
      .map((v, i) => [x(taus[i]).toFixed(1), y(v).toFixed(1)])
      .reverse()
      .map(([px, py]) => `L${px},${py}`)
      .join("");
    return `${top}${bottom}Z`;
  }, []);

  const eventPaths = useMemo(() => events.map((e) => line(e)), []);
  const last = taus.length - 1;
  const hv = hoverIdx !== null ? hoverIdx : null;

  return (
    <figure className="m-0">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="w-full h-auto select-none"
        role="img"
        aria-label={`Line chart. ${n} CPI releases from 2020 to 2024. Individual S&P 500 reactions range several percent in either direction, while the average stays within about a quarter of a percent of zero.`}
        onMouseLeave={() => setHoverIdx(null)}
      >
        <defs>
          <clipPath id="hero-plot">
            <rect x={M.left} y={M.top} width={W - M.left - M.right} height={H - M.top - M.bottom} />
          </clipPath>
        </defs>

        {/* Grid */}
        {[-4, -2, 0, 2, 4].map((v) => (
          <g key={v}>
            <line
              x1={M.left}
              x2={W - M.right}
              y1={y(v)}
              y2={y(v)}
              stroke="#C9C1B1"
              strokeOpacity={v === 0 ? 0.45 : 0.12}
              strokeWidth={1}
            />
            <text x={M.left - 10} y={y(v) + 4} textAnchor="end" fontSize={11} fill="#C9C1B1" fillOpacity={0.75} className="tabular">
              {v > 0 ? `+${v}%` : v < 0 ? `−${Math.abs(v)}%` : "0%"}
            </text>
          </g>
        ))}

        {/* Release-day marker */}
        <line x1={x(0)} x2={x(0)} y1={M.top - 10} y2={H - M.bottom} stroke="#FFB162" strokeOpacity={0.55} strokeWidth={1} strokeDasharray="3 4" />
        <text x={x(0) + 6} y={M.top - 2} fontSize={11} fill="#FFB162">
          Release day
        </text>

        <g clipPath="url(#hero-plot)">
          {/* One line per release */}
          {eventPaths.map((d, i) => (
            <path
              key={i}
              d={d}
              fill="none"
              stroke="#EEE9DF"
              strokeOpacity={hv === i ? 0.95 : 0.13}
              strokeWidth={hv === i ? 1.6 : 1}
              pointerEvents="none"
              style={{ transition: "stroke-opacity 120ms" }}
            />
          ))}
          {/* Wider invisible hit areas so a single release is easy to hover */}
          {eventPaths.map((d, i) => (
            <path key={`hit-${i}`} d={d} fill="none" stroke="transparent" strokeWidth={7} pointerEvents="stroke" onMouseEnter={() => setHoverIdx(i)} />
          ))}
          {/* Average and its 95% range */}
          <path d={band} fill="#FFB162" fillOpacity={0.16} pointerEvents="none" />
          <path d={line(caar)} fill="none" stroke="#FFB162" strokeWidth={2.75} strokeLinejoin="round" strokeLinecap="round" pathLength={1} className="draw-in" pointerEvents="none" />
        </g>

        {/* Direct labels at the right edge instead of a legend */}
        <text x={x(taus[last]) + 10} y={y(caar[last]) + 4} fontSize={12} fontWeight={500} fill="#FFB162">
          Average
        </text>
        <text x={x(taus[last]) + 10} y={y(caar[last]) + 19} fontSize={11} fill="#C9C1B1" fillOpacity={0.8}>
          of {n} releases
        </text>
        <text x={x(taus[last]) + 10} y={y(3.2)} fontSize={11} fill="#C9C1B1" fillOpacity={0.8}>
          Single
        </text>
        <text x={x(taus[last]) + 10} y={y(3.2) + 14} fontSize={11} fill="#C9C1B1" fillOpacity={0.8}>
          releases
        </text>

        {/* X axis */}
        {taus.map((t) => (
          <text key={t} x={x(t)} y={H - M.bottom + 18} textAnchor="middle" fontSize={11} fill="#C9C1B1" fillOpacity={t === 0 ? 1 : 0.75} className="tabular">
            {t === 0 ? "0" : t > 0 ? `+${t}` : `−${Math.abs(t)}`}
          </text>
        ))}
        <text x={(M.left + W - M.right) / 2} y={H - 8} textAnchor="middle" fontSize={11} fill="#C9C1B1" fillOpacity={0.75}>
          Trading days from the release
        </text>
      </svg>
      <figcaption className="mt-3 text-xs leading-relaxed text-oatmeal/80 max-w-xl">
        S&amp;P 500 ETF (SPY) around each US inflation report, 2020–2024, measured against a normal day. Each thin line is one
        release; the orange line is the average with its 95% range. Hover a line to pick out one release. Bundled sample data.
      </figcaption>
    </figure>
  );
};
