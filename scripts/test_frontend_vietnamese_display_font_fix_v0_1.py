from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]

index = (ROOT / "index.html").read_text(encoding="utf-8")
css = (ROOT / "src" / "styles.css").read_text(encoding="utf-8")

checks = [
    ("Be Vietnam Pro loaded", "family=Be+Vietnam+Pro" in index),
    ("Fraunces Google font removed", "family=Fraunces" not in index),
    ("display font variable exists", "--font-display:'Be Vietnam Pro'" in css),
    ("Fraunces CSS removed", "font-family:'Fraunces'" not in css),
    ("landing hero uses display variable", ".hero-copy h1{font-family:var(--font-display)" in css),
    ("section heading uses display variable", ".section-intro h2,.story-sticky h2{font-family:var(--font-display)" in css),
    ("CTA heading uses display variable", ".cta-section h2{font-family:var(--font-display)" in css),
    ("page heading uses display variable", ".page-heading h1{font-family:var(--font-display)" in css),
]

failed = []

print("=" * 80)
print("FRONTEND VIETNAMESE DISPLAY FONT FIX V0.1 REGRESSION")
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
