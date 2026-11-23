import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import Plot from "react-plotly.js";
import { Layers, X } from "lucide-react";

import { api } from "../api/client";
import { getBasePlotlyLayout, getChartThemeColors, plotConfig } from "../charts/chartTheme";
import { Button, EmptyState, ErrorState, PageHeader, Panel, Select, Skeleton, cx } from "../components/ui";
import {
  assetName,
  eventShort,
  fmtChange,
  fmtPeriod,
  fmtReleaseET,
  fmtValue,
  indicatorName,
  indicatorUnit,
  signClass,
} from "../lib/format";
import { Indicator } from "../types";

interface MacroOverviewProps {
  isDark: boolean;
}

const Sparkline: React.FC<{ values: number[]; selected: boolean }> = ({ values, selected }) => {
  const w = 120;
  const h = 28;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pts = values.map((v, i) => `${((i / (values.length - 1)) * w).toFixed(1)},${(h - 2 - ((v - min) / range) * (h - 4)).toFixed(1)}`);
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-7" preserveAspectRatio="none" aria-hidden>
      <polyline
        points={pts.join(" ")}
        fill="none"
        strokeWidth={1.5}
        vectorEffect="non-scaling-stroke"
        strokeLinejoin="round"
        className={selected ? "stroke-burning-flame" : "stroke-blue-fantastic/70 dark:stroke-oatmeal/70"}
      />
    </svg>
  );
};

