from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
state = (ROOT / "src" / "state.js").read_text(encoding="utf-8")
views = (ROOT / "src" / "views.js").read_text(encoding="utf-8")

checks = [
    (
        "logout clears selected subject",
        "saveUi({ selectedSubjectId: null });" in state,
    ),
    (
        "analytics reads saved subject",
        "const savedSid=selectedSubject();" in views,
    ),
    (
        "analytics validates subject membership in current list",
        "subjects.some(s=>Number(s.id)===Number(savedSid))" in views,
    ),
    (
        "analytics falls back to first current subject",
        ": subjects[0]?.id;" in views,
    ),
    (
        "analytics persists resolved subject",
        "saveUi({selectedSubjectId:sid});" in views,
    ),
]

failed = []

print("=" * 80)
print("ANALYTICS SUBJECT STATE FRONTEND V0.1 REGRESSION")
print("=" * 80)

for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

node = shutil.which("node")
if node:
    for rel in [
        "src/api.js",
        "src/state.js",
        "src/ui.js",
        "src/views.js",
        "src/app.js",
    ]:
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
