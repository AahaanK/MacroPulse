import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Download, FileSpreadsheet } from "lucide-react";

import { api } from "../api/client";
import { EmptyState, ErrorState, Field, PageHeader, Select, Signed, Skeleton, Term, Toolbar, buttonClass } from "../components/ui";
import { eventLabel, eventPlural, modelLabel, num, parseUtc, pval, signed, windowLabel, windowShort } from "../lib/format";

interface ReportsProps {
  isDark: boolean;
}

export const Reports: React.FC<ReportsProps> = () => {
  const [selectedStudyId, setSelectedStudyId] = useState<number | null>(null);

  const { data: savedStudies, isLoading: loadingStudies, isError: studiesError, error: studiesErr, refetch } = useQuery({
    queryKey: ["savedStudies"],
    queryFn: api.getSavedStudies,
  });

  const { data: reportData, isLoading: loadingReport, isError: reportError, error: reportErr } = useQuery({
    queryKey: ["reportDetail", selectedStudyId],
    queryFn: () => api.generateReport(selectedStudyId as number),
    enabled: selectedStudyId !== null,
  });

  // Auto-select the most recent study once the list loads.
  React.useEffect(() => {
    if (savedStudies && savedStudies.length > 0 && selectedStudyId === null) {
      setSelectedStudyId(savedStudies[0].id);
    }
  }, [savedStudies, selectedStudyId]);

  const studyOptionLabel = (s: any) => {
    const c = s.config ?? {};
    const when = parseUtc(s.created_at).toLocaleString("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
    const what = c.event_type && c.asset_symbol ? `${eventLabel(c.event_type)} · ${c.asset_symbol} · ${modelLabel(c.model_type).toLowerCase()}` : s.name;
    return `#${s.id} ${what} (${when})`;
  };

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader title="Reports" description="Every study you run is saved. Pick one to read it as a report, or download it as a PDF or a spreadsheet." />

      <Toolbar>
        <Field label="Study" htmlFor="rp-study" className="w-full md:flex-1 md:max-w-2xl">
          <Select
            id="rp-study"
            value={selectedStudyId ?? ""}
            onChange={(e) => setSelectedStudyId(Number(e.target.value))}
            disabled={!savedStudies?.length}
          >
            {!savedStudies?.length && <option value="">{loadingStudies ? "Loading studies…" : "No studies yet"}</option>}
            {savedStudies?.map((s: any) => (
              <option key={s.id} value={s.id}>
                {studyOptionLabel(s)}
              </option>
            ))}
          </Select>
        </Field>
        {selectedStudyId !== null && (
          <div className="flex flex-wrap items-center gap-2 md:ml-auto">
            <a href={`/api/reports/${selectedStudyId}.pdf`} target="_blank" rel="noreferrer" download className={buttonClass("primary")}>
              <Download />
              Download PDF
            </a>
            <a href={`/api/reports/${selectedStudyId}.csv`} download className={buttonClass("secondary")}>
              <FileSpreadsheet />
              Download CSV
            </a>
          </div>
        )}
      </Toolbar>

      {studiesError ? (
        <div className="panel">
          <ErrorState error={studiesErr} onRetry={() => refetch()} what="saved studies" />
        </div>
      ) : !loadingStudies && !savedStudies?.length ? (
        <div className="panel">
          <EmptyState
            title="No studies saved yet"
            action={
              <Link to="/lab" className={buttonClass("primary")}>
                Run a study
              </Link>
            }
          >
            Run an event study and it will appear here automatically.
          </EmptyState>
        </div>
      ) : reportError ? (
        <div className="panel">
          <ErrorState error={reportErr} what="this report" />
        </div>
      ) : loadingReport || loadingStudies || !reportData ? (
        <div className="panel p-8 space-y-4 max-w-4xl mx-auto">
          <Skeleton className="h-4 w-1/3" />
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-24 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <article className="panel max-w-4xl mx-auto px-6 py-8 sm:px-12 sm:py-12">
          <header className="pb-6 border-b border-oatmeal dark:border-blue-fantastic">
            <div className="flex flex-wrap justify-between gap-2 text-xs text-oatmeal-dark dark:text-oatmeal">
              <span>MacroPulse research report</span>
              <span>Study #{reportData.study_id ?? selectedStudyId}</span>
            </div>
            <h1 className="mt-4 font-serif text-[28px] sm:text-[32px] leading-tight tracking-[-0.01em] text-abyssal dark:text-palladian">
              How {reportData.asset_symbol} reacts to {eventPlural(reportData.event_type)}
            </h1>
            <p className="mt-3 text-[13px] text-oatmeal-dark dark:text-oatmeal">
              {reportData.n_included} releases studied
              {reportData.n_excluded ? `, ${reportData.n_excluded} left out` : ""} · {modelLabel(reportData.config.model_type)} ·{" "}
              {reportData.is_demo ? "Sample data" : "Live data"} · <Term k="fingerprint">Fingerprint</Term>{" "}
              <span className="code-id">{reportData.input_fingerprint}</span>
            </p>
          </header>

          <section className="pt-8">
            <h2 className="text-[15px] font-semibold">1. Summary</h2>
            <p className="mt-3 font-serif text-[17px] leading-[1.7] text-abyssal dark:text-palladian">{reportData.primary_verdict}</p>
          </section>

          <section className="pt-8">
            <h2 className="text-[15px] font-semibold">2. Method</h2>
            <dl className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4 text-[13px]">
              <div>
                <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">Asset</dt>
                <dd className="mt-0.5 font-medium">
                  {reportData.asset_symbol} <span className="font-normal text-oatmeal-dark dark:text-oatmeal">({reportData.unit})</span>
                </dd>
              </div>
              <div>
                <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">
                  <Term k="model">Normal day</Term>
                </dt>
                <dd className="mt-0.5 font-medium">
                  {modelLabel(reportData.config.model_type)}
                  {reportData.config.benchmark_symbol && reportData.config.model_type !== "mean_adjusted" ? ` (${reportData.config.benchmark_symbol})` : ""}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">
                  <Term k="event_window">Days measured</Term>
                </dt>
                <dd className="mt-0.5 font-medium tabular">
                  {signed(reportData.config.event_window[0], 0) || "0"} to {signed(reportData.config.event_window[1], 0) || "0"}
                </dd>
              </div>
              <div>
                <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">
                  <Term k="estimation_window">Quiet period</Term>
                </dt>
                <dd className="mt-0.5 font-medium tabular">
                  {num(reportData.config.estimation_window[0], 0)} to {num(reportData.config.estimation_window[1], 0)}
                </dd>
              </div>
            </dl>
          </section>

          <section className="pt-8">
            <h2 className="text-[15px] font-semibold">3. Results by window</h2>
            <p className="mt-1 text-xs text-oatmeal-dark dark:text-oatmeal">Total extra move over each window, averaged across releases.</p>
            <div className="mt-4 overflow-x-auto rounded border border-oatmeal/80 dark:border-blue-fantastic">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Window</th>
                    <th className="num">Releases</th>
                    <th className="num">Average</th>
                    <th className="num">Median</th>
                    <th className="num">
                      <Term k="t_stat">t</Term>
                    </th>
                    <th className="num">
                      <Term k="p_value">p</Term>
                    </th>
                    <th className="num">
                      <Term k="bmp">Adj. test</Term>
                    </th>
                    <th className="num">
                      <Term k="sign_test">Up / down</Term>
                    </th>
                    <th className="num">
                      <Term k="bootstrap_ci">95% range</Term>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(reportData.window_stats).map(([wKey, s]: [string, any]) => (
                    <tr key={wKey}>
                      <td className="whitespace-nowrap" title={windowLabel(wKey)}>
                        {windowShort(wKey)}
                      </td>
                      <td className="num">{s.n_events}</td>
                      <td className="num font-medium">
                        <Signed value={s.mean_car} digits={3} unit={reportData.unit} />
                      </td>
                      <td className="num">{signed(s.median_car, 3)}</td>
                      <td className="num">{num(s.t_stat, 2)}</td>
                      <td className="num">{pval(s.p_value_t)}</td>
                      <td className="num">{s.bmp_stat !== null ? num(s.bmp_stat, 2) : "—"}</td>
                      <td className="num">
                        {s.sign_stat_positive} / {s.sign_stat_negative}
                      </td>
                      <td className="num whitespace-nowrap">
                        {signed(s.bootstrap_ci_lower, 2)} to {signed(s.bootstrap_ci_upper, 2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="pt-8">
            <h2 className="text-[15px] font-semibold">4. Limitations</h2>
            <ul className="mt-3 space-y-2 text-[14px] leading-relaxed text-blue-fantastic/90 dark:text-oatmeal list-disc pl-5">
              {reportData.window_stats[reportData.primary_window]?.caveats.map((c: string, i: number) => (
                <li key={i}>{c}</li>
              ))}
            </ul>
          </section>

          <footer className="mt-10 pt-5 border-t border-oatmeal dark:border-blue-fantastic flex flex-wrap justify-between gap-2 text-xs text-oatmeal-dark dark:text-oatmeal">
            <span>
              <Term k="seed">Random seed</Term> {reportData.config.seed}
            </span>
            <span>MacroPulse {reportData.app_version}</span>
            <span>Same data and settings always reproduce this report.</span>
          </footer>
        </article>
      )}
    </div>
  );
};
