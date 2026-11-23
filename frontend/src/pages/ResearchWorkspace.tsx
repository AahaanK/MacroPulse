import React, { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FilePlus2, Plus, RotateCcw } from "lucide-react";

import { api } from "../api/client";
import { Button, EmptyState, ErrorState, Field, Input, Notice, PageHeader, Panel, Segmented, Select, Signed, TableSkeleton, Term, Textarea, Toolbar, cx } from "../components/ui";
import { eventLabel, modelLabel, num, parseUtc, pval } from "../lib/format";

interface ResearchWorkspaceProps {
  isDark: boolean;
}

type Tab = "robustness" | "projects" | "notes";

function variationLabel(v: string): string {
  if (v.startsWith("Baseline")) return "Baseline";
  if (v.startsWith("Market Model")) return "Adjusted for market sensitivity";
  if (v.startsWith("Mean Adjusted")) return "Compared with its own average";
  if (v.startsWith("Shorter Est Window")) {
    const d = v.match(/\((\d+)d\)/)?.[1];
    return `Shorter quiet period${d ? ` (${d} days)` : ""}`;
  }
  if (v.startsWith("Alternative Benchmark")) {
    const b = v.match(/\(([^)]+)\)/)?.[1];
    return `Different benchmark${b ? ` (${b})` : ""}`;
  }
  return v;
}

