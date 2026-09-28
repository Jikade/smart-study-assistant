from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSS = ROOT / "src" / "styles.css"

css = CSS.read_text(encoding="utf-8")

replacements = [
    (
        ".page-heading h1{font-family:var(--font-display);font-size:clamp(2.35rem,4vw,4.7rem);line-height:.95;",
        ".page-heading h1{font-family:var(--font-display);font-size:clamp(2.35rem,4vw,4.7rem);line-height:1.08;",
        "page heading",
    ),
    (
        ".hero-copy h1{font-family:var(--font-display);font-size:clamp(4.4rem,8vw,8.4rem);line-height:.82;",
        ".hero-copy h1{font-family:var(--font-display);font-size:clamp(4.4rem,8vw,8.4rem);line-height:1.02;",
        "hero heading",
    ),
    (
        ".section-intro h2,.story-sticky h2{font-family:var(--font-display);font-size:clamp(3rem,6vw,6rem);line-height:.93;",
        ".section-intro h2,.story-sticky h2{font-family:var(--font-display);font-size:clamp(3rem,6vw,6rem);line-height:1.08;",
        "section/story heading",
    ),
    (
        ".cta-section h2{font-family:var(--font-display);font-size:clamp(2.6rem,5vw,5rem);line-height:.95;",
        ".cta-section h2{font-family:var(--font-display);font-size:clamp(2.6rem,5vw,5rem);line-height:1.08;",
        "cta heading",
    ),
]

for old, new, label in replacements:
    if old not in css:
        raise SystemExit(f"[FAIL] anchor not found: {label}")
    css = css.replace(old, new, 1)

CSS.write_text(css, encoding="utf-8")

print("=" * 80)
print("FRONTEND VIETNAMESE HEADING LINE-HEIGHT FIX V0.1 APPLIED")
print("=" * 80)
print("Hero heading        : 0.82 -> 1.02")
print("Section headings    : 0.93 -> 1.08")
print("CTA heading         : 0.95 -> 1.08")
print("Page headings       : 0.95 -> 1.08")
print("=" * 80)
