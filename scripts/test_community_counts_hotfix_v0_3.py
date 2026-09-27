from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "app" / "api" / "v1" / "routers" / "community.py"
source = PATH.read_text(encoding="utf-8")

checks = [
    ("func imported", "from sqlalchemy import delete, func, select, text" in source),
    ("like_count response", '"like_count": int(like_count or 0)' in source),
    ("save_count response", '"save_count": int(save_count or 0)' in source),
    ("liked_by_me remains", 'post["liked_by_me"]' in source),
    ("saved_by_me remains", 'post["saved_by_me"]' in source),
]

failed = []

print("=" * 80)
print("COMMUNITY COUNTS BACKEND V0.3 REGRESSION")
print("=" * 80)

for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

if failed:
    raise SystemExit(1)

from app.main import app
app.openapi()
print("[PASS] FastAPI import/OpenAPI")
print("Result: PASS")
