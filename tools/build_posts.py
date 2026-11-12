#!/usr/bin/env python3
"""生産者・ショップのカードと Instagram 投稿を tools/entries.json からサイトに反映する。

    python3 tools/build_posts.py

投稿の kind で行き先が変わる:
  producer → producers/index.html（生産者のページ）にカードと日本地図のピンを差し込む
  shop     → shops/index.html（ショップのページ）にカードと世界地図のピンを差し込む
             images/directory/<slug>/ に logo / portrait / photo（.jpg .jpeg .png .webp）があればカードに表示する
             photo がなく投稿画像（instagram/<slug>/01.png）があれば、表紙をカードの写真に使う
             ピンの位置は "geo": [{"q": "静岡県牧之原市", "lat": 34.74, "lng": 138.22}]（市町村の単位まで）。
             geo がなければ、国内は region（都道府県）の県庁所在地に立てる。海外で geo がないものは地図に出ない
             生産者の「地図を開く」は geo の市町村で Google マップを開く（番地は出さない）。ショップは "map"（住所）があればそれを使う
  旧 directory/index.html は、生産者・ショップのページへ移すだけのページとして毎回書き出す
  education → learn/<slug>/index.html（独立した LP）を作り、learn/index.html（一覧）に載せる
             投稿画像（instagram/<slug>/*.png）があればそれを並べ、なければ Instagram の埋め込みを使う
  tools/course.json → learn/basics/（自然茶基礎コース。目次と各回のページ。各回は Instagram の動画1本＋読みもの）
生成物はそのまま commit する（GitHub Pages にビルド工程はない）。
"""
import json
import re
from html import escape
from urllib.parse import quote
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "tools" / "entries.json"
IMAGES = ROOT / "images" / "directory"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")
SLIDES = ROOT / "instagram"  # tools/render_slides.py が書き出す投稿画像 instagram/<slug>/01.png ...
DIRECTORY = ROOT / "directory" / "index.html"  # 旧ページ（移動の案内だけ）
PAGES = {"producer": ROOT / "producers" / "index.html", "shop": ROOT / "shops" / "index.html"}
LEARN_DIR = ROOT / "learn"
LANGS = ("ja", "en", "fr")
DIRECTORY_KINDS = ("producer", "shop")

# 地図の図法（tools/make_maps.py と共通）。正距円筒図法。日本地図は沖縄・奄美を左上の囲みに入れる
MAPS = {
    "japan": {"w": 1000, "h": 1096, "lon0": 128.6, "lat0": 45.6, "k": 70.2, "cos": 0.809,
              "inset": {"lat_max": 29.5, "lng_max": 131.5, "lon0": 122.8, "lat0": 28.9, "x": 10, "y": 10, "w": 432, "h": 351}},
    "world": {"w": 1000, "h": 389, "lon0": -180.0, "lat0": 83.0, "k": 1000 / 360, "cos": 1.0},
}
MAP_OF = {"producer": "japan", "shop": "world"}


def project(m, lat, lng):
    """緯度経度 → 地図の SVG 座標（px）。"""
    i = m.get("inset")
    if i and lat < i["lat_max"] and lng < i["lng_max"]:
        return i["x"] + (lng - i["lon0"]) * m["k"] * m["cos"], i["y"] + (i["lat0"] - lat) * m["k"]
    return (lng - m["lon0"]) * m["k"] * m["cos"], (m["lat0"] - lat) * m["k"]


# geo がないときのピン（都道府県庁の位置。国土地理院の住所検索で取得）
PREF = {
    "北海道": (43.06, 141.35), "青森県": (40.82, 140.74), "岩手県": (39.70, 141.15), "宮城県": (38.27, 140.87),
    "秋田県": (39.72, 140.10), "山形県": (38.24, 140.36), "福島県": (37.75, 140.47), "茨城県": (36.34, 140.45),
    "栃木県": (36.57, 139.88), "群馬県": (36.39, 139.06), "埼玉県": (35.86, 139.65), "千葉県": (35.61, 140.12),
    "東京都": (35.69, 139.69), "神奈川県": (35.45, 139.64), "新潟県": (37.90, 139.02), "富山県": (36.70, 137.21),
    "石川県": (36.59, 136.63), "福井県": (36.07, 136.22), "山梨県": (35.66, 138.57), "長野県": (36.65, 138.18),
    "岐阜県": (35.39, 136.72), "静岡県": (34.98, 138.38), "愛知県": (35.18, 136.91), "三重県": (34.73, 136.51),
    "滋賀県": (35.00, 135.87), "京都府": (35.02, 135.76), "大阪府": (34.69, 135.52), "兵庫県": (34.69, 135.18),
    "奈良県": (34.69, 135.83), "和歌山県": (34.23, 135.17), "鳥取県": (35.50, 134.24), "島根県": (35.47, 133.05),
    "岡山県": (34.66, 133.93), "広島県": (34.40, 132.46), "山口県": (34.19, 131.47), "徳島県": (34.07, 134.56),
    "香川県": (34.34, 134.04), "愛媛県": (33.84, 132.77), "高知県": (33.56, 133.53), "福岡県": (33.61, 130.42),
    "佐賀県": (33.25, 130.30), "長崎県": (32.74, 129.87), "熊本県": (32.79, 130.74), "大分県": (33.24, 131.61),
    "宮崎県": (31.91, 131.42), "鹿児島県": (31.56, 130.56), "沖縄県": (26.21, 127.68),
}
JAPAN = {"ja": "日本", "en": "Japan", "fr": "Japon"}