export const ResearchWorkspace: React.FC<ResearchWorkspaceProps> = () => {
  const queryClient = useQueryClient();
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDesc, setNewProjectDesc] = useState("");
  const [activeTab, setActiveTab] = useState<Tab>("robustness");
  const [noteContent, setNoteContent] = useState("");
  const [noteProjectId, setNoteProjectId] = useState<number | null>(null);
  const [notesFilter, setNotesFilter] = useState<number | "all">("all");
  const [robustnessEvent, setRobustnessEvent] = useState("CPI");
  const [robustnessAsset, setRobustnessAsset] = useState("SPY");
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  const { data: projects, isLoading: loadingProjects } = useQuery({ queryKey: ["projects"], queryFn: api.getProjects });
  const { data: notes, isLoading: loadingNotes } = useQuery({ queryKey: ["notes"], queryFn: api.getNotes });

  useEffect(() => {
    if (noteProjectId === null && projects?.length) setNoteProjectId(projects[0].id);
  }, [projects, noteProjectId]);

  useEffect(() => {
    if (!savedMessage) return;
    const t = setTimeout(() => setSavedMessage(null), 3500);
    return () => clearTimeout(t);
  }, [savedMessage]);

  const createProjectMutation = useMutation({
    mutationFn: (payload: { name: string; description: string }) => api.createProject(payload),
    onSuccess: (p) => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setNewProjectName("");
      setNewProjectDesc("");
      setSavedMessage(`Project “${p?.name ?? "Untitled"}” created.`);
      if (p?.id) setNoteProjectId(p.id);
    },
  });

  const createNoteMutation = useMutation({
    mutationFn: (payload: { project_id: number; body_md: string }) => api.createNote(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notes"] });
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setNoteContent("");
      setSavedMessage("Note saved.");
    },
  });

  const {
    data: robustnessData,
    isLoading: loadingRobustness,
    isFetching: fetchingRobustness,
    isError: robustnessError,
    error: robustnessErr,
    refetch: rerunRobustness,
  } = useQuery({
    queryKey: ["robustness", robustnessEvent, robustnessAsset],
    queryFn: () => api.runRobustness({ event_type: robustnessEvent, asset_symbol: robustnessAsset }),
  });

  const projectName = (id: number) => projects?.find((p: any) => p.id === id)?.name ?? `Project ${id}`;
  const visibleNotes = (notes ?? []).filter((n: any) => notesFilter === "all" || n.project_id === notesFilter);
  const results: any[] = robustnessData?.results ?? [];
  const sigCount = results.filter((r) => r.is_significant).length;

  return (
    <div className="mx-auto max-w-page px-4 sm:px-6 py-6 space-y-5">
      <PageHeader title="Workspace" description="Check whether a finding holds up under different settings, organise your research into projects, and keep notes." />

      <Segmented<Tab>
        variant="tabs"
        label="Workspace sections"
        value={activeTab}
        onChange={setActiveTab}
        items={[
          { value: "robustness", label: "Robustness check" },
          { value: "projects", label: `Projects${projects ? ` (${projects.length})` : ""}` },
          { value: "notes", label: `Notes${notes ? ` (${notes.length})` : ""}` },
        ]}
      />

      {savedMessage && (
        <div role="status" className="text-[13px] text-blue-fantastic dark:text-burning-flame">
          {savedMessage}
        </div>
      )}

      {/* ---------------------------------------------------------------- Robustness */}
      {activeTab === "robustness" && (
        <div className="space-y-5">
          <Toolbar>
            <Field label="Release type" htmlFor="rb-type" className="w-full sm:w-60">
              <Select id="rb-type" value={robustnessEvent} onChange={(e) => setRobustnessEvent(e.target.value)}>
                {["CPI", "FOMC", "NFP"].map((v) => (
                  <option key={v} value={v}>
                    {eventLabel(v)}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Asset" htmlFor="rb-asset" className="w-full sm:w-64">
              <Select id="rb-asset" value={robustnessAsset} onChange={(e) => setRobustnessAsset(e.target.value)}>
                <option value="SPY">SPY · S&amp;P 500</option>
                <option value="QQQ">QQQ · Nasdaq-100</option>
                <option value="TLT">TLT · Long-term Treasuries</option>
              </Select>
            </Field>
            <Button icon={<RotateCcw />} onClick={() => rerunRobustness()} loading={fetchingRobustness}>
              {fetchingRobustness ? "Running…" : "Run again"}
            </Button>
          </Toolbar>

          <Panel
            title={<Term k="robustness">Does the result hold up?</Term>}
            sub="The same question, answered with different reasonable settings. A finding you can trust should look similar across all of them."
            actions={
              results.length > 0 && (
                <span className="text-xs text-oatmeal-dark dark:text-oatmeal tabular">
                  Significant in {sigCount} of {results.length} versions
                </span>
              )
            }
            bodyClassName="p-0"
          >
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>What counts as normal</th>
                    <th className="num">Releases</th>
                    <th className="num">
                      <Term k="car">Average move</Term>, day 0 to +1
                    </th>
                    <th className="num">
                      <Term k="t_stat">t-statistic</Term>
                    </th>
                    <th className="num">
                      <Term k="p_value">p-value</Term>
                    </th>
                    <th>Result</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingRobustness ? (
                    <TableSkeleton cols={7} rows={5} />
                  ) : robustnessError ? (
                    <tr>
                      <td colSpan={7}>
                        <ErrorState error={robustnessErr} onRetry={() => rerunRobustness()} what="the robustness check" />
                      </td>
                    </tr>
                  ) : (
                    results.map((r, idx) => (
                      <tr key={idx} className={cx("row-hover", fetchingRobustness && "opacity-60")}>
                        <td className="font-medium" title={r.variation}>{variationLabel(r.variation)}</td>
                        <td className="text-blue-fantastic/85 dark:text-oatmeal">{modelLabel(r.model)}</td>
                        <td className="num">{r.n_events}</td>
                        <td className="num font-medium">
                          <Signed value={r.mean_car} unit="%" />
                        </td>
                        <td className="num">{num(r.t_stat, 2)}</td>
                        <td className="num">{pval(r.p_value)}</td>
                        <td>
                          {r.n_events === 0 ? (
                            <span className="text-xs text-truffle dark:text-truffle-soft">Not enough data</span>
                          ) : r.is_significant ? (
                            <span className="tag tag-strong">Significant</span>
                          ) : (
                            <span className="text-xs text-oatmeal-dark dark:text-oatmeal">Not significant</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Panel>

          {robustnessAsset === "SPY" && results.some((r) => r.model !== "mean_adjusted" && r.mean_car === 0 && r.t_stat === 0) && (
            <Notice>
              Versions that compare SPY with the market use SPY as the market, so they always show zero. Look at the versions that compare SPY with its own
              average, or choose QQQ or TLT.
            </Notice>
          )}
        </div>
      )}

      {/* ---------------------------------------------------------------- Projects */}
      {activeTab === "projects" && (
        <div className="space-y-5">
          <Panel title="New project">
            <form
              className="grid grid-cols-1 md:grid-cols-[1fr_1.4fr_auto] gap-4 items-end"
              onSubmit={(e) => {
                e.preventDefault();
                if (newProjectName.trim()) createProjectMutation.mutate({ name: newProjectName.trim(), description: newProjectDesc.trim() });
              }}
            >
              <Field label="Name" htmlFor="pj-name">
                <Input id="pj-name" placeholder="e.g. Inflation surprises and long bonds" value={newProjectName} onChange={(e) => setNewProjectName(e.target.value)} />
              </Field>
              <Field label="Question or description" htmlFor="pj-desc">
                <Input id="pj-desc" placeholder="What are you trying to find out?" value={newProjectDesc} onChange={(e) => setNewProjectDesc(e.target.value)} />
              </Field>
              <Button type="submit" variant="primary" icon={<Plus />} disabled={!newProjectName.trim()} loading={createProjectMutation.isPending}>
                Create project
              </Button>
            </form>
            {createProjectMutation.isError && (
              <p className="mt-3 text-xs text-truffle dark:text-truffle-soft">Couldn't create the project: {(createProjectMutation.error as Error).message}</p>
            )}
          </Panel>

          {loadingProjects ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="skeleton h-32" />
              ))}
            </div>
          ) : !projects?.length ? (
            <div className="panel">
              <EmptyState title="No projects yet">Create one above to group related studies and notes.</EmptyState>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {projects.map((p: any) => (
                <article key={p.id} className="panel p-4 flex flex-col">
                  <h3 className="text-[15px] font-semibold leading-snug">{p.name}</h3>
                  <p className="mt-1.5 text-[13px] leading-relaxed text-blue-fantastic/85 dark:text-oatmeal flex-1">{p.description || "No description."}</p>
                  <div className="mt-4 pt-3 border-t border-oatmeal/60 dark:border-blue-fantastic flex items-center justify-between text-xs text-oatmeal-dark dark:text-oatmeal tabular">
                    <span>
                      {p.study_count} stud{p.study_count === 1 ? "y" : "ies"} · {p.note_count} note{p.note_count === 1 ? "" : "s"}
                    </span>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setNoteProjectId(p.id);
                        setNotesFilter(p.id);
                        setActiveTab("notes");
                      }}
                    >
                      Open notes
                    </Button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ---------------------------------------------------------------- Notes */}
      {activeTab === "notes" && (
        <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] gap-5 items-start">
          <Panel title="New note" className="lg:sticky lg:top-4">
            {!projects?.length && !loadingProjects ? (
              <EmptyState
                title="Create a project first"
                action={
                  <Button size="sm" onClick={() => setActiveTab("projects")}>
                    Go to projects
                  </Button>
                }
              >
                Every note belongs to a project.
              </EmptyState>
            ) : (
              <form
                className="space-y-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (noteContent.trim() && noteProjectId) createNoteMutation.mutate({ project_id: noteProjectId, body_md: noteContent });
                }}
              >
                <Field label="Project" htmlFor="nt-project">
                  <Select id="nt-project" value={noteProjectId ?? ""} onChange={(e) => setNoteProjectId(Number(e.target.value))}>
                    {projects?.map((p: any) => (
                      <option key={p.id} value={p.id}>
                        {p.name}
                      </option>
                    ))}
                  </Select>
                </Field>
                <Field label="Note" htmlFor="nt-body" hint="Plain text or Markdown.">
                  <Textarea
                    id="nt-body"
                    rows={6}
                    placeholder="What did you find? What would you test next?"
                    value={noteContent}
                    onChange={(e) => setNoteContent(e.target.value)}
                  />
                </Field>
                <Button type="submit" variant="primary" icon={<FilePlus2 />} disabled={!noteContent.trim() || !noteProjectId} loading={createNoteMutation.isPending}>
                  Save note
                </Button>
                {createNoteMutation.isError && (
                  <p className="text-xs text-truffle dark:text-truffle-soft">Couldn't save the note: {(createNoteMutation.error as Error).message}</p>
                )}
              </form>
            )}
          </Panel>

          <section className="space-y-3" aria-label="Notes">
            <div className="flex items-end justify-between gap-3">
              <h2 className="text-sm font-semibold">
                {visibleNotes.length} note{visibleNotes.length === 1 ? "" : "s"}
              </h2>
              <Select
                aria-label="Filter notes by project"
                className="!w-56"
                value={notesFilter}
                onChange={(e) => setNotesFilter(e.target.value === "all" ? "all" : Number(e.target.value))}
              >
                <option value="all">All projects</option>
                {projects?.map((p: any) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </Select>
            </div>
            {loadingNotes ? (
              <div className="skeleton h-24" />
            ) : visibleNotes.length === 0 ? (
              <div className="panel">
                <EmptyState title="No notes here yet">Notes you save appear here, newest first.</EmptyState>
              </div>
            ) : (
              visibleNotes.map((n: any) => (
                <article key={n.id} className="panel px-4 py-3.5">
                  <div className="flex flex-wrap items-baseline justify-between gap-2 text-xs text-oatmeal-dark dark:text-oatmeal">
                    <span className="font-medium text-blue-fantastic dark:text-oatmeal">{projectName(n.project_id)}</span>
                    <time dateTime={n.created_at}>
                      {parseUtc(n.created_at).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" })}
                    </time>
                  </div>
                  <div className="mt-2 text-[14px] leading-relaxed whitespace-pre-wrap">{n.body_md}</div>
                </article>
              ))
            )}
          </section>
        </div>
      )}
    </div>
  );
};
