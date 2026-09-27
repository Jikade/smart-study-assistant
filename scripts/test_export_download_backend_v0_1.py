from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'app' / 'api' / 'v1' / 'routers' / 'exports.py'
s = p.read_text(encoding='utf-8')
checks = [
    ('FileResponse', 'from fastapi.responses import FileResponse' in s),
    ('download route', '@router.get("/{export_id}/download")' in s),
    ('owner check', 'job.user_id != user.id' in s),
    ('completed check', 'job.status != "COMPLETED"' in s),
    ('file existence', 'path.is_file()' in s),
]
for name, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
if not all(ok for _, ok in checks):
    raise SystemExit(1)
from app.main import app
assert 'get' in app.openapi()['paths']['/api/v1/exports/{export_id}/download']
print('[PASS] OpenAPI')
print('Result: PASS')
