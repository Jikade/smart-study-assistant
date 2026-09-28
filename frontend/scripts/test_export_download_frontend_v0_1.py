from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
api = (ROOT / 'src' / 'api.js').read_text(encoding='utf-8')
app = (ROOT / 'src' / 'app.js').read_text(encoding='utf-8')
views = (ROOT / 'src' / 'views.js').read_text(encoding='utf-8')
readme = (ROOT / 'README.md').read_text(encoding='utf-8')
coverage = (ROOT / 'ENDPOINT_COVERAGE.md').read_text(encoding='utf-8')

checks = [
    ('download endpoint catalog', '/exports/{export_id}/download' in api),
    ('rawBlob helper', 'async function rawBlob(' in api),
    ('download client', 'downloadExport: id => rawBlob' in api),
    ('download event', "on('[data-download-export]','click',downloadExport);" in app),
    ('blob URL', 'URL.createObjectURL(blob)' in app),
    ('download filename', 'data-download-filename' in views),
    ('unsafe absolute link removed', "api.mediaBase+'/'+String(r.file_url)" not in views),
    ('endpoint UI 62', '<span class="endpoint-count">62</span>' in views),
    ('README 62', '## 62 endpoint được map' in readme),
    ('Exports count 3', '| Exports | 3 |' in coverage),
    ('Total 62', '| **Total** | **62** |' in coverage),
]
failed = []
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
