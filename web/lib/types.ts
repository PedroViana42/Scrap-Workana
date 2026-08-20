export type RelevanceBand = "excellent" | "strong" | "interesting" | "low" | "very_low" | string;

export type JobListItem = {
  id: number;
  title: string;
  company: string | null;
  source: string;
  url: string;
  location: string | null;
  remote: boolean;
  remote_type: string;
  employment_type: string;
  seniority: string;
  technologies: string[];
  published_at: string | null;
  first_seen_at: string;
  last_seen_at: string;
  relevance_score: number | null;
  relevance_band: RelevanceBand | null;
};

export type JobDetail = JobListItem & {
  description: string | null;
  salary: {
    min: string | number | null;
    max: string | number | null;
    currency: string | null;
  };
  relevance_reasons: RelevanceReasons | null;
};

export type RelevanceReasons = {
  positive?: string[];
  negative?: string[];
  matched_roles?: string[];
  matched_technologies?: string[];
  matched_location_signals?: string[];
  matched_seniority_signals?: string[];
  [key: string]: unknown;
};

export type JobsPage = {
  items: JobListItem[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
};

export type SourceItem = {
  name: string;
  display_name: string;
  content_type: string;
  enabled: boolean;
  status: string;
  collector: string | null;
  priority: number;
};

export type StatsResponse = {
  jobs_total: number;
  jobs_active: number;
  sources_total: number;
  sources_enabled: number;
  company_sources_enabled: number;
  jobs_by_relevance_band: Record<string, number>;
  scrape_runs_24h: Record<string, number>;
  last_successful_scrape: string | null;
};

export type JobSearchParams = {
  view?: JobView;
  q?: string;
  source?: string;
  company?: string;
  remote?: string;
  employment_type?: string;
  seniority?: string;
  min_score?: string;
  max_score?: string;
  relevance_band?: string;
  active?: string;
  location?: string;
  technology?: string;
  page?: string;
  page_size?: string;
};

export type JobView = "for-me" | "brazil" | "remote" | "goiania";
