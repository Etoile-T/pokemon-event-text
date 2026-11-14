# 使った もの と ライセンス

この スキルは 次の 2つの スキルの 考え方を 使って いる。文章は この プロジェクトむけに 書きなおした。
banned_words.toml の 一部は humanizer-ja-modes の references/banned-ja.md から えらんで かなに なおした もの。

## kgmkm/novel2agent-jp

https://github.com/kgmkm/novel2agent-jp

使った 所: キャラの TOML テンプレート（characters/*.toml の 型を 小さく した もの）、キャラ発想ガイド（欠点先行・三層・
対照人物 → flaw / quirk / heat / relations）、決まった 事実の 一元化（[[established]] と proposed / confirmed → facts.toml）、
書く まえに 文脈を そろえる 手順（文脈パック → references/read-event.md の 場面メモ）、
推敲の 4つの 視点の 読みくらべ（MoA → references/review.md の ②）、本文の 機械検査（check_prose.py の 禁止語彙・一人称 → scripts/check_event_text.py の WORD・CHARA）。

```
MIT License

Copyright (c) 2026 kgmkm

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## harupan119/claude-skills-ja（skills/humanizer-ja-modes）

https://github.com/harupan119/claude-skills-ja

使った 所: 3層モデル（記号・語彙・思考構造）、casual モードの 書きかえ方針（具体を 入れる・立場を とる・リズムを くずす・
口語の 飾りは 体温では ない）、禁止語の 一覧（banned-ja.md から ゲームの 台詞で 出そうな ものを えらんだ）、
「草稿 → まだ AI っぽい 所 → 最終版」の 出し方。

humanizer-ja-modes 自体も blader/humanizer（MIT, Copyright (c) 2025 Siqi Chen）ほかの 考え方を もとに して いる
（同リポジトリの THIRD-PARTY-NOTICES.md）。

```
MIT License

Copyright (c) 2026 harupan119

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
