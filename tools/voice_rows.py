"""Build the voice-clip translation work file (docs/voice_subtitles.md).

Usage:
  python tools/voice_rows.py [--muf <Ultimate Frontier project>]   build / refresh work/translation/en/voice/voice.json
  python tools/voice_rows.py --stats                                print counts only

Ported from Macross Ultimate Frontier. Ace Frontier shares most of its clips
with MUF (byte-identical files, see tools/voice_transcribe.py --reuse), so a
clip whose transcript was reused from a MUF clip takes that clip's reviewed
English, flags and notes from the MUF project (its work file, then its slices,
then `same_as` repeats resolved), and is marked `muf` = the MUF clip id.
Only the other clips go into the AF slices. Most of them are the same line
recorded again (same clip id, about the same length), so such a row carries
`muf_ref`: the MUF clip's transcript and English, as a reference only.

Inputs:
  work/source/voice/transcripts.json          Whisper output (Japanese, local)
  work/translation/en/voice/speakers.en.json  who speaks each prefix
  data/script/*.fes                           which missions use which clip numbers
  <MUF>/work/translation/en/voice/            voice.json and slices/vslice_*.en.json

Output (gitignored, holds Japanese): work/translation/en/voice/voice.json
  rows: row, id, prefix, num, speaker, series, jp, dur, whisper, missions
  (a hint only), skip, same_as, muf, en, flags, notes.
AF slices (work/translation/en/voice/slices/vslice_NNN.en.json) win over the
work file and over MUF.

Row order (80 rows per slice): the clips to translate (operators by number,
custom pilots by number, named characters by series, speaker, number), then
after the slices the clips with nothing to translate (skipped or repeats of
an earlier clip of the same character) and the clips that have MUF English.
"""

import glob
import json
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VDIR = os.path.join(ROOT, "work", "translation", "en", "voice")
WORK = os.path.join(VDIR, "voice.json")
SLICES = os.path.join(VDIR, "slices")
TRANSCRIPTS = os.path.join(ROOT, "work", "source", "voice", "transcripts.json")
SCRIPTS = os.path.join(ROOT, "work", "source", "dat", "data", "script")
MUF = os.path.join(os.path.dirname(ROOT), "Macross Ultimate Frontier")
SLICE_ROWS = 80

OPERATORS = ["o0_of0", "o0_of1", "o0_om0", "os_mis"]
CUSTOM = ["p0_om0", "p0_om1", "p0_of0", "p0_of1"]
SERIES_ORDER = ["Macross Zero", "SDF Macross", "Macross: Do You Remember Love?", "Macross Plus",
                "Macross 7", "Macross Dynamite 7", "Macross Frontier", "Macross II"]
MAX_MISSIONS = 6   # a clip number used by more missions than this is a stock line


def fes_numbers():
    """clip number -> sorted list of mission ids whose script pool has that number."""
    use = {}
    for f in sorted(glob.glob(os.path.join(SCRIPTS, "*.fes"))):
        d = open(f, "rb").read()
        pool = struct.unpack_from("<H", d, 0x12)[0]
        mid = os.path.basename(f)[:-4].upper()
        for s in set(d[pool:].split(b"\0")):
            if re.fullmatch(rb"\d{3,4}", s):
                use.setdefault(int(s), set()).add(mid)
    return {n: sorted(m) for n, m in use.items()}


def skip_reason(cid, num, t):
    if not cid.startswith("v"):
        return "sound effect"
    if cid.startswith("vp") and 900 <= num < 1000:
        return "era prologue narration: already on screen as English text"
    if "silent" in t.get("flags", []):
        return "no speech: silent placeholder clip"
    if "hallucination" in t.get("flags", []):
        return "no speech Whisper could read (shout, drums, effect)"
    return ""


def muf_lines(muf):
    """MUF clip id -> {en, flags, notes, skip} as MUF's export sees it."""
    vdir = os.path.join(muf, "work", "translation", "en", "voice")
    rows = json.load(open(os.path.join(vdir, "voice.json"), encoding="utf-8"))["rows"]
    out = {r["id"]: {"en": r.get("en", ""), "flags": r.get("flags", []), "notes": r.get("notes", ""),
                     "skip": r["skip"], "same_as": r.get("same_as", "")} for r in rows}
    for p in sorted(glob.glob(os.path.join(vdir, "slices", "vslice_*.en.json"))):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            out[r["id"]].update({k: r[k] for k in ("en", "flags", "notes") if k in r})
    for o in out.values():
        if o["same_as"]:
            src = out.get(o["same_as"], {})
            o.update(en=src.get("en", ""), flags=src.get("flags", []), notes=src.get("notes", ""))
    return out


