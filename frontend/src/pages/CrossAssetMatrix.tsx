import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { ErrorState, Field, PageHeader, Panel, Segmented, Select, Signed, TableSkeleton, Term, cx } from "../components/ui";
import { assetName, eventLabel, eventPlural, num, pval } from "../lib/format";

interface CrossAssetMatrixProps {
  isDark: boolean;
}

const MATRIX_SYMBOLS = ["SPY", "QQQ", "DIA", "SHY", "TLT", "UUP", "GLD", "USO", "DGS2", "DGS10", "^VIX"];
const CORR_SYMBOLS = ["SPY", "QQQ", "TLT", "UUP", "GLD", "^VIX"];
// Cross-asset studies are available for these release types.
const MATRIX_EVENTS = ["CPI", "FOMC", "NFP"];

type CorrView = "normal" | "event" | "diff";

function unitWord(unit: string, metric: string): string {
  if (metric === "return") return "% return";
  if (unit === "bp") return "basis points";
  return "index points";
}

/** Cell colour for a correlation value, using palette tints only. */
function corrStyle(v: number, isDark: boolean, isDiagonal: boolean, scale = 1): React.CSSProperties {
  if (isDiagonal) return {};
  const a = Math.min(1, Math.abs(v) / scale) * (isDark ? 0.42 : 0.34);
  const rgb = v >= 0 ? (isDark ? "255, 177, 98" : "44, 59, 77") : "163, 81, 57";
  return { backgroundColor: `rgba(${rgb}, ${a.toFixed(3)})` };
}

