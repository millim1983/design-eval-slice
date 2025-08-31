import type {
  RubricDSL,
  AnalyzeResponse,
  ReportEvent,
  Project,
  Submission,
  Judge,
  Assignment,
} from "./types";

const j = async <T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> => {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json() as Promise<T>;
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
      return fetch("/uploads", { method: "POST", body: form }).then((r) => {
        if (!r.ok) throw new Error("upload failed");
        return r.json();
      });
    }
    return j<{ submission_id: string; created_at: string }>("POST", "/uploads", p);
  },

  analyze: (submission_id: string) =>
    j<AnalyzeResponse>("POST", "/analyze", { submission_id }),

  chat: (submission_id: string, message: string) =>
    j<{
      answer: string;
      citations: string[];
      model_version: string;
      prompt_snapshot: string;
    }>("POST", "/chat", { submission_id, message }),

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
};

export default api;

  