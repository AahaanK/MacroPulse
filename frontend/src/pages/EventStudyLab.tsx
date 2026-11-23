import React, { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { z } from "zod";
import { ChevronDown, ChevronRight, Download, Play, SlidersHorizontal } from "lucide-react";

import { api } from "../api/client";
import { AARBarChart } from "../charts/AARBarChart";
import { CAARLineChart } from "../charts/CAARLineChart";
import { CARHistogram } from "../charts/CARHistogram";
import { EventStudyResult, WindowStats } from "../types";
import {
  Button,
  Checkbox,
  EmptyState,
  Field,
  Input,
  Notice,
  PageHeader,
  Panel,
  Segmented,
  Select,
  Signed,
  Skeleton,
  Stat,
  StatRow,
  Term,
} from "../components/ui";
import {
  EVENT_TYPES,
  downloadCsv,
  effectLabel,
  eventLabel,
  eventPlural,
  fmtDate,
  fmtPeriod,
  modelLabel,
  num,
  pval,
  signClass,
  signed,
  tauLabel,
  windowLabel,
  windowShort,
} from "../lib/format";

const studySchema = z
  .object({
    event_type: z.string().min(1, "Choose a release type"),
    asset_symbol: z.string().min(1, "Choose an asset"),
    benchmark_symbol: z.string().nullable(),
    start_date: z.string().optional().nullable(),
    end_date: z.string().optional().nullable(),
    tau_start: z.number({ invalid_type_error: "Enter a whole number" }).int().min(-30, "Start no earlier than −30").max(0, "Start must be 0 or earlier"),
    tau_end: z.number({ invalid_type_error: "Enter a whole number" }).int().min(0, "End must be 0 or later").max(30, "End no later than +30"),
    est_start: z.number({ invalid_type_error: "Enter a whole number" }).int().min(-500, "No earlier than −500").max(-30, "No later than −30"),
    est_end: z.number({ invalid_type_error: "Enter a whole number" }).int().min(-30, "No earlier than −30").max(-2, "No later than −2"),
    return_method: z.enum(["simple", "log"]),
    model_type: z.enum(["mean_adjusted", "market_adjusted", "market_model"]),
    use_first_release: z.boolean(),
    exclude_overlapping: z.boolean(),
    seed: z.number({ invalid_type_error: "Enter a whole number" }).int().default(42),
  })
  .refine((data) => data.tau_start <= data.tau_end, {
    message: "The window must start on or before the day it ends",
    path: ["tau_start"],
  })
  .refine((data) => data.est_start < data.est_end, {
    message: "The quiet period must start before it ends",
    path: ["est_start"],
  })
  .refine((data) => data.est_end < data.tau_start, {
    message: "The quiet period must end before the release window begins",
    path: ["est_end"],
  })
  .refine((data) => !data.start_date || !data.end_date || data.start_date <= data.end_date, {
    message: "The start date must be before the end date",
    path: ["start_date"],
  });

type StudyFormData = z.infer<typeof studySchema>;

// Defaults. The original default compared SPY with SPY under the market-adjusted model, which
// always produces exactly zero; comparing SPY with its own average day gives a meaningful first result.
const DEFAULTS: StudyFormData = {
  event_type: "CPI",
  asset_symbol: "SPY",
  benchmark_symbol: "SPY",
  start_date: "2020-01-01",
  end_date: "2024-12-31",
  tau_start: -1,
  tau_end: 3,
  est_start: -260,
  est_end: -11,
  return_method: "simple",
  model_type: "mean_adjusted",
  use_first_release: true,
  exclude_overlapping: false,
  seed: 42,
};

interface EventStudyLabProps {
  isDark: boolean;
}

function plainSummary(study: EventStudyResult, s: WindowStats, windowKey: string): string {
  const unit = study.unit;
  const amount = signed(Math.abs(s.mean_car), 2, unit).replace(/^[+−]/, "");
  const span = windowLabel(windowKey).toLowerCase();
  const isReturn = study.metric_type === "return";
  const verb = isReturn ? "did" : "moved";
  const how = isReturn ? (s.mean_car >= 0 ? "better" : "worse") : s.mean_car >= 0 ? "higher" : "lower";
  const significant = s.p_value_t < 0.05;
  const lead = `Across ${s.n_events} ${eventPlural(study.event_type)}, ${study.asset_symbol} ${verb} ${amount} ${how} than on a normal day, over the ${span}.`;
  const tail = significant
    ? " That is larger than everyday market noise would usually produce, so the reaction is statistically significant."
    : " That is within the range of everyday market noise, so there is no clear evidence of a consistent reaction.";
  return lead + tail;
}

export const EventStudyLab: React.FC<EventStudyLabProps> = ({ isDark }) => {
  const [activeWindowKey, setActiveWindowKey] = useState<string>("[+0,+1]");
  const [expandedEvent, setExpandedEvent] = useState<string | number | null>(null);
  const [showConfigDetails, setShowConfigDetails] = useState<boolean>(false);

  const { data: assets } = useQuery({ queryKey: ["assets"], queryFn: api.getAssets });

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<StudyFormData>({
    resolver: zodResolver(studySchema),
    defaultValues: DEFAULTS,
  });

  const selectedModel = watch("model_type");
  const useFirstRelease = watch("use_first_release");
  const assetSymbol = watch("asset_symbol");
  const benchmarkSymbol = watch("benchmark_symbol");
  const comparingWithItself = selectedModel !== "mean_adjusted" && assetSymbol === benchmarkSymbol;

  const studyMutation = useMutation({
    mutationFn: (data: StudyFormData) => {
      const payload = {
        event_type: data.event_type,
        asset_symbol: data.asset_symbol,
        benchmark_symbol: data.model_type === "mean_adjusted" ? null : data.benchmark_symbol,
        start_date: data.start_date || null,
        end_date: data.end_date || null,
        event_window: [data.tau_start, data.tau_end],
        estimation_window: [data.est_start, data.est_end],
        return_method: data.return_method,
        model_type: data.model_type,
        use_first_release: data.use_first_release,
        exclude_overlapping: data.exclude_overlapping,
        seed: data.seed,
      };
      return api.runEventStudy(payload);
    },
    onSuccess: (data) => {
      const defaultWin = data.window_stats["[+0,+1]"] ? "[+0,+1]" : data.primary_window;
      setActiveWindowKey(defaultWin);
      setExpandedEvent(null);
    },
  });

  // Run once on first load with the default settings.
  React.useEffect(() => {
    studyMutation.mutate(DEFAULTS);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onSubmit = (formData: StudyFormData) => studyMutation.mutate(formData);

  const study = studyMutation.data;
  const activeStats: WindowStats | undefined = study?.window_stats[activeWindowKey];
  const assetName = useMemo(() => assets?.find((a) => a.symbol === study?.asset_symbol)?.name, [assets, study]);

  const handleExportCSV = () => {
    if (!study) return;
    const headers = ["Event ID", "Event Type", "Period Date", "Release Date (Day 0)", `CAR ${activeWindowKey} (${study.unit})`, "Model Alpha", "Model Beta"];
    const rows = study.per_event.map((ev) => [
      ev.event_id,
      ev.event_type,
      ev.period_date,
      ev.day_0_date,
      ev.window_cars[activeWindowKey] ?? 0,
      ev.model_alpha,
      ev.model_beta,
    ]);
    downloadCsv(`event_study_${study.event_type}_${study.asset_symbol}.csv`, [headers, ...rows]);
  };

  const errorList = Object.entries(errors).map(([key, val]) => ({ key, msg: val?.message?.toString() }));

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader
        title="Event study"
        description="Measure how an asset moved in the days around each economic release, compared with a normal day, and whether the difference is more than chance."
      />

      {/* ---------------------------------------------------------------- Settings */}
      <Panel
        title="Study settings"
        actions={
          <Button
            variant="ghost"
            size="sm"
            icon={<SlidersHorizontal />}
            onClick={() => setShowConfigDetails(!showConfigDetails)}
            aria-expanded={showConfigDetails}
            aria-controls="advanced-settings"
          >
            {showConfigDetails ? "Hide advanced settings" : "Advanced settings"}
          </Button>
        }
      >
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-4 gap-y-4">
            <Field label="Release type" htmlFor="event_type">
              <Select id="event_type" {...register("event_type")}>
                {EVENT_TYPES.map((e) => (
                  <option key={e.value} value={e.value}>
                    {e.label}
                  </option>
                ))}
              </Select>
            </Field>

            <Field label="Asset" htmlFor="asset_symbol">
              <Select id="asset_symbol" {...register("asset_symbol")}>
                {assets ? (
                  assets.map((a) => (
                    <option key={a.symbol} value={a.symbol}>
                      {a.symbol} · {a.name}
                    </option>
                  ))
                ) : (
                  <option value="SPY">SPY · S&amp;P 500 ETF</option>
                )}
              </Select>
            </Field>

            <Field label="What counts as normal" term="model" htmlFor="model_type">
              <Select id="model_type" {...register("model_type")}>
                <option value="mean_adjusted">Its own average day</option>
                <option value="market_adjusted">The market's move that day</option>
                <option value="market_model">The market, adjusted for sensitivity</option>
              </Select>
            </Field>

            <Field
              label="Market benchmark"
              term="benchmark"
              htmlFor="benchmark_symbol"
              hint={selectedModel === "mean_adjusted" ? "Not used when comparing with its own average." : undefined}
            >
              <Select id="benchmark_symbol" {...register("benchmark_symbol")} disabled={selectedModel === "mean_adjusted"}>
                <option value="SPY">SPY · S&amp;P 500</option>
                <option value="QQQ">QQQ · Nasdaq-100</option>
                <option value="DIA">DIA · Dow Jones</option>
              </Select>
            </Field>

            <Field label="From" htmlFor="start_date" error={errors.start_date?.message}>
              <Input id="start_date" type="date" min="2020-01-01" max="2024-12-31" {...register("start_date")} />
            </Field>

            <Field label="To" htmlFor="end_date">
              <Input id="end_date" type="date" min="2020-01-01" max="2024-12-31" {...register("end_date")} />
            </Field>

            <Field label="Days to measure" term="event_window" hint="0 is the release day. −1 is the day before.">
              <div className="flex items-center gap-2">
                <Input aria-label="First day" type="number" min={-30} max={0} {...register("tau_start", { valueAsNumber: true })} />
                <span className="text-xs text-oatmeal-dark dark:text-oatmeal">to</span>
                <Input aria-label="Last day" type="number" min={0} max={30} {...register("tau_end", { valueAsNumber: true })} />
              </div>
            </Field>

            <div className="flex items-start pt-0 lg:pt-[22px]">
              <Button type="submit" variant="primary" className="w-full" icon={<Play />} loading={studyMutation.isPending}>
                {studyMutation.isPending ? "Running study…" : "Run study"}
              </Button>
            </div>
          </div>

          {showConfigDetails && (
            <div id="advanced-settings" className="mt-5 pt-5 border-t border-oatmeal/60 dark:border-blue-fantastic grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-4 gap-y-4">
              <Field label="Quiet period" term="estimation_window" hint="Trading days before the release used to learn a normal day.">
                <div className="flex items-center gap-2">
                  <Input aria-label="Quiet period start" type="number" {...register("est_start", { valueAsNumber: true })} />
                  <span className="text-xs text-oatmeal-dark dark:text-oatmeal">to</span>
                  <Input aria-label="Quiet period end" type="number" {...register("est_end", { valueAsNumber: true })} />
                </div>
              </Field>

              <Field label="Return calculation" term="return_method" htmlFor="return_method">
                <Select id="return_method" {...register("return_method")}>
                  <option value="simple">Simple percentage change</option>
                  <option value="log">Log return</option>
                </Select>
              </Field>

              <div className="space-y-3 sm:pt-[22px]">
                <Checkbox
                  {...register("use_first_release")}
                  label={<Term k="first_release">Use numbers as first published</Term>}
                  description={!useFirstRelease ? undefined : "Recommended."}
                />
                {!useFirstRelease && (
                  <p className="text-2xs text-truffle dark:text-truffle-soft pl-6">
                    Revised numbers weren't known on release day, which can make results look better than they were.
                  </p>
                )}
                <Checkbox {...register("exclude_overlapping")} label={<Term k="overlap">Skip releases with overlapping windows</Term>} />
              </div>

              <Field label="Random seed" term="seed" htmlFor="seed">
                <Input id="seed" type="number" {...register("seed", { valueAsNumber: true })} />
              </Field>

              <div className="sm:col-span-2 lg:col-span-4">
                <Button size="sm" variant="ghost" onClick={() => reset(DEFAULTS)}>
                  Reset all settings to defaults
                </Button>
              </div>
            </div>
          )}

          {errorList.length > 0 && (
            <div className="mt-4" role="alert">
              <Notice tone="warn" title="Check these settings">
                <ul className="list-disc pl-4 space-y-0.5">
                  {errorList.map((e) => (
                    <li key={e.key}>{e.msg}</li>
                  ))}
                </ul>
              </Notice>
            </div>
          )}

          {comparingWithItself && (
            <div className="mt-4">
              <Notice tone="warn">
                The asset and the benchmark are both {assetSymbol}. Comparing an asset with itself always gives a result of exactly zero. Choose a
                different benchmark or compare with its own average day.
              </Notice>
            </div>
          )}
        </form>
      </Panel>

      {studyMutation.isError && (
        <Notice tone="warn" title="The study couldn't run">
          {(studyMutation.error as Error)?.message}. Check the settings above, or that the MacroPulse server is running.
        </Notice>
      )}

      {/* ---------------------------------------------------------------- Results */}
      {!study && studyMutation.isPending && (
        <div className="space-y-5" aria-busy>
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-20 w-full" />
          <div className="grid gap-5 md:grid-cols-2">
            <Skeleton className="h-80" />
            <Skeleton className="h-80" />
          </div>
        </div>
      )}

      {study && (
        <div className={`space-y-5 transition-opacity duration-150 ${studyMutation.isPending ? "opacity-60" : ""}`}>
          {/* Summary */}
          <section className="panel p-5 border-l-[3px] border-l-burning-flame dark:border-l-burning-flame">
            <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
              <div className="space-y-2 max-w-3xl">
                <h2 className="text-xs text-oatmeal-dark dark:text-oatmeal">
                  {eventLabel(study.event_type)} and {study.asset_symbol}
                  {assetName ? ` (${assetName})` : ""} · {modelLabel(study.config.model_type).toLowerCase()}
                </h2>
                <p className="text-[17px] leading-relaxed font-medium text-abyssal dark:text-palladian">
                  {activeStats ? plainSummary(study, activeStats, activeWindowKey) : study.primary_verdict}
                </p>
                <p className="text-xs leading-relaxed text-oatmeal-dark dark:text-oatmeal/80">
                  <span className="font-medium">Technical summary:</span> {activeStats?.verdict || study.primary_verdict}
                </p>
              </div>
              <div className="flex shrink-0 flex-wrap items-center gap-2">
                <Button size="sm" icon={<Download />} onClick={handleExportCSV}>
                  Download CSV
                </Button>
              </div>
            </div>
            <div className="mt-3 text-2xs text-oatmeal-dark dark:text-oatmeal/70">
              <Term k="fingerprint">Data fingerprint</Term> <span className="code-id">{study.input_fingerprint}</span>
              {study.is_demo && <> · Sample data</>}
            </div>
          </section>

          {/* Window picker */}
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-sm font-semibold">
                <Term k="event_window">Measurement window</Term>
              </h2>
              <span className="text-xs text-oatmeal-dark dark:text-oatmeal">{windowLabel(activeWindowKey)}</span>
            </div>
            <div className="overflow-x-auto -mx-1 px-1 pb-1">
              <Segmented
                label="Measurement window"
                value={activeWindowKey}
                onChange={setActiveWindowKey}
                items={Object.keys(study.window_stats).map((wKey) => ({
                  value: wKey,
                  label: (
                    <span className="tabular">
                      {windowShort(wKey)}
                      <span className="ml-1.5 opacity-70">{signed(study.window_stats[wKey].mean_car, 2, study.unit)}</span>
                    </span>
                  ),
                }))}
              />
            </div>
          </div>

          {/* Key statistics */}
          {activeStats && (
            <StatRow>
              <Stat label="Releases studied" value={activeStats.n_events} sub={study.n_excluded ? `${study.n_excluded} left out` : "None left out"} />
              <Stat
                label="Average extra move"
                term="car"
                value={<Signed value={activeStats.mean_car} digits={2} unit={study.unit} />}
                sub={`Median ${signed(activeStats.median_car, 2, study.unit)}`}
              />
              <Stat
                label="t-statistic"
                term="t_stat"
                value={num(activeStats.t_stat, 2)}
                sub={
                  <span className={activeStats.p_value_t < 0.05 ? "font-medium text-abyssal dark:text-burning-flame" : ""}>
                    p = {pval(activeStats.p_value_t)}
                    {activeStats.p_value_t < 0.05 ? ", significant" : ""}
                  </span>
                }
              />
              <Stat
                label="Volatility-adjusted test"
                term="bmp"
                value={activeStats.bmp_stat !== null ? num(activeStats.bmp_stat, 2) : "—"}
                sub={activeStats.p_value_bmp !== null ? `p = ${pval(activeStats.p_value_bmp)}` : "Not available"}
              />
              <Stat
                label="95% range"
                term="bootstrap_ci"
                value={
                  <span className="text-base">
                    {signed(activeStats.bootstrap_ci_lower, 2)} to {signed(activeStats.bootstrap_ci_upper, 2, study.unit)}
                  </span>
                }
                sub={activeStats.bootstrap_ci_lower <= 0 && activeStats.bootstrap_ci_upper >= 0 ? "Includes zero" : "Excludes zero"}
              />
              <Stat label="Effect size" term="effect_size" value={num(activeStats.effect_size_d, 2)} sub={effectLabel(activeStats.effect_size_band)} />
            </StatRow>
          )}

          {/* Charts */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            <Panel
              title={<Term k="aar">Average extra move by day</Term>}
              sub="Bars show the average across releases. Whiskers show the 95% range."
              bodyClassName="px-2 pb-2 pt-3"
            >
              <AARBarChart aarSeries={study.aar_series} isDark={isDark} unit={study.unit} assetSymbol={study.asset_symbol} />
            </Panel>
            <Panel
              title={<Term k="caar">Running total of the average extra move</Term>}
              sub="The shaded band is the 95% range from resampling releases."
              bodyClassName="px-2 pb-2 pt-3"
            >
              <CAARLineChart aarSeries={study.aar_series} isDark={isDark} unit={study.unit} assetSymbol={study.asset_symbol} />
            </Panel>
          </div>

          <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
            <Panel
              className="xl:col-span-2"
              title="How individual releases spread out"
              sub={`Total extra move for each release, ${windowLabel(activeWindowKey).toLowerCase()}.`}
              bodyClassName="px-2 pb-2 pt-3"
            >
              {activeStats && (
                <CARHistogram
                  carValues={study.per_event.map((ev) => ev.window_cars[activeWindowKey] ?? 0)}
                  meanCar={activeStats.mean_car}
                  medianCar={activeStats.median_car}
                  isDark={isDark}
                  unit={study.unit}
                  windowLabel={activeWindowKey}
                />
              )}
            </Panel>

            <Panel title="Other checks" sub="Tests that don't assume moves follow a bell curve.">
              <dl className="divide-y divide-oatmeal/50 dark:divide-blue-fantastic text-[13px] -mt-1">
                <div className="flex items-baseline justify-between gap-4 py-2.5">
                  <dt>
                    <Term k="sign_test">Up vs. down releases</Term>
                  </dt>
                  <dd className="tabular font-medium text-right">
                    {activeStats?.sign_stat_positive} up, {activeStats?.sign_stat_negative} down
                    <div className="text-2xs font-normal text-oatmeal-dark dark:text-oatmeal">p = {pval(activeStats?.p_value_sign)}</div>
                  </dd>
                </div>
                <div className="flex items-baseline justify-between gap-4 py-2.5">
                  <dt>
                    <Term k="wilcoxon">Wilcoxon signed-rank</Term>
                  </dt>
                  <dd className="tabular font-medium text-right">
                    {activeStats?.p_value_wilcoxon !== null && activeStats?.p_value_wilcoxon !== undefined
                      ? `p = ${pval(activeStats.p_value_wilcoxon)}`
                      : "Not enough moves"}
                  </dd>
                </div>
              </dl>

              <h3 className="mt-5 text-[13px] font-semibold">Keep in mind</h3>
              <ul className="mt-2 space-y-2 text-xs leading-relaxed text-blue-fantastic/90 dark:text-oatmeal">
                {activeStats?.caveats.map((c, i) => (
                  <li key={i} className="pl-3 border-l-2 border-oatmeal dark:border-blue-fantastic-light">
                    {c}
                  </li>
                ))}
              </ul>

              {study.n_excluded > 0 && (
                <details className="mt-5 group">
                  <summary className="cursor-pointer list-none flex items-center gap-1.5 text-[13px] font-medium text-truffle dark:text-truffle-soft">
                    <ChevronRight className="w-3.5 h-3.5 transition-transform group-open:rotate-90" />
                    {study.n_excluded} release{study.n_excluded === 1 ? "" : "s"} left out
                  </summary>
                  <ul className="mt-2 max-h-40 overflow-y-auto space-y-1.5 text-xs text-blue-fantastic/90 dark:text-oatmeal">
                    {study.excluded_events.map((ex, idx) => (
                      <li key={idx}>
                        <span className="font-medium tabular">{fmtPeriod(ex.period_date)}</span>: {ex.reason.replace(/_/g, " ")}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </Panel>
          </div>

          {/* Per-release table */}
          <Panel
            title={`Each release (${study.per_event.length})`}
            sub="In order of publication. Select a row to see the day-by-day moves."
            bodyClassName="p-0"
          >
            {study.per_event.length === 0 ? (
              <EmptyState title="No releases matched these settings">Try a wider date range or a shorter quiet period.</EmptyState>
            ) : (
              <div className="max-h-[28rem] overflow-auto">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th className="w-8" aria-label="Expand" />
                      <th>Release for</th>
                      <th>First trading day</th>
                      <th className="num">
                        <Term k="abnormal_return">Release-day move</Term>
                      </th>
                      <th className="num">
                        <Term k="car">Total move</Term>, {windowShort(activeWindowKey).toLowerCase()}
                      </th>
                      <th className="num">
                        <Term k="alpha">Alpha</Term>
                      </th>
                      <th className="num">
                        <Term k="beta">Beta</Term>
                      </th>
                      <th>Notes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {study.per_event.map((ev) => {
                      const carVal = ev.window_cars[activeWindowKey] ?? 0;
                      const ar0 = ev.tau_ar[0] ?? 0;
                      const open = expandedEvent === ev.event_id;
                      const taus = Object.keys(ev.tau_ar)
                        .map(Number)
                        .sort((a, b) => a - b);
                      return (
                        <React.Fragment key={ev.event_id}>
                          <tr
                            className="row-hover cursor-pointer"
                            aria-selected={open}
                            aria-expanded={open}
                            tabIndex={0}
                            onClick={() => setExpandedEvent(open ? null : ev.event_id)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" || e.key === " ") {
                                e.preventDefault();
                                setExpandedEvent(open ? null : ev.event_id);
                              }
                            }}
                          >
                            <td className="text-oatmeal-dark dark:text-oatmeal">
                              {open ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                            </td>
                            <td className="font-medium">{fmtPeriod(ev.period_date)}</td>
                            <td className="text-blue-fantastic/90 dark:text-oatmeal">{fmtDate(ev.day_0_date)}</td>
                            <td className="num">
                              <Signed value={ar0} unit={study.unit} />
                            </td>
                            <td className="num font-medium">
                              <Signed value={carVal} unit={study.unit} />
                            </td>
                            <td className="num text-blue-fantastic/80 dark:text-oatmeal">{num(ev.model_alpha, 4)}</td>
                            <td className="num text-blue-fantastic/80 dark:text-oatmeal">{num(ev.model_beta, 2)}</td>
                            <td>
                              <div className="flex gap-1.5">
                                {ev.is_intraday_release && <span className="tag" title="Released during trading hours">During trading</span>}
                                {ev.is_overlapping && <span className="tag tag-warn" title="Window overlaps another release">Overlaps</span>}
                              </div>
                            </td>
                          </tr>
                          {open && (
                            <tr>
                              <td />
                              <td colSpan={7} className="!pt-1 !pb-4">
                                <div className="text-xs text-oatmeal-dark dark:text-oatmeal mb-2">
                                  Extra move on each day, and running total
                                </div>
                                <div className="flex flex-wrap gap-x-6 gap-y-2 tabular text-[13px]">
                                  {taus.map((t) => (
                                    <div key={t} className="min-w-[4.5rem]">
                                      <div className="text-2xs text-oatmeal-dark dark:text-oatmeal">
                                        {t === 0 ? "Release day" : `Day ${tauLabel(t)}`}
                                      </div>
                                      <div className={signClass(ev.tau_ar[t])}>{signed(ev.tau_ar[t], 2, study.unit)}</div>
                                      <div className="text-2xs text-oatmeal-dark dark:text-oatmeal">
                                        Total {signed(ev.tau_car[t], 2, study.unit)}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Panel>
        </div>
      )}
    </div>
  );
};
