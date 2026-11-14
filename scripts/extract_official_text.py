#!/usr/bin/env python3
"""元の 日本語版 ファイアレッド（BPRJ）の 台詞を ラベルごとに 取り出し、手元の 控えに 書き出す。

だれの 台詞かは pokefirered（vendor/pokefirered）の 台本と 地図から つける:
  - ラベルの 名前に ある 人物（Rival → グリーン、Misty → カスミ など）
  - trainerbattle の トレーナー（種類と 名前。種類の 日本語は src/battle_main.c の 表）
  - 話しかけた 人の 見た目（map.json の graphics_id → src/data/speaker_npc_labels.h の 名札）
  - 看板（MSGBOX_SIGN）・地の文（{PLAYER}は 〜を もらった！ の 形）

**公式の 文は スキルの フォルダに 置かない**（スキルは 公開 リポジトリ）。控えは 既定で
~/.cache/pokemon-event-text/official_frlg.jsonl に 書く。ROM は 読むだけで、どこにも 写さない。
主人公の 家（PalletTown_PlayersHouse_* / PlayersHouse_*）の 台詞と 台本は 読まずに 外す。

使い方（改造の リポジトリの 根で）:
  python3 -I .claude/skills/pokemon-event-text/scripts/extract_official_text.py
  python3 -I .../extract_official_text.py --baserom roms/baserom_fr.gba --out ~/.cache/pokemon-event-text/official_frlg.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUT = Path.home() / ".cache" / "pokemon-event-text" / "official_frlg.jsonl"
ROM_BASE = 0x08000000

# 主人公の 家は 読まない・書き出さない（ユーザーの 決まり）
EXCLUDED_DIR_PREFIX = "PalletTown_PlayersHouse"
# 家の 中で 使う 共通の 文（おかあさんの 台詞）も 外す
EXCLUDED_LABEL_RE = re.compile(r"PlayersHouse|^Text_Mom|^Text_HadQuiteAnExperienceTakeRest$")
EXCLUDED_TAGS = {"おかあさん"}

# ラベルの 名前（CamelCase の 語）→ 人物。語が 1つでも 合えば その 人
NAMED_WORDS: dict[str, str] = {
    "Rival": "グリーン", "Champion": "グリーン",
    "Oak": "オーキド", "Daisy": "ナナミ",
    "Brock": "タケシ", "Misty": "カスミ", "Surge": "マチス", "Erika": "エリカ",
    "Koga": "キョウ", "Sabrina": "ナツメ", "Blaine": "カツラ", "Giovanni": "サカキ",
    "Lorelei": "カンナ", "Bruno": "シバ", "Agatha": "キクコ", "Lance": "ワタル",
    "Bill": "マサキ", "Fuji": "フジろうじん", "Celio": "ニシキ",
}
# 人物 → その 人の 見た目の 名前に ふくまれる 語（ラベルの 名前が 合っても、別の 人が 話して いれば そちらを とる）
NAMED_GFX = {
    "グリーン": ("BLUE", "RIVAL"), "オーキド": ("OAK",), "ナナミ": ("DAISY",), "タケシ": ("BROCK",),
    "カスミ": ("MISTY",), "マチス": ("SURGE",), "エリカ": ("ERIKA",), "キョウ": ("KOGA",),
    "ナツメ": ("SABRINA",), "カツラ": ("BLAINE",), "サカキ": ("GIOVANNI",), "カンナ": ("LORELEI",),
    "シバ": ("BRUNO",), "キクコ": ("AGATHA",), "ワタル": ("LANCE",), "マサキ": ("BILL",),
    "フジろうじん": ("FUJI",), "ニシキ": ("CELIO",),
    "ロケットだん（したっぱ）": ("ROCKET",), "ロケットだん（かんぶ）": ("ROCKET",),
}
GRUNT_WORDS = {"Grunt", "Grunts", "Rocket", "Rockets"}
ADMIN_WORDS = {"Admin", "Admins", "Executive"}

TEXT_TOKEN_RE = re.compile(r"\b([A-Za-z0-9_]+)\b")
LABEL_LINE_RE = re.compile(r"^([A-Za-z0-9_]+)::?\s*(@.*)?$")
TEXTCOLOR_RE = re.compile(r"^\s*textcolor\s+(\w+)")
TRAINERBATTLE_RE = re.compile(r"^\s*(trainerbattle\w*)\s+(.*)$")
SYSTEM_RE = re.compile(r"^\{PLAYER\}(は|の|が)")
PREFIX_RE = re.compile(r"(?:^|\\p)(\{RIVAL\}|[^\s　『「{}\\$]{1,8})『")
PREFIX_ALIASES = {"{RIVAL}": "グリーン"}
SYSTEM_VERB_RE = re.compile(r"(もらった|うけとった|てに[　 ]?いれた|なかまに[　 ]?なった|わたした|しまった|つかった|おぼえた)")


def find_repo_root() -> Path:
    for p in [Path.cwd(), *Path.cwd().parents, SKILL_DIR, *SKILL_DIR.parents]:
        if (p / "charmap.txt").exists() and (p / "tools" / "bprj_text").is_dir():
            return p
    sys.exit("[ERROR] 改造の リポジトリ（charmap.txt と tools/bprj_text の ある 所）が 見つかりません")


def camel_words(label: str) -> list[str]:
    tail = label.split("_Text_", 1)[-1]
    return re.findall(r"[A-Z][a-z]+|[A-Z]+(?![a-z])|\d+", tail.replace("_", " "))


# ---------- 名札の 表（この 改造の src から） ----------

def load_gfx_labels(root: Path) -> dict[str, str]:
    """OBJ_EVENT_GFX_* → 名札（src/data/speaker_npc_labels.h）"""
    path = root / "src" / "data" / "speaker_npc_labels.h"
    text = path.read_text(encoding="utf-8")
    names = dict(re.findall(r'static const u8 (sLabel_\w+)\[\] = _\("([^"]*)"\)', text))
    return {gfx: names[var] for gfx, var in re.findall(r"\{\s*(OBJ_EVENT_GFX_\w+),\s*(sLabel_\w+)\s*\}", text) if var in names}


def load_trainer_class_names(root: Path) -> dict[str, str]:
    """TRAINER_CLASS_* → 種類の 名前（src/battle_main.c）"""
    text = (root / "src" / "battle_main.c").read_text(encoding="utf-8")
    out = {}
    for cls, name in re.findall(r"\[(TRAINER_CLASS_\w+)\]\s*=\s*\{\s*_\(\"([^\"]*)\"\)", text):
        out[cls] = name.replace("{JPN}", "")
    return out


def load_vendor_trainer_classes(vendor: Path) -> dict[str, str]:
    """TRAINER_* → TRAINER_CLASS_*（pokefirered の src/data/trainers.h）"""
    text = (vendor / "src" / "data" / "trainers.h").read_text(encoding="utf-8")
    return dict(re.findall(r"\[(TRAINER_\w+)\]\s*=\s*\{\s*\.trainerClass\s*=\s*(TRAINER_CLASS_\w+)", text))


# ---------- pokefirered の 台本を 読む ----------

def script_files(vendor: Path) -> list[Path]:
    files = []
    for p in sorted((vendor / "data" / "maps").glob("*/scripts.inc")):
        if not p.parent.name.startswith(EXCLUDED_DIR_PREFIX):
            files.append(p)
    files += sorted((vendor / "data" / "scripts").glob("*.inc"))
    return files


def parse_scripts(vendor: Path, text_labels: set[str]):
    """台本を ラベルの かたまりに 分けて、使う 文・行き先・トレーナー・文字の 色を 集める"""
    blocks: dict[str, dict] = {}
    file_of: dict[str, str] = {}
    for path in script_files(vendor):
        cur = None
        color = None
        map_name = path.parent.name if path.parent.parent.name == "maps" else None
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            code = line.split("@", 1)[0]
            m = LABEL_LINE_RE.match(code.strip()) if not code.startswith((" ", "\t")) else None
            if m:
                cur = {"texts": [], "next": [], "map": map_name}
                blocks[m.group(1)] = cur
                file_of[m.group(1)] = str(path)
                color = None
                continue
            if cur is None or not code.strip():
                continue
            tm = TEXTCOLOR_RE.match(code)
            if tm:
                color = tm.group(1)
                continue
            bm = TRAINERBATTLE_RE.match(code)
            if bm:
                args = [a.strip() for a in bm.group(2).split(",")]
                trainer = args[0] if args and args[0].startswith("TRAINER_") else None
                texts = [a for a in args if a in text_labels]
                for k, t in enumerate(texts):
                    role = "intro" if k == 0 and "no_intro" not in bm.group(1) and "earlyrival" not in bm.group(1) else "after"
                    if "rematch" in bm.group(1) and role == "intro":
                        role = "rematch"
                    cur["texts"].append({"label": t, "trainer": trainer, "role": role, "color": color})
                for a in args:
                    if a in blocks or re.match(r"\w+_EventScript_\w+", a):
                        cur["next"].append(a)
                continue
            sign = "MSGBOX_SIGN" in code
            for tok in TEXT_TOKEN_RE.findall(code):
                if tok in text_labels:
                    cur["texts"].append({"label": tok, "trainer": None, "role": "sign" if sign else None, "color": color})
                elif "_EventScript_" in tok or tok.startswith("EventScript_"):
                    cur["next"].append(tok)
    return blocks, file_of


def parse_map_objects(vendor: Path) -> dict[str, list[tuple[str, str]]]:
    """スクリプトの ラベル → [(地図, 見た目)]。看板は 見た目 'SIGN'"""
    out: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in sorted((vendor / "data" / "maps").glob("*/map.json")):
        if path.parent.name.startswith(EXCLUDED_DIR_PREFIX):
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        name = path.parent.name
        for ev in data.get("object_events") or []:
            if ev.get("script") and ev["script"] != "0x0":
                out[ev["script"]].append((name, ev.get("graphics_id", "")))
        for ev in data.get("bg_events") or []:
            if ev.get("script") and ev.get("type") == "sign":
                out[ev["script"]].append((name, "SIGN"))
    return out


def reach(blocks: dict, start: str, limit: int = 60) -> list[tuple[str, dict]]:
    """start から goto/call で たどれる 文（近い 順）"""
    seen, out, q = {start}, [], deque([start])
    while q and len(seen) < limit:
        b = blocks.get(q.popleft())
        if not b:
            continue
        out.extend((t["label"], t) for t in b["texts"])
        for n in b["next"]:
            if n not in seen and n in blocks:
                seen.add(n)
                q.append(n)
    return out


# ---------- 文を 読む ----------

def load_decoder(root: Path):
    sys.path.insert(0, str(root / "tools" / "bprj_text"))
    import extract_text  # noqa: E402  改造の リポジトリの 道具（ビルドと 同じ 読み方）
    chars, names = extract_text.load_charmap()
    return lambda data: extract_text.decode(data, chars, names)


def rom_reader(rom: bytes, decode):
    def read(addr: str, length: int) -> str:
        off = int(addr, 16) - ROM_BASE
        return "".join(decode(rom[off:off + length]))
    return read


def classify_kind(label: str, info: dict | None, text: str, speaker: str | None) -> str:
    words = camel_words(label)
    role = (info or {}).get("role")
    if role == "sign" or "Sign" in words:
        return "看板"
    if role == "rematch" or ("Rematch" in words and "Intro" in words):
        return "再戦"
    if words and words[-1] == "Victory":
        return "勝ったとき"
    if role == "intro" or (words and words[-1] == "Intro"):
        return "勝負のまえ"
    if (words and words[-1] in ("Defeat", "Defeated")) or (info and info.get("trainer") and role == "after" and "Defeat" in words):
        return "負け"
    if "PostBattle" in "".join(words) or (words[-2:] == ["Post", "Battle"]):
        return "勝負のあと"
    body = text.rstrip("$")
    if SYSTEM_RE.match(body) and SYSTEM_VERB_RE.search(body.split("\\p")[0]):
        return "地の文"
    if (info or {}).get("color") == "NPC_TEXT_COLOR_NEUTRAL" and speaker is None:
        return "地の文"
    return "台詞"


def prefix_speakers(text: str) -> list[str]:
    """ページの 頭の「名前『」（公式の 台詞にも ある 名札）。出た 順に 重ねずに"""
    out = []
    for m in PREFIX_RE.finditer(text):
        name = PREFIX_ALIASES.get(m.group(1), m.group(1))
        if name not in out:
            out.append(name)
    return out


TRAINER_PEOPLE = (
    ("RIVAL", "グリーン"), ("CHAMPION", "グリーン"), ("GIOVANNI", "サカキ"), ("BOSS", "サカキ"),
    ("ADMIN", "ロケットだん（かんぶ）"), ("ROCKET", "ロケットだん（したっぱ）"), ("GRUNT", "ロケットだん（したっぱ）"),
    ("LEADER_BROCK", "タケシ"), ("LEADER_MISTY", "カスミ"), ("LEADER_LT_SURGE", "マチス"), ("LEADER_ERIKA", "エリカ"),
    ("LEADER_KOGA", "キョウ"), ("LEADER_SABRINA", "ナツメ"), ("LEADER_BLAINE", "カツラ"),
    ("ELITE_FOUR_LORELEI", "カンナ"), ("ELITE_FOUR_BRUNO", "シバ"), ("ELITE_FOUR_AGATHA", "キクコ"),
    ("ELITE_FOUR_LANCE", "ワタル"),
)


def named_speaker(label: str, trainer: str | None) -> str | None:
    """トレーナーなら トレーナーの 名前だけで、ちがえば ラベルの 語で 決める（PAINTER_DAISY は ナナミでは ない）"""
    if trainer:
        return next((name for key, name in TRAINER_PEOPLE if key in trainer), None)
    words = camel_words(label)
    for w in words:
        if w in NAMED_WORDS:
            return NAMED_WORDS[w]
    if set(words) & ADMIN_WORDS:
        return "ロケットだん（かんぶ）"
    if set(words) & GRUNT_WORDS:
        return "ロケットだん（したっぱ）"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="日本語版 FR の 台詞を だれの 台詞か つけて 控えに 書き出す")
    ap.add_argument("--baserom", type=Path, help="日本語版 FR（BPRJ）の ROM。既定は <リポジトリ>/roms/baserom_fr.gba")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"控え（既定 {DEFAULT_OUT}）")
    args = ap.parse_args()

    root = find_repo_root()
    vendor = root / "vendor" / "pokefirered"
    db = json.loads((root / "tools" / "data" / "bprj_text_symbols.json").read_text(encoding="utf-8"))
    rom_path = args.baserom or root / "roms" / "baserom_fr.gba"
    out = args.out.expanduser().resolve()
    if SKILL_DIR in out.parents:
        sys.exit("[ERROR] 控えを スキルの フォルダの 中には 書かない（公開 リポジトリ）")
    try:
        rom = rom_path.read_bytes()
    except OSError as e:
        sys.exit(f"[ERROR] ROM を 読めません: {e}")
    if hashlib.sha1(rom).hexdigest() != db["rom_sha1"]:
        sys.exit(f"[ERROR] {rom_path} は 日本語版 FR（BPRJ）の 未改変 ROM では ありません")

    read = rom_reader(rom, load_decoder(root))
    text_db = {k: v for k, v in db["text"].items() if not EXCLUDED_LABEL_RE.search(k)}
    blocks, _ = parse_scripts(vendor, set(text_db))
    objects = parse_map_objects(vendor)
    gfx_names = load_gfx_labels(root)
    class_names = load_trainer_class_names(root)
    vendor_classes = load_vendor_trainer_classes(vendor)
    trainer_names = {}
    for t, (addr, length) in db.get("trainer_names", {}).items():
        try:
            trainer_names[t] = read(addr, length).rstrip("$")
        except (ValueError, IndexError):
            pass

    # 文 → 使われる 所（直接 かかる ブロック と、たどった 人の 見た目）
    direct: dict[str, dict] = {}
    for name, b in blocks.items():
        for t in b["texts"]:
            prev = direct.get(t["label"])
            if prev is None or (t["trainer"] and not prev.get("trainer")) or (t["role"] and not prev.get("role")):
                direct[t["label"]] = {**t, "map": b["map"], "script": name}
    via_object: dict[str, tuple[str, str]] = {}
    for script, places in objects.items():
        for label, _info in reach(blocks, script):
            via_object.setdefault(label, places[0])

    rows, failed = [], 0
    for label, (addr, length) in sorted(text_db.items()):
        try:
            text = read(addr, length)
        except (ValueError, IndexError):
            failed += 1
            continue
        info = direct.get(label)
        trainer = info.get("trainer") if info else None
        place = via_object.get(label)
        map_name = (info or {}).get("map") or (place[0] if place else None) or label.split("_Text_")[0]
        gfx = place[1] if place else None
        tclass = vendor_classes.get(trainer) if trainer else None
        tclass_jp = (class_names.get(f"{tclass}_FRLG") or class_names.get(tclass or "")) if tclass else None
        tags = prefix_speakers(text)
        by_label = named_speaker(label, trainer)
        if (by_label and not trainer and gfx and (gfx == "SIGN" or gfx in gfx_names)
                and not any(k in gfx for k in NAMED_GFX.get(by_label, ()))):
            by_label = None     # ラベルの 人に ついて 話す 町の 人・看板（場面の 中の 名前の ある 人は のこす）
        speaker = tags[0] if tags else by_label
        source = ("tag" if tags else "label") if speaker else None
        if speaker is None and tclass_jp:
            speaker, source = tclass_jp, "trainer"
        if speaker is None and gfx == "SIGN":
            speaker, source = "かんばん", "sign"
        if speaker is None and gfx:
            person = next((n for n, keys in NAMED_GFX.items() if "ロケット" not in n and any(k in gfx for k in keys)), None)
            if person:
                speaker, source = person, "graphics"
        if speaker is None and gfx and gfx in gfx_names:
            speaker, source = gfx_names[gfx], "graphics"
        if EXCLUDED_TAGS & set(tags):
            continue
        kind = classify_kind(label, info, text, speaker)
        if kind == "地の文" and not tags:
            speaker, source = "システム", "system"
        rows.append({
            "label": label, "map": map_name, "speaker": speaker, "speaker_from": source,
            "kind": kind, "tags": tags, "trainer": trainer, "trainer_class": tclass_jp,
            "trainer_name": trainer_names.get(trainer) if trainer else None,
            "graphics": gfx, "color": (info or {}).get("color"), "text": text,
        })

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    named = sum(1 for r in rows if r["speaker"])
    print(f"{out} に {len(rows)} 件（話し手つき {named} 件、読めなかった 文 {failed} 件、主人公の 家は 外した）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
