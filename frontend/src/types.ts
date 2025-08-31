export type RubricDSL = {
  award_id: string; version: string;
  criteria: Array<{ id: string; label: string; description?: string;
    scale: { type: "int"|"float"|"enum"; min?: number; max?: number; enum?: string[] };
    weight: number; guideline_refs?: string[]; evidence_queries?: string[];
    required_checks?: string[]; visibility?: { show_model_suggestion_after_initial_score?: boolean }; }>;
  aggregation: { method: "weighted_mean"|"median"|"trimmed_mean"; outlier_policy?: string };
};
export type AnalyzeFinding = { region:{x:number;y:number;w:number;h:number}; label:string; confidence:number; explanation:string; citations?:string[]; };
export type AnalyzeResponse = { findings: AnalyzeFinding[]; model_version:string; prompt_snapshot:string; };
export type ReportEvent = { kind: string; at: string; payload: any };

export type UploadRequest = {
  title: string;
  author_id: string;
  asset_url?: string;
  meta?: any;
};
export type UploadResponse = { submission_id: string; created_at: string };

export type AnalyzeRequest = { submission_id: string };

export type ChatRequest = { submission_id: string; message: string };
export type ChatResponse = {
  answer: string;
  citations: string[];
  model_version: string;
  prompt_snapshot: string;
};

export type EvaluationScore = {
  criteria_id: string;
  score: number;
  reason?: string;
  citation_ids?: string[];
  checks?: any;
};
export type ModelSuggestion = {
  criteria_id?: string;
  suggested_score?: number;
  explanation?: string;
  citation_ids?: string[];
};
export type EvaluateRequest = {
  submission_id: string;
  judge_id: string;
  rubric_version: string;
  scores: EvaluationScore[];
  model_suggestions?: ModelSuggestion[];
  submitted_at?: string;
};
export type EvaluateResponse = { ok: boolean };
