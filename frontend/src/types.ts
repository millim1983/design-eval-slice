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
