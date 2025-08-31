export const api = {
  upload: (p:{title:string;author_id:string;asset_url?:string;meta?:any}) =>
    j("POST","/uploads",p),
  analyze: (submission_id:string) =>
    j("POST","/analyze",{submission_id}),
  search: (q:string) =>
    j("POST","/search-guideline",{award_id:"aw_2025_kda", query:q}),
  rubric: () => j("GET","/rubrics/aw_2025_kda/1.0.0"),
  evaluate: (rec:any) =>
    j("POST","/evaluate",rec),

  // main 브랜치 기능 유지
  review: (p:{submission_id:string; findings:any; note?:string}) =>
    j("POST","/review",p),
  report: (sid:string) =>
    j("GET",`/report/${sid}`),

  // 새로 추가된 프로젝트 심사 워크플로우 API
  createProject: (name:string) =>
    j("POST","/projects",{name}),
  listProjects: () =>
    j("GET","/projects"),
  createSubmission: (project_id:number,title:string) =>
    j("POST",`/projects/${project_id}/submissions`,{title}),
  listSubmissions: (project_id:number) =>
    j("GET",`/projects/${project_id}/submissions`),
  createJudge: (name:string) =>
    j("POST","/judges",{name}),
  listJudges: () =>
    j("GET","/judges"),
  assignJudge: (submission_id:number,judge_id:number) =>
    j("POST","/assignments",{submission_id,judge_id}),
  recordScore: (assignment_id:number,score:number) =>
    j("PUT",`/assignments/${assignment_id}/score`,{score}),
  finalScore: (submission_id:number) =>
    j("GET",`/submissions/${submission_id}/final-score`)
};
export default api;
