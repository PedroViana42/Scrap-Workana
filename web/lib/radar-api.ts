import { matchesJobView } from "@/lib/job-location";
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
  const apiParams: JobSearchParams = { ...params, page: "1", page_size: "100", min_score: params.min_score ?? "70", active: params.active ?? "true" };
  apiParams.view = undefined;
  const first = await getJobs(apiParams);
  const pages = [first];
  for (let page = 2; page <= first.pages; page += 1) {
    pages.push(await getJobs({ ...apiParams, page: String(page) }));
  }
  const matched = pages.flatMap((page) => page.items).filter((job) => matchesJobView(job, params.view));
  const start = (requestedPage - 1) * requestedPageSize;
  return {
    items: matched.slice(start, start + requestedPageSize),
    page: requestedPage,
    page_size: requestedPageSize,
    total: matched.length,
    pages: Math.max(1, Math.ceil(matched.length / requestedPageSize)),
  };
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
