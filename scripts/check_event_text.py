#!/usr/bin/env python3
"""イベントの台詞を ラベル単位で 調べる（pokemon-event-text スキルの 道具）。

tools/check_jp_text.py は リポジトリ全体の「.string の 引用符・衝突の 印・
日本語の 字が charmap に あるか」を 見る。こちらは それと 重ならない、
台詞の 中身と 形を ラベルごとに 見る:

  LEN    1行の 長さ（ふつうの 窓 27字・電話 24字を こえたら エラー、目安を こえたら 注意）
  LINES  1ページに \\n が 2つ 以上（窓は 2行。3行目は \\l で 送る）
  CHAR   charmap に ない 字（check_jp_text が 見ない ♪ ～ （ ） → なども）、漢字（かなで 書く）
  TAG    名札「名前『」の 形（ページの 頭だけ・8字まで・空白なし・「 で 書いて いない）
  CLOSE  閉じの 』（名札の ページに 』 が ある）
  CRY    ポケモンの 鳴き声を 「」で 囲んで いる
  WORD   禁止語・言いすぎの 言葉（banned_words.toml）
  CHARA  人物の 表（characters/*.toml）の [check] に 合わない 呼び方・言葉
  STYLE  {KUN} の 使い方、全角と 半角の 空白の まぜ書き

使い方:
  python3 check_event_text.py data/maps/Route9_Frlg/scripts.inc
  python3 check_event_text.py data/maps/Route9_Frlg/scripts.inc --label NanamiBye --label Ariana
  python3 check_event_text.py 下書き.inc --phone        # 電話の 文と して 見る
  python3 check_event_text.py ... --strict               # 注意でも 終了コード 1
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]

FIELD_MAX = 27          # ふつうの 窓: 幅 27 タイル × 8px、字は どれも 8px（src/menu.c, src/text.c）
FIELD_SOFT = 21         # いまの 台本の 行は ほぼ 21字 まで
PHONE_MAX = 24          # 電話の 窓: 幅 28 タイル、絵の 分 32px あけて 書く（src/match_call.c）
PHONE_SOFT = 20
SPEAKER_NAME_MAX = 8    # src/field_speaker_prefix.c の SPEAKER_NAME_MAX_GLYPHS

# 置きかえ文字の 字数（ふだん, いちばん 長い とき）
PLACEHOLDER_WIDTH = {
    "PLAYER": (5, 7),       # PLAYER_NAME_LENGTH 7
    "RIVAL": (5, 7),
    "KUN": (2, 3),          # くん / ちゃん
    "STR_VAR_1": (5, 7),
    "STR_VAR_2": (5, 7),
    "STR_VAR_3": (5, 7),
}

LABEL_RE = re.compile(r'^([A-Za-z0-9_]+):{1,2}\s*$')
STRING_RE = re.compile(r'^\s*\.string\s+"((?:\\.|[^"\\])*)"')
BRACE_RE = re.compile(r"\{([^}]*)\}")
KANA_RE = re.compile(r"[\u3040-\u30ff]")
KANJI_RE = re.compile(r"[\u3400-\u9fff]")
CRY_BODY_RE = re.compile(r"^「[\u30a0-\u30ffー・ッ！!？?…〜\s]+」$")


@dataclass
class Finding:
    level: str
    kind: str
    line_no: int
    label: str
    message: str
    text: str = ""


@dataclass
class TextBlock:
    label: str
    first_line: int
    raw: str                        # .string を つないだ 中身（$ まで）
    line_nos: list[int] = field(default_factory=list)


# ---------- 読みこみ ----------

def find_repo_root(start: Path) -> Path | None:
    for p in [start, *start.parents]:
        if (p / "charmap.txt").exists():
            return p
    return None


def charmap_lines(path: Path, depth: int = 0):
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r'^\.include\s+"([^"]+)"', line.strip())
        if m and depth < 8 and (path.parent / m.group(1)).exists():
            yield from charmap_lines(path.parent / m.group(1), depth + 1)
        else:
            yield line


def load_charmap(root: Path) -> tuple[set[str], set[str]]:
    """(charmap に ある 字, 漢字の 字の 一覧に ある 字)"""
    chars: set[str] = set()
    for line in charmap_lines(root / "charmap.txt"):
        m = re.match(r"^'((?:\\.|[^'\\])*)'\s*=", line.strip())
        if not m:
            continue
        raw = m.group(1)
        ch = {"\\'": "'", "\\\\": "\\"}.get(raw, raw)
        if len(ch) == 1:
            chars.add(ch)
    atlas: set[str] = set()
    atlas_path = root / "graphics/fonts/kanji/koden12_atlas.txt"
    if atlas_path.exists():
        atlas = set("".join(atlas_path.read_text(encoding="utf-8").split()))
    return chars, atlas


def load_toml(path: Path) -> dict:
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError) as e:
        print(f"[ERROR] {path} を 読めません: {e}", file=sys.stderr)
        return {}


def load_banned(path: Path) -> list[dict]:
    words = []
    for group in load_toml(path).get("group", []):
        for w in group.get("words", []):
            words.append({"word": w, "level": group.get("level", "WARN"),
                          "why": group.get("why", ""), "name": group.get("name", ""),
                          "anywhere": group.get("anywhere", False)})
    return words


def banned_regex(item: dict) -> re.Pattern[str]:
    chars = [re.escape(c) for c in item["word"] if c not in " 　"]
    body = r"[ 　]?".join(chars)
    if item["anywhere"]:
        return re.compile(body)
    return re.compile(r"(?:^|(?<=[ 　『「…！？!?、。／]))" + body)


def load_character_checks(chara_dir: Path) -> dict[str, dict]:
    """名札の 名前 → [check]"""
    checks: dict[str, dict] = {}
    for p in sorted(chara_dir.glob("*.toml")):
        data = load_toml(p)
        check = data.get("check", {})
        for name in check.get("tags", []):
            checks[name] = check
    return checks


def read_blocks(path: Path) -> tuple[list[TextBlock], set[str]]:
    """ラベルごとの 文と、pokenavcall で 使われる ラベル"""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    phone_labels = {m.group(1) for line in lines for m in [re.search(r"\bpokenavcall\s+([A-Za-z0-9_]+)", line)] if m}
    blocks: list[TextBlock] = []
    label = None
    cur: TextBlock | None = None
    for i, line in enumerate(lines, start=1):
        lm = LABEL_RE.match(line)
        if lm:
            label = lm.group(1)
            cur = None
            continue
        sm = STRING_RE.match(line)
        if sm and label:
            if cur is None:
                cur = TextBlock(label, i, "")
                blocks.append(cur)
            cur.raw += sm.group(1)
            cur.line_nos.append(i)
            continue
        if line.strip() and not line.strip().startswith("@"):
            cur = None
            if not line.startswith((" ", "\t")):
                label = None
    for b in blocks:
        b.raw = b.raw.split("$")[0]
    return blocks, phone_labels


# ---------- 文の 分解 ----------

def split_pages(raw: str) -> list[list[tuple[str, str]]]:
    """ページ → [(区切りの 種類, 行の 中身)]。区切りは 'start' 'n' 'l'"""
    pages = []
    for page in raw.split("\\p"):
        parts = re.split(r"(\\[nl])", page)
        rows = [("start", parts[0])]
        for k in range(1, len(parts), 2):
            rows.append((parts[k][1], parts[k + 1]))
        pages.append(rows)
    return pages


def speaker_prefix(text: str) -> tuple[str | None, str]:
    """ページの 頭の「名前『」を 取る。(名前, 残り)。名札で なければ (None, text)"""
    body = re.sub(r"^(\{(?!PLAYER|RIVAL|KUN|STR_VAR)[^}]*\})+", "", text)
    m = re.match(r"^([^『」「\s]{1,20}?)『", body)
    if not m:
        return None, text
    return m.group(1), body[m.end():]


def glyphs(text: str) -> list[str]:
    """{...} を ひとかたまりと した 字の 列"""
    out, pos = [], 0
    for m in BRACE_RE.finditer(text):
        out.extend(text[pos:m.start()])
        out.append(m.group(0))
        pos = m.end()
    out.extend(text[pos:])
    return out


def width(text: str) -> tuple[int, int]:
    """(ふだんの 字数, いちばん 長い ときの 字数)"""
    usual = worst = 0
    for g in glyphs(text):
        if g.startswith("{"):
            key = g[1:-1].strip()
            if key.startswith("0x"):
                usual += 1
                worst += 1
            elif key in PLACEHOLDER_WIDTH:
                a, b = PLACEHOLDER_WIDTH[key]
                usual += a
                worst += b
            continue
        usual += 1
        worst += 1
    return usual, worst


def name_glyph_count(name: str) -> int:
    return len([g for g in glyphs(name)])


# ---------- 調べる ----------

def check_block(b: TextBlock, is_phone: bool, charmap: set[str], atlas: set[str],
                banned: list[dict], chara: dict[str, dict]) -> list[Finding]:
    out: list[Finding] = []
    L = b.first_line

    def add(level, kind, msg, text=""):
        out.append(Finding(level, kind, L, b.label, msg, text))

    hard, soft = (PHONE_MAX, PHONE_SOFT) if is_phone else (FIELD_MAX, FIELD_SOFT)
    plain = BRACE_RE.sub("", b.raw).replace("\\n", "").replace("\\p", "").replace("\\l", "")

    # 字
    bad_chars = sorted({c for c in plain if c not in charmap and c not in atlas and c != "\\"})
    for c in bad_chars:
        add("ERROR", "CHAR", f"charmap に ない 字 {c!r}", c)
    kanji = sorted({c for c in plain if KANJI_RE.match(c)})
    if kanji:
        add("WARN", "CHAR", f"漢字が ある（台本は かなで 書く）: {''.join(kanji)}")

    # 空白の まぜ書き
    if " " in plain and "　" in plain:
        add("WARN", "STYLE", "半角と 全角の 空白が まざって いる（新しい 台詞は 半角に そろえる）")

    # {KUN}
    if re.search(r"(?<!\{PLAYER\})\{KUN\}", b.raw):
        add("WARN", "STYLE", "{KUN} の まえに {PLAYER} が ない")
    if re.search(r"\{PLAYER\}(くん|ちゃん)", b.raw):
        add("WARN", "STYLE", "{PLAYER}くん と 書かず {PLAYER}{KUN} に する")

    for pno, rows in enumerate(split_pages(b.raw), start=1):
        name, first_body = speaker_prefix(rows[0][1])
        page_lines = [first_body if i == 0 and name else r[1] for i, r in enumerate(rows)]
        page_text = "".join(page_lines)
        shown = " / ".join(page_lines)
        where = f"{pno}ページ"

        # 名札の 形
        if name is not None:
            if " " in name or "　" in name:
                add("ERROR", "TAG", f"{where}: 名札の 名前に 空白（名札に ならない）", name)
            elif name_glyph_count(name) > SPEAKER_NAME_MAX:
                add("ERROR", "TAG", f"{where}: 名札の 名前が {SPEAKER_NAME_MAX}字を こえる（名札に ならない）", name)
            first_line_rest = first_body
            if "』" in first_line_rest:
                add("ERROR", "CLOSE", f"{where}: 名札と 同じ 行に 』（題名と みなされ 名札に ならない）", rows[0][1])
            elif "』" in page_text:
                add("WARN", "CLOSE", f"{where}: 閉じの 』 は 書かない", shown)
        else:
            m = re.match(r"^([\u30a0-\u30ff{}A-Z_？]{1,10})[「:：]", rows[0][1])
            if m and "」" not in rows[0][1]:
                add("WARN", "TAG", f"{where}: 名札は「名前『」で 書く（「 や ： では 名札に ならない）", rows[0][1])
        for kind_, text in rows[1:]:
            if re.match(r"^[^『「\s]{1,8}『", text) and "』" not in text:
                add("ERROR", "TAG", f"{where}: 名札が 行の とちゅう（\\{kind_} の あと）。名札は ページの 頭だけ。\\p で 区切る", text)

        # 行の 数
        n_count = sum(1 for k, _ in rows if k == "n")
        if n_count > 1:
            add("ERROR", "LINES", f"{where}: \\n が {n_count}つ（窓は 2行。3行目からは \\l か \\p）")
        if rows[0][0] == "start" and len(rows) > 1 and rows[1][0] == "l":
            add("WARN", "LINES", f"{where}: 1行目の すぐ あとが \\l（2行目は \\n）")

        # 行の 長さ
        for i, text in enumerate(page_lines):
            usual, worst = width(text)
            if worst > hard:
                add("ERROR", "LEN", f"{where}: {worst}字（いちばん 長い 名前の とき）> 窓の {hard}字", text)
            elif usual > soft:
                add("WARN", "LEN", f"{where}: {usual}字 > 目安 {soft}字", text)

        # 鳴き声の かっこ
        body = page_text.strip()
        if CRY_BODY_RE.match(body):
            add("ERROR", "CRY", f"{where}: 鳴き声を 「」で 囲まない（名札を 付けるなら ピカチュウ『ピカッ！ の 形）", body)
        if name is not None and body.startswith("「"):
            add("WARN", "CRY", f"{where}: 名札の あとに 「（名札が あれば かっこは いらない）", body)

        # 人物の 表
        check = chara.get(name or "", {})
        if check:
            call = check.get("player_call")
            if call == "{PLAYER}{KUN}" and re.search(r"\{PLAYER\}(?!\{KUN\})", page_text):
                add("WARN", "CHARA", f"{where}: {name}は 主人公を {{PLAYER}}{{KUN}} と よぶ", shown)
            if call == "{PLAYER}" and "{PLAYER}{KUN}" in page_text:
                add("WARN", "CHARA", f"{where}: {name}は 主人公を 呼びすて（{{KUN}} を 付けない）", shown)
            for w in check.get("ng_words", []):
                if w in page_text:
                    add("WARN", "CHARA", f"{where}: {name}は「{w}」を 言わない（characters の [check]）", shown)

    # 禁止語（ラベル 全体で）
    # 台本は 文節ごとに 空白を 入れるので、字の あいだの 空白は あっても なくても よい。
    # anywhere で ない 組は 文節の 頭から だけ 照らす（「いじょう かち」を「じょうか」と とらない）
    joined = b.raw.replace("\\n", " ").replace("\\l", " ").replace("\\p", "／")
    for item in banned:
        if banned_regex(item).search(joined):
            add(item["level"], "WORD", f"「{item['word']}」{item['name']}: {item['why']}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="イベントの 台詞を ラベル単位で 調べる")
    ap.add_argument("files", nargs="+", type=Path)
    ap.add_argument("--label", action="append", default=[], help="ラベル名の 一部（何度でも）")
    ap.add_argument("--phone", action="store_true", help="ぜんぶ 電話の 文と して 見る")
    ap.add_argument("--root", type=Path, help="リポジトリの 根（charmap.txt の ある 所）")
    ap.add_argument("--banned", type=Path, default=SKILL_DIR / "banned_words.toml")
    ap.add_argument("--characters", type=Path, default=SKILL_DIR / "characters")
    ap.add_argument("--strict", action="store_true", help="注意（WARN）でも 終了コード 1")
    args = ap.parse_args()

    root = args.root or find_repo_root(Path.cwd()) or find_repo_root(SKILL_DIR)
    if root is None or not (root / "charmap.txt").exists():
        print("[ERROR] charmap.txt が 見つかりません。--root を 指定して ください")
        return 2
    charmap, atlas = load_charmap(root)
    banned = load_banned(args.banned)
    chara = load_character_checks(args.characters)

    total = {"ERROR": 0, "WARN": 0}
    checked = 0
    for path in args.files:
        if not path.exists():
            print(f"[ERROR] {path} が ありません")
            total["ERROR"] += 1
            continue
        blocks, phone_labels = read_blocks(path)
        all_labels = {b.label for b in blocks}
        for b in blocks:
            # ラベル名を まるごと 書いたら その ラベルだけ、一部なら ふくむ もの すべて
            if args.label and not any(b.label == s if s in all_labels else s in b.label for s in args.label):
                continue
            if not KANA_RE.search(b.raw):
                continue                    # 英語の まま の 文は 見ない
            checked += 1
            is_phone = args.phone or b.label in phone_labels or b.label.startswith("MatchCall_Text_")
            for f in check_block(b, is_phone, charmap, atlas, banned, chara):
                total[f.level] = total.get(f.level, 0) + 1
                tail = f"  | {f.text}" if f.text else ""
                print(f"{path}:{f.line_no}: [{f.level}] {f.kind} {f.label}: {f.message}{tail}")
    print(f"-- {checked} ラベル: エラー {total['ERROR']} / 注意 {total['WARN']}")
    if total["ERROR"] or (args.strict and total["WARN"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