def build(muf=MUF):
    trans = json.load(open(TRANSCRIPTS, encoding="utf-8"))
    speakers = json.load(open(os.path.join(VDIR, "speakers.en.json"), encoding="utf-8"))["speakers"]
    uses = fes_numbers()
    mlines = muf_lines(muf)
    mtrans = json.load(open(os.path.join(muf, "work", "source", "voice", "transcripts.json"), encoding="utf-8"))
    old = {}
    if os.path.exists(WORK):
        old = {r["id"]: r for r in json.load(open(WORK, encoding="utf-8"))["rows"] if not r.get("muf")}
    sliced = {}
    for p in sorted(glob.glob(os.path.join(SLICES, "vslice_*.en.json"))):
        for r in json.load(open(p, encoding="utf-8"))["rows"]:
            sliced[r["id"]] = {k: r[k] for k in ("en", "flags", "notes") if k in r}
            old.setdefault(r["id"], {}).update(sliced[r["id"]])

    clips = {}
    for cid in trans:
        m = re.fullmatch(r"v(\w+?)_(\d+)", cid)
        if m and m.group(1) in speakers:
            clips[cid] = (m.group(1), int(m.group(2)))

    def key(cid):
        prefix, num = clips[cid]
        if prefix in OPERATORS:
            return (0, num, OPERATORS.index(prefix))
        if prefix in CUSTOM:
            return (1, num, CUSTOM.index(prefix))
        sp = speakers[prefix]
        series = SERIES_ORDER.index(sp["series"]) if sp["series"] in SERIES_ORDER else 99
        return (2, series, sp["name"], prefix, num)

    def from_muf(cid):
        src = trans[cid].get("reused_from", "")
        return src if src in mlines else ""

    order, first, dups = sorted(clips, key=key), {}, {}
    for cid in order:
        prefix = clips[cid][0]
        if prefix in OPERATORS or prefix in CUSTOM or from_muf(cid):
            continue
        k = (speakers[prefix]["name"], trans[cid]["jp"])
        if trans[cid]["jp"] and k in first:
            dups[cid] = first[k]
        else:
            first.setdefault(k, cid)

    def tail_row(c):
        prefix, num = clips[c]
        if from_muf(c) or c in dups:
            return True
        return prefix not in OPERATORS and prefix not in CUSTOM and bool(skip_reason(c, num, trans[c]))
    tail = [c for c in order if tail_row(c)]
    order = [c for c in order if c not in tail] + tail

    rows = []
    for i, cid in enumerate(order, 1):
        prefix, num = clips[cid]
        t, sp = trans[cid], speakers[prefix]
        src = from_muf(cid)
        if src:
            ml = mlines[src]
            o = dict({"en": ml["en"], "flags": ml["flags"], "notes": ml["notes"]}, **sliced.get(cid, {}))
            skip = skip_reason(cid, num, t) or (ml["skip"] if ml["skip"] and not ml["same_as"] else "")
        else:
            o = old.get(cid, {})
            skip = skip_reason(cid, num, t) or ("same line as " + dups[cid] if cid in dups else "")
        missions = uses.get(num, [])
        rows.append({
            "row": i, "id": cid, "prefix": prefix, "num": num,
            "speaker": sp["name"], "series": sp["series"],
            "jp": t["jp"], "dur": t["dur"], "whisper": t["flags"],
            "missions": missions if len(missions) <= MAX_MISSIONS else ["(stock line, %d missions)" % len(missions)],
            "skip": skip, "same_as": dups.get(cid, ""), "muf": src,
            "muf_ref": {"jp": mtrans[cid]["jp"], "dur": mtrans[cid]["dur"], "en": mlines[cid]["en"]}
            if not src and cid in mlines and cid in mtrans else None,
            "en": o.get("en", ""), "flags": o.get("flags", []), "notes": o.get("notes", ""),
        })
    to_slice = len(order) - len(tail)
    meta = {"about": "Voice-clip subtitles (docs/voice_subtitles.md). Rows hold Japanese: not for git; "
                     "the slices are the committed copy. Rows with `muf` take Ultimate Frontier's English.",
            "slice_rows": SLICE_ROWS, "slices": -(-to_slice // SLICE_ROWS), "after_slices": len(rows) - to_slice}
    return {"_meta": meta, "rows": rows}


def main():
    muf = sys.argv[sys.argv.index("--muf") + 1] if "--muf" in sys.argv else MUF
    d = build(muf)
    rows = d["rows"]
    print("%d rows: %d in %d slices; %d from MUF (%d with English); %d skipped, %d repeats; %d with English"
          % (len(rows), len(rows) - d["_meta"]["after_slices"], d["_meta"]["slices"],
             sum(1 for r in rows if r["muf"]), sum(1 for r in rows if r["muf"] and r["en"]),
             sum(1 for r in rows if r["skip"] and not r["same_as"]), sum(1 for r in rows if r["same_as"]),
             sum(1 for r in rows if r["en"])))
    if "--stats" in sys.argv:
        return
    json.dump(d, open(WORK, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", WORK)


if __name__ == "__main__":
    main()
