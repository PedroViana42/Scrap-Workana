import type { JobDetail, JobsPage, JobSearchParams, SourceItem, StatsResponse } from "@/lib/types";

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
    if (value !== undefined && value !== "") {
      query.set(key, value);
    }
  }
  const suffix = query.toString() ? `?${query}` : "";
  return request<JobsPage>(`/jobs${suffix}`);
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
