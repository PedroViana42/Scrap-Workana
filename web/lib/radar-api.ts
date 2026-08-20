import { homeGroupForJob, matchesJobView } from "@/lib/job-location";
import type { JobDetail, JobsPage, JobSearchParams, JobView, SourceItem, StatsResponse } from "@/lib/types";

const API_BASE_URL = process.env.RADAR_API_BASE_URL ?? "http://127.0.0.1:8000";
const TIMEOUT_MS = 8000;

export class RadarApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message);
    this.name = "RadarApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      cache: "no-store",
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new RadarApiError("API request failed", response.status);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof RadarApiError) {
      throw error;
    }
    throw new RadarApiError("API unavailable");
  } finally {
    clearTimeout(timeout);
  }
}

export function getJobs(params: JobSearchParams = {}): Promise<JobsPage> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (key !== "view" && value !== undefined && value !== "") {
      query.set(key, value);
    }
  }
  const suffix = query.toString() ? `?${query}` : "";
  return request<JobsPage>(`/jobs${suffix}`);
}

export async function getCuratedJobs(params: JobSearchParams & { view: JobView }): Promise<JobsPage> {
  const requestedPage = Math.max(1, Number(params.page) || 1);
  const requestedPageSize = Math.max(1, Number(params.page_size) || 20);
  const baseParams: JobSearchParams = { ...params, page: "1", page_size: "100", active: params.active ?? "true" };
  baseParams.view = undefined;
  let candidates;
  if (params.view === "for-me") {
    const levels: Array<"HIGH" | "MEDIUM" | "LOW"> = params.attainability ? [params.attainability] : ["HIGH", "MEDIUM"];
    const requestedMinimum = Number(params.min_score) || 0;
    const results = await Promise.all(levels.flatMap((level) => {
      if (level === "LOW") return [];
      const groupMinimum = level === "HIGH" ? 60 : 75;
      return [getAllJobs({ ...baseParams, attainability: level, min_score: String(Math.max(requestedMinimum, groupMinimum)) })];
    }));
    candidates = results.flatMap((result) => result);
  } else {
    candidates = await getAllJobs({ ...baseParams, min_score: params.min_score ?? "70" });
  }
  const matched = candidates
    .filter((job) => matchesJobView(job, params.view))
    .sort((left, right) => {
      if (params.view === "for-me") {
        const order = { grounded: 0, stretch: 1 } as const;
        const groupDifference = order[homeGroupForJob(left)!] - order[homeGroupForJob(right)!];
        if (groupDifference) return groupDifference;
      }
      return (right.relevance_score ?? -1) - (left.relevance_score ?? -1)
        || Date.parse(right.published_at ?? right.last_seen_at) - Date.parse(left.published_at ?? left.last_seen_at);
    });
  const start = (requestedPage - 1) * requestedPageSize;
  return {
    items: matched.slice(start, start + requestedPageSize),
    page: requestedPage,
    page_size: requestedPageSize,
    total: matched.length,
    pages: Math.max(1, Math.ceil(matched.length / requestedPageSize)),
  };
}

async function getAllJobs(params: JobSearchParams) {
  const first = await getJobs(params);
  if (first.pages <= 1) return first.items;
  const remaining = await Promise.all(Array.from({ length: first.pages - 1 }, (_, index) => getJobs({ ...params, page: String(index + 2) })));
  return [first, ...remaining].flatMap((page) => page.items);
}

export function getJob(id: string | number): Promise<JobDetail> {
  return request<JobDetail>(`/jobs/${id}`);
}

export function getSources(): Promise<SourceItem[]> {
  return request<SourceItem[]>("/sources");
}

export function getStats(): Promise<StatsResponse> {
  return request<StatsResponse>("/stats");
}

export function getApiBaseUrlForReport() {
  return API_BASE_URL;
}
