CREATE TABLE IF NOT EXISTS assignments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id INTEGER NOT NULL REFERENCES submissions(id),
  judge_id INTEGER NOT NULL REFERENCES judges(id),
  score REAL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_assignments_submission ON assignments(submission_id);
CREATE INDEX IF NOT EXISTS ix_assignments_judge ON assignments(judge_id);
