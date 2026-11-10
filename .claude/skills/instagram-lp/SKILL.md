---
name: instagram-lp
description: 協会の Instagram（@japan_natural_tea）に投稿済みのポストをサイトに載せる。生産者の投稿は「生産者とショップ」ページの生産者欄へ、ショップの投稿はショップ欄へ、学び（educational）の投稿は naturaltea.jp/learn/<slug>/ の独立したLPにする。「このインスタ投稿をLPにして」「投稿をサイトに載せて」「ポストをLP化」と投稿URLが渡されたら使う。
---

# Instagram 投稿をサイトに載せる

投稿の内容で行き先が決まる（ユーザーの指定）:

| 投稿の内容 | kind | 行き先 |
|---|---|---|
| 生産者（farmer）の紹介 | `producer` | producers/index.html にカードと日本地図のピン |
| ショップ・カフェの紹介 | `shop` | shops/index.html にカードと世界地図のピン |
| 学び（自然茶・日本茶・淹れ方・茶道など educational） | `education` | learn/<slug>/ の独立したLP（投稿の埋め込み＋本文）、learn/ の一覧に追加 |

どれにも当てはまらない投稿（お知らせ等）はユーザーに確認する。

1. **投稿を読む**: 内蔵ブラウザで投稿URLを開き、`meta[property="og:description"]` からキャプション、`time[datetime]` から投稿日を取る。読めないときはキャプションを貼ってもらう。
2. **tools/entries.json に1件追加**（既存の項目と同じ形。カードは並び順どおりに出る）
   - 共通: `slug`（英小文字とハイフン）, `kind`, `instagram`（投稿URL）, `date`（YYYY-MM-DD）, `body`（段落の配列）, `points`（任意・短い語の配列）, `links`（任意・外部サイト）
   - `producer` / `shop`: `name`（店名・農園名。言語で表記が違うときは `name_i18n`）, `region`（国や県の短い表記）, `place`（所在地や形態）。任意で `person`（顔写真の横に出す名前）, `facts`（ラベルと値、`badge: true` で丸バッジ）, `geo`（地図のピン。`[{"q": "静岡県牧之原市", "lat": 34.74, "lng": 138.22}]` のように市町村まで。座標は国土地理院の住所検索 `https://msearch.gsi.go.jp/address-search/AddressSearch?q=<市町村>` で取る。海外は都市名と座標）, `map`（ショップの Google マップ用の住所。生産者は geo の市町村で開くので不要）, `kind_label`（「カフェ・小売店」など種別の言い換え）, `instagram`（紹介投稿があれば）
   - **画像**（producer / shop）: `images/directory/<slug>/` に `logo`・`portrait`（顔写真）・`photo`（お店や畑）を `.jpg/.jpeg/.png/.webp` で置くと自動で表示。登録フォームの「写真・ロゴ」欄の画像を使う（ユーザーが Jotform から保存して置く）。置く前に `sips -Z 1600 photo.jpg`、ロゴと顔写真は `sips -Z 400` で縮める。掲載に同意した人の画像だけ使う
   - `education`: `title`, `lead`
   - 文字列はすべて ja・en・fr の3言語（`name` と `links` を除く）。**キャプションにない事実は足さない**。個人の連絡先は載せない。「Founding member／イニシャルメンバー」は使わない
3. **生成**: `python3 tools/build_posts.py`
   - producers/index.html・shops/index.html の `<!-- POSTS:… -->` と `<!-- MAP -->` の間（カードと地図のピン、件数）を書き換える
   - learn/ 以下を書き出す。生成HTMLは手で直さない
4. **確認**: `python3 -m http.server 8765` で該当ページを開き、3言語・スマホ幅（はみ出しなし）を見る。終わったらサーバーを止める
5. **commit**（push はユーザーが自分のターミナルで行う）
