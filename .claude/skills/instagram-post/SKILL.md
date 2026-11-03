---
name: instagram-post
description: 協会の Instagram（@japan_natural_tea）用の投稿を Claude で作り、同時にサイトのページ（生産者・ショップのカード、または学びのLP）も作る。「インスタ投稿を作って」「ポストを作って」「〇〇を紹介する投稿を作りたい」と言われたら使う。投稿済みのポストをサイトに載せるだけなら instagram-lp を使う。
---

# Instagram 投稿とサイトのページを一緒に作る

投稿のスライド画像・キャプション・サイトのページを、`tools/entries.json` の1件から全部つくる。

## 1. 中身を決める
- 何を紹介するか聞く: 生産者（`producer`）／ショップ（`shop`）／学び（`education`）。それ以外はどこに載せるか確認する
- 事実はユーザーの話・相手のサイト・登録フォームの内容から取る。**分からないことは作らずに聞く**
- 画像: ロゴ・顔写真・お店や畑の写真があれば `images/directory/<slug>/logo|portrait|photo.<ext>` に置いてもらう（Finder で場所を教えてもらい、こちらでコピーしてもよい）。ロゴは表紙スライドにも載る

## 2. tools/entries.json に1件書く
サイト用の項目は instagram-lp スキルの説明と同じ（producer/shop は `name`・`region`・`place`・`body`…、education は `title`・`lead`・`body`…、すべて ja/en/fr）。それに加えて:
- `date`: 投稿予定日（YYYY-MM-DD）
- `slides`: スライドの配列（4〜7枚が目安）。書き方は `tools/render_slides.py` の冒頭にある例のとおり
  - 1枚目 `cover`: `label`（例 `SHOPS / UK`, `FARMERS / NARA`, `LEARN / BASICS`）, `kicker`（日本語の短い一言）, `title`, `body`
  - 途中 `text`（見出し＋本文＋箇条書き）, `grid`（お茶の種類などを3列の枠で）
  - 最後 `cta`: 相手のサイトや来店方法と、`box` に協会への DM の呼びかけ
  - スライドの文は英語、`kicker` だけ日本語（Tencha の投稿と同じ形）。1枚に詰め込まない
- `caption`: 投稿のキャプション（英語。1行目は投稿の要約、絵文字は控えめ、最後に `📩 @japan_natural_tea` `🔗 <相手のサイト> ／ naturaltea.jp`、ハッシュタグ5個前後）
- 「Founding member／イニシャルメンバー」は使わない。個人の連絡先は載せない

## 3. 画像とページを作る
```bash
python3 tools/render_slides.py <slug>   # instagram/<slug>/01.png… と caption.txt
python3 tools/build_posts.py            # サイトのページを更新
```
- 画像を `sips -Z 540` で縮めて Read で全部見る。はみ出し・詰め込みがあれば文を短くして作り直す
- サイトは `python3 -m http.server 8765` で確認（producer/shop → /directory/ のカード。写真がなければ表紙スライドがカードの写真になる。education → /learn/<slug>/ にスライドが並ぶ）。終わったらサーバーを止める

## 4. 渡す
- スライド画像（instagram/<slug>/*.png）を SendUserFile でユーザーに送り、caption.txt の中身も見せる。Instagram への投稿はユーザーがする
- commit する（push はユーザーが自分のターミナルで行う）
- 投稿後に URL をもらったら、その項目に `instagram` を足して `python3 tools/build_posts.py` を再実行し、commit（カードに「紹介投稿を見る」リンクが付く）
