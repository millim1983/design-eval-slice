CREATE TABLE IF NOT EXISTS training_dataset (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  submission_id TEXT NOT NULL,
  image_path TEXT NOT NULL,
  evaluation_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_training_submission ON training_dataset (submission_id);
