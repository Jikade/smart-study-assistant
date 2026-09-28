from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
CSS = ROOT / "src" / "styles.css"

index = INDEX.read_text(encoding="utf-8")
css = CSS.read_text(encoding="utf-8")

old_font_link = (
    '<link href="https://fonts.googleapis.com/css2?'
    'family=DM+Sans:wght@400;500;600;700&'
    'family=Fraunces:opsz,wght@9..144,600;9..144,700&'
    'display=swap" rel="stylesheet" />'
)

new_font_link = (
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Be+Vietnam+Pro:ital,wght@0,600;0,700;0,800;1,600;1,700&'
    'family=DM+Sans:wght@400;500;600;700&'
    'display=swap" rel="stylesheet" />'
)

if old_font_link not in index:
    raise SystemExit("[FAIL] Google Fonts link anchor not found")

index = index.replace(old_font_link, new_font_link, 1)

root_anchor = (
    "  --shadow:0 24px 70px rgba(31,24,17,.10);"
    "--radius:28px;--radius-sm:18px;--sidebar:258px;\n"
    "  font-family:'DM Sans',system-ui,sans-serif;"
    "color:var(--ink);background:var(--paper)\n"
)

root_replacement = (
    "  --shadow:0 24px 70px rgba(31,24,17,.10);"
    "--radius:28px;--radius-sm:18px;--sidebar:258px;\n"
    "  --font-display:'Be Vietnam Pro','DM Sans',system-ui,sans-serif;\n"
    "  font-family:'DM Sans',system-ui,sans-serif;"
    "color:var(--ink);background:var(--paper)\n"
)

if root_anchor not in css:
    raise SystemExit("[FAIL] :root font anchor not found")

css = css.replace(root_anchor, root_replacement, 1)

fraunces_count = css.count("font-family:'Fraunces'")
if fraunces_count == 0:
    raise SystemExit("[FAIL] No Fraunces declarations found")

css = css.replace(
    "font-family:'Fraunces'",
    "font-family:var(--font-display)",
)

INDEX.write_text(index, encoding="utf-8")
CSS.write_text(css, encoding="utf-8")

print("=" * 80)
print("FRONTEND VIETNAMESE DISPLAY FONT FIX V0.1 APPLIED")
print("=" * 80)
print("Old display font      : Fraunces")
print("New display font      : Be Vietnam Pro")
print("Body font             : DM Sans (unchanged)")
print(f"Display declarations  : {fraunces_count} replaced")
print("Landing headings      : fixed")
print("Other display headings: normalized")
print("=" * 80)