KINDS = {
    "education": {
        "label": {"ja": "学び", "en": "Learn", "fr": "Apprendre"},
        "cta_title": {"ja": "自然茶の輪に、加わりませんか", "en": "Join the circle of natural tea", "fr": "Rejoignez le cercle du thé naturel"},
        "cta_text": {
            "ja": "協会ではメンバーを募集しています。オンラインコースやツアーの案内も、いち早くお届けします。",
            "en": "The association is looking for members, who also hear first about our online courses and tours.",
            "fr": "L’association recherche des membres, qui sont aussi les premiers informés de nos cours en ligne et de nos circuits.",
        },
        "cta_button": {"ja": "メンバーに応募する", "en": "Apply to become a member", "fr": "Devenir membre"},
        "cta_href": "/#join",
    },
}

UI = {
    "learn": {"ja": "学び", "en": "Learn", "fr": "Apprendre"},
    "home": {"ja": "トップ", "en": "Home", "fr": "Accueil"},
    "list_title": {"ja": "自然茶を学ぶ", "en": "Learn about natural tea", "fr": "Apprendre le thé naturel"},
    "list_lead": {
        "ja": "協会の Instagram（@japan_natural_tea）で発信した、自然茶や日本茶について学べる投稿を、読みものとしてまとめています。",
        "en": "Posts from our Instagram (@japan_natural_tea) about natural tea and Japanese tea, collected here as articles.",
        "fr": "Les publications de notre Instagram (@japan_natural_tea) sur le thé naturel et le thé japonais, réunies ici sous forme d’articles.",
    },
    "empty": {
        "ja": "最初の記事を準備しています。公開までは Instagram でご覧ください。",
        "en": "Our first article is on its way. Until then, find us on Instagram.",
        "fr": "Notre premier article est en préparation. En attendant, retrouvez-nous sur Instagram.",
    },
    "read": {"ja": "記事を読む", "en": "Read more", "fr": "Lire la suite"},
    "on_ig": {"ja": "Instagram で見る", "en": "View on Instagram", "fr": "Voir sur Instagram"},
    "ig_feature": {"ja": "紹介投稿を見る", "en": "See our Instagram post", "fr": "Voir notre publication"},
    "map": {"ja": "地図を開く", "en": "Open map", "fr": "Ouvrir la carte"},
    "back": {"ja": "学びの記事一覧へ", "en": "Back to all articles", "fr": "Retour aux articles"},
    "follow": {"ja": "Instagram をフォロー", "en": "Follow us on Instagram", "fr": "Suivez-nous sur Instagram"},
    "shop": {"ja": "ショップ", "en": "Shop", "fr": "Boutique"},
    "producer": {"ja": "生産者", "en": "Producer", "fr": "Producteur"},
    "course": {"ja": "無料オンラインコース", "en": "Free online course", "fr": "Cours en ligne gratuit"},
    "lessons_n": {"ja": "全{n}回", "en": "{n} lessons", "fr": "{n} leçons"},
    "lesson_n": {"ja": "第{n}回", "en": "Lesson {n}", "fr": "Leçon {n}"},
    "start": {"ja": "第1回からはじめる", "en": "Start with lesson 1", "fr": "Commencer par la leçon 1"},
    "open_course": {"ja": "コースを見る", "en": "View the course", "fr": "Voir le cours"},
    "takeaway": {"ja": "この回のひとこと", "en": "Key takeaway", "fr": "À retenir"},
    "sources": {"ja": "出典", "en": "Sources", "fr": "Sources"},
    "prev": {"ja": "前の回", "en": "Previous", "fr": "Précédente"},
    "next": {"ja": "次の回", "en": "Next", "fr": "Suivante"},
    "toc": {"ja": "コースの目次へ", "en": "All lessons", "fr": "Toutes les leçons"},
    "watch_ig": {"ja": "Instagram で動画を見る", "en": "Watch on Instagram", "fr": "Voir la vidéo sur Instagram"},
    "course_note": {
        "ja": "各回は1〜2分の動画と、数分で読める文章です。どの回からでも見られますが、順番に見ると、自然茶の考え方から日本茶のいままでがつながります。",
        "en": "Each lesson is a one- or two-minute video and a few minutes of reading. You can start anywhere, but taken in order they lead from the idea of natural tea to where Japanese tea stands today.",
        "fr": "Chaque leçon associe une vidéo d’une ou deux minutes et quelques minutes de lecture. Vous pouvez commencer où vous voulez, mais dans l’ordre, elles mènent de l’idée du thé naturel à la situation actuelle du thé japonais.",
    },
}

