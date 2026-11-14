# pokemon-event-text

日本語の ポケモン FR 改造（pokeemerald-expansion の FRLG 対応フォーク）で、イベントの 台詞を 書く・直す ための Claude Code スキルです。

- `SKILL.md` … スキルの 本体（手順）
- `characters/*.toml` … 人物ごとの 話し方の 表
- `facts.toml` … 物語で 決まって いる こと
- `references/` … 場面の 読み方・台本の 書き方・見直しの 手順
- `banned_words.toml` と `scripts/check_event_text.py` … 台詞の 検査の 道具（Python 標準ライブラリだけで 動く）

## 使い方

改造の リポジトリの `.claude/skills/pokemon-event-text/` に 置きます。

```
python3 scripts/check_event_text.py --strict data/maps/Route9_Frlg/scripts.inc
```

## ライセンス

MIT。novel2agent-jp と humanizer-ja-modes（どちらも MIT）の 考え方を 使って います。くわしくは `LICENSES.md` を 見て ください。
