# 一般社団法人 日本自然茶協会 — 公式サイト naturaltea.jp

このフォルダは協会の公式サイト（1ページ完結型の静的サイト）と設立書類の置き場です。
サイト本体は `index.html` 1ファイル。Cowork（Claude デスクトップ）で作成し、ここから Claude Code に引き継いでいます。

## 最初にやること（重要）

**ローカルの `index.html` には、まだ GitHub に反映していない変更が含まれています。**
最初の作業として、最新の `index.html` を GitHub の `main` に push して公開してください。

未反映の変更（2026-10 時点）:
- 初回表示の言語を英語（`lang-en`）にデフォルト化
- 生産者名の英語表記を「Yusando Inc.」に変更
- 入会セクションに「メンバー募集」見出し＋メンバー応募フォーム（Jotform 263016570075049）を埋め込み、お問い合わせフォームはボタン化
- 「自然茶とは（無肥料・無農薬）」セクション新設（比較表＋意義3点）
- 「代表挨拶」セクション新設（礒﨑 遼太郎）
- 「Founding member／イニシャルメンバー」表記をすべて削除
- 入会セクション内（`#register`）に生産者登録・販売店登録の2フォームを横並びで埋め込み
- 協会概要に 設立日 2026年5月7日／代表理事 礒﨑 遼太郎 を追加

## 公開の仕組み

- ホスティング: GitHub Pages。リポジトリ `Yusandonatural/naturaltea`（`main` ブランチ `/(root)`）
- カスタムドメイン: `naturaltea.jp`（リポジトリ直下の `CNAME` ファイルに記載）。DNS はムームードメイン（A レコード4件 → GitHub Pages IP、`www` → `yusandonatural.github.io`）
- HTTPS: Enforce HTTPS 有効済み
- **デプロイ = `index.html` と `CNAME` を `main` に push するだけ。** 1〜2分で反映
- このフォルダはまだ git 管理ではない。推奨手順:
  ```bash
  git clone https://github.com/Yusandonatural/naturaltea.git
  cp "index.html" naturaltea/index.html   # このフォルダの最新版を上書き
  cp CLAUDE.md naturaltea/CLAUDE.md
  cd naturaltea && git add -A && git commit -m "Update site" && git push
  ```
  以降は `naturaltea/` を作業ディレクトリにして Claude Code を起動すると、編集→commit→push が直接できる（Cowork ではブラウザ経由のアップロードしかできず不安定だった）

## index.html の構造とルール

### 3言語の仕組み（必ず守る）
- テキストは必ず3つの span を並べて書く:
  ```html
  <span class="ja-only">日本語</span><span class="en-only">English</span><span class="fr-only">Français</span>
  ```
- `body.lang-ja / lang-en / lang-fr` の class で表示を切り替える（CSS で該当 span のみ `display:inline`）
- 言語切替ボタン: ヘッダーの `#btn-ja / #btn-en / #btn-fr`、JS の `setLang()`。選択は `localStorage('jnta_lang')` に保存。**初回デフォルトは英語**
- 新しい文言を足すときは必ず3言語ぶん追加する。追加後に以下で件数が一致することを確認:
  ```bash
  grep -o 'class="en-only"' index.html | wc -l
  grep -o 'class="fr-only"' index.html | wc -l   # ← 同じ数になること
  python3 -c "import html.parser;html.parser.HTMLParser().feed(open('index.html',encoding='utf-8').read());print('parse OK')"
  ```

### ページ
- `index.html` — トップ（1ページ構成、下記セクション）
- `directory/index.html` — 生産者とショップの紹介ページ（naturaltea.jp/directory/）。CSS はページ内に持つ（トップと同じ変数・ヘッダー・フッター）。ヘッダーナビの「生産者とショップ」と、トップの `#producers`・`#visit` 下の「すべて見る」リンクから来る。言語は `localStorage('jnta_lang')` を共有
- `posts/` — Instagram 投稿のLP（naturaltea.jp/posts/ が一覧、/posts/<slug>/ が各投稿）。**`posts/posts.json` を編集して `python3 tools/build_posts.py` で生成**する。生成HTMLは手で直さない（デザインを変えるときは tools/build_posts.py の CSS／テンプレートを直して再生成）。手順は `.claude/skills/instagram-lp/SKILL.md`（「このインスタ投稿をLPにして <URL>」で使う）
- ページを足したら、ヘッダー／フッターのリンクと3言語 span 件数チェックを各ページで行う