export const MacroOverview: React.FC<MacroOverviewProps> = ({ isDark }) => {
  const [selectedSeriesCode, setSelectedSeriesCode] = useState<string>("CPI");
  const [compareMode, setCompareMode] = useState<boolean>(false);
  const [compareCode, setCompareCode] = useState<string>("DGS10");

  const colors = getChartThemeColors(isDark);
  const layout = getBasePlotlyLayout(isDark);

  const { data: indicators, isLoading: loadingIndicators, isError: indicatorsError, error, refetch } = useQuery({
    queryKey: ["indicators"],
    queryFn: api.getIndicators,
  });

  const { data: assets } = useQuery({ queryKey: ["assets"], queryFn: api.getAssets });

  const { data: recentEvents, isLoading: loadingEvents } = useQuery({
    queryKey: ["recentEvents"],
    queryFn: () => api.getEvents({ page: 1, page_size: 8 }),
  });

  const { data: seriesData, isLoading: loadingSeries } = useQuery({
    queryKey: ["indicatorSeries", selectedSeriesCode],
    queryFn: () => api.getIndicatorSeries(selectedSeriesCode),
    enabled: !!selectedSeriesCode,
  });

  const effectiveCompare = compareMode && compareCode !== selectedSeriesCode ? compareCode : null;
  const { data: compareData } = useQuery({
    queryKey: ["indicatorSeries", effectiveCompare],
    queryFn: () => api.getIndicatorSeries(effectiveCompare as string),
    enabled: !!effectiveCompare,
  });

  const currentInd = indicators?.find((i) => i.code === selectedSeriesCode);
  const compareInd = indicators?.find((i) => i.code === effectiveCompare);

  const traces: any[] = [];
  if (seriesData?.data) {
    traces.push({
      type: "scatter",
      mode: "lines",
      x: seriesData.data.map((d) => d.date),
      y: seriesData.data.map((d) => d.value),
      line: { color: colors.primarySeries, width: 2 },
      name: indicatorName(selectedSeriesCode),
      hovertemplate: `%{x|%b %d, %Y}<br>${indicatorName(selectedSeriesCode)}: %{y:,.2f}<extra></extra>`,
    });
  }
  if (effectiveCompare && compareData?.data) {
    traces.push({
      type: "scatter",
      mode: "lines",
      x: compareData.data.map((d) => d.date),
      y: compareData.data.map((d) => d.value),
      yaxis: "y2",
      line: { color: isDark ? "#FFB162" : "#A35139", width: 1.75, dash: "dot" },
      name: indicatorName(effectiveCompare),
      hovertemplate: `%{x|%b %d, %Y}<br>${indicatorName(effectiveCompare)}: %{y:,.2f}<extra></extra>`,
    });
  }

  const renderTile = (ind: Indicator) => {
    const isSelected = ind.code === selectedSeriesCode;
    return (
      <button
        key={ind.code}
        type="button"
        onClick={() => setSelectedSeriesCode(ind.code)}
        aria-pressed={isSelected}
        className={cx(
          "relative text-left p-3.5 transition-colors focus-visible:z-10",
          isSelected
            ? "!bg-abyssal text-palladian dark:!bg-blue-fantastic"
            : "hover:!bg-palladian dark:hover:!bg-abyssal-light"
        )}
      >
        {isSelected && <span className="absolute inset-x-0 top-0 h-[2px] bg-burning-flame" aria-hidden />}
        <div className={cx("text-xs leading-snug min-h-[2rem]", isSelected ? "text-oatmeal" : "text-blue-fantastic/85 dark:text-oatmeal")}>
          {indicatorName(ind.code, ind.name)}
        </div>
        <div className="mt-1 flex items-baseline justify-between gap-2">
          <span className="text-lg font-semibold tabular tracking-[-0.01em]">{fmtValue(ind.latest_value)}</span>
          {ind.abs_change !== null && (
            <span className={cx("text-xs tabular", isSelected ? "text-burning-flame" : signClass(ind.abs_change))}>
              {fmtChange(ind.abs_change, Math.abs(ind.latest_value ?? 0) >= 1000 ? 0 : 2)}
            </span>
          )}
        </div>
        {ind.sparkline && ind.sparkline.length > 2 && (
          <div className="mt-2">
            <Sparkline values={ind.sparkline} selected={isSelected} />
          </div>
        )}
        <div className={cx("mt-1.5 text-2xs tabular", isSelected ? "text-oatmeal/80" : "text-oatmeal-dark dark:text-oatmeal/70")}>
          {ind.latest_period ? fmtPeriod(ind.latest_period) : "—"} · {ind.frequency.toLowerCase()}
        </div>
      </button>
    );
  };

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader
        title="Market overview"
        description="The latest reading of each economic indicator tracked by MacroPulse. Select one to see its full history."
      />

      {/* Indicator grid */}
      <section aria-label="Economic indicators">
        {loadingIndicators ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
            {[...Array(12)].map((_, i) => (
              <Skeleton key={i} className="h-36" />
            ))}
          </div>
        ) : indicatorsError ? (
          <div className="panel">
            <ErrorState error={error} onRetry={() => refetch()} what="indicators" />
          </div>
        ) : (
          <div className="grid gap-px overflow-hidden rounded-md border border-oatmeal/80 bg-oatmeal/60 dark:border-blue-fantastic dark:bg-blue-fantastic grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 [&>*]:bg-palladian-light dark:[&>*]:bg-abyssal-mid">
            {indicators?.map((ind) => renderTile(ind))}
            {/* Pad to a multiple of 12 so every breakpoint (2/3/4/6 columns) ends on a full row */}
            {indicators &&
              [...Array((12 - (indicators.length % 12)) % 12)].map((_, i) => <div key={`f${i}`} aria-hidden />)}
          </div>
        )}
      </section>

      {/* History chart */}
      <Panel
        title={currentInd ? indicatorName(currentInd.code, currentInd.name) : "Indicator history"}
        sub={
          currentInd && (
            <>
              {currentInd.name}. {indicatorUnit(currentInd.code, currentInd.units)}. FRED series <span className="code-id">{currentInd.fred_series_id}</span>.
            </>
          )
        }
        actions={
          <>
            {compareMode && (
              <Select aria-label="Indicator to compare" value={compareCode} onChange={(e) => setCompareCode(e.target.value)} className="!w-56">
                {indicators
                  ?.filter((i) => i.code !== selectedSeriesCode)
                  .map((i) => (
                    <option key={i.code} value={i.code}>
                      {indicatorName(i.code, i.name)}
                    </option>
                  ))}
              </Select>
            )}
            <Button
              size="md"
              icon={compareMode ? <X /> : <Layers />}
              onClick={() => {
                if (!compareMode && compareCode === selectedSeriesCode) {
                  const other = indicators?.find((i) => i.code !== selectedSeriesCode);
                  if (other) setCompareCode(other.code);
                }
                setCompareMode(!compareMode);
              }}
              aria-pressed={compareMode}
            >
              {compareMode ? "Stop comparing" : "Compare with another"}
            </Button>
          </>
        }
        bodyClassName="px-2 pb-2 pt-3"
      >
        <div className="w-full h-80">
          {traces.length ? (
            <Plot
              data={traces}
              layout={{
                ...layout,
                showlegend: !!effectiveCompare,
                xaxis: { ...layout.xaxis, type: "date" },
                yaxis: {
                  ...layout.yaxis,
                  title: { ...(layout.yaxis as any).title, text: currentInd ? indicatorUnit(currentInd.code, currentInd.units) : "Value" },
                },
                ...(effectiveCompare
                  ? {
                      yaxis2: {
                        ...(layout.yaxis as any),
                        overlaying: "y",
                        side: "right",
                        showgrid: false,
                        title: { ...(layout.yaxis as any).title, text: compareInd ? indicatorUnit(compareInd.code, compareInd.units) : "" },
                      },
                      margin: { ...layout.margin, r: 56 },
                    }
                  : {}),
                autosize: true,
              }}
              useResizeHandler
              style={{ width: "100%", height: "100%" }}
              config={plotConfig}
            />
          ) : loadingSeries ? (
            <Skeleton className="h-full w-full" />
          ) : (
            <EmptyState title="No history available for this indicator" />
          )}
        </div>
      </Panel>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Panel
          title="Latest releases"
          sub="Values as first published, with the change from the previous release."
          actions={
            <Link to="/events" className="text-link text-[13px]">
              Full calendar
            </Link>
          }
          bodyClassName="p-0"
        >
          <div className="max-h-80 overflow-y-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Release</th>
                  <th>Published (ET)</th>
                  <th className="num">Value</th>
                  <th className="num">Change</th>
                </tr>
              </thead>
              <tbody>
                {loadingEvents
                  ? [...Array(6)].map((_, i) => (
                      <tr key={i}>
                        <td colSpan={4}>
                          <Skeleton className="h-4 w-full" />
                        </td>
                      </tr>
                    ))
                  : recentEvents?.items.map((ev) => (
                      <tr key={ev.id}>
                        <td>
                          <span className="font-medium">{eventShort(ev.event_type)}</span>{" "}
                          <span className="text-oatmeal-dark dark:text-oatmeal">for {fmtPeriod(ev.period_date)}</span>
                        </td>
                        <td className="text-blue-fantastic/85 dark:text-oatmeal whitespace-nowrap">{fmtReleaseET(ev.release_ts)}</td>
                        <td className="num">{fmtValue(ev.actual_first_release)}</td>
                        <td className={cx("num", signClass(ev.change_value))}>{fmtChange(ev.change_value, Math.abs(ev.actual_first_release) >= 1000 ? 0 : 2)}</td>
                      </tr>
                    ))}
              </tbody>
            </table>
          </div>
        </Panel>

        <Panel title="Assets covered" sub="Markets measured in every study. Yields and the VIX are measured in point changes, not percentages." bodyClassName="p-0">
          <div className="max-h-80 overflow-y-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Asset</th>
                  <th>Type</th>
                  <th className="num">Measured in</th>
                </tr>
              </thead>
              <tbody>
                {assets?.map((a) => (
                  <tr key={a.symbol}>
                    <td>
                      <span className="font-medium">{a.symbol}</span>{" "}
                      <span className="text-oatmeal-dark dark:text-oatmeal">{assetName(a.symbol, a.name)}</span>
                    </td>
                    <td>{a.asset_class === "FX" ? "Currency" : a.asset_class}</td>
                    <td className="num text-blue-fantastic/85 dark:text-oatmeal">
                      {a.metric_type === "return" ? "% return" : a.unit === "bp" ? "Basis points" : "Index points"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      </div>
    </div>
  );
};
