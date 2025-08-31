CREATE TABLE IF NOT EXISTS evidence_ledger (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  submission_id TEXT NOT NULL,
  user_id TEXT,
  at TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  raw_output TEXT,
  image TEXT
);
CREATE INDEX IF NOT EXISTS ix_evidence_submission ON evidence_ledger (submission_id);
CREATE INDEX IF NOT EXISTS ix_evidence_kind ON evidence_ledger (kind);
