from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
app = (ROOT / 'src' / 'app.js').read_text(encoding='utf-8')
styles = (ROOT / 'src' / 'styles.css').read_text(encoding='utf-8')

checks = [
    ('result detail fetch', 'await api.attemptResult(' in app),
    ('correct label', "'✓ Đúng'" in app),
    ('wrong label', "'✕ Sai'" in app),
    ('unanswered label', "'— Bỏ trống'" in app),
    ('selected answer', 'Bạn chọn' in app),
    ('correct answer', 'Đáp án đúng' in app),
    ('explanation', 'Giải thích' in app),
    ('question review', 'Xem lại từng câu' in app),
    ('correct style', '.result-question.result-correct' in styles),
    ('wrong style', '.result-question.result-wrong' in styles),
    ('answer grid', '.result-answer-grid' in styles),
]

failed = []
print('=' * 80)
print('QUIZ DETAILED RESULT FRONTEND V0.1 REGRESSION')
print('=' * 80)
for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

node = shutil.which('node')
if node:
    for rel in ['src/api.js','src/state.js','src/ui.js','src/views.js','src/app.js']:
        cp = subprocess.run([node, '--check', str(ROOT / rel)], capture_output=True, text=True)
        ok = cp.returncode == 0
        print(f"[{'PASS' if ok else 'FAIL'}] node --check {rel}")
        if not ok:
            print(cp.stderr)
            failed.append(rel)

if failed:
    raise SystemExit(1)
print('Result: PASS')