### セクション構成（上から順）
1. `#top` ヒーロー
2. `#about` 協会について（設立趣旨・想い・ミッション）
3. `#founder` 代表挨拶
4. `#natural` 自然茶とは — **無肥料・無農薬**を大きく掲げ、慣行／有機／自然栽培の比較表
5. `#context` 日本茶の今（課題と世界からの注目、統計3点＋出典リンク）
6. `#business` 事業内容（5つの取り組み）
7. `#upcoming` 準備中の活動（深緑背景、6項目: ティーツアー／オンラインコース／年1回のカンファレンス／YouTube生産者紹介／サンプルアソートパック／メールマガジン。開始したら各項目に申込・視聴リンクを足す）
8. `#producers` 生産者紹介（株式会社 悠三堂 / Yusando Inc.、奈良市上深川町227、Googleマップ埋め込み）
9. `#visit` カフェ・小売店（YUSANDO NATURAL TEA、都祁吐山町920、予約制、Googleマップ）
10. `#join` 入会（メンバー募集＋メンバー応募フォーム → 生産者・販売店の登録 `#register`（生産者登録＋販売店登録フォーム、横並び）→ お問い合わせボタン）
11. `#instagram`（@japan_natural_tea）
12. `#org` 協会概要（名称・代表理事・所在地・設立日 2026-05-07・事業年度）

### 埋め込み
- Jotform は `<iframe id="JotFormIFrame-<formID>" src="https://form.jotform.com/<formID>">` で埋め込み、末尾の `jotformEmbedHandler(...)` に同じ ID を登録すると高さが自動調整される
- Google マップは API キー不要の `https://maps.google.com/maps?q=<住所URLエンコード>&z=15&hl=ja&output=embed` を iframe で埋め込み（`.map-embed`）

### Jotform フォーム一覧
| 用途 | Form ID | 言語 |
|---|---|---|
| お問い合わせ（種類: 入会申し込み／お問い合わせ の選択あり） | 261521964938063 | 日英仏 |
| メンバー応募 | 263016570075049 | 日英 |
| 生産者登録（農家向け） | 263026980551054 | 日本語 |
| 販売店登録（店舗向け、掲載希望の項目あり） | 263026716489061 | 日英 |

Jotform は MCP コネクタ（または https://www.jotform.com/build/<formID>）で編集可能。回答の閲覧・要約も MCP で可能。

埋め込みフォーム3つ（メンバー応募・生産者登録・販売店登録）は書式を統一済み。新しいフォームも同じにする:
- 見出し・ページタイトル: `Japan Natural Tea Association — <用途英語> (日本自然茶協会 <用途>フォーム)`
- 色: ページ背景 #F5F0E6、フォーム面と入力欄 #FBFAF6、見出し #243128、本文・ラベル #2F3431、送信ボタン #2F5D4A（文字 #FBFAF6）
- 書体: "Times New Roman", serif（全要素）。角丸: フォーム 6px、入力欄・ボタン 4px
- Jotform の「フォーム名」と「ページタイトル（Form Settings）」は別設定。両方そろえること

## 協会の方針（コンテンツ作成時に守る）

- 体制は代表理事（礒﨑 遼太郎）のみ。他の役員情報は載せない。会員種別や会費の複雑な制度は作らない（「ややこしいことはなしで」）
- 収益化は3本のみ: ①日本の生産者の紹介／お店の紹介 ②生産者向けのイベント／マルシェ ③海外での日本茶コースの開催
- 「Founding member／イニシャルメンバー」という表現は使わない。「メンバーを募集しています」とする
- 自然茶 = **無肥料・無農薬**（化学肥料だけでなく有機肥料も一切使わない）。この点を強調する。ただし協会概要のミッション文は定款の正式文言「農薬や化学肥料を使用しない」のまま
- デザインは和モダン・深緑基調（CSS 変数 `--green-*`, `--kinari`, `--matcha`）。明朝体見出し。既存のトーンを崩さない
- 統計・データを載せるときは出典（農林水産省等）をリンク付きで明記する

## 今後の候補
- 「事業内容」を収益3本に合わせて組み替え、それぞれに「登録する／参加する／お問い合わせ」ボタンを付ける
- お知らせ・活動報告、イベント／マルシェ情報、海外日本茶コースの案内、登録生産者・販売店の一覧 などのコンテンツ枠
- 登録生産者・販売店が増えたら `directory/index.html` に `.entry` カードを足す（掲載は登録フォームで「掲載可」の回答のみ。メール・電話は載せない）。件数は `.jump .count` も更新

## 関連
- Instagram: @japan_natural_tea
- 生産者・カフェ運営: 株式会社 悠三堂（yusando.com）
- 設立書類（定款・設立趣旨書など）は同フォルダ内の .docx / `公証人提出用/`。役員名簿には個人の住所・生年月日が含まれるため、サイトには載せない
