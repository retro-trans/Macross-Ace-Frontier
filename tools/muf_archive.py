"""Extract and repack the data archives of Macross Ace Frontier (PSP).

Copied from the Macross Ultimate Frontier project, same engine. Extraction
and repack are checked on Ace Frontier (byte-identical round trip).

PSP_GAME/USRDIR holds three files (see docs/formats.md):
  macross.idx   PIDX0 v2 index: directory tree of macross.dat + fileset table
  macross.dat   PIDX0 v1 header copy, then raw files aligned to 0x800
                (0x8000 for data/sound/voice/)
  fileset.dat   PIDX0 v1 header copy, then FSTS bundles aligned to 0x800;
                each bundle holds XOR/LZSS-packed copies of game files

Usage:
  python tools/muf_archive.py extract <USRDIR> <out_dir>
  python tools/muf_archive.py repack  <dir> <out_USRDIR> [--base <USRDIR>]
                                      [--overlay <tree>] [--recompress-all] [--jobs N]
  python tools/muf_archive.py verify  <USRDIR_a> <USRDIR_b>

extract writes every file to <out_dir>/data/... (macross.dat files and the
decoded fileset members share one tree; a path in both always has the same
content) and the layout to <out_dir>/_meta/.

repack rebuilds all three archive files from <dir>. Members whose content is
unchanged are copied from --base when given, everything else is re-encoded
with tools/muf_lzss.py, which reproduces the original encoder byte for byte.
--overlay <tree> takes data/... files from <tree> instead of <dir> when they
exist there (used for patched files such as the VWF font). Overlay files under
DAT_ONLY (the voice clips with a subtitle tail) replace only the macross.dat
copy: the copies inside fileset bundles stay as they are, so no memory is
added (docs/voice_subtitles.md).
"""

import argparse
import hashlib
import json
import os
import struct
import sys
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import muf_lzss  # noqa: E402

IDX_NAME = "macross.idx"
DAT_NAME = "macross.dat"
FILESET_NAME = "fileset.dat"
DAT_ALIGN = 0x800
DAT_ONLY = ("data/sound/voice/",)  # overlay files used for macross.dat only
VOICE_ALIGN = 0x8000  # streamed voice clips in macross.dat
FSTS_ALIGN = 0x10
ENTRY_SIZE = 24
FSTS_HEADER = 0x20
FSTS_ENTRY = 16


def align(x, a):
    return (x + a - 1) // a * a


def dat_align(path):
    return VOICE_ALIGN if path.startswith("data/sound/voice/") else DAT_ALIGN


def md5(data):
    return hashlib.md5(data).hexdigest()


def cstr(buf, off):
    return buf[off:buf.index(b"\0", off)].decode("ascii")


class Pidx:
    """PIDX0 header. Used by macross.idx (v2) and the heads of both .dat files (v1).

    0x00 'PIDX0\\0\\0\\0'   0x08 version
    0x0C entry table offset  0x10 entry count
    0x14 root entry count    0x18 fileset table offset  0x1C its size
    0x20 name table offset   0x24 its size
    0x28 container slots up to the entry table, 0x28 bytes each: name offset,
         20 zero bytes, 16-byte id that pairs the index with its .dat file
    """

    def __init__(self, buf):
        if buf[:5] != b"PIDX0":
            raise ValueError("not a PIDX0 header")
        (self.version, self.ent_off, self.ent_count, self.roots,
         self.tbl_off, self.tbl_size, self.name_off, self.name_size) = struct.unpack_from("<8I", buf, 8)
        self.buf = buf

    def name(self, off):
        return cstr(self.buf, self.name_off + off)

    def entry(self, i):
        """(type, name, a, b, c, d). Dir: type 1, a = child count, b = first child.
        File: type 0, a = container name offset, b = offset, c = size."""
        return struct.unpack_from("<6I", self.buf, self.ent_off + ENTRY_SIZE * i)

    def entry_pos(self, i):
        return self.ent_off + ENTRY_SIZE * i

    def fileset_records(self):
        """List of (record position, (name, container, offset, size, member count))."""
        if self.tbl_size <= 4:
            return []
        count = struct.unpack_from("<I", self.buf, self.tbl_off)[0]
        ptrs = struct.unpack_from("<%dI" % count, self.buf, self.tbl_off + 4)
        return [(self.tbl_off + p, struct.unpack_from("<5I", self.buf, self.tbl_off + p)) for p in ptrs]

    def walk(self):
        """Yield (entry index, path) for every file in the directory tree."""
        out = []

        def rec(i, prefix):
            t, nm, a, b, _, _ = self.entry(i)
            path = prefix + self.name(nm)
            if t == 1:
                for j in range(b, b + a):
                    rec(j, path + "/")
            else:
                out.append((i, path))

        rec(0, "")
        return out


