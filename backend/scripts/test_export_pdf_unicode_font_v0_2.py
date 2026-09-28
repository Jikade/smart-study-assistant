from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "app" / "services" / "export_service.py"

source = PATH.read_text(encoding="utf-8")

checks = [
    ("pdfmetrics import", "from reportlab.pdfbase import pdfmetrics" in source),
    ("TTFont import", "from reportlab.pdfbase.ttfonts import TTFont" in source),
    ("Arial candidate", 'Path("C:/Windows/Fonts/arial.ttf")' in source),
    ("Segoe UI candidate", 'Path("C:/Windows/Fonts/segoeui.ttf")' in source),
    ("DejaVu candidate", "DejaVuSans.ttf" in source),
    ("unicode font registration", "pdfmetrics.registerFont(" in source),
    ("title uses unicode font", 'title_style.fontName = font_name' in source),
    ("body uses unicode font", 'body_style.fontName = font_name' in source),
]

failed = []

print("=" * 80)
print("EXPORT PDF UNICODE FONT V0.2 REGRESSION")
print("=" * 80)

for label, ok in checks:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        failed.append(label)

if failed:
    raise SystemExit(1)

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate
from app.services.export_service import _register_pdf_unicode_font

font_name = _register_pdf_unicode_font()
print(f"[PASS] Unicode font registered: {font_name}")

with TemporaryDirectory() as tmp:
    pdf_path = Path(tmp) / "unicode_vi_test.pdf"
    styles = getSampleStyleSheet()

    style = styles["BodyText"].clone("UnicodeVietnameseTest")
    style.fontName = font_name

    text = (
        "Tiếng Việt kiểm tra: Giá trị thặng dư, "
        "quy luật giá trị, Đổi mới, Hồ Chí Minh."
    )

    SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
    ).build([
        Paragraph(
            text,
            style,
        )
    ])

    if not pdf_path.is_file() or pdf_path.stat().st_size < 1000:
        raise SystemExit("[FAIL] Unicode Vietnamese PDF was not generated")

    print(
        f"[PASS] Vietnamese PDF generated: "
        f"{pdf_path.stat().st_size} bytes"
    )

print("Result: PASS")
