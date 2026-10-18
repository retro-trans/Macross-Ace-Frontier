"""Rewrite the romanized HUD target labels in the EBOOT, in place.

Usage:
  python tools/hud_labels.py <in EBOOT> <out EBOOT> [--labels work/translation/en/hud_labels.en.json] [--dry-run]

Next to each Japanese unit and object name, the unit table holds an all-caps ASCII name that the
HUD's lock-on label shows ("BARAUTA SHIP(F)"). The developers' romanizations differ from the
glossary (BARAUTA / BAJURA for Varauta / Vajra). Each row of the labels file gives the file offset,
the original label and the English one. The original must be at that offset, and the new label must
fit in the zero bytes after it (it is written over them, NUL-padded). The labels are in the text
segment, which tools/eboot_insert.py does not move, so the offsets hold on a patched EBOOT too.
"""
import json
import os
import sys


def main():
    args = sys.argv[1:]
    labels = os.path.join("work", "translation", "en", "hud_labels.en.json")
    if "--labels" in args:
        i = args.index("--labels")
        labels = args[i + 1]
        del args[i:i + 2]
    dry = "--dry-run" in args
    src, dst = [a for a in args if not a.startswith("--")]
    d = bytearray(open(src, "rb").read())
    rows = json.load(open(labels, encoding="utf-8"))["rows"]
    for r in rows:
        off = int(r["offset"], 16)
        old, new = r["from"].encode("ascii"), r["to"].encode("ascii")
        end = off + len(old)
        if bytes(d[off:end]) != old or d[end] != 0 or (off and d[off - 1] != 0):
            sys.exit("0x%06X: expected %r, found %r" % (off, r["from"], bytes(d[off:end + 4])))
        room = end
        while d[room] == 0:
            room += 1
        if len(new) + 1 > room - off:
            sys.exit("0x%06X: %r needs %d bytes, %d free" % (off, r["to"], len(new) + 1, room - off))
        d[off:room] = new + bytes(room - off - len(new))
    print("%d HUD labels %s" % (len(rows), "checked (dry run)" if dry else "written"))
    if not dry:
        open(dst, "wb").write(d)


if __name__ == "__main__":
    main()
