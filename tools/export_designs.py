"""Rebuild designs/ previews from designs/canvas-source and export PNG + PDF downloads.

Usage (from the project root):  python tools/export_designs.py
Needs Google Chrome and the Python packages Pillow and PyMuPDF.
"""
import json, re, subprocess, zipfile
from pathlib import Path
import pymupdf

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "designs" / "canvas-source"
OUT = ROOT / "designs"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# Canvas asset URLs -> optimized local logo (previews live in designs/preview/)
LOGO = "../../assets/logo/logo-1024.webp"
BLOBS = {
    "/_blob/f70652e0767dd46c5de22c97a1c50e36": LOGO,
    "/_blob/90076e16560a9b0c6ebc8516b12273b0": LOGO,
}
# Boards exported again at exact size, ready to upload to Facebook
FACEBOOK = {"FacebookProfile": "profile-720x720.png", "FacebookCover": "cover-1640x624.png"}

canvas = json.loads((SRC / "canvas.json").read_text(encoding="utf-8"))
for d in ("preview", "images", "pdf", "facebook"):
    (OUT / d).mkdir(exist_ok=True)

def chrome(*args):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--no-pdf-header-footer", "--virtual-time-budget=8000", *args],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

boards = []
for f in canvas["order"]:
    b = canvas["boards"][f]
    name, title, w, h = f.replace(".dc.html", ""), b["title"], b["w"], b["h"]
    s = (SRC / f).read_text(encoding="utf-8")
    helmet = re.search(r"<helmet>(.*?)</helmet>", s, re.S).group(1)
    body = re.search(r"</helmet>(.*?)</x-dc>", s, re.S).group(1)
    for k, v in BLOBS.items():
        body = body.replace(k, v)
    page_css = (f"<style>@page{{size:{w}px {h}px;margin:0}}"
                "html{-webkit-print-color-adjust:exact;print-color-adjust:exact}</style>")
    if "paper_mm" in b:   # print piece laid out at 1px = 1mm: print the PDF at real size
        pw, ph = b["paper_mm"]
        page_css = (f"<style>@page{{size:{pw}mm {ph}mm;margin:0}}"
                    f"@media print{{body{{zoom:{96 / 25.4:.4f}}}}}"
                    "html{-webkit-print-color-adjust:exact;print-color-adjust:exact}</style>")
    html = (f'<!doctype html>\n<html lang="ar" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
            f"<title>{title}</title>\n{helmet}\n{page_css}\n</head>\n<body>\n{body}\n</body>\n</html>\n")
    preview = OUT / "preview" / f"{name}.html"
    preview.write_text(html, encoding="utf-8")
    url = preview.resolve().as_uri()
    chrome("--force-device-scale-factor=2", f"--window-size={w},{h}",
           f"--screenshot={OUT / 'images' / f'{name}.png'}", url)
    chrome(f"--print-to-pdf={OUT / 'pdf' / f'{name}.pdf'}", url)
    if name in FACEBOOK:
        chrome("--force-device-scale-factor=1", f"--window-size={w},{h}",
               f"--screenshot={OUT / 'facebook' / FACEBOOK[name]}", url)
    boards.append((name, title, w, h))
    print("exported", name)

# One combined PDF and one ZIP of all images
merged = pymupdf.open()
for name, *_ in boards:
    with pymupdf.open(OUT / "pdf" / f"{name}.pdf") as d:
        merged.insert_pdf(d, from_page=0, to_page=0)
merged.save(OUT / "pdf" / "light-windows-identity.pdf")
with zipfile.ZipFile(OUT / "images" / "light-windows-identity-images.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for name, *_ in boards:
        z.write(OUT / "images" / f"{name}.png", f"{name}.png")
    for p in (OUT / "facebook").glob("*.png"):
        z.write(p, f"facebook/{p.name}")
    for p in (ROOT / "assets" / "logo").glob("logo-*"):
        z.write(p, f"logo/{p.name}")

# Gallery page with download links
cards = []
for name, title, w, h in boards:
    sc = 480 / w
    cards.append(f'''<figure>
  <a class="thumb" href="preview/{name}.html" style="height:{round(h * sc)}px"><iframe src="preview/{name}.html" tabindex="-1" aria-hidden="true" style="width:{w}px;height:{h}px;transform:scale({sc:.4f})"></iframe></a>
  <figcaption><span>{title}</span>
    <span class="dl"><a href="images/{name}.png" download>PNG</a><a href="pdf/{name}.pdf" download>PDF</a></span>
  </figcaption>
</figure>''')
(OUT / "index.html").write_text(f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Visual Identity</title>
<script>
  // Opened as ".../designs" (no slash), relative links would resolve to the site root. Add the slash.
  if (location.protocol !== "file:" && !location.pathname.endsWith("/") && !/\\.html?$/.test(location.pathname))
    location.replace(location.pathname + "/" + location.search + location.hash);
</script>
<link rel="icon" href="../assets/logo/favicon.ico" sizes="any">
<style>
body{{margin:0;background:#E9E5DA;font-family:system-ui,sans-serif;color:#063D1F}}
header{{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;padding:32px 40px 0}}
h1{{font-size:22px;margin:0}}
.all{{display:flex;flex-wrap:wrap;gap:10px}}
.btn{{display:inline-flex;align-items:center;min-height:44px;padding:0 20px;border-radius:999px;background:#0B5A2E;color:#fff;text-decoration:none;font-weight:600;font-size:15px}}
.btn:hover{{background:#063D1F}}
.btn.alt{{background:#C9A04A;color:#063D1F}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(480px,1fr));gap:40px;padding:32px 40px;align-items:start}}
figure{{margin:0}}
.thumb{{display:block;width:480px;max-width:100%;overflow:hidden;border-radius:8px}}
iframe{{border:0;transform-origin:0 0;pointer-events:none;background:#fff}}
figcaption{{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-top:10px;font-weight:600;max-width:480px}}
.dl{{display:flex;gap:8px}}
.dl a{{display:inline-flex;align-items:center;min-height:36px;padding:0 14px;border-radius:999px;border:2px solid #0B5A2E;color:#0B5A2E;text-decoration:none;font-size:14px}}
.dl a:hover{{background:#0B5A2E;color:#fff}}
@media (max-width:600px){{header,.grid{{padding-inline:16px}}.grid{{grid-template-columns:1fr}}}}
</style></head>
<body>
<header><h1>Light Windows — Visual Identity</h1>
<div class="all"><a class="btn" href="pdf/light-windows-identity.pdf" download>Download all (PDF)</a><a class="btn alt" href="images/light-windows-identity-images.zip" download>Download all images (ZIP)</a><a class="btn" href="../assets/logo/logo-2048.png" download>Logo (2048 PNG)</a></div></header>
<div class="grid">
{chr(10).join(cards)}
</div></body></html>
''', encoding="utf-8")
print("done")
