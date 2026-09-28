from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
views = (ROOT / "src" / "views.js").read_text(encoding="utf-8")
app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")

checks = [
    ("quiz resources loaded", "api.listQuizzes({limit:100})" in views),
    ("deck resources loaded", "api.listDecks(100)" in views),
    ("study plans loaded", "api.listStudyPlans()" in views),
    ("resource select exists", 'name="resource"' in views),
    ("manual resource id removed", 'name="resource_id"' not in views),
    ("type/id encoded in option", "`${r.type}:${r.id}`" in views),
    ("resource parsed on submit", "String(fd.get('resource')||'').split(':')" in app),
    ("resource type sent", "resource_type,resource_id" in app),
    ("format preserved", "file_format:fd.get('file_format')" in app),
]

failed = []

print("=" * 80)
print("EXPORT RESOURCE PICKER FRONTEND V0.2 REGRESSION")
print("=" * 80)

for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

node = shutil.which("node")
if node:
    for rel in ["src/api.js","src/state.js","src/ui.js","src/views.js","src/app.js"]:
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
