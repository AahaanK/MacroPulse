import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RefreshCw } from "lucide-react";

import { api } from "../api/client";
import { Button, ErrorState, PageHeader, Panel, Stat, StatRow, TableSkeleton } from "../components/ui";
import { assetName, fmtDate, parseUtc } from "../lib/format";

interface DataIntegrityProps {
  isDark: boolean;
}

export const DataIntegrity: React.FC<DataIntegrityProps> = () => {
  const queryClient = useQueryClient();

  const { data: status, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dataStatus"],
    queryFn: api.getDataStatus,
  });

  const refreshMutation = useMutation({
    mutationFn: api.refreshData,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dataStatus"] });
    },
  });

  const lastRun = status?.last_ingestion_time ? parseUtc(status.last_ingestion_time) : null;

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader
        title="Data sources"
        description="Where MacroPulse's data comes from, how much of it there is, and what the app can't do with the current setup."
        actions={
          <div className="flex flex-col items-end gap-1">
            <Button variant="primary" icon={<RefreshCw className={refreshMutation.isPending ? "animate-spin" : ""} />} onClick={() => refreshMutation.mutate()} disabled={refreshMutation.isPending}>
              {refreshMutation.isPending ? "Updating data…" : "Check for new data"}
            </Button>
            {refreshMutation.isSuccess && (
              <span role="status" className="text-xs text-blue-fantastic dark:text-burning-flame">
                {refreshMutation.data?.message || "Update finished."}
              </span>
            )}
            {refreshMutation.isError && (
              <span role="alert" className="text-xs text-truffle dark:text-truffle-soft">
                Update failed: {(refreshMutation.error as Error).message}
              </span>
            )}
          </div>
        }
      />

      {isError ? (
        <div className="panel">
          <ErrorState error={error} onRetry={() => refetch()} what="data status" />
        </div>
      ) : (
        <StatRow cols="grid-cols-2 lg:grid-cols-4">
          <Stat
            label="Data mode"
            term="demo_data"
            value={status ? (status.is_live_mode ? "Live" : "Sample") : "—"}
            sub={status ? (status.is_live_mode ? "Connected to FRED with an API key" : "Bundled data, no API key set") : " "}
          />
          <Stat label="Daily prices" value={status ? status.total_prices.toLocaleString() : "—"} sub={status ? `${status.total_assets} assets` : " "} />
          <Stat
            label="Economic releases"
            value={status ? status.total_events.toLocaleString() : "—"}
            sub={status ? `${status.total_indicators} indicators` : " "}
          />
          <Stat
            label="Last update"
            value={status ? (status.last_ingestion_status ? status.last_ingestion_status.charAt(0) + status.last_ingestion_status.slice(1).toLowerCase() : "Ready") : "—"}
            sub={lastRun ? lastRun.toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" }) : " "}
          />
        </StatRow>
      )}

      {!!status?.disabled_modes?.length && (
        <Panel title="Current limitations" sub="Features that are switched off or limited with the current setup, and why.">
          <ul className="divide-y divide-oatmeal/60 dark:divide-blue-fantastic -my-2">
            {status.disabled_modes.map((dm, idx) => (
              <li key={idx} className="py-3 flex flex-col sm:flex-row sm:items-baseline gap-x-6 gap-y-1">
                <div className="sm:w-72 shrink-0">
                  <div className="text-[13px] font-medium">{dm.mode}</div>
                  <div className="text-xs text-truffle dark:text-truffle-soft">{dm.status}</div>
                </div>
                <p className="text-[13px] leading-relaxed text-blue-fantastic/90 dark:text-oatmeal">{dm.reason}</p>
              </li>
            ))}
          </ul>
          <p className="mt-4 pt-3 border-t border-oatmeal/60 dark:border-blue-fantastic text-xs text-oatmeal-dark dark:text-oatmeal">
            To use live data, set <span className="code-id">FRED_API_KEY</span> in the backend's <span className="code-id">.env</span> file and restart the
            server.
          </p>
        </Panel>
      )}

      <Panel title="Price history by asset" sub="Daily closing prices available for each asset." bodyClassName="p-0">
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Type</th>
                <th className="num">Trading days</th>
                <th>First day</th>
                <th>Last day</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <TableSkeleton cols={6} rows={11} />
              ) : (
                status?.series_coverage.map((c) => (
                  <tr key={c.symbol} className="row-hover">
                    <td className="whitespace-nowrap">
                      <span className="font-medium">{c.symbol}</span>{" "}
                      <span className="text-oatmeal-dark dark:text-oatmeal">{assetName(c.symbol, c.name)}</span>
                    </td>
                    <td className="text-blue-fantastic/85 dark:text-oatmeal">{c.class === "FX" ? "Currency" : c.class}</td>
                    <td className="num">{c.count.toLocaleString()}</td>
                    <td className="whitespace-nowrap">{fmtDate(c.start)}</td>
                    <td className="whitespace-nowrap">{fmtDate(c.end)}</td>
                    <td>
                      <span className={c.count > 0 ? "tag tag-strong" : "tag tag-warn"}>{c.count > 0 ? "Complete" : "Missing"}</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
};