NAV = [
    ("/about/", {"ja": "協会について", "en": "About", "fr": "À propos"}),
    ("/#natural", {"ja": "自然茶とは", "en": "Natural Tea", "fr": "Thé naturel"}),
    ("/producers/", {"ja": "生産者", "en": "Producers", "fr": "Producteurs"}),
    ("/shops/", {"ja": "ショップ", "en": "Shops", "fr": "Boutiques"}),
    ("/learn/", {"ja": "学び", "en": "Learn", "fr": "Apprendre"}),
    ("/#org", {"ja": "協会概要", "en": "Overview", "fr": "Présentation"}),
    ("/#join", {"ja": "入会・お問い合わせ", "en": "Membership", "fr": "Adhésion"}),
]
FOOT_EXTRA = [  # フッターだけに出す、協会ページ内の欄
    ("/about/#business", {"ja": "事業内容", "en": "Activities", "fr": "Activités"}),
    ("/about/#upcoming", {"ja": "準備中の活動", "en": "Coming soon", "fr": "À venir"}),
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
    --green-900:#2e3b33;--green-800:#3b4a40;--green-700:#4a5a4f;--green-600:#5d6e62;
    --matcha:#8aab6e;--kinari:#f4f1e8;--kinari-2:#ece7d8;--paper:#faf8f1;
    --ink:#242a24;--ink-soft:#434b43;--gold:#a98c4b;--line:#d7d2c2;
  }
  *{margin:0;padding:0;box-sizing:border-box;}
  body{font-family:'Sawarabi Mincho',serif;color:var(--ink);background:var(--paper);line-height:1.9;-webkit-font-smoothing:antialiased;font-weight:400;}
  .ja-only{display:inline;}.en-only{display:none;}.fr-only{display:none;}
  body.lang-ja{font-synthesis:none;}
  body.lang-en,body.lang-fr{font-family:'Cormorant Garamond','Sawarabi Mincho',serif;font-size:17px;font-weight:500;}
  body.lang-en .ja-only,body.lang-fr .ja-only{display:none;}
  body.lang-en .en-only{display:inline;}
  body.lang-fr .fr-only{display:inline;}
  h1,h2,h3{font-family:'Sawarabi Mincho',serif;font-weight:500;}
  body.lang-en :is(h1,h2,h3),body.lang-fr :is(h1,h2,h3){font-family:'Cormorant Garamond',serif;font-weight:600;}
  a{color:inherit;text-decoration:none;}
  a:focus-visible,button:focus-visible{outline:2px solid var(--matcha);outline-offset:3px;border-radius:4px;}

  header{position:fixed;top:0;left:0;width:100%;z-index:100;display:flex;align-items:center;justify-content:space-between;padding:18px 6vw;background:rgba(250,248,241,.85);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);}
  .brand{display:flex;align-items:center;gap:14px;}
  .brand .mark{width:42px;height:42px;border-radius:50%;background:var(--green-700);display:flex;align-items:center;justify-content:center;color:var(--kinari);font-family:'Sawarabi Mincho',serif;font-size:20px;flex-shrink:0;}
  .brand .name{line-height:1.3;}
  .brand .name b{font-family:'Sawarabi Mincho',serif;font-weight:600;font-size:15px;letter-spacing:.04em;color:var(--green-800);display:block;}
  .brand .name span{font-size:11px;letter-spacing:.18em;color:var(--ink-soft);text-transform:uppercase;}
  .brand-logo{height:40px;width:auto;display:block;}
  header{column-gap:32px;}
  @media(max-width:620px){.brand-logo{height:32px;}}
  .foot-brand img{width:150px;height:auto;display:block;}
  nav.main{display:flex;align-items:center;gap:clamp(16px,1.9vw,28px);}
  @media(max-width:1440px){.brand-logo{height:34px;} nav.main{gap:clamp(14px,1.4vw,28px);}}
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

  .page-head{background:var(--green-900);color:var(--kinari);padding:clamp(130px,16vw,180px) 6vw clamp(56px,7vw,84px);}
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
  .slides{display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory;border-radius:8px;max-width:540px;}
  .slides img{flex:0 0 100%;width:100%;aspect-ratio:4/5;object-fit:cover;scroll-snap-align:start;border-radius:8px;}
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
  @media(max-width:900px){.post-grid{grid-template-columns:minmax(0,1fr);}.ig-frame,.slides{margin:0 auto;}}

  .post-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:28px;}
  .post-card{background:#fdfcf8;border:1px solid var(--line);border-radius:8px;padding:clamp(24px,3vw,32px);display:flex;flex-direction:column;transition:border-color .2s;}
  .post-card:hover{border-color:var(--matcha);}
  .post-card .meta{color:var(--gold);font-size:13px;margin-bottom:10px;}
  .post-card h2{font-size:clamp(19px,2.2vw,22px);color:var(--green-800);line-height:1.5;margin-bottom:12px;}
  .post-card p{font-size:15px;color:var(--ink-soft);margin-bottom:18px;}
  .post-card .more{margin-top:auto;font-size:14px;color:var(--green-600);}
  .empty{font-size:16px;color:var(--ink-soft);}
  .follow{margin-top:44px;font-size:15px;}
  .follow a{color:var(--green-700);border-bottom:1px solid var(--matcha);}

  .course-card{display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:18px 32px;background:var(--green-900);color:var(--kinari);border-radius:8px;padding:clamp(26px,3.4vw,40px);margin-bottom:36px;}
  .course-card .meta{color:var(--matcha);margin-bottom:8px;}
  .course-card h2{font-size:clamp(22px,2.8vw,30px);line-height:1.4;margin-bottom:10px;}
  .course-card p{font-size:15px;color:rgba(244,241,232,.85);max-width:640px;}
  .course-card .btn{background:var(--matcha);color:var(--green-900);white-space:nowrap;}
  .course-card .btn:hover{background:var(--kinari);}
  @media(max-width:700px){.course-card{grid-template-columns:minmax(0,1fr);}.course-card .btn{justify-self:start;}}
  .page-head .btn{margin-top:30px;background:var(--matcha);color:var(--green-900);}
  .page-head .btn:hover{background:var(--kinari);}

  .lessons{list-style:none;counter-reset:lesson;max-width:820px;border-top:1px solid var(--line);}
  .lessons li a{display:grid;grid-template-columns:3.2em minmax(0,1fr);gap:0 18px;padding:24px 4px;border-bottom:1px solid var(--line);transition:background .2s;}
  .lessons li a:hover{background:#fdfcf8;}
  .lessons .num{font-family:'Cormorant Garamond',serif;font-size:34px;line-height:1.1;color:var(--gold);}
  .lessons h2{font-size:clamp(18px,2vw,21px);color:var(--green-800);line-height:1.5;margin-bottom:4px;}
  .lessons p{font-size:15px;color:var(--ink-soft);}
  .course-note{max-width:820px;margin-top:36px;font-size:15px;color:var(--ink-soft);}

  .lesson-grid{display:grid;grid-template-columns:minmax(0,340px) minmax(0,1fr);gap:clamp(32px,5vw,64px);align-items:start;}
  .lesson-media{position:sticky;top:110px;}
  .reel{position:relative;aspect-ratio:9/16;overflow:hidden;border-radius:8px;background:#000;container-type:inline-size;}
  .reel .instagram-media{position:absolute!important;top:-54px!important;left:-21.112cqw!important;width:142.224cqw!important;min-width:0!important;max-width:none!important;height:calc(177.78cqw + 400px)!important;margin:0!important;border:0!important;border-radius:0!important;box-shadow:none!important;}
  .lesson-media .on-ig{display:inline-block;margin-top:12px;font-size:14px;color:var(--green-600);border-bottom:1px solid var(--matcha);}
  .takeaway{margin:8px 0 34px;padding:22px 0 22px 26px;border-left:2px solid var(--matcha);}
  .takeaway small{display:block;font-size:13px;letter-spacing:.08em;color:var(--gold);margin-bottom:6px;}
  .takeaway p{font-size:clamp(20px,2.4vw,26px)!important;line-height:1.6!important;color:var(--green-800);margin:0!important;}
  .sources{font-size:13px;color:var(--ink-soft);margin:-8px 0 34px;}
  .sources a{color:var(--green-600);border-bottom:1px solid var(--matcha);}
  .pager{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;border-top:1px solid var(--line);padding-top:22px;margin-top:8px;}
  .pager a{display:block;max-width:48%;font-size:14px;color:var(--ink-soft);}
  .pager a b{display:block;font-weight:500;font-size:16px;color:var(--green-800);}
  .pager a.next{text-align:right;margin-left:auto;}
  .pager a:hover b{color:var(--green-600);}
  .toc{margin-top:30px;font-size:15px;}
  .toc a{color:var(--green-700);border-bottom:1px solid var(--matcha);}
  @media(max-width:900px){.lesson-grid{grid-template-columns:minmax(0,1fr);}.lesson-media{position:static;max-width:340px;width:100%;margin:0 auto;}.pager a{max-width:100%;}}

  footer{background:var(--green-900);color:rgba(244,241,232,.75);padding:60px 6vw 34px;}
  .foot-top{display:flex;justify-content:space-between;flex-wrap:wrap;gap:30px;max-width:1080px;margin:0 auto 40px;}
  .foot-brand b{font-family:'Sawarabi Mincho',serif;color:var(--kinari);font-size:17px;display:block;margin-bottom:6px;}
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
        f'    <a class="navlink" href="{href}"{current if href == "/learn/" else ""}>{t_raw(label)}</a>'
        for href, label in NAV
    )
    foot = "\n".join(f'      <a href="{href}">{t_raw(label)}</a>' for href, label in [("/", UI["home"])] + NAV[:1] + FOOT_EXTRA + NAV[1:])
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:site_name" content="Japan Natural Tea Association 日本自然茶協会">
<meta property="og:image" content="https://naturaltea.jp/assets/logo/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sawarabi+Mincho&family=Cormorant+Garamond:wght@400;500;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
{extra_head}</head>
<body class="lang-en">
<!-- tools/build_posts.py で生成。直接編集せず tools/entries.json を直して再生成する -->

<header>
  <a href="/" class="brand">
    <img class="brand-logo" src="/assets/logo/jnta-logo-horizontal.svg" width="806" height="108" alt="Japan Natural Tea Association 日本自然茶協会">
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
    <div class="foot-brand"><img src="/assets/logo/jnta-logo-stacked-light.svg" width="483" height="486" alt="Japan Natural Tea Association 日本自然茶協会" loading="lazy"></div>
    <div class="foot-links">
{foot}
    </div>
  </div>
  <div class="foot-bottom">
    <span>© 2026 <span class="ja-only">一般社団法人 日本自然茶協会（JANATEA）</span><span class="en-only">Japan Natural Tea Association (JANATEA)</span><span class="fr-only">Japan Natural Tea Association (JANATEA)</span></span>
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


def links_html(p, ig_label=None):
    out = "".join(
        f'\n          <a href="{escape(x["url"])}" target="_blank" rel="noopener">{escape(x["label"])}</a>' for x in p.get("links", [])
    )
    # 生産者は市町村まで（番地は出さない）。ショップは訪ねられるよう住所（map）を優先
    where = (p["geo"][0]["q"] if p.get("geo") else p.get("map")) if p.get("kind") == "producer" else p.get("map")
    if where:
        q = quote(where)
        out += f'\n          <a href="https://www.google.com/maps/search/?api=1&amp;query={q}" target="_blank" rel="noopener">{t(UI["map"])}</a>'
    if p.get("instagram") and ig_label:
        out += f'\n          <a href="{ig_permalink(p["instagram"])}" target="_blank" rel="noopener">{t(ig_label)}</a>'
    return out


def render_post(p):
    kind = KINDS[p["kind"]]
    date = fmt_date(p["date"])
    slides = slide_images(p["slug"])
    if slides:
        imgs = "".join(f'\n        <img src="{src}" alt="{escape(p["title"]["en"])} {i}/{len(slides)}" loading="lazy">' for i, src in enumerate(slides, 1))
        media = f'    <div class="slides" tabindex="0">{imgs}\n    </div>'
    else:
        ig = ig_permalink(p["instagram"])
        media = f"""    <div class="ig-frame">
      <blockquote class="instagram-media" data-instgrm-permalink="{ig}" data-instgrm-version="14">
        <a class="ig-fallback" href="{ig}" target="_blank" rel="noopener">{t(UI["on_ig"])}</a>
      </blockquote>
    </div>"""
    paras = "\n".join(f"        <p>{t_at(p['body'], i)}</p>" for i in range(len(p["body"]["ja"])))
    points = ""
    if p.get("points"):
        items = "\n".join(f"          <li>{t_at(p['points'], i)}</li>" for i in range(len(p["points"]["ja"])))
        points = f'        <ul class="points">\n{items}\n        </ul>\n'
    body = f"""<div class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="/">{t(UI["home"])}</a>　/　<a href="/learn/">{t(UI["learn"])}</a></p>
    <p class="meta">{t(kind["label"])}　{t(date)}</p>
    <h1>{t(p["title"])}</h1>
    <p class="lead">{t(p["lead"])}</p>
  </div>
</div>

<section class="block">
  <div class="wrap post-grid">
{media}
    <article class="article">
{paras}
{points}        <div class="links">{links_html(p, UI["on_ig"])}
        </div>
        <div class="cta">
          <h2>{t(kind["cta_title"])}</h2>
          <p>{t(kind["cta_text"])}</p>
          <a class="btn" href="{kind["cta_href"]}">{t(kind["cta_button"])}</a>
        </div>
        <p class="back"><a href="/learn/">{t(UI["back"])}</a></p>
    </article>
  </div>
</section>"""
    title = f'{p["title"]["ja"]} | 日本自然茶協会 Japan Natural Tea Association'
    desc = f'{p["lead"]["ja"]} {p["lead"]["en"]}'
    extra = "" if slides else '<script async src="https://www.instagram.com/embed.js"></script>\n'
    return page(title, desc, f"https://naturaltea.jp/learn/{p['slug']}/", body, extra)


def render_list(posts, course=None):
    cards = []
    for p in posts:
        kind = KINDS[p["kind"]]
        cards.append(f"""      <a class="post-card" href="/learn/{p["slug"]}/">
        <p class="meta">{t(kind["label"])}　{t(fmt_date(p["date"]))}</p>
        <h2>{t(p["title"])}</h2>
        <p>{t(p["lead"])}</p>
        <span class="more">{t(UI["read"])}</span>
      </a>""")
    listing = (
        f'    <div class="post-list">\n{chr(10).join(cards)}\n    </div>'
        if cards
        else ("" if course else f'    <p class="empty">{t(UI["empty"])}</p>')
    )
    if course:
        listing = course_card(course) + listing
    body = f"""<div class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="/">{t(UI["home"])}</a>　/　{t(UI["learn"])}</p>
    <h1>{t(UI["list_title"])}</h1>
    <p class="lead">{t(UI["list_lead"])}</p>
  </div>
</div>

<section class="block">
  <div class="wrap">
{listing}
    <p class="follow"><a href="https://www.instagram.com/japan_natural_tea/" target="_blank" rel="noopener">{t(UI["follow"])}（@japan_natural_tea）</a></p>
  </div>
</section>"""
    return page(
        "学び | 日本自然茶協会 Japan Natural Tea Association",
        "日本自然茶協会の Instagram で発信した、自然茶や日本茶について学べる投稿のまとめ。",
        "https://naturaltea.jp/learn/",
        body,
    )


def slide_images(slug):
    return [f"/instagram/{slug}/{f.name}" for f in sorted((SLIDES / slug).glob("[0-9][0-9].png"))]


def find_image(slug, name):
    """images/directory/<slug>/<name>.<ext> があればサイト内のパスを返す。"""
    for ext in IMAGE_EXTS:
        f = IMAGES / slug / (name + ext)
        if f.exists():
            return f"/images/directory/{slug}/{name}{ext}"
    return None


def fact_value(f):
    v = t(f["value"])
    return f'<span class="badge">{v}</span>' if f.get("badge") else v


def entry_name(p):
    return t(p["name_i18n"]) if "name_i18n" in p else escape(p["name"])


def entry_alt(p):
    return p["name_i18n"]["en"] if "name_i18n" in p else p["name"]


def render_entry(p):
    """directory/index.html の .entry カード（生産者・ショップ）。"""
    slug, alt = p["slug"], escape(entry_alt(p))
    photo, logo, portrait = (find_image(slug, n) for n in ("photo", "logo", "portrait"))
    if not photo and slide_images(slug):
        photo = slide_images(slug)[0]
    kind_label = p.get("kind_label", UI[p["kind"]])
    kind = t({l: kind_label[l] + ("・" if l == "ja" else " · ") + p["region"][l] for l in LANGS})
    paras = "<br><br>".join(t_at(p["body"], i) for i in range(len(p["body"]["ja"])))

    out = f'      <article class="entry{" has-photo" if photo else ""}" id="{slug}">\n'
    if photo:
        out += f'        <img class="entry-photo" src="{photo}" alt="{alt}" loading="lazy">\n'
    out += '        <div class="entry-head">\n'
    if logo:
        out += f'          <img class="entry-logo" src="{logo}" alt="{alt} logo" loading="lazy">\n'
    about = f'        <p class="about">{paras}</p>\n' if p["body"]["ja"] else ""  # 名前と場所のみ掲載の人は紹介文なし
    out += f"""          <div>
            <p class="kind">{kind}</p>
            <h3>{entry_name(p)}</h3>
            <p class="place">{t(p["place"])}</p>
          </div>
        </div>
{about}"""
    if portrait:
        who = escape(p["person"]) if p.get("person") else ""
        out += f'        <div class="person"><img class="entry-portrait" src="{portrait}" alt="{who or alt}" loading="lazy">{f"<span>{who}</span>" if who else ""}</div>\n'
    if p.get("facts"):
        rows = "".join(
            f'\n          <dt>{t(f["label"])}</dt>\n          <dd>{fact_value(f)}</dd>'
            for f in p["facts"]
        )
        out += f'        <dl class="facts">{rows}\n        </dl>\n'
    if p.get("points"):
        out += '        <div class="tea-tags">\n' + "\n".join(
            f"          <span>{t_at(p['points'], i)}</span>" for i in range(len(p["points"]["ja"]))
        ) + "\n        </div>\n"
    out += f"""        <div class="links">{links_html(p, UI["ig_feature"])}
        </div>
      </article>
"""
    return out


def geo_points(p):
    """ピンを立てる場所。geo（市町村）→ 国内なら都道府県庁 → なし。"""
    if p.get("geo"):
        return [(g["lat"], g["lng"]) for g in p["geo"]]
    if p["region"]["ja"] in PREF:
        return [PREF[p["region"]["ja"]]]
    print(f"  ! {p['slug']}: geo がないので地図に出ません（海外は geo を書く）")
    return []


def area_of(p):
    """地図の下の集計に使う単位。生産者は都道府県、ショップは国。"""
    if p["kind"] == "producer":
        return p["region"]
    return JAPAN if p["region"]["ja"] in PREF else p["region"]


def plural(n, one, many):
    return f"{n} {one if n == 1 else many}"


def render_map(kind, items, base=""):
    """base: ピンのリンク先のページ（トップでは "/producers/" など、各ページでは同じページ内なので空）。"""
    m = MAPS[MAP_OF[kind]]
    pins = []
    for p in items:
        for lat, lng in geo_points(p):
            x, y = project(m, lat, lng)
            pins.append(
                f'        <a class="pin" href="{base}#{p["slug"]}" style="left:{x / m["w"] * 100:.2f}%;top:{y / m["h"] * 100:.2f}%">'
                f'<span class="tip">{entry_name(p)}<small>{t(p["region"])}</small></span></a>')
    areas = {}
    for p in items:
        a = area_of(p)
        areas.setdefault(a["ja"], [a, 0])[1] += 1
    n, r = len(items), len(areas)
    if kind == "producer":
        summary = {"ja": f"{n}軒の生産者　{r}都道府県", "en": f"{plural(n, 'producer', 'producers')} in {plural(r, 'prefecture', 'prefectures')}",
                   "fr": f"{plural(n, 'producteur', 'producteurs')} dans {plural(r, 'préfecture', 'préfectures')}"}
    else:
        summary = {"ja": f"{n}軒のショップ　{r}か国・地域", "en": f"{plural(n, 'shop', 'shops')} in {plural(r, 'country', 'countries')}",
                   "fr": f"{plural(n, 'boutique', 'boutiques')} dans {r} pays"}
    chips = "".join(f'<span>{t(a)}<b>{c}</b></span>' for a, c in sorted(areas.values(), key=lambda v: -v[1]))
    return (f'      <p class="map-sum">{t(summary)}</p>\n'
            f'      <div class="map map-{MAP_OF[kind]}" style="aspect-ratio:{m["w"]}/{m["h"]}">\n'
            f'        <img src="/assets/maps/{MAP_OF[kind]}.svg" alt="" width="{m["w"]}" height="{m["h"]}">\n'
            + "\n".join(pins) + "\n      </div>\n"
            f'      <div class="map-areas">{chips}</div>\n')


def replace_block(html, name, content, where):
    pat = re.compile(rf"(<!-- {name} -->\n).*?(\s*<!-- /{name} -->)", re.S)
    assert pat.search(html), f"{where} に <!-- {name} --> の目印がありません"
    return pat.sub(lambda mm: mm.group(1) + content + mm.group(2).lstrip("\n"), html)


def listed(posts, kind):
    """kind の項目を entries.json の並び順で。主催者（"organizer": true、悠三堂）はいつも一番下。"""
    return sorted((p for p in posts if p["kind"] == kind), key=lambda p: bool(p.get("organizer")))


def update_pages(posts):
    for kind, page_file in PAGES.items():
        where = page_file.relative_to(ROOT)
        items = listed(posts, kind)
        html = page_file.read_text(encoding="utf-8")
        html = replace_block(html, f"POSTS:{kind}", "".join(render_entry(p) for p in items), where)
        html = replace_block(html, "MAP", render_map(kind, items), where)
        page_file.write_text(html, encoding="utf-8")
        print("updated", where)
    # トップページの生産者・ショップ欄も同じ地図（ピンは各ページのカードへ）
    top = ROOT / "index.html"
    html = top.read_text(encoding="utf-8")
    for kind, page_file in PAGES.items():
        items = listed(posts, kind)
        html = replace_block(html, f"MAP:{kind}", render_map(kind, items, base=f"/{page_file.parent.name}/"), "index.html")
    top.write_text(html, encoding="utf-8")
    print("updated index.html (maps)")


REELS = ROOT / "tools" / "reels.json"  # トップの図解動画カルーセル。新しい順（先頭が最新）
MAX_REELS = 12


def update_reels():
    """tools/reels.json の動画を、トップの <!-- REELS --> の間に並べる。"""
    reels = json.loads(REELS.read_text(encoding="utf-8"))
    ids = []
    for r in reels:
        rid = r["id"].strip().strip("/").split("/")[-1]  # URL を貼っても ID だけ取り出す
        assert re.fullmatch(r"[A-Za-z0-9_-]{5,20}", rid), f"reels.json: ID が正しくありません: {r['id']}"
        if rid not in ids:
            ids.append(rid)
    items = "".join(
        f'    <div class="reel"><blockquote class="instagram-media" data-instgrm-permalink="https://www.instagram.com/reel/{rid}/" data-instgrm-version="14"></blockquote></div>\n'
        for rid in ids[:MAX_REELS])
    top = ROOT / "index.html"
    html = replace_block(top.read_text(encoding="utf-8"), "REELS", items, "index.html")
    top.write_text(html, encoding="utf-8")
    print(f"updated index.html (reels: {min(len(ids), MAX_REELS)})")


def write_redirect(posts):
    """旧 /directory/ は、#slug を見て生産者かショップのページへ送る。"""
    shops = json.dumps([p["slug"] for p in posts if p["kind"] == "shop"])
    DIRECTORY.parent.mkdir(exist_ok=True)
    DIRECTORY.write_text(f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>生産者・ショップ | 日本自然茶協会 Japan Natural Tea Association</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="https://naturaltea.jp/producers/">
<meta http-equiv="refresh" content="0; url=/producers/">
<!-- tools/build_posts.py で生成。旧ページのリンクを生産者・ショップのページへ送る -->
<script>
  (function(){{
    var shops={shops}, h=location.hash.slice(1);
    location.replace((h==='shops'||shops.indexOf(h)>=0 ? '/shops/' : '/producers/') + (h && h!=='shops' && h!=='producers' ? '#'+h : ''));
  }})();
</script>
</head>
<body style="font-family:serif;padding:40px">
<p><a href="/producers/">生産者 Producers</a> ・ <a href="/shops/">ショップ Shops</a></p>
</body>
</html>
""", encoding="utf-8")
    print("wrote", DIRECTORY.relative_to(ROOT))


COURSE = ROOT / "tools" / "course.json"  # 自然茶基礎コース → learn/<slug>/


def fill(d, **kw):
    return {l: d[l].format(**kw) for l in LANGS}


def course_card(c):
    n = len(c["lessons"])
    return f"""    <a class="course-card" href="/learn/{c["slug"]}/">
      <div>
        <p class="meta">{t(UI["course"])}　{t(fill(UI["lessons_n"], n=n))}</p>
        <h2>{t(c["title"])}</h2>
        <p>{t(c["lead"])}</p>
      </div>
      <span class="btn">{t(UI["open_course"])}</span>
    </a>
"""


def reel_html(rid):
    url = f"https://www.instagram.com/reel/{rid}/"
    return (f'      <div class="reel"><blockquote class="instagram-media" data-instgrm-permalink="{url}" data-instgrm-version="14"></blockquote></div>\n'
            f'      <a class="on-ig" href="{url}" target="_blank" rel="noopener">{t(UI["watch_ig"])}</a>')


def render_course(c):
    base = f"/learn/{c['slug']}/"
    items = "\n".join(f"""      <li><a href="{base}{l["slug"]}/">
        <span class="num">{i:02d}</span>
        <span><h2>{t(l["title"])}</h2><p>{t(l["lead"])}</p></span>
      </a></li>""" for i, l in enumerate(c["lessons"], 1))
    body = f"""<div class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="/">{t(UI["home"])}</a>　/　<a href="/learn/">{t(UI["learn"])}</a></p>
    <p class="meta">{t(UI["course"])}　{t(fill(UI["lessons_n"], n=len(c["lessons"])))}</p>
    <h1>{t(c["title"])}</h1>
    <p class="lead">{t(c["lead"])}</p>
    <a class="btn" href="{base}{c["lessons"][0]["slug"]}/">{t(UI["start"])}</a>
  </div>
</div>

<section class="block">
  <div class="wrap">
    <ol class="lessons">
{items}
    </ol>
    <p class="course-note">{t(UI["course_note"])}</p>
  </div>
</section>"""
    return page(f'{c["title"]["ja"]} {c["title"]["en"]} | 日本自然茶協会 Japan Natural Tea Association',
                f'{c["lead"]["ja"]} {c["lead"]["en"]}', f"https://naturaltea.jp{base}", body)


def render_lesson(c, i):
    lessons, base = c["lessons"], f"/learn/{c['slug']}/"
    l, n = lessons[i], i + 1
    paras = "\n".join(f"        <p>{t_at(l['body'], k)}</p>" for k in range(len(l["body"]["ja"])))
    sources = ""
    if l.get("sources"):
        links = "　/　".join(f'<a href="{escape(s["url"])}" target="_blank" rel="noopener">{t(s["label"])}</a>' for s in l["sources"])
        sources = f'        <p class="sources">{t(UI["sources"])}：{links}</p>\n'
    pager = ""
    if i > 0:
        p = lessons[i - 1]
        pager += f'<a class="prev" href="{base}{p["slug"]}/">← {t(UI["prev"])}<b>{t(p["title"])}</b></a>'
    if i + 1 < len(lessons):
        x = lessons[i + 1]
        pager += f'<a class="next" href="{base}{x["slug"]}/">{t(UI["next"])} →<b>{t(x["title"])}</b></a>'
    cta = ""
    if i + 1 == len(lessons):
        k = KINDS["education"]
        cta = f"""        <div class="cta">
          <h2>{t(k["cta_title"])}</h2>
          <p>{t(k["cta_text"])}</p>
          <a class="btn" href="{k["cta_href"]}">{t(k["cta_button"])}</a>
        </div>
"""
    body = f"""<div class="page-head">
  <div class="wrap">
    <p class="crumb"><a href="/">{t(UI["home"])}</a>　/　<a href="/learn/">{t(UI["learn"])}</a>　/　<a href="{base}">{t(c["title"])}</a></p>
    <p class="meta">{t(fill(UI["lesson_n"], n=n))} / {len(lessons)}</p>
    <h1>{t(l["title"])}</h1>
    <p class="lead">{t(l["lead"])}</p>
  </div>
</div>

<section class="block">
  <div class="wrap lesson-grid">
    <div class="lesson-media">
{reel_html(l["reel"])}
    </div>
    <article class="article">
{paras}
        <div class="takeaway"><small>{t(UI["takeaway"])}</small><p>{t(l["takeaway"])}</p></div>
{sources}{cta}        <nav class="pager">{pager}</nav>
        <p class="toc"><a href="{base}">{t(UI["toc"])}</a></p>
    </article>
  </div>
</section>"""
    return page(f'{l["title"]["ja"]}（{c["title"]["ja"]} 第{n}回） | 日本自然茶協会 Japan Natural Tea Association',
                f'{l["lead"]["ja"]} {l["lead"]["en"]}', f"https://naturaltea.jp{base}{l['slug']}/", body,
                '<script async src="https://www.instagram.com/embed.js"></script>\n')


def check_course(c):
    assert c["slug"] and re.fullmatch(r"[a-z0-9-]+", c["slug"]), "course.json: slug は英小文字・数字・-"
    for key in ("title", "lead"):
        assert set(c[key]) >= set(LANGS), f"course.json: {key} に ja/en/fr が必要"
    slugs = [l["slug"] for l in c["lessons"]]
    assert len(slugs) == len(set(slugs)), "course.json: 回の slug が重複しています"
    for l in c["lessons"]:
        s = l["slug"]
        assert re.fullmatch(r"[A-Za-z0-9_-]{5,20}", l["reel"]), f"course.json {s}: reel は Instagram の動画 ID"
        for key in ("title", "lead", "body", "takeaway"):
            assert set(l[key]) >= set(LANGS), f"course.json {s}: {key} に ja/en/fr が必要"
        assert len({len(l["body"][x]) for x in LANGS}) == 1, f"course.json {s}: body の数を3言語でそろえる"
        for src in l.get("sources", []):
            assert src["url"].startswith("http") and set(src["label"]) >= set(LANGS), f"course.json {s}: sources は url と3言語の label"


def write_course():
    if not COURSE.exists():
        return None
    c = json.loads(COURSE.read_text(encoding="utf-8"))
    check_course(c)
    out = LEARN_DIR / c["slug"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(render_course(c), encoding="utf-8")
    print("wrote", (out / "index.html").relative_to(ROOT))
    for i, l in enumerate(c["lessons"]):
        f = out / l["slug"] / "index.html"
        f.parent.mkdir(exist_ok=True)
        f.write_text(render_lesson(c, i), encoding="utf-8")
        print("wrote", f.relative_to(ROOT))
    return c


def check(p):
    s = p.get("slug", "?")
    assert p.get("kind") in DIRECTORY_KINDS + tuple(KINDS), f"{s}: kind は producer / shop / education のどれか"
    if p["kind"] in DIRECTORY_KINDS:
        assert "name" in p or "name_i18n" in p, f"{s}: name か name_i18n が必要"
        need = ("body", "region", "place")
        for g in p.get("geo", []):
            assert {"q", "lat", "lng"} <= set(g), f"{s}: geo は q / lat / lng をそろえる"
    else:
        assert p.get("date"), f"{s}: education には date が必要"
        assert p.get("instagram") or slide_images(s), f"{s}: education には instagram か投稿画像（render_slides.py）が必要"
        need = ("body", "title", "lead")
    for key in need:
        assert key in p and set(p[key]) >= set(LANGS), f"{s}: {key} に ja/en/fr が必要"
    for key in ("body", "points"):
        if p.get(key):
            assert len({len(p[key][l]) for l in LANGS}) == 1, f"{s}: {key} の数を3言語でそろえる"


def main():
    posts = json.loads(DATA.read_text(encoding="utf-8"))
    slugs = [p["slug"] for p in posts]
    assert len(slugs) == len(set(slugs)), "slug が重複しています"
    for p in posts:
        check(p)
    update_pages(posts)  # カードは entries.json の並び順
    update_reels()
    write_redirect(posts)

    learn = sorted((p for p in posts if p["kind"] in KINDS), key=lambda p: p["date"], reverse=True)
    for p in learn:
        out = LEARN_DIR / p["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_post(p), encoding="utf-8")
        print("wrote", out.relative_to(ROOT))
    LEARN_DIR.mkdir(exist_ok=True)
    course = write_course()
    assert not course or course["slug"] not in {p["slug"] for p in learn}, "course.json の slug が entries.json の学びの記事と重なっています"
    (LEARN_DIR / "index.html").write_text(render_list(learn, course), encoding="utf-8")
    print("wrote learn/index.html")


if __name__ == "__main__":
    main()
