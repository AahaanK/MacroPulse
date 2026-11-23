import {
  Asset,
  DataStatusSummary,
  EconomicEvent,
  EventStudyResult,
  Indicator,
} from "../types";

const API_BASE = "/api";

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errMsg = `Request failed: ${res.statusText} (${res.status})`;
    try {
      const errBody = await res.json();
      if (errBody?.error?.message) {
        errMsg = errBody.error.message;
      } else if (errBody?.detail) {
        errMsg = typeof errBody.detail === "string" ? errBody.detail : JSON.stringify(errBody.detail);
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errMsg);
  }

  return res.json();
}

export const api = {
  getHealth: () => fetchJson<{ status: string; data_mode: string }>("/health"),

  getDataStatus: () => fetchJson<DataStatusSummary>("/data-status"),

  getIndicators: () => fetchJson<Indicator[]>("/indicators"),

  getIndicatorSeries: (code: string, start?: string, end?: string) => {
    const params = new URLSearchParams();
    if (start) params.append("start", start);
    if (end) params.append("end", end);
    const qs = params.toString() ? `?${params.toString()}` : "";
    return fetchJson<{ code: string; data: Array<{ date: string; value: number }> }>(
      `/indicators/${code}/series${qs}`
    );
  },

  getAssets: () => fetchJson<Asset[]>("/assets"),

  getEvents: (params?: {
    event_type?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }) => {
    const query = new URLSearchParams();
    if (params?.event_type) query.append("event_type", params.event_type);
    if (params?.start_date) query.append("start_date", params.start_date);
    if (params?.end_date) query.append("end_date", params.end_date);
    if (params?.page) query.append("page", params.page.toString());
    if (params?.page_size) query.append("page_size", params.page_size.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return fetchJson<{
      items: EconomicEvent[];
      total: number;
      page: number;
      page_size: number;
    }>(`/events${qs}`);
  },

  getStudyDefaults: () => fetchJson<any>("/event-studies/defaults"),

  runEventStudy: (payload: any) =>
    fetchJson<EventStudyResult>("/event-studies/run", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getStudyResult: (resultId: number) =>
    fetchJson<EventStudyResult>(`/event-studies/${resultId}`),

  refreshData: () =>
    fetchJson<{ status: string; message: string }>("/data-status/refresh", {
      method: "POST",
    }),

  // ---- Endpoints previously called with raw fetch() inside pages. Same URLs and payloads;
  // routing them through fetchJson means HTTP errors now surface in the UI.

  analyzeSurprises: (payload: { event_type: string; asset_symbol: string; window_key: string }) =>
    fetchJson<any>("/surprises/analyze", { method: "POST", body: JSON.stringify(payload) }),

  getCorrelationMatrix: (payload: { event_type: string; symbols: string[] }) =>
    fetchJson<any>("/correlations/matrix", { method: "POST", body: JSON.stringify(payload) }),

  getEventVsNormalCorrelations: (payload: { event_type: string; symbols: string[] }) =>
    fetchJson<any>("/correlations/event-vs-normal", { method: "POST", body: JSON.stringify(payload) }),

  getRegimeHistory: () => fetchJson<any>("/regimes/history"),

  getConditionedStudy: (payload: { event_type: string; asset_symbol: string }) =>
    fetchJson<any>("/regimes/conditioned-study", { method: "POST", body: JSON.stringify(payload) }),

  getProjects: () => fetchJson<any[]>("/research/projects"),

  createProject: (payload: { name: string; description: string }) =>
    fetchJson<any>("/research/projects", { method: "POST", body: JSON.stringify(payload) }),

  getNotes: () => fetchJson<any[]>("/research/notes"),

  createNote: (payload: { project_id: number; body_md: string }) =>
    fetchJson<any>("/research/notes", { method: "POST", body: JSON.stringify(payload) }),

  runRobustness: (payload: { event_type: string; asset_symbol: string }) =>
    fetchJson<any>("/research/robustness", { method: "POST", body: JSON.stringify(payload) }),

  getSavedStudies: () => fetchJson<any[]>("/research/saved-studies"),

  generateReport: (studyId: number) =>
    fetchJson<any>("/reports/generate", { method: "POST", body: JSON.stringify({ study_id: studyId }) }),
};
