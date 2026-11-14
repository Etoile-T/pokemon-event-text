# pokemon-event-text

日本語の ポケモン FR 改造（pokeemerald-expansion の FRLG 対応フォーク）で、イベントの 台詞を 書く・直す ための Claude Code スキルです。
手本は 元の 日本語版 ファイアレッドの 台詞です。

- `SKILL.md` … スキルの 本体（手順）
- `characters/*.toml` … 人物ごとの 話し方の 表（`[official]` 公式の 台詞を 数えた もの / `[project]` 改造で 足した もの）
- `facts.toml` … 物語で 決まって いる こと
- `references/` … 場面の 読み方・台本の 書き方（公式の 数）・見直しの 手順
- `scripts/extract_official_text.py` … 手元の 日本語版 FR の ROM から 台詞を 取り出し、手元の 控え（`~/.cache/pokemon-event-text/`）に 書く
- `scripts/find_official.py` … 控えから 公式の 台詞を さがす・数える
- `banned_words.toml` と `scripts/check_event_text.py` … 台詞の 検査の 道具（Python 標準ライブラリだけで 動く）

**この リポジトリには 公式の 台詞の 文も ROM も 入って いません。** 控えは 各自の ROM から 作り、
スキルの フォルダの 外に 置きます（`.gitignore` でも `*.jsonl` `official_*` を 外して います）。
取り出しには 改造の リポジトリの `tools/bprj_text/`・`tools/data/bprj_text_symbols.json`・`vendor/pokefirered` が いります。

## 使い方

改造の リポジトリの `.claude/skills/pokemon-event-text/` に 置きます。

```
python3 -I scripts/extract_official_text.py                       # 1回だけ（roms/baserom_fr.gba が いる）
python3 -I scripts/find_official.py --speaker グリーン --kind 勝負のまえ
python3 -I scripts/check_event_text.py --strict data/maps/Route9_Frlg/scripts.inc
```

## ライセンス

MIT。novel2agent-jp と humanizer-ja-modes（どちらも MIT）の 考え方を 使って います。くわしくは `LICENSES.md` を 見て ください。
