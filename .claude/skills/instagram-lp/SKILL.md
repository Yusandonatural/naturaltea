---
name: instagram-lp
description: 協会の Instagram（@japan_natural_tea）に投稿済みのポストを、naturaltea.jp/posts/<slug>/ のLPにする。「このインスタ投稿をLPにして」「投稿をページ化」「ポストをLP化」と投稿URLが渡されたら使う。
---

# Instagram 投稿を LP にする

1. **投稿を読む**: 内蔵ブラウザで投稿URLを開き、`meta[property="og:description"]` からキャプション、`time[datetime]` から投稿日を取る。ログイン画面で読めないときは、キャプションを貼ってもらう。
2. **posts/posts.json に1件追加**（既存の項目と同じ形）
   - `slug`: 英小文字とハイフン（例 `tencha-london`）
   - `instagram`: 投稿URL（`https://www.instagram.com/p/<ID>/`）
   - `date`: 投稿日 `YYYY-MM-DD`
   - `kind`: `shop`（ショップ紹介）／`producer`（生産者紹介）／`news`（それ以外）
   - `title` / `lead` / `body`（段落の配列）/ `points`（任意・箇条書き）を ja・en・fr で。**キャプションにない事実は足さない**。翻訳は自然な文に
   - `links`: 投稿に出てくる外部サイト（任意）
   - 「Founding member／イニシャルメンバー」は使わない。個人の連絡先は載せない
3. **生成**: `python3 tools/build_posts.py`（posts/<slug>/index.html と posts/index.html を書き出す。生成HTMLは手で直さない）
4. **確認**: `python3 -m http.server 8765` で `/posts/<slug>/` を開き、埋め込み投稿・3言語・スマホ幅（はみ出しなし）を見る。終わったらサーバーを止める
5. **commit**（push はユーザーが自分のターミナルで行う）
