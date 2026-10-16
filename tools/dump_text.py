"""Dump the game's script text from an extracted archive tree to JSON.

Usage:
  python tools/dump_text.py [<dat_dir>] [<out_dir>]
  defaults: work/source/dat  work/source/text

Run tools/muf_archive.py extract first. The output contains Japanese and is
gitignored (work/source/). Sources and formats are described in
docs/formats.md:

  menu_text.json   data/menu/text/*.csv, every text cell
  fes_strings.json data/script/*.fes, Japanese strings of each string pool
  locate_names.json data/locate/*.csv, the display-name column

Every entry has an "id" that stays stable between dumps, the "source" file,
where the text sits, and "jp". Text is kept exactly as stored: "\\n" in the
CSVs is a literal backslash + n that the game turns into a line break, and
FES strings keep their real newline bytes.
"""

import csv
import io
import json
import os
import struct
import sys

ENCODING = "cp932"  # Shift-JIS as written by Windows tools
FES_POOL_PTR = 0x12  # u16: offset of the string pool in a FES 3.00/3.04 file


def has_japanese(s):
    return any(ord(c) > 0x7F for c in s)


def read_csv(path):
    raw = open(path, "rb").read()
    return list(csv.reader(io.StringIO(raw.decode(ENCODING), newline="")))


def dump_menu_text(root):
    entries = []
    folder = os.path.join(root, "data", "menu", "text")
    if not os.path.isdir(folder):  # Ace Frontier has no menu CSVs; its menu text is in the EBOOT
        return entries
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".csv"):
            continue
        rows = read_csv(os.path.join(folder, name))
        header = rows[0]
        for r, row in enumerate(rows[1:], start=1):
            key = row[0]
            for c in range(1, len(row)):
                if not row[c]:
                    continue
                col = header[c] if c < len(header) and header[c] else "col%d" % c
                entries.append({
                    "id": "%s:%s:%s" % (name[:-4], key, col),
                    "source": "data/menu/text/" + name,
                    "row": r,
                    "col": c,
                    "key": key,
                    "field": col,
                    "jp": row[c],
                })
    return entries


def fes_pool(data):
    # Ace Frontier uses FES 3.00; the pool pointer sits at the same offset as in 3.04
    if data[:8] not in (b"FES 3.00", b"FES 3.04"):
        raise ValueError("not a FES 3.00/3.04 file")
    start = struct.unpack_from("<H", data, FES_POOL_PTR)[0]
    off = start
    for s in data[start:].split(b"\0")[:-1]:
        yield off, s
        off += len(s) + 1


def dump_fes(root):
    entries = []
    folder = os.path.join(root, "data", "script")
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".fes"):
            continue
        data = open(os.path.join(folder, name), "rb").read()
        start = struct.unpack_from("<H", data, FES_POOL_PTR)[0]
        for off, s in fes_pool(data):
            if not any(b > 0x7F for b in s):
                continue  # ASCII identifiers: labels, voice ids, unit ids
            entries.append({
                "id": "%s:%04x" % (name[:-4], off - start),
                "source": "data/script/" + name,
                "offset": off,
                "pool_offset": off - start,
                "bytes": len(s),
                "jp": s.decode(ENCODING),
            })
    return entries


def dump_locate(root):
    entries = []
    folder = os.path.join(root, "data", "locate")
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".csv"):
            continue
        rows = read_csv(os.path.join(folder, name))
        for r, row in enumerate(rows[1:], start=1):
            if len(row) < 3 or not has_japanese(row[2]):
                continue
            entries.append({
                "id": "%s:%d:%s" % (name[:-4], r, row[0]),
                "source": "data/locate/" + name,
                "row": r,
                "col": 2,
                "key": row[0],
                "unit": row[1],
                "pilot": row[5] if len(row) > 5 else "",
                "jp": row[2],
            })
    return entries


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.join("work", "source", "dat")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join("work", "source", "text")
    os.makedirs(out, exist_ok=True)
    for fname, fn in (("menu_text.json", dump_menu_text),
                      ("fes_strings.json", dump_fes),
                      ("locate_names.json", dump_locate)):
        entries = fn(root)
        ids = [e["id"] for e in entries]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate ids in " + fname)
        with open(os.path.join(out, fname), "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=1)
        print("%-18s %5d entries, %6d chars" % (fname, len(entries), sum(len(e["jp"]) for e in entries)))


if __name__ == "__main__":
    main()
