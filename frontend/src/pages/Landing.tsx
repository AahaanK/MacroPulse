import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";
import { HeroFigure } from "../components/HeroFigure";
import { Logo } from "../components/Logo";
import { buttonClass } from "../components/ui";
import { eventShort, fmtChangeFor, fmtPeriod, fmtReleaseET, fmtValue } from "../lib/format";

const QUESTIONS = [
  {
    q: "Does the stock market move after an inflation report?",
    a: "Line up every CPI release with the S&P 500's moves around it, then test whether the average reaction is bigger than a normal day.",
    to: "/lab",
    cta: "Run an event study",
  },
  {
    q: "Do bigger surprises cause bigger moves?",
    a: "Plot each release's change against the market's reaction and measure how sensitive prices are to the size of the news.",
    to: "/surprises",
    cta: "Compare surprises",
  },
  {
    q: "Which assets react to the same news, and how?",
    a: "See stocks, Treasury bonds, yields, the dollar, gold, oil and the VIX side by side for one type of release.",
    to: "/matrix",
    cta: "Open the cross-asset view",
  },
  {
    q: "Does it matter whether the market was already nervous?",
    a: "Split releases by the market's mood the day before, judged from volatility, trend and the VIX, and compare the reactions.",
    to: "/regimes",
    cta: "Check market conditions",
  },
];

const STEPS = [
  {
    title: "Choose a release and an asset",
    body: "For example, every US inflation report from 2020 to 2024 and the S&P 500 ETF.",
  },
  {
    title: "Learn what a normal day looks like",
    body: "MacroPulse studies a quiet stretch of about a year that ends well before each release.",
  },
  {
    title: "Measure the extra move",
    body: "On the days around the release, it subtracts the normal return from what actually happened.",
  },
  {
    title: "Test whether it's more than chance",
    body: "Several statistical tests and a resampled 95% range show whether the pattern holds up.",
  },
];

const PRINCIPLES = [
  {
    title: "Numbers as first published",
    body: "Economic data is often revised months later. Studies use the figure markets actually saw on the day, taken from the St. Louis Fed's ALFRED archive.",
  },
  {
    title: "Exact release times",
    body: "Each release is matched to the first trading session that could react to it, using the official NYSE calendar.",
  },
  {
    title: "No hindsight",
    body: "Market-condition labels only use information available the day before. Nothing from the future leaks into a result.",
  },
  {
    title: "Reproducible results",
    body: "Every study carries a fingerprint of its data and settings, so the same question always returns the same answer.",
  },
];