def parse_fsts(buf):
    magic, count, hdr, name_off, name_size = struct.unpack_from("<4s4I", buf, 0)
    if magic != b"FSTS" or hdr != FSTS_HEADER:
        raise ValueError("bad FSTS header")
    members = []
    for i in range(count):
        noff, off, usize, csize = struct.unpack_from("<4I", buf, FSTS_HEADER + FSTS_ENTRY * i)
        members.append((cstr(buf, name_off + noff), off, usize, csize))
    return members, name_off, name_size


def build_fsts(members):
    """members: list of (path, packed blob). Returns the FSTS bytes."""
    count = len(members)
    names = b"".join(p.encode("ascii") + b"\0" for p, _ in members)
    name_off = FSTS_HEADER + FSTS_ENTRY * count
    out = bytearray(struct.pack("<4s4I12x", b"FSTS", count, FSTS_HEADER, name_off, len(names)))
    out += bytes(FSTS_ENTRY * count)
    out += names
    noff = 0
    for i, (path, blob) in enumerate(members):
        out += bytes(align(len(out), FSTS_ALIGN) - len(out))
        usize = struct.unpack_from("<I", blob, 4)[0]
        struct.pack_into("<4I", out, FSTS_HEADER + FSTS_ENTRY * i, noff, len(out), usize, len(blob))
        noff += len(path) + 1
        out += blob
    out += bytes(align(len(out), FSTS_ALIGN) - len(out))
    return bytes(out)


def safe_join(root, path):
    parts = path.split("/")
    if any(p in ("", ".", "..") for p in parts) or ":" in path or "\\" in path:
        raise ValueError("unsafe path in archive: %r" % path)
    return os.path.join(root, *parts)


