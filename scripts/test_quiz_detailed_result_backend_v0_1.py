from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'app' / 'api' / 'v1' / 'routers' / 'quizzes.py'
source = PATH.read_text(encoding='utf-8')

checks = [
    ('UserAnswer imported', 'UserAnswer,' in source),
    ('answer rows loaded', 'select(UserAnswer).where(' in source),
    ('question text', '"question_text":' in source),
    ('correct status', '"CORRECT"' in source),
    ('wrong status', '"WRONG"' in source),
    ('unanswered status', '"UNANSWERED"' in source),
    ('selected option', '"selected_option":' in source),
    ('correct option', '"correct_option":' in source),
    ('explanation', '"explanation": explanation' in source),
    ('points awarded', '"points_awarded":' in source),
    ('answers response', '"answers": details' in source),
]

failed = []
print('=' * 80)
print('QUIZ DETAILED RESULT BACKEND V0.1 REGRESSION')
print('=' * 80)

for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

if failed:
    raise SystemExit(1)

from app.main import app
schema = app.openapi()
path = '/api/v1/quizzes/attempts/{attempt_id}/result'
assert 'get' in schema['paths'][path]
print('[PASS] FastAPI import/OpenAPI')
print('Result: PASS')