export const CrossAssetMatrix: React.FC<CrossAssetMatrixProps> = ({ isDark }) => {
  const [eventType, setEventType] = useState<string>("CPI");
  const [corrView, setCorrView] = useState<CorrView>("event");

  const { data: matrixData, isLoading: loadingMatrix, isError, error, refetch } = useQuery({
    queryKey: ["crossAssetMatrix", eventType],
    queryFn: () => api.getCorrelationMatrix({ event_type: eventType, symbols: MATRIX_SYMBOLS }),
  });

  const { data: corrData, isLoading: loadingCorr } = useQuery({
    queryKey: ["correlationsEventVsNormal", eventType],
    queryFn: () => api.getEventVsNormalCorrelations({ event_type: eventType, symbols: CORR_SYMBOLS }),
  });

  const sentiment = matrixData?.sentiment_interpretation;

  const corrValue = (s1: string, s2: string): number => {
    const n = corrData?.normal_correlation?.[s1]?.[s2] ?? 0;
    const e = corrData?.event_correlation?.[s1]?.[s2] ?? 0;
    return corrView === "normal" ? n : corrView === "event" ? e : e - n;
  };

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader
        title="Cross-asset view"
        description="How stocks, bonds, interest rates, the dollar, gold, oil and volatility react to the same type of release, measured over the release day and the next day."
        actions={
          <Field label="Release type" htmlFor="m-type" className="w-64">
            <Select id="m-type" value={eventType} onChange={(e) => setEventType(e.target.value)}>
              {MATRIX_EVENTS.map((v) => (
                <option key={v} value={v}>
                  {eventLabel(v)}
                </option>
              ))}
            </Select>
          </Field>
        }
      />

      {sentiment && (
        <section className="panel p-5 border-l-[3px] border-l-burning-flame">
          <div className="flex flex-wrap items-baseline justify-between gap-3">
            <h2 className="text-xs text-oatmeal-dark dark:text-oatmeal">Overall reading</h2>
            <span className="tag tag-strong">{sentiment.regime}</span>
          </div>
          <p className="mt-2 text-[15px] leading-relaxed font-medium text-abyssal dark:text-palladian max-w-4xl">{sentiment.explanation}</p>
          <p className="mt-2 text-2xs text-oatmeal-dark dark:text-oatmeal/70">Rule applied: {sentiment.rule_name}</p>
        </section>
      )}

      <Panel
        title={`Average reaction to ${eventPlural(eventType)}`}
        sub="Total extra move over the release day and the next day. Each asset is measured in its own unit."
        bodyClassName="p-0"
      >
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Type</th>
                <th className="num">Releases</th>
                <th className="num">
                  <Term k="car">Average move</Term>
                </th>
                <th className="num">Median move</th>
                <th className="num">
                  <Term k="t_stat">t-statistic</Term>
                </th>
                <th className="num">
                  <Term k="p_value">p-value</Term>
                </th>
                <th>
                  <Term k="significant">Result</Term>
                </th>
              </tr>
            </thead>
            <tbody>
              {loadingMatrix ? (
                <TableSkeleton cols={8} rows={11} />
              ) : isError ? (
                <tr>
                  <td colSpan={8}>
                    <ErrorState error={error} onRetry={() => refetch()} what="cross-asset results" />
                  </td>
                </tr>
              ) : (
                matrixData?.assets?.map((a: any) => (
                  <tr key={a.symbol} className="row-hover">
                    <td className="whitespace-nowrap">
                      <span className="font-medium">{a.symbol}</span>{" "}
                      <span className="text-oatmeal-dark dark:text-oatmeal">{assetName(a.symbol, a.name)}</span>
                    </td>
                    <td className="text-blue-fantastic/85 dark:text-oatmeal whitespace-nowrap">
                      {a.asset_class === "FX" ? "Currency" : a.asset_class}
                      <span className="text-2xs text-oatmeal-dark dark:text-oatmeal/70"> · {unitWord(a.unit, a.metric_type)}</span>
                    </td>
                    <td className="num">{a.n_events}</td>
                    <td className="num font-medium">
                      <Signed value={a.mean_car} unit={a.unit} />
                    </td>
                    <td className="num">
                      <Signed value={a.median_car} unit={a.unit} className="!text-blue-fantastic/85 dark:!text-oatmeal" />
                    </td>
                    <td className="num">{num(a.t_stat, 2)}</td>
                    <td className="num">{pval(a.p_value)}</td>
                    <td>{a.is_significant ? <span className="tag tag-strong">Significant</span> : <span className="text-xs text-oatmeal-dark dark:text-oatmeal">Not significant</span>}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Panel>

      <Panel
        title={<Term k="correlation">Do assets move together?</Term>}
        sub={
          corrData
            ? `Correlation of daily moves on ${corrData.n_event_days} release days versus ${corrData.n_normal_days.toLocaleString()} ordinary trading days.`
            : "Correlation of daily moves on release days versus ordinary trading days."
        }
        actions={
          <Segmented<CorrView>
            label="Correlation view"
            value={corrView}
            onChange={setCorrView}
            items={[
              { value: "event", label: "Release days" },
              { value: "normal", label: "Ordinary days" },
              { value: "diff", label: "Difference" },
            ]}
          />
        }
      >
        {loadingCorr || !corrData ? (
          <div className="h-64 skeleton" />
        ) : (
          <div className="flex flex-col lg:flex-row gap-6">
            <div className="overflow-x-auto">
              <table className="text-[13px] tabular border-separate border-spacing-[3px]">
                <thead>
                  <tr>
                    <th />
                    {corrData.symbols.map((s: string) => (
                      <th key={s} className="px-2 pb-1 text-xs font-medium text-oatmeal-dark dark:text-oatmeal text-center">
                        {s}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {corrData.symbols.map((s1: string) => (
                    <tr key={s1}>
                      <th scope="row" className="pr-3 text-left text-xs font-medium text-oatmeal-dark dark:text-oatmeal whitespace-nowrap">
                        {s1} <span className="font-normal">{assetName(s1)}</span>
                      </th>
                      {corrData.symbols.map((s2: string) => {
                        const v = corrValue(s1, s2);
                        const diag = s1 === s2;
                        const strong = !diag && Math.abs(v) >= (corrView === "diff" ? 0.15 : 0.5);
                        return (
                          <td
                            key={s2}
                            title={diag ? undefined : `${s1} and ${s2}: ${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(2)}`}
                            style={corrStyle(v, isDark, diag, corrView === "diff" ? 0.4 : 1)}
                            className={cx(
                              "w-16 h-10 rounded-[3px] text-center",
                              diag ? "text-oatmeal-dark/60 dark:text-oatmeal/40" : strong ? "font-semibold" : ""
                            )}
                          >
                            {diag ? "—" : `${v >= 0 ? (corrView === "diff" ? "+" : "") : "−"}${Math.abs(v).toFixed(2)}`}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="text-[13px] leading-relaxed text-blue-fantastic/90 dark:text-oatmeal max-w-sm space-y-3">
              <p>
                {corrView === "diff"
                  ? "Release-day correlation minus ordinary-day correlation. Darker cells show pairs whose relationship changes most when news comes out."
                  : "+1 means two assets move in step, −1 means they move in opposite directions, and 0 means no relationship."}
              </p>
              <div className="flex items-center gap-3 text-xs">
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-[2px]" style={corrStyle(-0.8, isDark, false)} /> Opposite
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-[2px]" style={corrStyle(0.8, isDark, false)} /> Together
                </span>
              </div>
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
};
