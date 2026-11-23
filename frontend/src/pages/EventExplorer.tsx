import React, { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight, X } from "lucide-react";

import { api } from "../api/client";
import { EconomicEvent } from "../types";
import { Button, EmptyState, ErrorState, Field, Input, PageHeader, Panel, Select, TableSkeleton, Term, Toolbar, cx } from "../components/ui";
import { EVENT_TYPES, eventLabel, eventShort, fmtChangeFor, fmtPeriod, fmtReleaseET, fmtValue, parseUtc, signClass } from "../lib/format";

interface EventExplorerProps {
  isDark: boolean;
}

const PAGE_SIZE = 25;

function qualityLabel(q: string): string {
  if (q === "VERIFIED_TIMESTAMP") return "Verified time";
  if (q === "DEMO") return "Sample data";
  return q.replace(/_/g, " ").toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
}

export const EventExplorer: React.FC<EventExplorerProps> = () => {
  const [selectedEventType, setSelectedEventType] = useState<string>("");
  const [startDate, setStartDate] = useState<string>("");
  const [endDate, setEndDate] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const [selectedEvent, setSelectedEvent] = useState<EconomicEvent | null>(null);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["events", selectedEventType, startDate, endDate, page],
    queryFn: () =>
      api.getEvents({
        event_type: selectedEventType || undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        page,
        page_size: PAGE_SIZE,
      }),
    placeholderData: (prev) => prev,
  });

  const total = data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const hasFilters = !!(selectedEventType || startDate || endDate);

  useEffect(() => {
    if (!selectedEvent) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setSelectedEvent(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selectedEvent]);

  const clearFilters = () => {
    setSelectedEventType("");
    setStartDate("");
    setEndDate("");
    setPage(1);
  };

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader
        title="Release calendar"
        description="Every economic release in the database, with its exact publication time, the value first published and any later revision."
      />

      <Toolbar>
        <Field label="Release type" htmlFor="ev-type" className="w-full sm:w-60">
          <Select
            id="ev-type"
            value={selectedEventType}
            onChange={(e) => {
              setSelectedEventType(e.target.value);
              setPage(1);
            }}
          >
            <option value="">All release types</option>
            {EVENT_TYPES.map((e) => (
              <option key={e.value} value={e.value}>
                {e.label}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Published from" htmlFor="ev-from" className="w-[calc(50%-0.375rem)] sm:w-44">
          <Input
            id="ev-from"
            type="date"
            value={startDate}
            max={endDate || undefined}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPage(1);
            }}
          />
        </Field>
        <Field label="Published to" htmlFor="ev-to" className="w-[calc(50%-0.375rem)] sm:w-44">
          <Input
            id="ev-to"
            type="date"
            value={endDate}
            min={startDate || undefined}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPage(1);
            }}
          />
        </Field>
        <div className="flex items-center gap-3 sm:ml-auto pb-1.5 text-xs text-oatmeal-dark dark:text-oatmeal tabular">
          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={clearFilters}>
              Clear filters
            </Button>
          )}
          <span role="status">{isFetching && !isLoading ? "Updating…" : `${total.toLocaleString()} release${total === 1 ? "" : "s"}`}</span>
        </div>
      </Toolbar>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 items-start">
        <Panel className={selectedEvent ? "xl:col-span-2" : "xl:col-span-3"} bodyClassName="p-0">
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Release</th>
                  <th>Reference month</th>
                  <th>Published (Eastern Time)</th>
                  <th className="num">
                    <Term k="first_release">First published</Term>
                  </th>
                  <th className="num">Latest revised</th>
                  <th className="num">Change vs. prior</th>
                  <th>Source quality</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <TableSkeleton cols={7} rows={10} />
                ) : isError ? (
                  <tr>
                    <td colSpan={7}>
                      <ErrorState error={error} onRetry={() => refetch()} what="releases" />
                    </td>
                  </tr>
                ) : data?.items.length === 0 ? (
                  <tr>
                    <td colSpan={7}>
                      <EmptyState
                        title="No releases match these filters"
                        action={
                          <Button size="sm" onClick={clearFilters}>
                            Clear filters
                          </Button>
                        }
                      >
                        Sample data covers 2020 to 2024.
                      </EmptyState>
                    </td>
                  </tr>
                ) : (
                  data?.items.map((ev) => {
                    const isSelected = selectedEvent?.id === ev.id;
                    const revised = ev.actual_latest !== null && Math.abs(ev.actual_latest - ev.actual_first_release) > 1e-9;
                    return (
                      <tr
                        key={ev.id}
                        tabIndex={0}
                        aria-selected={isSelected}
                        onClick={() => setSelectedEvent(isSelected ? null : ev)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" || e.key === " ") {
                            e.preventDefault();
                            setSelectedEvent(isSelected ? null : ev);
                          }
                        }}
                        className="row-hover cursor-pointer"
                      >
                        <td className="font-medium whitespace-nowrap">{eventShort(ev.event_type)}</td>
                        <td>{fmtPeriod(ev.period_date)}</td>
                        <td className="whitespace-nowrap text-blue-fantastic/85 dark:text-oatmeal">{fmtReleaseET(ev.release_ts)}</td>
                        <td className="num font-medium">{fmtValue(ev.actual_first_release)}</td>
                        <td className="num text-blue-fantastic/85 dark:text-oatmeal">
                          {ev.actual_latest !== null ? fmtValue(ev.actual_latest) : "—"}
                          {revised && <span className="ml-1 text-2xs">(revised)</span>}
                        </td>
                        <td className={cx("num", signClass(ev.change_value))}>{fmtChangeFor(ev.change_value, ev.actual_first_release)}</td>
                        <td>
                          <span className={ev.data_quality === "VERIFIED_TIMESTAMP" ? "tag tag-strong" : "tag"}>{qualityLabel(ev.data_quality)}</span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between gap-3 px-4 py-3 border-t border-oatmeal/60 dark:border-blue-fantastic text-xs">
            <span className="text-oatmeal-dark dark:text-oatmeal tabular">
              {total > 0 ? `Showing ${(page - 1) * PAGE_SIZE + 1}–${Math.min(page * PAGE_SIZE, total)} of ${total}` : "No results"}
            </span>
            <div className="flex items-center gap-2">
              <span className="text-oatmeal-dark dark:text-oatmeal tabular mr-1">
                Page {page} of {totalPages}
              </span>
              <Button size="sm" iconOnly aria-label="Previous page" icon={<ChevronLeft />} disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))} />
              <Button
                size="sm"
                iconOnly
                aria-label="Next page"
                icon={<ChevronRight />}
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              />
            </div>
          </div>
        </Panel>

        {selectedEvent && (
          <Panel
            as="aside"
            className="xl:sticky xl:top-4"
            title={`${eventLabel(selectedEvent.event_type)}`}
            sub={`For ${fmtPeriod(selectedEvent.period_date)}`}
            actions={<Button size="sm" variant="ghost" iconOnly aria-label="Close details" icon={<X />} onClick={() => setSelectedEvent(null)} />}
          >
            <dl className="space-y-4 text-[13px]">
              <div>
                <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">Published</dt>
                <dd className="mt-0.5">{fmtReleaseET(selectedEvent.release_ts, "long")} Eastern Time</dd>
                <dd className="text-2xs text-oatmeal-dark dark:text-oatmeal tabular mt-0.5">
                  {parseUtc(selectedEvent.release_ts).toISOString().replace("T", " ").slice(0, 16)} UTC
                </dd>
              </div>
              <div>
                <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">How the time was confirmed</dt>
                <dd className="mt-0.5">{selectedEvent.timestamp_source.replace(/_/g, " ")}</dd>
                <dd className="mt-1">
                  <span className="tag">{qualityLabel(selectedEvent.data_quality)}</span>
                </dd>
              </div>
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-oatmeal/60 dark:border-blue-fantastic">
                <div>
                  <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">
                    <Term k="first_release">First published</Term>
                  </dt>
                  <dd className="mt-0.5 text-lg font-semibold tabular">{fmtValue(selectedEvent.actual_first_release)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">Latest revised</dt>
                  <dd className="mt-0.5 text-lg font-semibold tabular">
                    {selectedEvent.actual_latest !== null ? fmtValue(selectedEvent.actual_latest) : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">Previous release</dt>
                  <dd className="mt-0.5 tabular">{fmtValue(selectedEvent.previous_first_release)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">Change</dt>
                  <dd className={cx("mt-0.5 tabular", signClass(selectedEvent.change_value))}>{fmtChangeFor(selectedEvent.change_value, selectedEvent.actual_first_release)}</dd>
                </div>
              </div>
              <div className="pt-4 border-t border-oatmeal/60 dark:border-blue-fantastic">
                <dt className="text-xs text-oatmeal-dark dark:text-oatmeal">
                  <Term k="consensus">Economists' forecast</Term>
                </dt>
                {selectedEvent.has_consensus ? (
                  <dd className="mt-0.5 font-medium tabular">{fmtValue(selectedEvent.consensus_value)}</dd>
                ) : (
                  <dd className="mt-0.5 text-blue-fantastic/85 dark:text-oatmeal leading-relaxed">
                    Not available. Surprise studies use the change from the previous release instead ({fmtChangeFor(selectedEvent.change_value, selectedEvent.actual_first_release)}).
                  </dd>
                )}
              </div>
            </dl>
          </Panel>
        )}
      </div>
    </div>
  );
};
