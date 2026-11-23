import React, { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Plot from "react-plotly.js";

import { api } from "../api/client";
import { getBasePlotlyLayout, getChartThemeColors, plotConfig } from "../charts/chartTheme";
import { ErrorState, Field, Notice, PageHeader, Panel, Select, Signed, Skeleton, Stat, StatRow, Term, Toolbar, cx } from "../components/ui";
import { EVENT_TYPES, assetName, eventPlural, fmtPeriod, num, pval, signed, windowLabel } from "../lib/format";

interface SurpriseAnalyzerProps {
  isDark: boolean;
}

const WINDOWS = ["[+0,+0]", "[+0,+1]", "[-1,+1]", "[+0,+3]"];

export const SurpriseAnalyzer: React.FC<SurpriseAnalyzerProps> = ({ isDark }) => {
  const [eventType, setEventType] = useState<string>("CPI");
  const [assetSymbol, setAssetSymbol] = useState<string>("SPY");
  const [windowKey, setWindowKey] = useState<string>("[+0,+1]");

  const colors = getChartThemeColors(isDark);
  const layout = getBasePlotlyLayout(isDark);

  const { data: assets } = useQuery({ queryKey: ["assets"], queryFn: api.getAssets });

  // Same endpoint and payload as before; a keyed query re-runs whenever a selection changes.
  const { data, isLoading, isFetching, isError, error, refetch } = useQuery({
    queryKey: ["surprises", eventType, assetSymbol, windowKey],
    queryFn: () => api.analyzeSurprises({ event_type: eventType, asset_symbol: assetSymbol, window_key: windowKey }),
    placeholderData: (prev) => prev,
  });

  const unit: string = data?.unit ?? "%";

  const scatterTraces = useMemo(() => {
    if (!data?.data_points?.length) return [];
    const pts = data.data_points;
    const xVals = pts.map((p: any) => p.surprise);
    const yVals = pts.map((p: any) => p.car);
    const minX = Math.min(...xVals);
    const maxX = Math.max(...xVals);
    const reg = data.regression;

    return [
      {
        type: "scatter",
        mode: "markers",
        x: xVals,
        y: yVals,
        text: pts.map((p: any) => fmtPeriod(p.period_date)),
        marker: {
          size: 8,
          color: yVals.map((v: number) => (v >= 0 ? colors.positiveSeries : colors.negativeSeries)),
          opacity: 0.8,
          line: { color: isDark ? "#212E3C" : "#F8F5F0", width: 1 },
        },
        name: "Releases",
        hovertemplate: `%{text}<br>Surprise: %{x:+.2f}<br>Extra move: %{y:+.2f}${unit}<extra></extra>`,
      },
      {
        type: "scatter",
        mode: "lines",
        x: [minX, maxX],
        y: [reg.intercept + reg.slope * minX, reg.intercept + reg.slope * maxX],
        line: { color: isDark ? "#EEE9DF" : "#FFB162", width: isDark ? 1.75 : 3 },
        name: "Best-fit line",
        hoverinfo: "skip",
      },
    ];
  }, [data, colors, isDark, unit]);

  const buckets: any[] = data?.quintile_buckets ?? [];
  const maxAbsBucket = Math.max(0.0001, ...buckets.map((b) => Math.abs(b.mean_car)));
  const isConsensus = data?.mode === "consensus_surprise";

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader
        title="Surprises"
        description="Does the size of the news matter? Each dot is one release: how much the number changed, against how the market moved."
      />

      <Toolbar>
        <Field label="Release type" htmlFor="s-type" className="w-full sm:w-60">
          <Select id="s-type" value={eventType} onChange={(e) => setEventType(e.target.value)}>
            {EVENT_TYPES.map((e) => (
              <option key={e.value} value={e.value}>
                {e.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Asset" htmlFor="s-asset" className="w-full sm:w-64">
          <Select id="s-asset" value={assetSymbol} onChange={(e) => setAssetSymbol(e.target.value)}>
            {(assets ?? [{ symbol: "SPY", name: "S&P 500" } as any]).map((a: any) => (
              <option key={a.symbol} value={a.symbol}>
                {a.symbol} · {assetName(a.symbol, a.name)}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Days measured" term="event_window" htmlFor="s-window" className="w-full sm:w-64">
          <Select id="s-window" value={windowKey} onChange={(e) => setWindowKey(e.target.value)}>
            {WINDOWS.map((w) => (
              <option key={w} value={w}>
                {windowLabel(w)}
              </option>
            ))}
          </Select>
        </Field>
        <span className="sm:ml-auto pb-1.5 text-xs text-oatmeal-dark dark:text-oatmeal" role="status">
          {isFetching ? "Updating…" : isConsensus ? "Measuring against forecasts" : "Measuring change from the previous release"}
        </span>
      </Toolbar>

      <Notice>
        {isConsensus ? (
          <>
            A <Term k="surprise">surprise</Term> here is the published number minus the economists' forecast, scaled by how much it usually varies.
          </>
        ) : (
          <>
            MacroPulse has no economists' forecasts, so a <Term k="surprise">surprise</Term> is measured as the change from the previous release
            (both as first published), scaled by how much it usually changes. Only past data is used for the scaling.
          </>
        )}
      </Notice>

      {isError && !data && (
        <div className="panel">
          <ErrorState error={error} onRetry={() => refetch()} what="the surprise analysis" />
        </div>
      )}

      {isLoading && (
        <div className="grid gap-5 lg:grid-cols-3">
          <Skeleton className="h-96 lg:col-span-2" />
          <Skeleton className="h-96" />
        </div>
      )}

      {data?.regression && (
        <div className={cx("space-y-5 transition-opacity", isFetching && "opacity-60")}>
          <StatRow cols="grid-cols-2 md:grid-cols-4">
            <Stat label="Sensitivity" term="slope" value={num(data.regression.slope, 3)} sub={`Standard error ${num(data.regression.se_slope, 3)}`} />
            <Stat
              label="p-value"
              term="p_value"
              value={pval(data.regression.p_value)}
              sub={data.regression.p_value < 0.05 ? "Significant" : "Not significant"}
              valueClassName={data.regression.p_value < 0.05 ? "text-blue-fantastic dark:text-burning-flame" : undefined}
            />
            <Stat label="Explained by the surprise" term="r_squared" value={`${(data.regression.r_squared * 100).toFixed(1)}%`} sub={`t = ${num(data.regression.t_stat, 2)}`} />
            <Stat
              label="95% range for sensitivity"
              term="ci"
              value={<span className="text-base">{`${num(data.regression.ci_lower, 3)} to ${num(data.regression.ci_upper, 3)}`}</span>}
              sub={data.regression.ci_lower <= 0 && data.regression.ci_upper >= 0 ? "Includes zero" : "Excludes zero"}
            />
          </StatRow>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <Panel
              className="lg:col-span-2"
              title={`${eventPlural(data.event_type).replace(/^\w/, (c: string) => c.toUpperCase())} vs. ${data.asset_symbol}`}
              sub={`${windowLabel(windowKey)}. Right means a bigger-than-usual increase in the number; up means the asset did better than normal.`}
              bodyClassName="px-2 pb-2 pt-3"
            >
              <div className="w-full h-96">
                <Plot
                  data={scatterTraces as any}
                  layout={{
                    ...layout,
                    xaxis: { ...layout.xaxis, showgrid: true, title: { ...(layout.xaxis as any).title, text: "Size of surprise (standard deviations)" } },
                    yaxis: {
                      ...layout.yaxis,
                      title: { ...(layout.yaxis as any).title, text: `Extra move (${data.unit})` },
                      ticksuffix: data.unit === "%" ? "%" : "",
                    },
                    autosize: true,
                  }}
                  useResizeHandler
                  style={{ width: "100%", height: "100%" }}
                  config={plotConfig}
                />
              </div>
            </Panel>

            <Panel title={<Term k="asymmetry">Rises vs. falls</Term>} sub="Do increases and decreases in the number move the market differently?">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-oatmeal-dark dark:text-oatmeal">When the number rose</div>
                  <div className="mt-1 text-xl font-semibold">
                    <Signed value={data.asymmetry.pos_mean_car} unit={data.unit} />
                  </div>
                  <div className="text-2xs text-oatmeal-dark dark:text-oatmeal">average, {data.asymmetry.pos_n} releases</div>
                </div>
                <div>
                  <div className="text-xs text-oatmeal-dark dark:text-oatmeal">When the number fell</div>
                  <div className="mt-1 text-xl font-semibold">
                    <Signed value={data.asymmetry.neg_mean_car} unit={data.unit} />
                  </div>
                  <div className="text-2xs text-oatmeal-dark dark:text-oatmeal">average, {data.asymmetry.neg_n} releases</div>
                </div>
              </div>
              <p className="mt-4 pt-4 border-t border-oatmeal/60 dark:border-blue-fantastic text-[13px] leading-relaxed text-blue-fantastic/90 dark:text-oatmeal">
                {data.asymmetry.verdict}
              </p>
            </Panel>
          </div>

          <Panel
            title={<Term k="quintile">From smallest to largest surprise</Term>}
            sub="Releases sorted by surprise and split into five equal groups, with the average extra move in each."
            bodyClassName="p-0"
          >
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Group</th>
                    <th>Surprise range</th>
                    <th className="num">Releases</th>
                    <th className="num">Average extra move</th>
                    <th className="w-[40%] hidden md:table-cell" aria-label="Bar" />
                  </tr>
                </thead>
                <tbody>
                  {buckets.map((b, idx) => {
                    const pct = (Math.abs(b.mean_car) / maxAbsBucket) * 50;
                    return (
                      <tr key={idx}>
                        <td className="font-medium whitespace-nowrap">
                          {idx === 0 ? "Smallest" : idx === buckets.length - 1 ? "Largest" : `Group ${idx + 1}`}
                        </td>
                        <td className="tabular text-blue-fantastic/85 dark:text-oatmeal whitespace-nowrap">
                          {signed(b.min_x, 2)} to {signed(b.max_x, 2)}
                        </td>
                        <td className="num">{b.count}</td>
                        <td className="num font-medium">
                          <Signed value={b.mean_car} unit={data.unit} />
                        </td>
                        <td className="hidden md:table-cell">
                          <div className="relative h-3">
                            <div className="absolute left-1/2 top-[-4px] bottom-[-4px] w-px bg-oatmeal dark:bg-blue-fantastic-light" aria-hidden />
                            <div
                              className={cx(
                                "absolute top-0 h-3 rounded-[2px]",
                                b.mean_car >= 0 ? "bg-blue-fantastic/80 dark:bg-burning-flame/80" : "bg-truffle/80 dark:bg-truffle-soft/80"
                              )}
                              style={b.mean_car >= 0 ? { left: "50%", width: `${pct}%` } : { right: "50%", width: `${pct}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      )}

      {data && !data.regression && !isLoading && (
        <div className="panel">
          <ErrorState error={new Error(data?.error?.message ?? "Not enough releases for this combination")} what="the surprise analysis" />
        </div>
      )}
    </div>
  );
};
