#!/usr/bin/env python3
"""特性・道具・わざの 説明文を 検査する／手本を さがす。

  検査（ファイルの 中の ぜんぶ、または 名前で しぼる）:
    python3 -I check_description.py ability --name BOND_THUNDER
    python3 -I check_description.py item --name BOND_ORB
    python3 -I check_description.py move --all
  下書きを 直接 検査（改行は \\n）:
    python3 -I check_description.py ability --text "でんきわざを さきに だせる\\nとくせいも タイプも むしして あたる"
  手本を さがす（今 入って いる 説明から、言葉で）:
    python3 -I check_description.py ability --grep "フィールド"

決まりは references/format.md の「特性・道具・わざの 説明」。リポジトリの 一番上で 動かす。
"""
import argparse
import re
import sys
from pathlib import Path

FILES = {
    "ability": "src/data/abilities.h",
    "item": "src/data/items.h",
    "move": "src/data/moves_info.h",
}
# 種類ごとの 行の 数と 1行の 字数（このROMの 今の 説明を 数えた 値）
LIMITS = {
    "ability": {"max_lines": 2, "warn_lines": 2, "max_chars": 21, "warn_chars": 21},
    "item": {"max_lines": 3, "warn_lines": 99, "max_chars": 17, "warn_chars": 17},
    "move": {"max_lines": 2, "warn_lines": 99, "max_chars": 33, "warn_chars": 25},
}
PARTICLE_END = tuple("をがにではともへやの")
VERBISH_END = tuple("るいうすくつむぬぶぐただ")
MOVE_TAGS = {
    "さわる", "さわらない", "まもりむし", "さき", "おと", "きる", "たま", "パンチ", "はんどう", "かぜ",
    "ためる", "あと", "きゅうしゅう", "おどり", "まもる", "キバ", "こな", "ひっちゅう", "はどう",
}
CONTROL = re.compile(r"\{[^}]*\}")
KANJI = re.compile(r"[一-鿿]")
HEAD = re.compile(r"^\s*\[((?:ABILITY|ITEM|MOVE)_\w+)\]\s*=", re.M)
DESC = re.compile(r"\.description\s*=\s*COMPOUND_STRING\((.*?)\)\s*,", re.S)


def strings_of(source):
    return "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', source))


def visible(line):
    return CONTROL.sub("", line)


def entries(kind):
    """[定数] = { の 行で 区切り、その 中の さいしょの .description を 取る（閉じかっこの 字下げに よらない）"""
    text = Path(FILES[kind]).read_text(encoding="utf-8")
    heads = list(HEAD.finditer(text))
    for i, head in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        match = DESC.search(text, head.end(), end)
        if match:
            yield head.group(1), strings_of(match.group(1))


def looks_like_noun_list(line):
    """空白で 区切った 言葉が 2つ 以上 あって、助詞も 動きの 終わりも ない 行"""
    words = visible(line).split()
    if len(words) < 2:
        return False
    if any(w.endswith(PARTICLE_END) or "を" in w or "が" in w for w in words):
        return False
    return not words[-1].endswith(VERBISH_END) or words[-1].endswith("なし")


def check(kind, name, desc):
    errors, warns = [], []
    lines = desc.split("\\n")
    limit = LIMITS[kind]
    if len(lines) > limit["max_lines"]:
        errors.append(f"{len(lines)}行（{limit['max_lines']}行まで）")
    elif kind == "ability" and len(lines) >= limit["warn_lines"]:
        warns.append("2行。公式の 特性は ほぼ 1行。専用特性で どうしても 足りない ときだけ")
    if kind == "move" and len(lines) != 2:
        errors.append("わざは 1行目 効果・2行目 札の 2行")
    for i, line in enumerate(lines, 1):
        n = len(visible(line))
        if n > limit["max_chars"]:
            errors.append(f"{i}行目 {n}字（{limit['max_chars']}字まで）: {visible(line)}")
        elif n > limit["warn_chars"]:
            warns.append(f"{i}行目 {n}字（長め）: {visible(line)}")
        if KANJI.search(line):
            errors.append(f"{i}行目に 漢字: {visible(line)}")
        if kind == "item" and i > 1 and not line.startswith("{JPN}"):
            warns.append(f"{i}行目の 頭に {{JPN}} が ない（ほかの 道具に そろえる）")
    if kind == "ability" and visible(desc) != "とくせい なし" and any(looks_like_noun_list(l) for l in lines):
        warns.append("名詞を ならべて いる ように 見える。動きの ある 短い 文に（例: ひこうわざを さきに だせる）")
    return errors, warns


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("kind", choices=sorted(FILES))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name", help="定数の 名前の 一部（例: BOND_THUNDER）")
    group.add_argument("--all", action="store_true", help="ファイルの ぜんぶ")
    group.add_argument("--text", help="下書きを 直接 検査（改行は \\n）")
    group.add_argument("--grep", help="この 言葉を ふくむ 今の 説明を 手本と して 見せる")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    if args.grep:
        hits = [(n, d) for n, d in entries(args.kind) if args.grep in visible(d)]
        for n, d in hits[: args.limit]:
            print(f"{n}: {visible(d).replace(chr(92) + 'n', ' / ')}")
        print(f"-- {len(hits)} 件")
        return 0

    targets = [("（下書き）", args.text)] if args.text else [
        (n, d) for n, d in entries(args.kind) if args.all or args.name.upper() in n
    ]
    if not targets:
        print("あてはまる 説明が ありません")
        return 1
    n_err = n_warn = 0
    for name, desc in targets:
        errors, warns = check(args.kind, name, desc)
        if errors or warns or not args.all:
            print(f"{name}: {visible(desc).replace(chr(92) + 'n', ' / ')}")
            for e in errors:
                print(f"  エラー: {e}")
            for w in warns:
                print(f"  注意: {w}")
        n_err += len(errors)
        n_warn += len(warns)
    print(f"-- {len(targets)} 件: エラー {n_err} / 注意 {n_warn}")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
