#!/usr/bin/env python3
"""Instagram 投稿の LP を posts/posts.json から生成する。

    python3 tools/build_posts.py

posts/<slug>/index.html（投稿ごとの LP）と posts/index.html（一覧）を書き出す。
生成物はそのまま commit する（GitHub Pages にビルド工程はない）。
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
LANGS = ("ja", "en", "fr")

KINDS = {
    "shop": {
        "label": {"ja": "ショップ紹介", "en": "Shop feature", "fr": "Boutique à la une"},
        "cta_title": {"ja": "あなたのお店も紹介します", "en": "We’d love to feature your shop", "fr": "Nous aimerions présenter votre boutique"},
        "cta_text": {
            "ja": "自然茶を扱う、または扱いたいショップ・カフェ・オンラインショップは、販売店登録フォームからご登録ください。",
            "en": "Shops, cafés and online stores that carry natural tea, or would like to, can register through the shop form.",
            "fr": "Les boutiques, cafés et boutiques en ligne qui proposent du thé naturel, ou souhaitent le faire, peuvent s’inscrire via le formulaire boutiques.",
        },
        "cta_button": {"ja": "販売店登録をする", "en": "Register your shop", "fr": "Inscrire votre boutique"},
        "cta_href": "/#register",
    },
    "producer": {
        "label": {"ja": "生産者紹介", "en": "Producer feature", "fr": "Producteur à la une"},
        "cta_title": {"ja": "あなたの農園も紹介します", "en": "We’d love to feature your farm", "fr": "Nous aimerions présenter votre exploitation"},
        "cta_text": {
            "ja": "無肥料・無農薬でお茶を育てている方は、生産者登録フォームからご登録ください。",
            "en": "If you grow tea with no fertilizer and no pesticides, register through the producer form.",
            "fr": "Si vous cultivez du thé sans engrais ni pesticides, inscrivez-vous via le formulaire producteurs.",
        },
        "cta_button": {"ja": "生産者登録をする", "en": "Register as a producer", "fr": "S’inscrire comme producteur"},
        "cta_href": "/#register",
    },
    "news": {
        "label": {"ja": "お知らせ", "en": "News", "fr": "Actualités"},
        "cta_title": {"ja": "自然茶の輪に、加わりませんか", "en": "Join the circle of natural tea", "fr": "Rejoignez le cercle du thé naturel"},
        "cta_text": {
            "ja": "協会ではメンバーを募集しています。活動の案内もいち早くお届けします。",
            "en": "The association is looking for members, who also hear about our activities first.",
            "fr": "L’association recherche des membres, qui sont aussi les premiers informés de nos activités.",
        },
        "cta_button": {"ja": "メンバーに応募する", "en": "Apply to become a member", "fr": "Devenir membre"},
        "cta_href": "/#join",
    },
}

UI = {
    "posts": {"ja": "投稿", "en": "Posts", "fr": "Publications"},
    "home": {"ja": "トップ", "en": "Home", "fr": "Accueil"},
    "list_title": {"ja": "Instagram の投稿から", "en": "From our Instagram", "fr": "Depuis notre Instagram"},
    "list_lead": {
        "ja": "協会の Instagram（@japan_natural_tea）で紹介した生産者・お店・活動を、ここにまとめています。",
        "en": "The growers, shops and activities we’ve featured on our Instagram (@japan_natural_tea), collected in one place.",
        "fr": "Les producteurs, boutiques et activités présentés sur notre Instagram (@japan_natural_tea), réunis en un seul endroit.",
    },
    "read": {"ja": "記事を読む", "en": "Read more", "fr": "Lire la suite"},
    "on_ig": {"ja": "Instagram で見る", "en": "View on Instagram", "fr": "Voir sur Instagram"},
    "back": {"ja": "投稿一覧へ戻る", "en": "Back to all posts", "fr": "Retour aux publications"},
    "follow": {"ja": "Instagram をフォロー", "en": "Follow us on Instagram", "fr": "Suivez-nous sur Instagram"},
}

NAV = [
    ("/#about", {"ja": "協会について", "en": "About", "fr": "À propos"}),
    ("/#natural", {"ja": "自然茶とは", "en": "Natural Tea", "fr": "Thé naturel"}),
    ("/#business", {"ja": "事業内容", "en": "Activities", "fr": "Activités"}),
    ("/directory/", {"ja": "生産者とショップ", "en": "Producers &amp; Shops", "fr": "Producteurs &amp; boutiques"}),
    ("/posts/", {"ja": "投稿", "en": "Posts", "fr": "Publications"}),
    ("/#org", {"ja": "協会概要", "en": "Overview", "fr": "Présentation"}),
    ("/#join", {"ja": "入会・お問い合わせ", "en": "Membership", "fr": "Adhésion"}),
]


def t(d):
    """3言語の span を並べる（d の値は HTML エスケープ済みの前提ではない）。"""
    return "".join(f'<span class="{l}-only">{escape(d[l], quote=False)}</span>' for l in LANGS)


def t_at(d, i):
    """d が言語ごとのリストのとき、i 番目を3言語の span にする。"""
    return t({l: d[l][i] for l in LANGS})


def t_raw(d):
    return "".join(f'<span class="{l}-only">{d[l]}</span>' for l in LANGS)


def fmt_date(iso):
    y, m, d = (int(x) for x in iso.split("-"))
    months_en = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    months_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    return {"ja": f"{y}年{m}月{d}日", "en": f"{months_en[m-1]} {d}, {y}", "fr": f"{d} {months_fr[m-1]} {y}"}


CSS = """
  :root{
    --green-900:#1f3326;--green-800:#2a4a35;--green-700:#35603f;--green-600:#4a7a54;
    --matcha:#8aab6e;--kinari:#f4f1e8;--kinari-2:#ece7d8;--paper:#faf8f1;
    --ink:#242a24;--ink-soft:#434b43;--gold:#a98c4b;--line:#d7d2c2;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:'Noto Serif JP',serif;color:var(--ink);background:var(--paper);line-height:1.9;-webkit-font-smoothing:antialiased;font-weight:400;}
  .ja-only{display:inline;}.en-only{display:none;}.fr-only{display:none;}
  body.lang-en,body.lang-fr{font-family:'Cormorant Garamond','Noto Serif JP',serif;font-size:17px;font-weight:500;}
  body.lang-en .ja-only,body.lang-fr .ja-only{display:none;}
  body.lang-en .en-only{display:inline;}
  body.lang-fr .fr-only{display:inline;}
  h1,h2,h3{font-family:'Noto Serif JP',serif;font-weight:500;}
  body.lang-en :is(h1,h2,h3),body.lang-fr :is(h1,h2,h3){font-family:'Cormorant Garamond',serif;font-weight:600;}
  a{color:inherit;text-decoration:none;}
  a:focus-visible,button:focus-visible{outline:2px solid var(--matcha);outline-offset:3px;border-radius:4px;}

  header{position:fixed;top:0;left:0;width:100%;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:18px 6vw;background:rgba(250,248,241,.85);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);}
  .brand{display:flex;align-items:center;gap:14px;}
  .brand .mark{width:42px;height:42px;border-radius:50%;background:var(--green-700);display:flex;align-items:center;justify-content:center;color:var(--kinari);font-family:'Noto Serif JP',serif;font-size:20px;flex-shrink:0;}
  .brand .name{line-height:1.3;}
  .brand .name b{font-family:'Noto Serif JP',serif;font-weight:600;font-size:15px;letter-spacing:.04em;color:var(--green-800);display:block;}
  .brand .name span{font-size:11px;letter-spacing:.18em;color:var(--ink-soft);text-transform:uppercase;}
  nav.main{display:flex;align-items:center;gap:clamp(16px,1.9vw,28px);}
  nav.main a.navlink{white-space:nowrap;font-size:13px;letter-spacing:.06em;color:var(--ink-soft);transition:color .2s;}
  nav.main a.navlink:hover{color:var(--green-700);}
  nav.main a.navlink[aria-current="page"]{color:var(--green-800);border-bottom:1px solid var(--matcha);}
  .lang-toggle{display:flex;border:1px solid var(--green-600);border-radius:999px;overflow:hidden;font-size:12px;letter-spacing:.05em;}
  .lang-toggle button{background:transparent;border:none;cursor:pointer;padding:6px 13px;white-space:nowrap;color:var(--green-700);font-family:inherit;transition:.2s;}
  .lang-toggle button.active{background:var(--green-700);color:var(--kinari);}
  .menu-btn{display:none;background:none;border:none;cursor:pointer;font-size:24px;color:var(--green-800);}
  @media(max-width:1180px){
    nav.main{position:fixed;top:0;right:0;height:100vh;width:74%;max-width:320px;flex-direction:column;justify-content:center;gap:26px;background:var(--green-900);transform:translateX(100%);transition:transform .35s;padding:40px;}
    nav.main.open{transform:none;}
    nav.main a.navlink{color:var(--kinari);font-size:16px;}
    nav.main a.navlink[aria-current="page"]{color:var(--matcha);}
    .menu-btn{display:block;z-index:120;}
    .menu-btn.open{color:var(--kinari);}
    nav.main .lang-toggle{border-color:var(--matcha);}
    nav.main .lang-toggle button{color:var(--kinari);}
    nav.main .lang-toggle button.active{background:var(--matcha);color:var(--green-900);}
  }

  .page-head{background:radial-gradient(circle at 75% 20%,var(--green-700),var(--green-900));color:var(--kinari);padding:clamp(130px,16vw,180px) 6vw clamp(56px,7vw,84px);}
  .wrap{max-width:1080px;margin:0 auto;}
  .crumb{font-size:13px;letter-spacing:.08em;color:var(--matcha);margin-bottom:20px;}
  .crumb a{border-bottom:1px solid rgba(138,171,110,.5);}
  .crumb a:hover{color:var(--kinari);}
  .meta{font-size:14px;letter-spacing:.06em;color:var(--matcha);margin-bottom:14px;}
  .page-head h1{font-size:clamp(28px,4.4vw,48px);line-height:1.4;letter-spacing:.02em;margin-bottom:20px;max-width:860px;}
  .page-head p.lead{max-width:680px;font-size:clamp(15px,1.7vw,18px);color:rgba(244,241,232,.88);}

  section.block{padding:clamp(56px,8vw,100px) 6vw;}
  .post-grid{display:grid;grid-template-columns:minmax(0,540px) minmax(0,1fr);gap:clamp(32px,5vw,64px);align-items:start;}
  .ig-frame{max-width:540px;width:100%;}
  .ig-frame .instagram-media{margin:0!important;min-width:0!important;width:100%!important;}
  .ig-fallback{display:block;border:1px solid var(--line);border-radius:8px;padding:28px;text-align:center;color:var(--green-700);background:#fdfcf8;}
  .article p{font-size:16px;line-height:2;margin-bottom:1.2em;}
  body.lang-en .article p,body.lang-fr .article p{font-size:18px;}
  .points{list-style:none;border-top:1px solid var(--line);margin:28px 0;}
  .points li{padding:12px 0 12px 28px;border-bottom:1px solid var(--line);position:relative;font-size:15px;}
  .points li::before{content:"";position:absolute;left:0;top:1.45em;width:14px;height:1px;background:var(--matcha);}
  .links{display:flex;flex-wrap:wrap;gap:10px 22px;font-size:15px;margin-bottom:36px;}
  .links a{color:var(--green-600);border-bottom:1px solid var(--matcha);padding-bottom:1px;}
  .links a:hover{color:var(--green-800);}
  .cta{background:var(--kinari);border:1px solid var(--line);border-radius:8px;padding:clamp(24px,3vw,34px);}
  .cta h2{font-size:clamp(19px,2.2vw,23px);color:var(--green-800);margin-bottom:8px;}
  .cta p{font-size:15px;color:var(--ink-soft);margin-bottom:18px;}
  .btn{display:inline-block;padding:11px 26px;border-radius:999px;font-size:14px;letter-spacing:.06em;background:var(--green-700);color:var(--kinari);transition:background .2s;}
  .btn:hover{background:var(--green-800);}
  .back{margin-top:44px;font-size:15px;}
  .back a{color:var(--green-700);border-bottom:1px solid var(--matcha);}
  @media(max-width:900px){.post-grid{grid-template-columns:minmax(0,1fr);}.ig-frame{margin:0 auto;}}

  .post-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:28px;}
  .post-card{background:#fdfcf8;border:1px solid var(--line);border-radius:8px;padding:clamp(24px,3vw,32px);display:flex;flex-direction:column;transition:border-color .2s;}
  .post-card:hover{border-color:var(--matcha);}
  .post-card .meta{color:var(--gold);font-size:13px;margin-bottom:10px;}
  .post-card h2{font-size:clamp(19px,2.2vw,22px);color:var(--green-800);line-height:1.5;margin-bottom:12px;}
  .post-card p{font-size:15px;color:var(--ink-soft);margin-bottom:18px;}
  .post-card .more{margin-top:auto;font-size:14px;color:var(--green-600);}
  .follow{margin-top:44px;font-size:15px;}
  .follow a{color:var(--green-700);border-bottom:1px solid var(--matcha);}

  footer{background:var(--green-900);color:rgba(244,241,232,.75);padding:60px 6vw 34px;}
  .foot-top{display:flex;justify-content:space-between;flex-wrap:wrap;gap:30px;max-width:1080px;margin:0 auto 40px;}
  .foot-brand b{font-family:'Noto Serif JP',serif;color:var(--kinari);font-size:17px;display:block;margin-bottom:6px;}
  body.lang-en .foot-brand b,body.lang-fr .foot-brand b{font-family:'Cormorant Garamond',serif;}
  .foot-brand span{font-size:12px;letter-spacing:.15em;}
  .foot-links{display:flex;gap:28px;flex-wrap:wrap;font-size:13px;}
  .foot-links a:hover{color:var(--kinari);}
  .foot-bottom{max-width:1080px;margin:0 auto;border-top:1px solid rgba(244,241,232,.15);padding-top:22px;font-size:12px;letter-spacing:.05em;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;}
"""

SCRIPT = """
<script>
  function setLang(l){
    document.body.classList.remove('lang-ja','lang-en','lang-fr');
    document.body.classList.add('lang-'+l);
    document.documentElement.lang = l;
    ['ja','en','fr'].forEach(function(k){ document.getElementById('btn-'+k).classList.toggle('active', k===l); });
    try{localStorage.setItem('jnta_lang', l);}catch(e){}
  }
  (function(){
    var saved=null;
    try{saved=localStorage.getItem('jnta_lang');}catch(e){}
    setLang(saved || 'en');
  })();
  var nav=document.getElementById('nav'), mb=document.getElementById('menuBtn');
  mb.addEventListener('click', function(){ nav.classList.toggle('open'); mb.classList.toggle('open'); mb.textContent = nav.classList.contains('open')?'✕':'☰'; });
  nav.querySelectorAll('a.navlink').forEach(function(a){ a.addEventListener('click', function(){ nav.classList.remove('open'); mb.classList.remove('open'); mb.textContent='☰'; }); });
</script>
"""


def page(title, description, canonical, body, extra_head=""):
    current = ' aria-current="page"'
    nav = "\n".join(
        f'    <a class="navlink" href="{href}"{current if href == "/posts/" else ""}>{t_raw(label)}</a>'
        for href, label in NAV
    )
    foot = "\n".join(f'      <a href="{href}">{t_raw(label)}</a>' for href, label in [("/", UI["home"])] + NAV)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;600;700&family=Cormorant+Garamond:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
{extra_head}</head>
<body class="lang-en">
<!-- tools/build_posts.py で生成。直接編集せず posts/posts.json を直して再生成する -->

<header>
  <a href="/" class="brand">
    <span class="mark">茶</span>
    <span class="name">
      <b><span class="ja-only">日本自然茶協会</span><span class="en-only">Japan Natural Tea</span><span class="fr-only">Japan Natural Tea</span></b>
      <span class="ja-only">JAPAN NATURAL TEA ASSOCIATION</span>
      <span class="en-only">ASSOCIATION · 日本自然茶協会</span><span class="fr-only">ASSOCIATION · 日本自然茶協会</span>
    </span>
  </a>
  <nav class="main" id="nav">
{nav}
    <div class="lang-toggle">
      <button id="btn-ja" onclick="setLang('ja')">日本語</button>
      <button id="btn-en" class="active" onclick="setLang('en')">EN</button>
      <button id="btn-fr" onclick="setLang('fr')">FR</button>
    </div>
  </nav>
  <button class="menu-btn" id="menuBtn" aria-label="menu">☰</button>
</header>

<main>
{body}
</main>

<footer>
  <div class="foot-top">
    <div class="foot-brand">
      <b><span class="ja-only">一般社団法人 日本自然茶協会</span><span class="en-only">Japan Natural Tea Association</span><span class="fr-only">Japan Natural Tea Association</span></b>
      <span class="ja-only">JAPAN NATURAL TEA ASSOCIATION</span>
      <span class="en-only">一般社団法人 日本自然茶協会</span><span class="fr-only">一般社団法人 日本自然茶協会</span>
    </div>
    <div class="foot-links">
{foot}
    </div>
  </div>
  <div class="foot-bottom">
    <span>© 2026 <span class="ja-only">一般社団法人 日本自然茶協会</span><span class="en-only">Japan Natural Tea Association</span><span class="fr-only">Japan Natural Tea Association</span></span>
    <span class="ja-only">奈良県奈良市都祁吐山町920</span>
    <span class="en-only">Nara City, Nara, Japan</span><span class="fr-only">Ville de Nara, Nara, Japon</span>
  </div>
</footer>
{SCRIPT}</body>
</html>
"""


def ig_permalink(url):
    url = url.split("?")[0]
    return url if url.endswith("/") else url + "/"


def render_post(p):
    kind = KINDS[p["kind"]]
    date = fmt_date(p["date"])
    ig = ig_permalink(p["instagram"])
    paras = "\n".join(f"        <p>{t_at(p['body'], i)}</p>" for i in range(len(p["body"]["ja"])))
    points = ""
    if p.get("points"):
        items = "\n".join(f"          <li>{t_at(p['points'], i)}</li>" for i in range(len(p["points"]["ja"])))
        points = f'        <ul class="points">\n{items}\n        </ul>\n'
    links = "".join(
        f'\n          <a href="{escape(x["url"])}" target="_blank" rel="noopener">{escape(x["label"])}</a>' for x in p.get("links", [])
    )
    links += f'\n          <a href="{ig}" target="_blank" rel="noopener">{t(UI["on_ig"])}</a>'
    body = f"""<div class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="/">{t(UI["home"])}</a>　/　<a href="/posts/">{t(UI["posts"])}</a></p>
    <p class="meta">{t(kind["label"])}　{t(date)}</p>
    <h1>{t(p["title"])}</h1>
    <p class="lead">{t(p["lead"])}</p>
  </div>
</div>

<section class="block">
  <div class="wrap post-grid">
    <div class="ig-frame">
      <blockquote class="instagram-media" data-instgrm-permalink="{ig}" data-instgrm-version="14">
        <a class="ig-fallback" href="{ig}" target="_blank" rel="noopener">{t(UI["on_ig"])}</a>
      </blockquote>
    </div>
    <article class="article">
{paras}
{points}        <div class="links">{links}
        </div>
        <div class="cta">
          <h2>{t(kind["cta_title"])}</h2>
          <p>{t(kind["cta_text"])}</p>
          <a class="btn" href="{kind["cta_href"]}">{t(kind["cta_button"])}</a>
        </div>
        <p class="back"><a href="/posts/">{t(UI["back"])}</a></p>
    </article>
  </div>
</section>"""
    title = f'{p["title"]["ja"]} | 日本自然茶協会 Japan Natural Tea Association'
    desc = f'{p["lead"]["ja"]} {p["lead"]["en"]}'
    extra = '<script async src="https://www.instagram.com/embed.js"></script>\n'
    return page(title, desc, f"https://naturaltea.jp/posts/{p['slug']}/", body, extra)


def render_list(posts):
    cards = []
    for p in posts:
        kind = KINDS[p["kind"]]
        cards.append(f"""      <a class="post-card" href="/posts/{p["slug"]}/">
        <p class="meta">{t(kind["label"])}　{t(fmt_date(p["date"]))}</p>
        <h2>{t(p["title"])}</h2>
        <p>{t(p["lead"])}</p>
        <span class="more">{t(UI["read"])}</span>
      </a>""")
    body = f"""<div class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="/">{t(UI["home"])}</a>　/　{t(UI["posts"])}</p>
    <h1>{t(UI["list_title"])}</h1>
    <p class="lead">{t(UI["list_lead"])}</p>
  </div>
</div>

<section class="block">
  <div class="wrap">
    <div class="post-list">
{chr(10).join(cards)}
    </div>
    <p class="follow"><a href="https://www.instagram.com/japan_natural_tea/" target="_blank" rel="noopener">{t(UI["follow"])}（@japan_natural_tea）</a></p>
  </div>
</section>"""
    return page(
        "投稿 | 日本自然茶協会 Japan Natural Tea Association",
        "日本自然茶協会の Instagram で紹介した生産者・お店・活動のまとめ。",
        "https://naturaltea.jp/posts/",
        body,
    )


def main():
    posts = json.loads((POSTS_DIR / "posts.json").read_text(encoding="utf-8"))
    slugs = [p["slug"] for p in posts]
    assert len(slugs) == len(set(slugs)), "slug が重複しています"
    for p in posts:
        assert p["kind"] in KINDS, f'{p["slug"]}: kind は {list(KINDS)} のどれか'
        for key in ("title", "lead", "body"):
            assert set(p[key]) >= set(LANGS), f'{p["slug"]}: {key} に ja/en/fr が必要'
        assert len({len(p["body"][l]) for l in LANGS}) == 1, f'{p["slug"]}: body の段落数を3言語でそろえる'
        if p.get("points"):
            assert len({len(p["points"][l]) for l in LANGS}) == 1, f'{p["slug"]}: points の数を3言語でそろえる'
    posts.sort(key=lambda p: p["date"], reverse=True)
    for p in posts:
        out = POSTS_DIR / p["slug"] / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(render_post(p), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))
    (POSTS_DIR / "index.html").write_text(render_list(posts), encoding="utf-8")
    print("wrote posts/index.html")


if __name__ == "__main__":
    main()
