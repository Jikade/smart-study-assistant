from pathlib import Path
import subprocess
import shutil

ROOT = Path(__file__).resolve().parents[1]

api = (ROOT / "src" / "api.js").read_text(encoding="utf-8")
app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
views = (ROOT / "src" / "views.js").read_text(encoding="utf-8")
readme = (ROOT / "README.md").read_text(encoding="utf-8")
coverage = (ROOT / "ENDPOINT_COVERAGE.md").read_text(encoding="utf-8")

checks = [
    ("V5 generate endpoint catalog", "['POST','/quizzes/generate-v5',true,'Quizzes']" in api),
    ("V5 preview endpoint catalog", "['POST','/quizzes/generate-v5-preview',true,'Quizzes']" in api),
    ("V5 generate client method", "generateQuizV5:" in api),
    ("V5 preview client method", "previewQuizV5:" in api),
    ("V5 submit path", "await api.generateQuizV5(payload)" in app),
    ("V5 requires selected document", "Quiz V5 cần chọn ít nhất một tài liệu READY." in app),
    ("Document ids sent by quiz/deck", app.count("document_ids:documentIds") >= 2),
    ("V5 is default UI mode", '<option value="v5">V5 Deterministic (khuyến nghị)</option>' in views),
    ("Document multi-select exists", 'name="${esc(name)}" multiple' in views),
    ("Question cap is 5 in V5 UI", 'name="question_count" min="1" max="5" value="5"' in views),
    ("Subject family control exists", 'name="subject_family"' in views),
    ("Endpoint UI count is 61", '<span class="endpoint-count">61</span>' in views),
    ("README count 61", "## 61 endpoint được map" in readme),
    ("Coverage quiz count 13", "| Quizzes | 13 |" in coverage),
    ("Coverage total 61", "| **Total** | **61** |" in coverage),
    ("Legacy normal preserved", "api.generateQuiz" in app),
    ("Legacy weak preserved", "api.generateWeakQuiz" in app),
    ("Legacy adaptive preserved", "api.generateAdaptiveQuiz" in app),
    ("Legacy due preserved", "api.generateDueQuiz" in app),
]

failed = [label for label, ok in checks if not ok]

print("=" * 88)
print("FRONTEND QUIZ V5 INTEGRATION V1 REGRESSION")
print("=" * 88)
for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")

node = shutil.which("node")
if node:
    print("-" * 88)
    syntax_files = [
        "src/api.js",
        "src/state.js",
        "src/ui.js",
        "src/views.js",
        "src/app.js",
    ]
    for rel in syntax_files:
        p = ROOT / rel
        cp = subprocess.run(
            [node, "--check", str(p)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        ok = cp.returncode == 0
        print(f"[{'PASS' if ok else 'FAIL'}] node --check {rel}")
        if not ok:
            failed.append(f"syntax {rel}")
            print(cp.stderr.strip())
else:
    print("[WARN] node not found; skipped JS syntax check")

print("=" * 88)
if failed:
    print("Result: FAIL")
    for label in failed:
        print(" -", label)
    raise SystemExit(1)

print("Result: PASS")
print("=" * 88)
