import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { Button, EmptyState, ErrorState, Field, PageHeader, Panel, Select, Signed, Skeleton, TableSkeleton, Term, Toolbar, cx } from "../components/ui";
import { EVENT_TYPES, eventPlural, fmtDate, regimeDetail, regimeLabel, signed } from "../lib/format";

interface RegimeAnalysisProps {
  isDark: boolean;
}

const REGIME_EVENTS = ["CPI", "FOMC", "NFP"];
const REGIME_ASSETS = [
  { value: "SPY", label: "SPY · S&P 500" },
  { value: "QQQ", label: "QQQ · Nasdaq-100" },
  { value: "TLT", label: "TLT · Long-term Treasuries" },
  { value: "^VIX", label: "^VIX · Volatility index" },
];

const REGIMES = [
  {
    key: "High Vol / Risk-Off",
    rule: "Recent volatility in the top 30% of its history, and either the VIX at 22 or above or the 50-day average below the 200-day average.",
  },
  {
    key: "Low Vol / Risk-On",
    rule: "Recent volatility in the bottom 40%, the VIX at 16 or below, and the 50-day average above the 200-day average.",
  },
  {
    key: "Transitional / unclassified",
    rule: "Signals disagree or sit between the thresholds, so no label is forced.",
  },
];

function ordinal(n: number): string {
  const v = n % 100;
  const suffix = v >= 11 && v <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[n % 10] ?? "th";
  return `${n}${suffix}`;
}

function regimeTag(label: string): string {
  if (label.includes("High Vol")) return "tag tag-warn";
  if (label.includes("Low Vol")) return "tag tag-strong";
  return "tag";
}

