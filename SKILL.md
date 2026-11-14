---
name: pokemon-event-text
description: この FR 改造（PokeEm-expansion-CanuseJP）で、イベントの 台詞・地の文・電話（pokenavcall）の 文を 新しく 書く、または 直す ときに 使う。地図の scripts.inc を 読んで 場面を つかみ、人物の 表（characters/*.toml）と 決まった 事実（facts.toml）に そって、台本の 形式（かな・半角空白・1行 21字・名札「名前『」）で 書き、humanizer の casual と 4つの 視点で 見直し、scripts/check_event_text.py で 検査する。ナナミ・ミオ・グリーン・ロケットだん・カエデの 人たち などの 台詞は ここから。
---

# イベントの 台詞を 書く

台詞を 書く たびに 決まりを 説明して もらわずに すむ ための 手順。ユーザーへの 返事は 日本語。

## 手順

1. **場面を 読む** → `references/read-event.md`
   - scripts.inc と map.json から「だれが・どこで・何を・旗の 条件」を 場面メモに 書き出す
   - 同じ 人物が 出る 前後の イベントを 読み、知って いる こと・約束・口調を そろえる
   - **主人公の 家（PalletTown_PlayersHouse_*）は ユーザーの ゆるし なく 開かない**
2. **人物と 事実を 読む** → `characters/<人物>.toml` と `facts.toml`
   - 一人称・主人公の 呼び方（{PLAYER}{KUN} か 呼びすてか）・語尾・口ぐせ・言わない こと
   - `[open]` に ある ゆれ（ミオの 呼び方、ランスの 口調）は ユーザーに きいてから 書く
3. **書く** → `references/format.md`
   - かなだけ・文節ごとに 半角空白・1行 21字まで（電話 20字）・1ページ 2行・`\n` `\l` `\p` `$`
   - 名札は `名前『`（閉じの 』 は 書かない、ページの 頭だけ）。鳴き声は 「」なし
   - 短く。仕組みや 事情を 説明させない。元の ゲームの 台詞を 写さない
4. **見直す** → `references/review.md`
   - ① humanizer casual で AI っぽさを ぬく ② 4つの 視点（口調・つながり・説明くささ・テンポ）で 読みくらべる
5. **検査する**
   ```
   python3 -I .claude/skills/pokemon-event-text/scripts/check_event_text.py data/maps/<地図>/scripts.inc --label <ラベルの 一部>
   ```
   - 下書きは scratchpad に `.inc` で 置いて 同じ 道具に かけて よい（電話なら `--phone`）
   - リポジトリ全体の 引用符・衝突の 印は `python3 tools/check_jp_text.py`（この 道具は それと 重ならない 所を 見る）
6. **見せる**: 下書き → 気に なった 所 → 直した 台詞 → 検査の 結果。新しく 決まった 事実は facts.toml に `proposed` で 足す

## 守る こと

- 悪役の「こども」「ガキ」は わざと。直さない
- 恋人の 場面は におわせる 程度
- 台詞の 中身だけ たのまれたら 台詞だけ。位置・向き・動きを たのまれたら 台詞の 話に そらさない
- 確かめで エミュや Porymap を 動かす ときは 音を 出さない

## ファイル

| ファイル | 中身 |
|---|---|
| `references/read-event.md` | イベントを 読む 手順と 場面メモの 形 |
| `references/format.md` | 台本の 書き方（字・空白・行の 長さ・改行・名札・鳴き声・地の文・電話）と 根拠 |
| `references/review.md` | humanizer casual の 要点、4つの 視点、直さない もの |
| `characters/*.toml` | 人物の 表（ナナミ・ミオ・グリーン・シルバー・アポロ・ランス・アテナ・ライデン・したっぱ・マツバ・カエデの 人たち・オーキド） |
| `facts.toml` | 物語で 決まった こと |
| `banned_words.toml` | 禁止語・言いすぎの 言葉（道具が 読む） |
| `scripts/check_event_text.py` | 台詞の 検査（行の 長さ・字・名札・』・鳴き声・禁止語・人物の 呼び方） |
| `LICENSES.md` | novel2agent-jp と humanizer-ja-modes の MIT 表示 |
