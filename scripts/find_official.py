#!/usr/bin/env python3
"""公式（日本語版 FR）の 台詞を 控えから さがす・数える（pokemon-event-text スキルの 道具）。

控えは extract_official_text.py が 作る（既定 ~/.cache/pokemon-event-text/official_frlg.jsonl）。
台詞を 書く まえに、同じ 人・同じ 種類の 場面の 公式の 台詞を 読む ために 使う。
**出力を スキルの フォルダや 公開 リポジトリに 写さない。** 語尾や 呼び方の 数文字なら 書いて よい。

使い方:
  find_official.py --speaker グリーン --kind 勝負のまえ
  find_official.py --speaker カスミ --stats            # 一人称・呼び方・文末・長さを 数える
  find_official.py --speaker ロケットだん --kind 負け --limit 10
  find_official.py --grep "もらった！" --kind 地の文
  find_official.py --map CeruleanCity                  # 地図の 名前の 一部
  find_official.py --style                             # 字・記号・行の 長さの 全体の 数

--kind: 台詞 / 勝負のまえ / 負け / 勝負のあと / 再戦 / 勝ったとき / 看板 / 地の文
--speaker は 名札・人物・トレーナーの 種類・見た目の 名札の どれかに 一部が 合えば 出す。
  見た目だけで 決めた 人は「町の 人の 型」（おじさん・おねえさん・おんなのこ …）。
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_CACHE = Path.home() / ".cache" / "pokemon-event-text" / "official_frlg.jsonl"
NOT_DIALOGUE = ("Help", "gFameChecker", "Braille", "gText", "gOakSpeech")
KINDS = ("台詞", "勝負のまえ", "負け", "勝負のあと", "再戦", "勝ったとき", "看板", "地の文")
TAG_RE = re.compile(r"^(\{[^}]*\})*(\{RIVAL\}|[^\s　『「{}\\$]{1,8})『")
BOUND = r"(?:^|(?<=[\s　『！？…ー]))"
FIRST_PERSON = re.compile(BOUND + r"(おれさま|おれたち|おれ|ぼくたち|ぼく|わたしたち|わたし|あたし|わし|わたくし|おいら|われわれ|うち)"
                          r"(?=[はがのもにをとって　 ！？…やらへ]|$)")
SECOND_PERSON = re.compile(BOUND + r"(おまえさん|おまえたち|おまえ|きみたち|きみ|あなた|あんた|こども|ガキ|こぞう|ぼうや|"
                           r"\{PLAYER\}\{KUN\}|\{PLAYER\}(?!\{KUN\})|てめえ|きさま)")
PLACEHOLDER_WIDTH = {"PLAYER": 5, "RIVAL": 5, "KUN": 2}   # 元の FR の 名前は 5字まで


def load(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"[ERROR] 控え {path} が ありません。先に scripts/extract_official_text.py を 動かして ください")
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def is_dialogue(r: dict) -> bool:
    return not r["label"].startswith(NOT_DIALOGUE) and re.search(r"[ぁ-ん]", r["text"]) is not None


def matches(r: dict, args) -> bool:
    if args.kind and r["kind"] != args.kind:
        return False
    if args.map and args.map.lower() not in (r["map"] or "").lower():
        return False
    if args.speaker:
        names = [r.get("speaker") or "", r.get("trainer_class") or "", *r.get("tags", [])]
        if not any(args.speaker in n for n in names):
            return False
    if args.grep:
        flat = re.sub(r"[ 　]", "", r["text"])
        if not re.search(re.sub(r"[ 　]", "", args.grep), flat):
            return False
    return True


def pages(text: str) -> list[str]:
    return text.rstrip("$").split("\\p")


def body_lines(text: str) -> list[str]:
    out = []
    for p in pages(text):
        out += re.split(r"\\[nl]", TAG_RE.sub("", p))
    return out


def width(line: str) -> int:
    n = 0
    for m in re.finditer(r"\{([^}]*)\}|.", line):
        if m.group(1) is None:
            n += 1
        else:
            key = m.group(1)
            n += PLACEHOLDER_WIDTH.get(key, 5 if key.startswith("STR_VAR") else 0)
    return n


def sentence_ends(text: str) -> Counter:
    """文の 終わり（ページの 終わり・！ ？ の まえ）の さいごの 2字"""
    ends = Counter()
    body = re.sub(r"\{[^}]*\}", "", text)
    for seg in re.split(r"\\p|\$|[！？]+", body):
        seg = re.split(r"\\[nl]", seg)[-1].split("『")[-1]
        seg = re.sub(r"[…ー　\sッっ]+$", "", seg)
        if seg:
            ends[seg[-2:]] += 1
    return ends


def show(rows: list[dict], limit: int) -> None:
    for r in rows[:limit]:
        who = r.get("speaker") or "（不明）"
        extra = f" / {r['trainer_class']}" if r.get("trainer_class") and r["trainer_class"] != who else ""
        print(f"■ {r['label']}  [{r['kind']}] {who}{extra}  ({r.get('speaker_from') or '-'})")
        for p in pages(r["text"]):
            for part in re.split(r"(\\[nl])", p):
                if part == "\\l":
                    print("   ↑（\\l で おくる）")
                elif part != "\\n":
                    print(f"  {part}")
            print("  ─")
    if len(rows) > limit:
        print(f"…ほか {len(rows) - limit} 件（--limit で ふやす）")


def stats(rows: list[dict]) -> None:
    if not rows:
        print("0 件")
        return
    lines = [l for r in rows for l in body_lines(r["text"])]
    pg = [len(pages(r["text"])) for r in rows]
    widths = sorted(width(l) for l in lines)
    joined = "\n".join(lines)
    ends = Counter()
    for r in rows:
        ends.update(sentence_ends(r["text"]))
    print(f"{len(rows)} 件 / ページ {sum(pg)} / 行 {len(lines)}")
    print(f"  1件の ページ 平均 {sum(pg)/len(pg):.1f}  1ページの 行 平均 {len(lines)/sum(pg):.1f}")
    print(f"  1行の 字数 平均 {sum(widths)/len(widths):.1f}  9割が {widths[int(len(widths)*0.9)]}字まで  いちばん 長い {widths[-1]}字")
    print(f"  一人称 {Counter(FIRST_PERSON.findall(joined)).most_common(6)}")
    print(f"  相手の 呼び方 {Counter(SECOND_PERSON.findall(joined)).most_common(8)}")
    print(f"  文末 {ends.most_common(16)}")
    print(f"  ！{joined.count('！')} ？{joined.count('？')} …{joined.count('…')}（……{joined.count('……')}）"
          f" ッ{joined.count('ッ')} ー{joined.count('ー')}")
    print(f"  種類 {dict(Counter(r['kind'] for r in rows))}")


def style(rows: list[dict]) -> None:
    dl = [r for r in rows if is_dialogue(r) and r["kind"] != "看板"]
    text = "\n".join(r["text"] for r in dl)
    lines = [l for r in dl for l in body_lines(r["text"])]
    widths = Counter(width(l) for l in lines)
    total = sum(widths.values())
    print(f"台詞 {len(dl)} 件・行 {total}")
    for w in range(14, 23):
        print(f"  {w}字まで {sum(v for k, v in widths.items() if k <= w) / total:.1%}")
    per_page = Counter(len(re.split(r"\\[nl]", TAG_RE.sub("", p))) for r in dl for p in pages(r["text"]))
    tp = sum(per_page.values())
    print("  1ページの 行:", {k: f"{v/tp:.0%}" for k, v in sorted(per_page.items()) if v / tp >= 0.01})
    runs = Counter(len(m.group(0)) for m in re.finditer("…+", text))
    print(f"  … の つらなり {dict(sorted(runs.items()))}  …の あと 空白 {len(re.findall('…[　 ]', text))} / 字 {len(re.findall('…[ぁ-んァ-ン]', text))}")
    print(f"  ッ！ {text.count('ッ！')} / っ！ {text.count('っ！')}  ！！ {text.count('！！')}  ！？ {text.count('！？')}")
    print(f"  。 {text.count('。')}  、 {text.count('、')}  漢字 {len(re.findall(r'[一-鿿]', text))}  〜 {text.count('〜')}")
    end = Counter()
    for r in dl:
        for p in pages(r["text"]):
            s = re.sub(r"\{[^}]*\}$", "", p)
            end[s[-1:] if s[-1:] in "！？…" else "なし"] += 1
    te = sum(end.values())
    print("  ページの 終わり:", {k: f"{v/te:.0%}" for k, v in end.most_common()})
    print(f"  名札「名前『」の ある 台詞 {sum(1 for r in dl if r.get('tags'))} / {len(dl)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="公式（日本語版 FR）の 台詞を 控えから さがす")
    ap.add_argument("--speaker", help="話し手（一部で よい）: グリーン カスミ ロケットだん おじさん …")
    ap.add_argument("--kind", choices=KINDS, help="場面の 種類")
    ap.add_argument("--map", help="地図の 名前の 一部（英語。CeruleanCity など）")
    ap.add_argument("--grep", help="文の 中を さがす 正規表現（空白は 無視）")
    ap.add_argument("--limit", type=int, default=8, help="出す 件数（既定 8）")
    ap.add_argument("--shuffle", action="store_true", help="ならびを まぜる（町の 人の 型を いろいろ 見る とき）")
    ap.add_argument("--stats", action="store_true", help="文を 出さず、一人称・呼び方・文末・長さを 数える")
    ap.add_argument("--style", action="store_true", help="字・記号・行の 長さの 全体の 数")
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    args = ap.parse_args()

    rows = load(args.cache.expanduser())
    if args.style:
        style(rows)
        return 0
    found = [r for r in rows if is_dialogue(r) and matches(r, args)]
    if args.shuffle:
        random.shuffle(found)
    if args.stats:
        stats(found)
    else:
        show(found, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