export const RegimeAnalysis: React.FC<RegimeAnalysisProps> = () => {
  const [eventType, setEventType] = useState<string>("CPI");
  const [assetSymbol, setAssetSymbol] = useState<string>("SPY");
  const [rows, setRows] = useState<number>(30);

  const { data: regimeHistory, isLoading: loadingHistory, isError: historyError, error, refetch } = useQuery({
    queryKey: ["regimeHistory"],
    queryFn: api.getRegimeHistory,
  });

  const { data: conditionedStudy, isLoading: loadingStudy, isFetching } = useQuery({
    queryKey: ["conditionedStudy", eventType, assetSymbol],
    queryFn: () => api.getConditionedStudy({ event_type: eventType, asset_symbol: assetSymbol }),
    placeholderData: (prev) => prev,
  });

  const dist: Record<string, number> = regimeHistory?.distribution || {};
  const totalDays = Object.values(dist).reduce((a, b) => a + b, 0);
  // Newest first.
  const history: any[] = [...(regimeHistory?.history ?? [])].sort((a, b) => (a.date < b.date ? 1 : -1));

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader
        title="Market conditions"
        description="Do markets react differently to news when they're already nervous? Each trading day is labelled calm, nervous or mixed, using only information from the day before."
      />

      {/* Distribution of regimes */}
      <Panel
        title={<Term k="regime">How each day is labelled</Term>}
        sub={
          <>
            Based on the previous day's <Term k="realized_vol">21-day volatility</Term>, the <Term k="sma">50- and 200-day averages</Term>, and the{" "}
            <Term k="vix">VIX</Term>. Nothing from the day itself is used, so there's no <Term k="look_ahead">hindsight</Term>.
          </>
        }
        bodyClassName="p-0"
      >
        {loadingHistory ? (
          <div className="p-4">
            <Skeleton className="h-28" />
          </div>
        ) : historyError ? (
          <ErrorState error={error} onRetry={() => refetch()} what="market conditions" />
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 md:divide-x divide-y md:divide-y-0 divide-oatmeal/60 dark:divide-blue-fantastic">
              {REGIMES.map((r) => {
                const count = dist[r.key] ?? 0;
                const share = totalDays ? (count / totalDays) * 100 : 0;
                return (
                  <div key={r.key} className="p-4">
                    <div className="flex items-baseline justify-between gap-2">
                      <h3 className="text-[13px] font-semibold">{regimeLabel(r.key)}</h3>
                      <span className="text-2xs text-oatmeal-dark dark:text-oatmeal">{regimeDetail(r.key)}</span>
                    </div>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-2xl font-semibold tabular">{count.toLocaleString()}</span>
                      <span className="text-xs text-oatmeal-dark dark:text-oatmeal tabular">days · {share.toFixed(0)}%</span>
                    </div>
                    <p className="mt-2 text-xs leading-relaxed text-blue-fantastic/85 dark:text-oatmeal">{r.rule}</p>
                  </div>
                );
              })}
            </div>
            {totalDays > 0 && (
              <div className="flex h-1.5 overflow-hidden rounded-b-md" aria-hidden>
                <div className="bg-truffle" style={{ width: `${((dist[REGIMES[0].key] ?? 0) / totalDays) * 100}%` }} />
                <div className="bg-blue-fantastic dark:bg-burning-flame" style={{ width: `${((dist[REGIMES[1].key] ?? 0) / totalDays) * 100}%` }} />
                <div className="bg-oatmeal dark:bg-blue-fantastic-light flex-1" />
              </div>
            )}
          </>
        )}
      </Panel>

      {/* Conditioned study */}
      <Toolbar>
        <Field label="Release type" htmlFor="r-type" className="w-full sm:w-60">
          <Select id="r-type" value={eventType} onChange={(e) => setEventType(e.target.value)}>
            {EVENT_TYPES.filter((e) => REGIME_EVENTS.includes(e.value)).map((e) => (
              <option key={e.value} value={e.value}>
                {e.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Asset" htmlFor="r-asset" className="w-full sm:w-64">
          <Select id="r-asset" value={assetSymbol} onChange={(e) => setAssetSymbol(e.target.value)}>
            {REGIME_ASSETS.map((a) => (
              <option key={a.value} value={a.value}>
                {a.label}
              </option>
            ))}
          </Select>
        </Field>
        <span className="sm:ml-auto pb-1.5 text-xs text-oatmeal-dark dark:text-oatmeal" role="status">
          {isFetching ? "Updating…" : "Release day and the next day"}
        </span>
      </Toolbar>

      <Panel
        title={`${eventPlural(eventType).replace(/^\w/, (c) => c.toUpperCase())} and ${assetSymbol}, by market mood`}
        sub="Average extra move, grouped by how the market looked the day before each release."
        bodyClassName="p-0"
      >
        {loadingStudy ? (
          <div className="p-4">
            <Skeleton className="h-32" />
          </div>
        ) : (
          <div className={cx("grid grid-cols-1 md:grid-cols-3 md:divide-x divide-y md:divide-y-0 divide-oatmeal/60 dark:divide-blue-fantastic transition-opacity", isFetching && "opacity-60")}>
            {conditionedStudy?.regime_comparison?.map((rc: any) => (
              <div key={rc.regime} className="p-4">
                <div className="flex items-baseline justify-between gap-2">
                  <h3 className="text-[13px] font-semibold">{regimeLabel(rc.regime)}</h3>
                  <span className="text-xs text-oatmeal-dark dark:text-oatmeal tabular">
                    {rc.count} release{rc.count === 1 ? "" : "s"}
                  </span>
                </div>
                {rc.count === 0 ? (
                  <p className="mt-3 text-[13px] text-oatmeal-dark dark:text-oatmeal">No releases happened in this kind of market.</p>
                ) : (
                  <>
                    <div className="mt-2 text-2xl font-semibold">
                      <Signed value={rc.mean_car} unit={conditionedStudy.unit} />
                    </div>
                    <dl className="mt-2 flex gap-5 text-xs text-oatmeal-dark dark:text-oatmeal tabular">
                      <div>
                        <dt className="inline">Median </dt>
                        <dd className="inline text-abyssal dark:text-palladian">{signed(rc.median_car, 2, conditionedStudy.unit)}</dd>
                      </div>
                      <div>
                        <dt className="inline">Typical spread </dt>
                        <dd className="inline text-abyssal dark:text-palladian">±{rc.std_car.toFixed(2)}</dd>
                      </div>
                    </dl>
                    {rc.count < 10 && <p className="mt-2 text-2xs text-truffle dark:text-truffle-soft">Few releases, so treat this average with caution.</p>}
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </Panel>

      {/* Daily log */}
      <Panel title="Daily labels" sub="The most recent trading days and the readings used to label them." bodyClassName="p-0">
        <div className="max-h-[26rem] overflow-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Label</th>
                <th className="num">
                  <Term k="realized_vol">21-day volatility</Term>, day before
                </th>
                <th className="num">
                  <Term k="vol_percentile">Volatility rank</Term>
                </th>
                <th className="num">
                  <Term k="vix">VIX</Term>, day before
                </th>
              </tr>
            </thead>
            <tbody>
              {loadingHistory ? (
                <TableSkeleton cols={5} rows={8} />
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <EmptyState title="No labelled days yet" />
                  </td>
                </tr>
              ) : (
                history.slice(0, rows).map((h: any) => (
                  <tr key={h.date} className="row-hover">
                    <td className="whitespace-nowrap">{fmtDate(h.date)}</td>
                    <td>
                      <span className={regimeTag(h.label)} title={h.label}>
                        {regimeLabel(h.label)}
                      </span>
                    </td>
                    <td className="num">{h.vol_21d.toFixed(1)}%</td>
                    <td className="num">{ordinal(Math.round(h.vol_percentile))} percentile</td>
                    <td className="num">{h.vix.toFixed(1)}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {history.length > rows && (
          <div className="flex items-center justify-between gap-3 px-4 py-3 border-t border-oatmeal/60 dark:border-blue-fantastic text-xs text-oatmeal-dark dark:text-oatmeal">
            <span className="tabular">
              Showing {rows} of {history.length.toLocaleString()} days
            </span>
            <Button size="sm" onClick={() => setRows((r) => r + 60)}>
              Show 60 more
            </Button>
          </div>
        )}
      </Panel>
    </div>
  );
};