export const Landing: React.FC = () => {
  useEffect(() => {
    document.title = "MacroPulse — How markets react to economic news";
  }, []);

  const { data: status } = useQuery({ queryKey: ["dataStatus"], queryFn: api.getDataStatus, retry: 0 });
  const { data: recent, isError: recentError } = useQuery({
    queryKey: ["recentEvents"],
    queryFn: () => api.getEvents({ page: 1, page_size: 8 }),
    retry: 0,
  });

  const coverageStart = status?.series_coverage?.map((c) => c.start).filter(Boolean).sort()[0];
  const coverageEnd = status?.series_coverage?.map((c) => c.end).filter(Boolean).sort().slice(-1)[0];

  return (
    <div className="min-h-screen bg-palladian text-abyssal">
      {/* ------------------------------------------------ Header + hero (dark) */}
      <div className="bg-abyssal text-palladian">
        <header className="mx-auto max-w-page px-5 sm:px-8">
          <div className="flex h-16 items-center justify-between gap-6">
            <Link to="/" aria-label="MacroPulse home" className="rounded">
              <Logo tone="dark" size={28} />
            </Link>
            <nav className="hidden md:flex items-center gap-7 text-[13px] text-oatmeal" aria-label="Homepage">
              <a href="#questions" className="hover:text-palladian">What you can study</a>
              <a href="#how" className="hover:text-palladian">How it works</a>
              <a href="#data" className="hover:text-palladian">The data</a>
            </nav>
            <Link to="/lab" className={`${buttonClass("accent", "sm")} px-3.5`}>
              Explore dashboard
            </Link>
          </div>
        </header>

        <section className="mx-auto max-w-page px-5 sm:px-8 pt-12 pb-16 lg:pt-20 lg:pb-24 grid gap-12 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16 items-center">
          <div className="max-w-xl">
            <p className="text-sm text-burning-flame">Economic event research</p>
            <h1 className="mt-4 font-serif text-[2.5rem] leading-[1.1] sm:text-5xl sm:leading-[1.08] font-normal tracking-[-0.015em] text-palladian">
              See what every inflation report, jobs report and Fed decision did to markets.
            </h1>
            <p className="mt-6 text-[17px] leading-relaxed text-oatmeal max-w-[34rem]">
              MacroPulse lines up each economic release with the price moves around it, then tests whether
              the pattern is real or just the market&rsquo;s everyday noise.
            </p>
            <div className="mt-9 flex flex-wrap items-center gap-x-6 gap-y-4">
              <Link to="/lab" className={buttonClass("accent", "lg")}>
                Explore dashboard
              </Link>
              <Link to="/events" className="text-[15px] font-medium text-palladian underline decoration-oatmeal/40 underline-offset-4 hover:decoration-palladian">
                Browse the release calendar
              </Link>
            </div>
            {status && (
              <p className="mt-10 text-[13px] text-oatmeal/75 tabular">
                Built on {status.total_events.toLocaleString()} economic releases and{" "}
                {status.total_prices.toLocaleString()} daily prices across {status.total_assets} assets
                {coverageStart && coverageEnd ? `, from ${coverageStart.slice(0, 4)} to ${coverageEnd.slice(0, 4)}` : ""}.
              </p>
            )}
          </div>

          <div className="rounded-lg border border-blue-fantastic bg-abyssal-mid p-4 sm:p-6">
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
              <h2 className="text-[15px] font-medium text-palladian">S&amp;P 500 around US inflation reports</h2>
              <span className="text-xs text-oatmeal/70">Cumulative move beyond a normal day</span>
            </div>
            <HeroFigure />
          </div>
        </section>
      </div>

      {/* ------------------------------------------------------- Questions */}
      <section id="questions" className="scroll-mt-4 mx-auto max-w-page px-5 sm:px-8 py-20 lg:py-24">
        <div className="max-w-2xl">
          <h2 className="font-serif text-3xl sm:text-[2.125rem] leading-tight tracking-[-0.01em]">Questions you can answer</h2>
          <p className="mt-4 text-[17px] leading-relaxed text-blue-fantastic/85">
            Pick a question, choose your settings, and get a result in plain English with the statistics behind it.
          </p>
        </div>
        <div className="mt-12 grid gap-x-12 gap-y-10 md:grid-cols-2">
          {QUESTIONS.map((item) => (
            <article key={item.q} className="border-t border-oatmeal pt-6">
              <h3 className="text-lg font-semibold leading-snug tracking-[-0.005em]">{item.q}</h3>
              <p className="mt-2.5 text-[15px] leading-relaxed text-blue-fantastic/85 max-w-prose">{item.a}</p>
              <Link to={item.to} className="mt-4 inline-block text-link text-[14px]">
                {item.cta}
              </Link>
            </article>
          ))}
        </div>
      </section>

      {/* ---------------------------------------------------- How it works */}
      <section id="how" className="scroll-mt-4 bg-palladian-dark/70 border-y border-oatmeal/70">
        <div className="mx-auto max-w-page px-5 sm:px-8 py-20 lg:py-24">
          <div className="max-w-2xl">
            <h2 className="font-serif text-3xl sm:text-[2.125rem] leading-tight tracking-[-0.01em]">How a study works</h2>
            <p className="mt-4 text-[17px] leading-relaxed text-blue-fantastic/85">
              It&rsquo;s the event-study method used in academic finance, with every step visible and adjustable.
            </p>
          </div>

          {/* Timeline of one study */}
          <div className="mt-12 rounded-lg border border-oatmeal bg-palladian-light px-5 py-6 sm:px-8 sm:py-8" aria-label="Timeline of one release">
            <div className="relative h-14">
              <div className="absolute inset-x-0 top-6 h-px bg-oatmeal" aria-hidden />
              <div className="absolute left-0 top-3 h-6 rounded bg-blue-fantastic/10 border border-blue-fantastic/30" style={{ width: "68%" }} />
              <div className="absolute top-3 h-6 rounded bg-burning-flame/40 border border-burning-flame-dark/70" style={{ left: "80%", width: "17%" }} />
              <div className="absolute top-0 bottom-0 w-[2px] bg-truffle" style={{ left: "83.5%" }} aria-hidden />
            </div>
            <div className="relative mt-1 grid grid-cols-[68%_12%_20%] text-[13px] leading-snug">
              <div className="pr-4">
                <div className="font-medium">Quiet period</div>
                <div className="text-oatmeal-dark">About 250 trading days, used to learn a normal day</div>
              </div>
              <div className="pr-2 text-oatmeal-dark hidden sm:block">Gap</div>
              <div className="sm:pl-1">
                <div className="font-medium">Release window</div>
                <div className="text-oatmeal-dark">
                  Day before to 3 days after; <span className="text-truffle">release day</span> marked
                </div>
              </div>
            </div>
          </div>

          <ol className="mt-12 grid gap-x-10 gap-y-8 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((s, i) => (
              <li key={s.title}>
                <div className="flex items-baseline gap-3">
                  <span className="font-serif text-2xl text-truffle tabular" aria-hidden>
                    {i + 1}
                  </span>
                  <h3 className="text-[15px] font-semibold leading-snug">{s.title}</h3>
                </div>
                <p className="mt-2 pl-7 text-[14px] leading-relaxed text-blue-fantastic/85">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* ------------------------------------------------------- Data (dark) */}
      <section id="data" className="scroll-mt-4 bg-abyssal text-palladian">
        <div className="mx-auto max-w-page px-5 sm:px-8 py-20 lg:py-24 grid gap-14 lg:grid-cols-2">
          <div>
            <h2 className="font-serif text-3xl sm:text-[2.125rem] leading-tight tracking-[-0.01em]">Data you can check</h2>
            <p className="mt-4 text-[17px] leading-relaxed text-oatmeal max-w-xl">
              Results are only as good as their inputs. MacroPulse is strict about what goes in and shows you where it came from.
            </p>
            <dl className="mt-10 grid gap-x-10 gap-y-7 sm:grid-cols-2">
              {PRINCIPLES.map((p) => (
                <div key={p.title}>
                  <dt className="text-[15px] font-medium text-palladian">{p.title}</dt>
                  <dd className="mt-1.5 text-[14px] leading-relaxed text-oatmeal/85">{p.body}</dd>
                </div>
              ))}
            </dl>
            <p className="mt-10 text-[13px] text-oatmeal/70 max-w-xl">
              Sources: Federal Reserve Bank of St. Louis (FRED and ALFRED), Yahoo Finance daily prices, and the Federal Reserve&rsquo;s
              published FOMC calendar. Without a FRED API key, the app runs on bundled sample data and says so on every page.
            </p>
          </div>

          <div className="rounded-lg border border-blue-fantastic bg-abyssal-mid">
            <div className="flex items-baseline justify-between gap-4 border-b border-blue-fantastic px-5 py-4">
              <h3 className="text-[15px] font-medium">Latest releases in the database</h3>
              <Link to="/events" className="text-[13px] text-burning-flame hover:underline underline-offset-2">
                View all
              </Link>
            </div>
            {recent?.items?.length ? (
              <ul className="divide-y divide-blue-fantastic">
                {recent.items.slice(0, 7).map((ev) => (
                  <li key={ev.id} className="flex items-center justify-between gap-4 px-5 py-3 text-[14px]">
                    <div className="min-w-0">
                      <div className="font-medium">
                        {eventShort(ev.event_type)} <span className="font-normal text-oatmeal">for {fmtPeriod(ev.period_date)}</span>
                      </div>
                      <div className="text-xs text-oatmeal/70">Published {fmtReleaseET(ev.release_ts)} ET</div>
                    </div>
                    <div className="text-right tabular">
                      <div>{fmtValue(ev.actual_first_release)}</div>
                      <div className="text-xs text-oatmeal/70">
                        {ev.change_value !== null ? `${fmtChangeFor(ev.change_value, ev.actual_first_release)} vs prior` : "—"}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="px-5 py-10 text-[14px] text-oatmeal/80">
                {recentError
                  ? "The release list appears once the MacroPulse server is running on port 8001."
                  : "Loading releases…"}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------ Closing CTA */}
      <section className="mx-auto max-w-page px-5 sm:px-8 py-20 lg:py-24">
        <div className="flex flex-col items-start gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <h2 className="font-serif text-3xl sm:text-[2.125rem] leading-tight tracking-[-0.01em]">Start with the inflation report</h2>
            <p className="mt-4 text-[17px] leading-relaxed text-blue-fantastic/85">
              The dashboard opens with a ready-made study of CPI releases and the S&amp;P 500. Change any setting and run it again.
            </p>
          </div>
          <Link to="/lab" className={buttonClass("primary", "lg")}>
            Explore dashboard
          </Link>
        </div>
      </section>

      {/* ---------------------------------------------------------- Footer */}
      <footer className="bg-abyssal-dark text-oatmeal">
        <div className="mx-auto max-w-page px-5 sm:px-8 py-12 grid gap-10 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
          <div className="max-w-sm">
            <Logo tone="dark" size={26} />
            <p className="mt-4 text-[13px] leading-relaxed text-oatmeal/75">
              A research tool for studying how markets respond to economic news. Nothing here is investment advice.
            </p>
          </div>
          <FooterCol
            title="Analyse"
            links={[
              ["Event study", "/lab"],
              ["Surprises", "/surprises"],
              ["Cross-asset view", "/matrix"],
              ["Market conditions", "/regimes"],
            ]}
          />
          <FooterCol
            title="Browse"
            links={[
              ["Market overview", "/overview"],
              ["Release calendar", "/events"],
              ["Reports", "/reports"],
            ]}
          />
          <FooterCol
            title="About"
            links={[
              ["Data sources", "/integrity"],
              ["Workspace", "/workspace"],
            ]}
          />
        </div>
        <div className="border-t border-blue-fantastic/70">
          <div className="mx-auto max-w-page px-5 sm:px-8 py-5 text-xs text-oatmeal/60 flex flex-wrap justify-between gap-2">
            <span>MacroPulse 1.0.0</span>
            <span>Daily data. Reactions are measured from one market close to the next.</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

const FooterCol: React.FC<{ title: string; links: Array<[string, string]> }> = ({ title, links }) => (
  <div>
    <div className="text-[13px] font-medium text-palladian">{title}</div>
    <ul className="mt-3 space-y-2 text-[13px]">
      {links.map(([label, to]) => (
        <li key={to}>
          <Link to={to} className="text-oatmeal/80 hover:text-palladian">
            {label}
          </Link>
        </li>
      ))}
    </ul>
  </div>
);
