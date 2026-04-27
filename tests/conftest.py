import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.update({
    "llm_provider": "test",
    "prompts_dir": str(ROOT / "prompts"),
    "golden_path": str(ROOT / "data" / "golden.jsonl"),
    "db_path": str(ROOT / "data" / "runs.test.db"),
    "report_dir": str(ROOT / "reports"),
})
