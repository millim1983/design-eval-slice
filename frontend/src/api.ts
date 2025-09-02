import type {
    RubricDSL,
    AnalyzeResponse,
    ReportEvent,
    Project,
  Submission,
  Judge,
  Assignment,
    RagResponse,
    VisionResponse,
    ModerateResponse,
  } from "./types";

const API_BASE = (
  import.meta.env.VITE_API_URL ??
  import.meta.env.VITE_API_BASE ??
  "http://localhost:8000"
).replace(/\/+$/, "");

const j = async <T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> => {
  try {
    const res = await fetch(API_BASE + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      throw new Error(await res.text());
    }
    return res.json() as Promise<T>;
  } catch (err) {
    throw new Error(
      `API request failed: ${err instanceof Error ? err.message : String(err)}`,
    );
  }
};

export const api = {
upload: (p: {
    title: string;
    author_id: string;
    asset_url?: string;
    file?: File;
    meta?: any;
  }) => {
    if (p.file) {
      const form = new FormData();
      form.append("title", p.title);
      form.append("author_id", p.author_id);
      form.append("file", p.file);
      return fetch(API_BASE + "/uploads", { method: "POST", body: form }).then(
        async (r) => {
          if (!r.ok) {
            const msg = await r.text();
            throw new Error(msg || "upload failed");
          }
          return r.json();
        },
      );
    }
    return j<{ submission_id: string; created_at: string }>("POST", "/uploads", p);
  },

  analyze: (submission_id: string) =>
    j<AnalyzeResponse>("POST", "/analyze", { submission_id }),

  analyzeVision: (file: File, prompt?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (prompt) form.append("prompt", prompt);
    return fetch(API_BASE + "/analyze-vision", {
      method: "POST",
      body: form,
    }).then(async (r) => {
      if (!r.ok) {
        const msg = await r.text();
        throw new Error(msg || "analyze failed");
      }
      return r.json() as Promise<VisionResponse>;
    });
  },

  chat: async (submission_id: string, message: string) => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60_000);
    try {
      const res = await fetch(API_BASE + "/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ submission_id, message }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      if (!res.ok) {
        const msg = await res.text();
        throw new Error(`Server error: ${msg || res.statusText}`);
      }
      return (res.json() as Promise<{
        answer: string;
        citations: string[];
        model_version: string;
        prompt_snapshot: string;
      }>);
    } catch (err) {
      clearTimeout(timeoutId);
      if (err instanceof DOMException && err.name === "AbortError") {
        throw new Error("Network timeout");
      }
      throw new Error(
        `Network error: ${err instanceof Error ? err.message : String(err)}`,
      );
    }
  },

  search: (q: string) =>
    j<{ hits: any[] }>("POST", "/search-guideline", {
      award_id: "aw_2025_kda",
      query: q,
    }),

  rubric: () => j<RubricDSL>("GET", "/rubrics/aw_2025_kda/1.0.0"),

  evaluate: (rec: any) => j<any>("POST", "/evaluate", rec),

  report: (sid: string) =>
    j<{ submission_id: string; events: ReportEvent[] }>(
      "GET",
      `/report/${sid}`,
    ),

  createProject: (name: string) => j<Project>("POST", "/projects", { name }),
  listProjects: () =>
      j<{ projects: Project[] }>("GET", "/projects").then((r) => r.projects),
  createSubmission: (project_id: number, title: string) =>
    j<Submission>("POST", `/projects/${project_id}/submissions`, { title }),
  listSubmissions: (project_id: number) =>
    j<{ submissions: Submission[] }>(
      "GET",
      `/projects/${project_id}/submissions`,
    ).then((r) => r.submissions),

  createJudge: (name: string) => j<Judge>("POST", "/judges", { name }),
  listJudges: () =>
      j<{ judges: Judge[] }>("GET", "/judges").then((r) => r.judges),

  assignJudge: (submission_id: number, judge_id: number) =>
    j<Assignment>("POST", "/assignments", { submission_id, judge_id }),

  recordScore: (assignment_id: number, score: number) =>
    j<{ assignment_id: number; score: number }>(
      "PUT",
      `/assignments/${assignment_id}/score`,
      { score },
    ),

    finalScore: (submission_id: number) =>
      j<{ submission_id: number; final_score: number | null }>(
        "GET",
      `/submissions/${submission_id}/final-score`,
      ),

    ragEval: (query: string) =>
      j<RagResponse>("POST", "/rag-eval", { query }),
    refreshRag: () => j<{ ok: boolean }>("POST", "/rag-index/refresh"),

    moderate: (input: string, output?: string) =>
      j<ModerateResponse>("POST", "/moderate", { input, output }),
  };

export default api;

  