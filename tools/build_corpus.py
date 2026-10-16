"""Build the translation work file: every distinct Japanese string of Ace Frontier, once.

Usage: python tools/build_corpus.py [--dry-run]

Sources (from tools/dump_text.py and tools/dump_eboot.py, work/source/text/):
  eboot_strings.json   all menu, system, mission, profile, narration and name text
  fes_strings.json     mission script strings (objectives, tutorial lines)
  locate_names.json    mission unit display names

Each distinct Japanese string becomes ONE row with every place it occurs in "occ".
Rows are in game order, so neighbours give context. "group" says what kind of
text it is (EBOOT offset ranges, see docs/formats.md). Story-like groups
(mission, narration, profile, unit_desc, ingame) are cut into slices of 80 rows
(BASE_RULES); the UI groups into slices of up to 4,500 characters / 320 rows,
as in the MUF project.

Prefill: where the Macross Ultimate Frontier translation has the identical
Japanese string, its English is copied with status "tm" (translators review it).

Skipped: strings without kana/kanji, editor-only unit-list labels
(デモ用/顔絵用/ダミー/削除/テスト/予定) and the renderer's glyph test string.

Byte limits: EBOOT strings flagged in_place (pilot table) or inline_copy keep
their place, so "max_bytes" = capacity - 1.

Output: work/translation/en/corpus.json (gitignored: contains Japanese).
Existing English/flags/notes are carried over by the Japanese text.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "work", "source", "text")
OUT = os.path.join(ROOT, "work", "translation", "en", "corpus.json")
MUF_TR = os.path.join(ROOT, "..", "Macross Ultimate Frontier", "work", "translation", "en")
JPW = re.compile(r"[぀-ヿ㐀-鿿]")
INTERNAL = re.compile(r"デモ用|顔絵用|ダミー|^削除$|テスト|予定")
SKIP_IDS = {"eboot:241D6C"}  # full-width glyph test string of the renderer
STORY = {"mission", "narration", "profile", "unit_desc", "ingame"}
SLICE_ROWS_STORY = 80
SLICE_CHARS, SLICE_ROWS = 4500, 320
MIN_SLICE = 20
NL = chr(10)

# EBOOT file offset ranges -> group (docs/formats.md)
RANGES = [
    (0x24E9C8, 0x251380, "pilot_table"),
    (0x258FD0, 0x25A7A0, "unit_table"),
    (0x25AE3C, 0x264480, "mission"),
    (0x264480, 0x266B00, "stage_weapon"),
    (0x266B00, 0x26A3F0, "unit_desc"),
    (0x26C664, 0x26CC60, "skill"),
    (0x26CD40, 0x26E1E0, "narration"),
    (0x26EDE8, 0x26F09C, "profile"),
    (0x277E28, 0x278E70, "sound_test"),
    (0x27B954, 0x27BA6C, "rank"),
    (0x27BA6C, 0x27CF70, "profile"),
    (0x27D400, 0x27F030, "title"),
]


def group_of(off):
    for lo, hi, g in RANGES:
        if lo <= off < hi:
            return g
    return "ui"


def muf_tm():
    tm = {}
    for f in ("dialogue.json", "ui.json", "internal_labels.json", "ui_insert.json"):
        p = os.path.join(MUF_TR, f)
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        for r in (d["rows"] if isinstance(d, dict) else d):
            if r.get("jp") and r.get("en"):
                tm.setdefault(r["jp"], r["en"])
    return tm


def main():
    dry = "--dry-run" in sys.argv
    occ = []
    skipped = {"no_japanese": 0, "tail": 0, "internal": 0}
    for x in sorted(json.load(open(os.path.join(TEXT, "eboot_strings.json"), encoding="utf-8")), key=lambda e: e["offset"]):
        if x["id"] in SKIP_IDS:
            continue
        if x.get("tail_of"):
            skipped["tail"] += 1
            continue
        if not JPW.search(x["jp"]):
            skipped["no_japanese"] += 1
            continue
        o = {"id": x["id"], "ref": {"file": "EBOOT.BIN", "offset": x["offset"], "bytes": x["bytes"]}}
        if x.get("note"):  # not text (dump_eboot NOT_TEXT): kept so row ids stay stable, never translated
            o["not_text"] = x["note"]
        if x.get("in_place") or x.get("inline_copy"):
            o["max_bytes"] = x["capacity"] - 1
        occ.append((group_of(x["offset"]), x["jp"], o))
    for x in json.load(open(os.path.join(TEXT, "fes_strings.json"), encoding="utf-8")):
        occ.append(("ingame", x["jp"], {"id": "fes:" + x["id"], "ref": {"file": x["source"], "offset": x["offset"],
                                                                        "pool_offset": x["pool_offset"], "bytes": x["bytes"]}}))
    for x in json.load(open(os.path.join(TEXT, "locate_names.json"), encoding="utf-8")):
        if INTERNAL.search(x["jp"]):
            skipped["internal"] += 1
            continue
        if not JPW.search(x["jp"]):
            skipped["no_japanese"] += 1
            continue
        occ.append(("locate", x["jp"], {"id": "locate:" + x["id"], "ref": {"file": x["source"], "row": x["row"],
                                                                           "col": x["col"], "key": x["key"]}}))

    rows, by_jp = [], {}
    for grp, jp, o in occ:
        if jp not in by_jp:
            by_jp[jp] = {"group": grp, "jp": jp, "occ": []}
            rows.append(by_jp[jp])
        r = by_jp[jp]
        r["occ"].append(o)
        if "max_bytes" in o:
            r["max_bytes"] = min(r.get("max_bytes", 9999), o["max_bytes"])

    # re-wrapped text: the Japanese is hard-wrapped at a fixed width (often mid-word),
    # so the English is written as one paragraph and wrapped at build time.
    # wrap = {head: lines kept as written (a unit name), width: px at 14 px, lines: max lines}
    for r in rows:
        body = r["jp"].split(NL)
        tail = body[-1] == ""
        if tail:
            body = body[:-1]
        head = 0
        if r["group"] == "mission" and len(body) >= 3 and max(map(len, body)) >= 17:
            pass
        elif r["group"] == "profile" and len(body) >= 2 and max(map(len, body)) >= 25:
            pass
        elif r["group"] == "unit_desc" and len(body) >= 3 and max(map(len, body[1:])) >= 25:
            head = 1
        else:
            continue
        r["wrap"] = {"head": head, "lines": len(body) - head, "tail_newline": tail}
    for g in ("mission", "profile", "unit_desc"):
        w = [len(l) for r in rows if r["group"] == g and "wrap" in r for l in r["jp"].split(NL)[r["wrap"]["head"]:]]
        for r in rows:
            if r["group"] == g and "wrap" in r:
                r["wrap"]["width"] = max(w) * 14

    tm = muf_tm()
    old = {}
    if os.path.exists(OUT):
        old = {r["jp"]: r for r in json.load(open(OUT, encoding="utf-8"))["rows"]}
    sl, chars, n_in, story_prev = 0, 0, 0, None
    for i, r in enumerate(rows, 1):
        story = r["group"] in STORY
        full = (n_in >= SLICE_ROWS_STORY) if story else (chars + len(r["jp"]) > SLICE_CHARS or n_in >= SLICE_ROWS)
        if sl == 0 or full or story != story_prev:
            sl, chars, n_in = sl + 1, 0, 0
        story_prev = story
        chars += len(r["jp"])
        n_in += 1
        r["row"], r["slice"], r["id"] = i, sl, "u%04d" % i
        o = old.get(r["jp"], {})
        if any("not_text" in x for x in r["occ"]):
            r["en"], r["flags"], r["notes"], r["status"] = "", ["unfinished"], r["occ"][0]["not_text"], "not_text"
        elif o.get("en"):
            r["en"], r["flags"], r["notes"], r["status"] = o["en"], o.get("flags", []), o.get("notes", ""), o.get("status", "done")
        elif r["jp"] in tm:
            r["en"], r["flags"], r["notes"], r["status"] = tm[r["jp"]], [], "prefilled from the MUF translation", "tm"
        else:
            r["en"], r["flags"], r["notes"], r["status"] = "", [], "", "todo"

    # fold slices under MIN_SLICE rows into the previous slice, then renumber
    sizes = {}
    for r in rows:
        sizes[r["slice"]] = sizes.get(r["slice"], 0) + 1
    remap, n = {}, 0
    for k in sorted(sizes):
        if sizes[k] >= MIN_SLICE or n == 0:
            n += 1
        remap[k] = n
    for r in rows:
        r["slice"] = remap[r["slice"]]
    sl = n

    groups = {}
    for r in rows:
        g = groups.setdefault(r["group"], [0, 0, 0])
        g[0] += 1
        g[1] += r["status"] == "tm"
        g[2] += len(r["jp"])
    print("rows %d (occurrences %d), slices %d, chars %d" % (len(rows), len(occ), sl, sum(len(r["jp"]) for r in rows)))
    print("group: rows / prefilled / chars")
    for g, (n, t, c) in sorted(groups.items(), key=lambda kv: -kv[1][0]):
        print("  %-13s %5d %5d %6d" % (g, n, t, c))
    print("skipped", skipped, " prefilled", sum(r["status"] == "tm" for r in rows),
          " in-place limited", sum("max_bytes" in r for r in rows),
          " re-wrapped", {g: sum(1 for r in rows if r["group"] == g and "wrap" in r) for g in ("mission", "profile", "unit_desc")},
          " widths", {r["group"]: r["wrap"]["width"] for r in rows if "wrap" in r})
    per = {}
    for r in rows:
        per.setdefault(r["slice"], [r["group"], 0, 0])
        per[r["slice"]][1] += 1
        per[r["slice"]][2] += r["status"] == "todo"
    print("slices:", ", ".join("%d:%s %d (%d todo)" % (k, v[0], v[1], v[2]) for k, v in sorted(per.items())))
    if dry:
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"_meta": {"version": "0.1.0", "slice_rows_story": SLICE_ROWS_STORY, "slice_chars": SLICE_CHARS,
                             "slice_rows": SLICE_ROWS}, "rows": rows}, f, ensure_ascii=False, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
