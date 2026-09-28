from pathlib import Path
import shutil, subprocess

ROOT = Path(__file__).resolve().parents[1]
app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
css = (ROOT / "src" / "styles.css").read_text(encoding="utf-8")

checks = [
    ("celebration icon", "result-hero-icon" in app),
    ("correct badge text", "Chính xác" in app),
    ("wrong badge text", "Cần xem lại" in app),
    ("selected answer preserved", "Bạn chọn" in app),
    ("correct answer preserved", "Đáp án đúng" in app),
    ("animated correct icon", "@keyframes correctPulse" in css),
    ("animated wrong icon", "@keyframes wrongWiggle" in css),
    ("hero styles", ".result-hero{" in css),
    ("kpi styles", ".result-kpis{" in css),
    ("question polish", ".result-question.result-correct" in css),
]

failed = []

print("=" * 80)
print("QUIZ RESULT UI POLISH FRONTEND V0.1 REGRESSION")
print("=" * 80)

for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

node = shutil.which("node")
if node:
    for rel in ["src/api.js","src/state.js","src/ui.js","src/views.js","src/app.js"]:
        cp = subprocess.run([node, "--check", str(ROOT / rel)], capture_output=True, text=True)
        ok = cp.returncode == 0
        print(f"[{'PASS' if ok else 'FAIL'}] node --check {rel}")
        if not ok:
            print(cp.stderr)
            failed.append(rel)

if failed:
    raise SystemExit(1)

print("Result: PASS")
