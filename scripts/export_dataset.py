#!/usr/bin/env python3
import argparse, json, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "backend"))
from app.core.paths import DB_PATH

def main():
    parser = argparse.ArgumentParser(description="Export training dataset as JSONL")
    parser.add_argument("--out", default="training_dataset.jsonl", help="Output JSONL file path")
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT image_path, evaluation_json FROM training_dataset ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as f:
        for img, ev_json in rows:
            f.write(json.dumps({"image_path": img, "evaluation": json.loads(ev_json)}, ensure_ascii=False) + "\n")
    print(f"Exported {len(rows)} rows to {out_path}")

if __name__ == "__main__":
    main()
