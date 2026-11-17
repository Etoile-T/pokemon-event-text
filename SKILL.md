---
name: pokemon-event-text
description: この FR 改造（PokeEm-expansion-CanuseJP）で、イベントの 台詞・地の文・電話（pokenavcall）の 文、特性・道具・わざの 説明文を 新しく 書く、または 直す ときに 使う。手本は 元の 日本語版 ファイアレッドの 台詞。ROM から 取り出した 公式の 台詞の 控えで 同じ 人・同じ 場面の 型を 読んでから、人物の 表（characters/*.toml の [official] と [project]）と 決まった 事実（facts.toml）に そって、公式の 書き方（かな・文節ごとの 空白・1行 17字・1ページ 2行・名札「名前『」）で 書き、見直して scripts/check_event_text.py で 検査する。グリーン・カスミ・ナナミ・ミオ・ロケットだん・町の 人 などの 台詞は ここから。
---

# イベントの 台詞を 書く

**このスキルの 手本は 元の 日本語版 ファイアレッド（BPRJ）の 台詞。** 書き手の 好みで 作る 台詞の スキルでは ない。
台詞を 書く たびに 決まりを 説明して もらわずに すむ ための 手順。ユーザーへの 返事は 日本語。

## 手順

0. **公式の 控えを 用意する**（1回 だけ。ROM が かわらなければ やりなおさない）
   ```
   python3 -I .claude/skills/pokemon-event-text/scripts/extract_official_text.py
   ```
   - roms/baserom_fr.gba（日本語版 FR）から 台詞を ラベルごとに 取り出し、だれの 台詞か（名札・ラベルの 人・トレーナー・見た目）を つけて `~/.cache/pokemon-event-text/official_frlg.jsonl` に 書く
   - **控えは スキルの フォルダに 置かない・写さない**（スキルは 公開 リポジトリ）。主人公の 家の 台詞は 道具が 外す
1. **場面を 読む** → `references/read-event.md`
   - scripts.inc と map.json から「だれが・どこで・何を・旗の 条件」を 場面メモに 書き出す
   - 同じ 人物が 出る 前後の イベントを 読み、知って いる こと・約束・口調を そろえる
   - **主人公の 家（PalletTown_PlayersHouse_*）は ユーザーの ゆるし なく 開かない。grep には `--exclude-dir='PalletTown_PlayersHouse*'`**
2. **公式の 台詞を 読む**（書く まえに かならず）
   ```
   python3 -I .claude/skills/pokemon-event-text/scripts/find_official.py --speaker グリーン --kind 勝負のまえ
   python3 -I .claude/skills/pokemon-event-text/scripts/find_official.py --speaker カスミ --stats
   python3 -I .claude/skills/pokemon-event-text/scripts/find_official.py --speaker おねえさん --shuffle --limit 10
   python3 -I .claude/skills/pokemon-event-text/scripts/find_official.py --grep "もらった！" --kind 地の文
   ```
   - 同じ 人 → いなければ 近い 人（characters/*.toml の 頭に 書いた 手本。アテナ → FR の 女の かんぶ、ミオ → FR の ナナミ・おねえさん など）→ 同じ 種類の 場面（勝負の まえ・負け・地の文・看板）の 順で さがす
   - 3〜8件 読み、あいさつ → 本題 → しめ の ならび、語尾、1ページの 行の 数、記号の 使い方を つかむ
   - 公式の 文を 写さない。下書き・報告にも 長く 引かない（語尾や 呼び方の 数文字は よい）
3. **人物と 事実を 読む** → `characters/<人物>.toml` と `facts.toml`
   - [official] が 公式の 数、[project] が 改造で 足した こと、[conflicts] が ぶつかる 所。**ぶつかれば 公式が 先。ただし ユーザーが きめた ことは のこす**（グリーンの「カスミさん」など）
   - 名前の ない 人は `characters/town_people.toml`（おとこのこ・おねえさん・おじいさん … の 公式の 型）
   - `[open]` に ある ゆれは ユーザーに きいてから 書く
4. **書く** → `references/format.md`
   - かなだけ・文節ごとに 空白・**1行 17字まで（18字を こえない）**・1ページ 2行（3行目は `\l`）・`\n` `\l` `\p` `$`
   - 名札は `名前『`（閉じの 』 は 書かない、ページの 頭だけ）。鳴き声は `ピッピ『ぴっぴ！` の 形で「」なし
   - 「…」は 1つが ふつう。さけびは「ッ」（あッ！）。「、」「。」は 使わない
   - 地の文: 人から → `{PLAYER}は ○○から\n△△を もらった！`。わたす 人が いない → `てにいれた！`
   - 短く。仕組みや 事情を 説明させない
5. **見直す** → `references/review.md`
   - ⓪ 公式の 型と くらべる ① humanizer casual で AI っぽさを ぬく ② 4つの 視点（口調・つながり・説明くささ・テンポ）で 読みくらべる
6. **検査する**
   ```
   python3 -I .claude/skills/pokemon-event-text/scripts/check_event_text.py data/maps/<地図>/scripts.inc --label <ラベルの 一部>
   ```
   - 下書きは scratchpad に `.inc` で 置いて 同じ 道具に かけて よい（電話なら `--phone`）
   - リポジトリ全体の 引用符・衝突の 印は `python3 tools/check_jp_text.py`（この 道具は それと 重ならない 所を 見る）
7. **見せる**: **手本に した 公式の 台詞（ラベル名と、あわせた 型）** → 下書き → 気に なった 所 → 直した 台詞 → 検査の 結果。新しく 決まった 事実は facts.toml に `proposed` で 足す

## 特性・道具・わざの 説明を 書く ときは

台詞と 同じ スキルで 書く。手順は 短い:
1. 今 入って いる 説明から 手本を さがす: `python3 -I .claude/skills/pokemon-event-text/scripts/check_description.py ability --grep "フィールド"`（種類は ability / item / move）
2. `references/format.md` の「特性・道具・わざの 説明」の 決まりで 書く（特性は 1行で いちばんの 売りだけ・名詞を ならべない、道具は 3行で 1つの 文、わざは 効果＋札の 2行）
3. 検査: `check_description.py ability --text "下書き"` または `--name 定数の 一部`。リポジトリ全体は `--all`
4. ビルドして、つよさの 画面・バッグで 撮って 枠に おさまるか 見る

## 守る こと

- 英語の 台本（vendor/pokefirered や data/maps/*_Frlg の 英文）は ビルドで 日本語に 置きかわる 元。手本に しない
- 公式の 文・ROM・セーブを スキルの フォルダや 公開 リポジトリに 入れない
- 悪役の「こども」「ガキ」は わざと。直さない（公式の したっぱも 使う）
- 恋人の 場面は におわせる 程度
- 台詞の 中身だけ たのまれたら 台詞だけ。位置・向き・動きを たのまれたら 台詞の 話に そらさない
- 確かめで エミュや Porymap を 動かす ときは 音を 出さない

## ファイル

| ファイル | 中身 |
|---|---|
| `references/read-event.md` | イベントを 読む 手順と 場面メモの 形 |
| `references/format.md` | 台本の 書き方（字・空白・記号・行の 長さ・改行・名札・鳴き声・地の文・電話）と 公式の 数 |
| `references/review.md` | 公式の 型との くらべ方、humanizer casual の 要点、4つの 視点、直さない もの |
| `characters/*.toml` | 人物の 表（[official] 公式の 数 / [project] 改造 / [conflicts]）。town_people.toml は 町の 人の 型 |
| `facts.toml` | 物語で 決まった こと |
| `banned_words.toml` | 禁止語・言いすぎの 言葉・公式に ない 言い方（道具が 読む） |
| `scripts/extract_official_text.py` | ROM から 公式の 台詞を 取り出して 控えに 書く（控えは スキルの 外） |
| `scripts/find_official.py` | 控えから 公式の 台詞を さがす・数える（--speaker --kind --map --grep --stats --style） |
| `scripts/check_event_text.py` | 台詞の 検査（行の 長さ・字・名札・』・鳴き声・禁止語・人物の 呼び方・句読点） |
| `scripts/check_description.py` | 特性・道具・わざの 説明の 検査（行の 数・字数・漢字・名詞の ならべ・わざの 重複）と 手本さがし（--grep） |
| `LICENSES.md` | novel2agent-jp と humanizer-ja-modes の MIT 表示 |
