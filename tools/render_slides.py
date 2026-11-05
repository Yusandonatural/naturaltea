#!/usr/bin/env python3
"""tools/entries.json の "slides" から Instagram 投稿用の画像（1080x1350 PNG）を作る。

    python3 tools/render_slides.py <slug>      # 1件だけ
    python3 tools/render_slides.py             # slides を持つ全件

instagram/<slug>/01.png, 02.png ... と caption.txt を書き出す。
画像は Google Chrome のヘッドレスモードで撮る（フォントは Google Fonts から読む）。

slides の書き方（1枚ずつ）:
  {"type": "cover", "label": "SHOPS / UK", "kicker": "ロンドンの日本茶専門店",
   "title": "Tencha", "body": "A Japanese tea shop in London that carries natural tea."}
  {"type": "text", "section": "THE SHOP", "kicker": "お店について", "title": "Japanese tea\\nonly.",
   "body": "...", "items": ["...", "..."]}
  {"type": "grid", "section": "THE TEAS", "title": "From matcha to\\nfermented bancha.", "items": ["Matcha", ...]}
  {"type": "cta", "section": "FIND THEM", "kicker": "お店を訪ねる", "title": "Find them.",
   "body": "tencha.co.uk — shipping across the UK.", "box": "Send us a DM for more natural tea shops near you."}
背景は表紙が深緑、以降は生成り・深緑の交互（"theme": "dark" / "light" で指定もできる）。
表紙は images/directory/<slug>/logo.* があればロゴを載せる。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "entries.json"
OUT = ROOT / "instagram"
LOGOS = ROOT / "images" / "directory"
MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME = MAC_CHROME if Path(MAC_CHROME).exists() else shutil.which("google-chrome") or "chromium"
W, H = 1080, 1350
NO_SANDBOX = ["--no-sandbox"] if os.environ.get("CI") else []  # GitHub Actions 上の Chrome 用

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Source+Sans+3:wght@400;500&family=Noto+Serif+JP:wght@400;500&display=block');
*{margin:0;padding:0;box-sizing:border-box;}
html,body{width:1080px;height:1350px;overflow:hidden;}
.s{width:1080px;height:1350px;padding:96px 88px 84px;display:flex;flex-direction:column;position:relative;}
.dark{background:#232b22;color:#ecebe2;}
.light{background:#ecebe2;color:#232b22;}
.top{display:flex;justify-content:space-between;font-family:'Source Sans 3',sans-serif;font-size:27px;letter-spacing:.14em;}
.dark .top{color:#b7b48f;} .light .top{color:#6f6a4f;}
.main{flex:1;display:flex;flex-direction:column;justify-content:center;}
.kicker{font-family:'Noto Serif JP',serif;font-size:34px;letter-spacing:.08em;margin-bottom:26px;}
.dark .kicker{color:#b7b48f;} .light .kicker{color:#8a7f55;}
h1{font-family:'Source Serif 4',serif;font-weight:600;font-size:104px;line-height:1.08;letter-spacing:-.01em;white-space:pre-line;}
.k-cover h1{font-size:150px;}
.rule{width:110px;height:2px;margin:46px 0 40px;}
.dark .rule{background:#b7b48f;} .light .rule{background:#8a7f55;}
.body{font-family:'Source Serif 4',serif;font-size:42px;line-height:1.42;margin-top:34px;white-space:pre-line;}
.dark .body{color:#c9c7b6;} .light .body{color:#4d5048;}
.k-cover .body{margin-top:0;color:inherit;}
ul{list-style:none;margin-top:44px;}
li{font-family:'Source Sans 3',sans-serif;font-size:32px;line-height:1.4;padding:22px 0 22px 64px;position:relative;}
.dark li{border-top:1px solid rgba(236,235,226,.22);} .light li{border-top:1px solid rgba(35,43,34,.22);}
li:last-child{border-bottom:1px solid currentColor;border-bottom-color:inherit;}
.dark li:last-child{border-bottom:1px solid rgba(236,235,226,.22);} .light li:last-child{border-bottom:1px solid rgba(35,43,34,.22);}
li::before{content:"—";position:absolute;left:0;}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;margin-top:56px;}
.grid div{font-family:'Source Serif 4',serif;font-size:34px;line-height:1.2;text-align:center;padding:30px 12px;display:flex;align-items:center;justify-content:center;min-height:118px;}
.dark .grid div{border:2px solid #8f8c6c;} .light .grid div{border:2px solid #8a7f55;}
.box{margin-top:56px;padding:40px 44px;font-family:'Source Serif 4',serif;font-size:36px;line-height:1.45;}
.dark .box{border:2px solid #8f8c6c;} .light .box{border:2px solid #8a7f55;}
.box .handle{display:block;font-family:'Source Sans 3',sans-serif;font-size:29px;margin-top:18px;opacity:.75;}
.logo{width:240px;height:240px;object-fit:contain;margin-bottom:44px;}
.foot{display:flex;justify-content:space-between;font-family:'Source Sans 3',sans-serif;font-size:27px;letter-spacing:.03em;}
.dark .foot{color:#b7b48f;} .light .foot{color:#6f6a4f;}
"""