def write_file(root, path, data):
    dest = safe_join(root, path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(data)


# ---------------------------------------------------------------- extract

def extract(usrdir, out):
    idx_buf = open(os.path.join(usrdir, IDX_NAME), "rb").read()
    idx = Pidx(idx_buf)
    meta = os.path.join(out, "_meta")
    os.makedirs(meta, exist_ok=True)

    # macross.dat
    files = sorted(idx.walk(), key=lambda t: idx.entry(t[0])[3])
    with open(os.path.join(usrdir, DAT_NAME), "rb") as dat:
        head = Pidx(dat.read(idx.entry(files[0][0])[3]))
        dat_files = []
        for i, path in files:
            t, _, container, off, size, _ = idx.entry(i)
            if container != 0 or idx.name(container) != DAT_NAME:
                raise ValueError("file %s is not in macross.dat" % path)
            h = head.entry(i)
            if (h[3], h[4]) != (off, size):
                raise ValueError("macross.dat head disagrees with idx for %s" % path)
            dat.seek(off)
            data = dat.read(size)
            write_file(out, path, data)
            dat_files.append({"entry": i, "path": path, "offset": off, "size": size, "md5": md5(data)})
        dat.seek(0, 2)
        dat_total = dat.tell()
    with open(os.path.join(meta, "macross_dat_head.bin"), "wb") as f:
        f.write(head.buf)
    print("macross.dat: %d files" % len(dat_files))

    # fileset.dat
    written = {f["path"]: f["md5"] for f in dat_files}
    sets = []
    with open(os.path.join(usrdir, FILESET_NAME), "rb") as fs:
        records = idx.fileset_records()
        first = min(r[1][2] for r in records)
        fs_head = Pidx(fs.read(first))
        fs_records = fs_head.fileset_records()
        if len(fs_records) != len(records):
            raise ValueError("fileset.dat head disagrees with idx")
        # Ace Frontier stores the head's records in a different order than
        # the idx (Ultimate Frontier keeps the same order), so match by value.
        fs_keys = {r[1][2:] for r in fs_records}
        order = sorted(range(len(records)), key=lambda k: records[k][1][2])
        for k in order:
            _, (nm, container, off, size, count) = records[k]
            if idx.name(container) != FILESET_NAME:
                raise ValueError("fileset record not in fileset.dat")
            if (off, size, count) not in fs_keys:
                raise ValueError("fileset.dat head disagrees with idx")
            fs.seek(off)
            buf = fs.read(size)
            members, _, _ = parse_fsts(buf)
            entry = {"record": k, "name": idx.name(nm), "offset": off, "size": size, "members": []}
            for path, moff, usize, csize in members:
                blob = buf[moff:moff + csize]
                data = muf_lzss.decode(blob)
                if len(data) != usize:
                    raise ValueError("size mismatch in %s" % path)
                h = md5(data)
                if path in written:
                    if written[path] != h:
                        raise ValueError("two different contents for %s" % path)
                else:
                    write_file(out, path, data)
                    written[path] = h
                entry["members"].append({"path": path, "mode": muf_lzss.member_mode(blob),
                                         "offset": off + moff, "csize": csize, "md5": h})
            sets.append(entry)
        fs.seek(0, 2)
        fs_total = fs.tell()
    with open(os.path.join(meta, "fileset_dat_head.bin"), "wb") as f:
        f.write(fs_head.buf)
    with open(os.path.join(meta, IDX_NAME), "wb") as f:
        f.write(idx_buf)
    print("fileset.dat: %d sets, %d members, %d unique files in total"
          % (len(sets), sum(len(s["members"]) for s in sets), len(written)))

    manifest = {
        "format": "muf_archive 1",
        "macross_dat": {"size": dat_total, "files": dat_files},
        "fileset_dat": {"size": fs_total, "sets": sets},
    }
    with open(os.path.join(meta, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=0)


# ---------------------------------------------------------------- repack

def _encode_job(args):
    path, mode = args
    with open(path, "rb") as f:
        return muf_lzss.encode(f.read(), mode)


def repack(src, out, base=None, recompress_all=False, jobs=None, overlay=None):
    meta = os.path.join(src, "_meta")
    manifest = json.load(open(os.path.join(meta, "manifest.json"), encoding="utf-8"))
    idx = bytearray(open(os.path.join(meta, IDX_NAME), "rb").read())
    idx_p = Pidx(bytes(idx))
    os.makedirs(out, exist_ok=True)

    def src_file(path, fileset=False):
        """A file from the overlay tree when it has one, else from the extracted tree."""
        if overlay and not (fileset and path.startswith(DAT_ONLY)):
            o = safe_join(overlay, path)
            if os.path.isfile(o):
                return o
        return safe_join(src, path)

    # macross.dat: header copy, then each file at the next 0x800 boundary
    # (0x8000 for voice clips); the end is padded with the last file's alignment
    head = bytearray(open(os.path.join(meta, "macross_dat_head.bin"), "rb").read())
    head_p = Pidx(bytes(head))
    with open(os.path.join(out, DAT_NAME), "wb") as dat:
        dat.write(head)
        pos = len(head)
        changed = 0
        for f in manifest["macross_dat"]["files"]:
            data = open(src_file(f["path"]), "rb").read()
            if md5(data) != f["md5"]:
                changed += 1
            pos = align(pos, dat_align(f["path"]))
            dat.seek(pos)
            dat.write(data)
            for buf, p in ((idx, idx_p.entry_pos(f["entry"])), (head, head_p.entry_pos(f["entry"]))):
                struct.pack_into("<2I", buf, p + 12, pos, len(data))
            pos += len(data)
        dat.write(bytes(align(pos, dat_align(f["path"])) - pos))
        dat.seek(0)
        dat.write(head)
    print("macross.dat: %d files, %d changed" % (len(manifest["macross_dat"]["files"]), changed))

    # fileset.dat: decide which members need encoding
    base_fs = open(os.path.join(base, FILESET_NAME), "rb") if base else None
    todo = {}
    for s in manifest["fileset_dat"]["sets"]:
        for m in s["members"]:
            key = (m["path"], m["mode"])
            if key in todo:
                continue
            data_path = src_file(m["path"], fileset=True)
            if base_fs and not recompress_all and md5(open(data_path, "rb").read()) == m["md5"]:
                todo[key] = ("base", m["offset"], m["csize"])
            else:
                todo[key] = ("encode", data_path)
    encode_keys = [k for k, v in todo.items() if v[0] == "encode"]
    print("fileset.dat: encoding %d members, copying %d from base" % (len(encode_keys), len(todo) - len(encode_keys)))
    encoded = {}
    if encode_keys:
        args = [(todo[k][1], k[1]) for k in encode_keys]
        # biggest first so the pool stays busy
        order = sorted(range(len(args)), key=lambda i: -os.path.getsize(args[i][0]))
        with Pool(jobs) as pool:
            for n, blob in enumerate(pool.imap(_encode_job, [args[i] for i in order], chunksize=1)):
                encoded[encode_keys[order[n]]] = blob
                if (n + 1) % 2000 == 0:
                    print("  encoded %d/%d" % (n + 1, len(args)), flush=True)

    def blob_for(m):
        key = (m["path"], m["mode"])
        if key in encoded:
            return encoded[key]
        _, off, size = todo[key]
        base_fs.seek(off)
        return base_fs.read(size)

    fs_head = bytearray(open(os.path.join(meta, "fileset_dat_head.bin"), "rb").read())
    fs_head_p = Pidx(bytes(fs_head))
    idx_recs = idx_p.fileset_records()
    head_recs = fs_head_p.fileset_records()
    # Ace Frontier lists the head's records in another order than the idx: pair them
    # by their original (offset, size, count)
    head_pos = {r[1][2:]: r[0] for r in head_recs}
    head_for = [head_pos[r[1][2:]] for r in idx_recs]
    with open(os.path.join(out, FILESET_NAME), "wb") as fs:
        fs.write(fs_head)
        pos = len(fs_head)
        for s in manifest["fileset_dat"]["sets"]:
            fsts = build_fsts([(m["path"], blob_for(m)) for m in s["members"]])
            pos = align(pos, DAT_ALIGN)
            fs.seek(pos)
            fs.write(fsts)
            struct.pack_into("<3I", idx, idx_recs[s["record"]][0] + 8, pos, len(fsts), len(s["members"]))
            struct.pack_into("<3I", fs_head, head_for[s["record"]] + 8, pos, len(fsts), len(s["members"]))
            pos += len(fsts)
        fs.seek(0)
        fs.write(fs_head)
    if base_fs:
        base_fs.close()
    with open(os.path.join(out, IDX_NAME), "wb") as f:
        f.write(idx)
    print("fileset.dat: %d sets written" % len(manifest["fileset_dat"]["sets"]))


# ---------------------------------------------------------------- verify

def file_md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def verify(a, b):
    ok = True
    for name in (IDX_NAME, DAT_NAME, FILESET_NAME):
        ha, hb = file_md5(os.path.join(a, name)), file_md5(os.path.join(b, name))
        print("%-12s %s %s %s" % (name, ha, hb, "OK" if ha == hb else "DIFFERENT"))
        ok &= ha == hb
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("extract")
    p.add_argument("usrdir")
    p.add_argument("out")
    p = sub.add_parser("repack")
    p.add_argument("src")
    p.add_argument("out")
    p.add_argument("--base", help="original USRDIR; unchanged members are copied from it")
    p.add_argument("--recompress-all", action="store_true", help="re-encode every member even with --base")
    p.add_argument("--jobs", type=int, default=None)
    p.add_argument("--overlay", help="tree whose data/... files replace the extracted ones")
    p = sub.add_parser("verify")
    p.add_argument("a")
    p.add_argument("b")
    args = ap.parse_args()
    if args.cmd == "extract":
        extract(args.usrdir, args.out)
    elif args.cmd == "repack":
        repack(args.src, args.out, args.base, args.recompress_all, args.jobs, args.overlay)
    else:
        sys.exit(0 if verify(args.a, args.b) else 1)


if __name__ == "__main__":
    main()
