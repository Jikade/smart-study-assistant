from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
css = (ROOT / "src" / "styles.css").read_text(encoding="utf-8")

checks = [
    ("hero line-height", "hero-copy h1{font-family:var(--font-display);font-size:clamp(4.4rem,8vw,8.4rem);line-height:1.02;" in css),
    ("section line-height", ".section-intro h2,.story-sticky h2{font-family:var(--font-display);font-size:clamp(3rem,6vw,6rem);line-height:1.08;" in css),
    ("cta line-height", ".cta-section h2{font-family:var(--font-display);font-size:clamp(2.6rem,5vw,5rem);line-height:1.08;" in css),
    ("page heading line-height", ".page-heading h1{font-family:var(--font-display);font-size:clamp(2.35rem,4vw,4.7rem);line-height:1.08;" in css),
]

failed = []

print("=" * 80)
print("FRONTEND VIETNAMESE HEADING LINE-HEIGHT FIX V0.1 REGRESSION")
print("=" * 80)

for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

if failed:
    raise SystemExit(1)

print("Result: PASS")