def rel(path):
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def find_logo(slug):
    for ext in (".png", ".webp", ".jpg", ".jpeg"):
        f = LOGOS / slug / ("logo" + ext)
        if f.exists():
            return f
    return None


def slide_html(slug, sl, n, total):
    kind = sl.get("type", "text")
    theme = sl.get("theme") or ("dark" if kind == "cover" or n % 2 == 1 else "light")
    left = sl.get("label") if kind == "cover" else f"{n - 1:02d} / {sl.get('section', '')}".rstrip(" /")
    parts = []
    if kind == "cover":
        logo = find_logo(slug)
        if logo:
            parts.append(f'<img class="logo" src="{logo.as_uri()}" alt="">')
    if sl.get("kicker"):
        parts.append(f'<p class="kicker">{escape(sl["kicker"])}</p>')
    parts.append(f'<h1>{escape(sl["title"])}</h1>')
    if kind == "cover":
        parts.append('<div class="rule"></div>')
    if sl.get("body"):
        parts.append(f'<p class="body">{escape(sl["body"])}</p>')
    if kind == "grid":
        parts.append('<div class="grid">' + "".join(f"<div>{escape(x)}</div>" for x in sl.get("items", [])) + "</div>")
    elif sl.get("items"):
        parts.append("<ul>" + "".join(f"<li>{escape(x)}</li>" for x in sl["items"]) + "</ul>")
    if sl.get("box"):
        parts.append(f'<div class="box">{escape(sl["box"])}<span class="handle">@japan_natural_tea</span></div>')
    right_foot = "Swipe →" if kind == "cover" else ""
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{CSS}</style></head>
<body><div class="s {theme} k-{kind}">
<div class="top"><span>{escape(left or "")}</span><span>{n} / {total}</span></div>
<div class="main">{"".join(parts)}</div>
<div class="foot"><span>Japan Natural Tea Association</span><span>{right_foot}</span></div>
</div></body></html>"""


def render(entry):
    slug, slides = entry["slug"], entry["slides"]
    out = OUT / slug
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("[0-9][0-9].png"):
        old.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        for i, sl in enumerate(slides, 1):
            src = Path(tmp) / f"{i:02d}.html"
            src.write_text(slide_html(slug, sl, i, len(slides)), encoding="utf-8")
            png = out / f"{i:02d}.png"
            subprocess.run(
                [CHROME, *NO_SANDBOX, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                 f"--window-size={W},{H}", "--virtual-time-budget=8000", f"--screenshot={png}", src.as_uri()],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            print("wrote", rel(png))
    if entry.get("caption"):
        (out / "caption.txt").write_text(entry["caption"].rstrip() + "\n", encoding="utf-8")
        print("wrote", rel(out / "caption.txt"))


def main():
    entries = json.loads(DATA.read_text(encoding="utf-8"))
    want = sys.argv[1:]
    targets = [e for e in entries if e.get("slides") and (not want or e["slug"] in want)]
    missing = set(want) - {e["slug"] for e in targets}
    assert not missing, f"slides のある項目が見つかりません: {sorted(missing)}"
    for e in targets:
        render(e)


if __name__ == "__main__":
    main()
