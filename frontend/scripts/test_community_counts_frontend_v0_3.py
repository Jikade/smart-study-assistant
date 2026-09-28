from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
views = (ROOT / "src" / "views.js").read_text(encoding="utf-8")

checks = [
    ("like response count", "Number(r.like_count||0)" in app),
    ("save response count", "Number(r.save_count||0)" in app),
    ("initial like count", "Number(p.like_count||0)" in views),
    ("initial save count", "Number(p.save_count||0)" in views),
    ("per-user like state", "p.liked_by_me" in views),
    ("per-user save state", "p.saved_by_me" in views),
]

failed = []

for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

node = shutil.which("node")
if node:
    for rel in ["src/api.js", "src/state.js", "src/ui.js", "src/views.js", "src/app.js"]:
        cp = subprocess.run(
            [node, "--check", str(ROOT / rel)],
            capture_output=True,
            text=True,
        )
        ok = cp.returncode == 0
        print(f"[{'PASS' if ok else 'FAIL'}] node --check {rel}")
        if not ok:
            print(cp.stderr)
            failed.append(rel)

if failed:
    raise SystemExit(1)

print("Result: PASS")
