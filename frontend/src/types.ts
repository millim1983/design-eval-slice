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
export type Project = { project_id:number; name:string; created_at:string };
export type Submission = { submission_id:number; project_id?:number; title:string; created_at:string };
export type Judge = { judge_id:number; name:string; created_at:string };
export type Assignment = { assignment_id:number; submission_id:number; judge_id:number; score?:number|null; created_at:string };

export type EvaluateRequest = {
  submission_id: string;
  judge_id: string;
  rubric_version: string;
  scores: Array<{
    criteria_id: string;
    score: number;
    reason?: string;
    citation_ids?: string[];
    checks?: Record<string, any>;
  }>;
  model_suggestions?: Array<{
    criteria_id?: string;
    suggested_score?: number;
    explanation?: string;
    citation_ids?: string[];
  }>;
  submitted_at?: string;
};
