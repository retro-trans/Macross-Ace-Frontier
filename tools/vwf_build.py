"""Build the variable-width font (VWF) patch for Macross Ace Frontier: patched EBOOT + font.

Ported from the Macross Ultimate Frontier project (same engine, older text code here).

Usage:
  python tools/vwf_build.py --eboot <EBOOT> --table-va <vaddr> [--font F] [--out DIR] [--no-hd]
                            [--ttf F] [--ttf-index N]

<EBOOT> is a decrypted EBOOT: the original, or the output of tools/eboot_insert.py run with
--reserve 1024 (the width table needs 776 bytes of free, file-backed memory; eboot_insert
writes the reserved address to <EBOOT>.json, and --table-va auto reads it from there).

Writes <out>/EBOOT.BIN, <out>/data/extra/gpsp3_font14.fnt (overlay for muf_archive repack),
<out>/vwf_widths.json and previews. Details: docs/vwf.md.

How it works:
- English is single-byte ASCII. The printer maps ASCII through the table at 0x241CCC to a
  Shift-JIS code and draws that code's glyph. The 96 codes 0x20-0x7F are pointed at 96
  glyph slots holding rare kanji no game string uses (G0..G0+95); our glyphs replace them.
- Proportional spacing: the game's own bearing-table mode (font flag 0x20, table at
  descriptor +0x28, used by the small HUD fonts) is switched on for the 14 px font, and the
  printer, string width and line truncation route single-byte characters into it.
- 4x text: the font file gets a fifth 448x448 page (page 4) with the glyphs drawn at 4x
  (56 px cells, 8 per row). The font loader sizes its page table from the file, so the page
  loads by itself. The glyph draw callback (0xF2160) is wrapped: for an English glyph of the
  14 px font the wrapper sets the descriptor's cell size to 56, cells per row and rows per
  page to 8, passes glyph 4*128 + local (= page 4, same CLUT layer), and restores the fields.
  The sprite keeps its screen size, so only the texture detail changes.
- The EBOOT is a relocatable PRX: no patched word may carry a relocation, jumps are
  PC-relative, and the new table pointer gets an R_MIPS_32 relocation.
"""

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vwf_font  # noqa: E402

FONT14_DESC = 0x2A2B64   # font descriptor of gpsp3_font14.fnt (0x48 bytes; font index 3)
DESC_TABLE = 0x28        # bearing-table pointer (MUF: +0x24)
ASCII_TABLE = 0x241CCC   # ASCII 0x20.. -> Shift-JIS code, 2 bytes each (big-endian)
CODES_TABLE = 0x29F404   # glyph number -> code (descriptor +0x24)
GROUP_OFFSETS = 0x2A2A58  # 17 s16: first glyph number of each code group (descriptor +0x20)
# glyph draw callbacks the printer calls through a pointer, each wrapped by a dispatcher:
# (entry, stack frame, ra slot, cave, words free in the cave). Caves are relocation-free runs
# inside functions nothing references (tools/find_caves.py), within branch range of the entry.
CALLBACKS = [
    (0xF2160, 0x40, 0x34, 0xF270C, 73),  # plain glyph (most text); cave in unused 0xF26B4
    (0xF7AA4, 0x60, 0x54, 0xE6B4C, 53),  # glyph with an outline drawn from offset half-cells (help bar);
                                         # cave in unused 0xE6A74
]
CELL = 14
G0 = 1210                # group 2, codes 0x9F82..0xE772: 96 kanji that no game string uses
PAGE_BYTES = 448 * 448 // 2
HD_PAGE = 4              # page index of the 4x glyphs in the font file
HD_ROWS = 8              # rows per page the wrapper pretends, so glyph HD_PAGE*8*8*2 + L lands on page 4
DEFAULT_TTF = os.path.join("work", "fonts", "GenEiLateGo_v2.ttc")  # okoneya.jp, SIL OFL 1.1

# ------------------------------------------------------------- tiny assembler
R = {n: i for i, n in enumerate("zero at v0 v1 a0 a1 a2 a3 t0 t1 t2 t3 t4 t5 t6 t7 "
                                "s0 s1 s2 s3 s4 s5 s6 s7 t8 t9 k0 k1 gp sp fp ra".split())}


def _r(rs, rt, rd, sa, fn):
    return (R[rs] << 21) | (R[rt] << 16) | (R[rd] << 11) | (sa << 6) | fn


def _i(op, rs, rt, imm):
    return (op << 26) | (R[rs] << 21) | (R[rt] << 16) | (imm & 0xFFFF)


def _off(pc, target):
    off = (target - (pc + 4)) >> 2
    if not -0x8000 <= off < 0x8000:
        raise ValueError("branch out of range %x -> %x" % (pc, target))
    return off


NOP = 0
def move(rd, rs): return _r(rs, "zero", rd, 0, 0x21)
def jr(rs): return _r(rs, "zero", "zero", 0, 0x08)
def addiu(rt, rs, imm): return _i(0x09, rs, rt, imm)
def sltiu(rt, rs, imm): return _i(0x0B, rs, rt, imm)
def lw(rt, off, base): return _i(0x23, base, rt, off)
def sw(rt, off, base): return _i(0x2B, base, rt, off)
def beq(rs, rt, pc, target): return _i(0x04, rs, rt, _off(pc, target))
def b(pc, target): return beq("zero", "zero", pc, target)
def beqz(rs, pc, target): return beq(rs, "zero", pc, target)
def bne(rs, rt, pc, target): return _i(0x05, rs, rt, _off(pc, target))
def bal(pc, target): return (0x01 << 26) | (0x11 << 16) | (_off(pc, target) & 0xFFFF)


# ------------------------------------------------------------- ELF helpers

class Eboot:
    def __init__(self, data):
        self.d = bytearray(data)
        if self.d[:4] != b"\x7fELF":
            raise ValueError("EBOOT is not a decrypted ELF")
        phoff = struct.unpack_from("<I", self.d, 28)[0]
        ph = [struct.unpack_from("<8I", self.d, phoff + 32 * i) for i in range(struct.unpack_from("<H", self.d, 44)[0])]
        self.text_off = ph[0][1]
        self.data_off, self.data_va, self.data_filesz = ph[1][1], ph[1][2], ph[1][4]
        self.reloc_sites = self._reloc_sites()

    def _sections(self):
        shoff = struct.unpack_from("<I", self.d, 32)[0]
        shnum = struct.unpack_from("<H", self.d, 48)[0]
        return shoff, [list(struct.unpack_from("<10I", self.d, shoff + 40 * i)) for i in range(shnum)]

    def _reloc_sites(self):
        _, secs = self._sections()
        sites = set()
        for s in secs:
            if s[1] == 0x700000A0:
                for k in range(s[5] // 8):
                    off, info = struct.unpack_from("<2I", self.d, s[4] + 8 * k)
                    sites.add(off + (self.data_va if (info >> 8) & 0xFF == 1 else 0))
        return sites

    def foff(self, va):
        return va + (self.data_off - self.data_va if va >= self.data_va else self.text_off)

    def word(self, va):
        return struct.unpack_from("<I", self.d, self.foff(va))[0]

    def disasm(self, va):
        import capstone
        md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
        o = self.foff(va)
        for ins in md.disasm(bytes(self.d[o:o + 4]), va):
            return ("%s %s" % (ins.mnemonic, ins.op_str)).strip()
        return "?"

    def put_word(self, va, w, expect=None):
        if va in self.reloc_sites:
            raise ValueError("refusing to patch relocated word at %x" % va)
        if expect is not None and self.disasm(va) != expect:
            raise ValueError("unexpected instruction at %x: %r (wanted %r)" % (va, self.disasm(va), expect))
        struct.pack_into("<I", self.d, self.foff(va), w)

    def put_bytes(self, va, data):
        for a in range(va & ~3, va + len(data), 4):
            if a in self.reloc_sites:
                raise ValueError("refusing to overwrite relocated word at %x" % a)
        o = self.foff(va)
        self.d[o:o + len(data)] = data

    def append_reloc(self, r_offset, info):
        """Append one PSP relocation to the last relocation section and segment."""
        shoff, secs = self._sections()
        last = max((i for i, s in enumerate(secs) if s[1] == 0x700000A0), key=lambda i: secs[i][4])
        end = secs[last][4] + secs[last][5]
        self.d[end:end] = struct.pack("<2I", r_offset, info)
        for i, s in enumerate(secs):
            if i == last:
                s[5] += 8
            elif s[4] >= end and s[1] != 8:
                s[4] += 8
        shoff += 8
        struct.pack_into("<I", self.d, 32, shoff)
        for i, s in enumerate(secs):
            struct.pack_into("<10I", self.d, shoff + 40 * i, *s)
        phoff = struct.unpack_from("<I", self.d, 28)[0]
        phnum = struct.unpack_from("<H", self.d, 44)[0]
        for i in range(phnum):
            p = list(struct.unpack_from("<8I", self.d, phoff + 32 * i))
            if p[0] == 0x700000A0:
                if p[1] + p[4] != end:
                    raise ValueError("reloc segment does not end where the last reloc section ends")
                p[4] += 8
                struct.pack_into("<8I", self.d, phoff + 32 * i, *p)


# ------------------------------------------------------------- the patch

def glyph_slots(eb):
    offs = struct.unpack_from("<17h", eb.d, eb.foff(GROUP_OFFSETS))
    codes = [struct.unpack_from(">H", eb.d, eb.foff(CODES_TABLE) + 2 * i)[0] for i in range(offs[16])]
    if not (offs[2] <= G0 and G0 + 96 <= offs[3]) or codes[G0] != 0x9F82 or codes[G0 + 95] != 0xE772:
        raise ValueError("glyph code table is not the original one")
    return codes[G0:G0 + 96]


def code_patches():
    """(vaddr, new word, original instruction as capstone prints it). MUF addresses in comments."""
    p = []

    def at(va, new, orig):
        p.append((va, new, orig))

    # printer 0xF34CC (MUF 0x159560)
    at(0xF3AB8, b(0xF3AB8, 0xF3774), "mtc1 $zero, $f1")                  # 159B84: SB advance -> bearing-table code
    at(0xF3C28, NOP, "mul.s $f2, $f2, $f0")                              # 159D18: SB glyph drawn full size, not x0.8
    at(0xF3D34, move("a2", "s6"), "subu $a2, $s6, $v0")                  # 159ED4: '(' '[' drawn at the pen
    at(0xF37F0, addiu("v0", "zero", 0x100), "addiu $v0, $zero, 0x20")    # 1598C8: space uses the table too
    at(0xF3B48, addiu("v1", "zero", 0x100), "addiu $v1, $zero, 0x40")    # 159C2C: '`' is no longer special
    at(0xF3B50, sltiu("v0", "a0", 0x60), "sltiu $v0, $a0, 0x5b")         # 159C34: ASCII table covers 0x20-0x7F
    # string width 0xF3014 (MUF 0x1590A8)
    at(0xF30E8, NOP, "beqz $t0, 0xf31a4")                                # 15917C: SB chars always use the table
    at(0xF30B0, addiu("t7", "zero", 0x100), "addiu $t7, $zero, 0x20")    # 159144: space too
    # line truncation 0xF32E8 (MUF 0x15937C)
    at(0xF3468, b(0xF3468, 0xF334C), "mtc1 $a1, $f1")                    # 1594FC
    at(0xF332C, addiu("t9", "zero", 0x100), "addiu $t9, $zero, 0x20")    # 1593C0
    return p


def dispatcher_code(pc, body, frame, ra_off):
    """Entered from a callback (a0 = font descriptor, a1 = glyph; a2-a3, t0-t3 = draw args).
    body = callback + 8: the callback without its first two words (addiu sp,-frame / sw ra,ra_off(sp))."""
    code, fix = [], {}

    def emit(w, name=None):
        if name:
            fix[name] = len(code)
        code.append(w)

    def here():
        return pc + 4 * len(code)

    emit(addiu("sp", "sp", -0x30))
    emit(sw("ra", 0x10, "sp"))
    emit(sw("s0", 0x14, "sp"))
    emit(move("s0", "a0"))
    emit(lw("t4", 8, "a0"))
    emit(addiu("t5", "zero", CELL))
    emit(None, "bne_cell")                       # bne t4, t5, normal
    emit(addiu("t6", "a1", -G0))                 # delay: page-local glyph number
    emit(sltiu("t7", "t6", 96))
    emit(None, "beqz_range")                     # beqz t7, normal
    emit(NOP)
    # 4x glyph: save descriptor +8 .. +0x14, point them at page 4
    for k, off in enumerate((8, 0xC, 0x10, 0x14)):
        emit(lw("t4", off, "a0"))
        emit(sw("t4", 0x18 + 4 * k, "sp"))
    emit(addiu("t4", "zero", vwf_font.BIG))
    emit(sw("t4", 8, "a0"))
    emit(sw("t4", 0xC, "a0"))
    emit(addiu("t4", "zero", vwf_font.HD_PER_ROW))
    emit(sw("t4", 0x10, "a0"))
    emit(addiu("t4", "zero", HD_ROWS))
    emit(sw("t4", 0x14, "a0"))
    emit(addiu("a1", "t6", HD_PAGE * vwf_font.HD_PER_ROW * HD_ROWS * 2))
    emit(addiu("sp", "sp", -frame))              # the two instructions the callback lost
    emit(None, "bal_hd")                         # bal body
    emit(sw("ra", ra_off, "sp"))                 # delay slot: the body returns here
    for k, off in enumerate((8, 0xC, 0x10, 0x14)):
        emit(lw("t4", 0x18 + 4 * k, "sp"))
        emit(sw("t4", off, "s0"))
    emit(None, "b_done")
    emit(NOP)
    normal = here()
    emit(addiu("sp", "sp", -frame))
    emit(None, "bal_normal")
    emit(sw("ra", ra_off, "sp"))
    done = here()
    emit(lw("ra", 0x10, "sp"))
    emit(lw("s0", 0x14, "sp"))
    emit(jr("ra"))
    emit(addiu("sp", "sp", 0x30))
    at = lambda n: pc + 4 * fix[n]  # noqa: E731
    code[fix["bne_cell"]] = bne("t4", "t5", at("bne_cell"), normal)
    code[fix["beqz_range"]] = beqz("t7", at("beqz_range"), normal)
    code[fix["bal_hd"]] = bal(at("bal_hd"), body)
    code[fix["b_done"]] = b(at("b_done"), done)
    code[fix["bal_normal"]] = bal(at("bal_normal"), body)
    return code


def hd_patches(eb):
    sizes = []
    for entry, frame, ra_off, cave, room in CALLBACKS:
        sizes.append(wrap_callback(eb, entry, frame, ra_off, cave, room))
    return sizes


def wrap_callback(eb, entry, frame, ra_off, cave, room):
    code = dispatcher_code(cave, entry + 8, frame, ra_off)
    if len(code) > room:
        raise ValueError("dispatcher does not fit the cave (%d words)" % len(code))
    for i, w in enumerate(code):
        eb.put_word(cave + 4 * i, w)
    eb.put_word(entry, b(entry, cave), "addiu $sp, $sp, -0x%x" % frame)
    eb.put_word(entry + 4, NOP, "sw $ra, 0x%x($sp)" % ra_off)
    return len(code)


def build(eboot_path, table_va, font_path, out, weight, ttf, ttf_index, hd):
    eb = Eboot(open(eboot_path, "rb").read())
    codes = glyph_slots(eb)
    if hd:
        glyphs, widths, info, hd_glyphs = vwf_font.build_set(ttf, weight, ttf_index, hd=True)
    else:
        glyphs, widths, info = vwf_font.build_set(ttf, weight, ttf_index)

    # font: our glyphs into slots G0..G0+95, then the 4x glyphs as page HD_PAGE
    font_in = open(font_path, "rb").read()
    atlas = vwf_font.read_atlas(font_in)
    for i, g in enumerate(glyphs):
        vwf_font.put_glyph(atlas, G0 + i, g)
    font_bytes = vwf_font.write_atlas(atlas)
    if hd:
        if len(font_bytes) > HD_PAGE * PAGE_BYTES:
            raise ValueError("font is larger than %d pages" % HD_PAGE)
        page = vwf_font.hd_page(hd_glyphs)[:PAGE_BYTES]
        font_bytes += bytes(HD_PAGE * PAGE_BYTES - len(font_bytes)) + page
        info["hd_page"] = HD_PAGE
        info["font_bytes"] = len(font_bytes)
    font_out = os.path.join(out, "data", "extra", "gpsp3_font14.fnt")
    os.makedirs(os.path.dirname(font_out), exist_ok=True)
    open(font_out, "wb").write(font_bytes)

    # ASCII -> code table
    eb.put_bytes(ASCII_TABLE, b"".join(struct.pack(">H", c) for c in codes))

    # width table in the reserved gap: guard entry (index -1) + 96 entries (L = 0, R = 14 - advance)
    table = struct.pack("<2i", 0, 0) + b"".join(struct.pack("<2i", 0, CELL - w) for w in widths)
    if not (eb.data_va <= table_va and table_va + len(table) <= eb.data_va + eb.data_filesz):
        raise ValueError("table vaddr 0x%X is not file-backed data" % table_va)
    if any(eb.d[eb.foff(table_va):eb.foff(table_va) + len(table)]):
        raise ValueError("table area at 0x%X is not empty (use eboot_insert --reserve)" % table_va)
    eb.put_bytes(table_va, table)

    # font descriptor: proportional flag + table pointer (value relative to the data segment)
    flags = struct.unpack_from("<H", eb.d, eb.foff(FONT14_DESC))[0]
    if flags != 0 or eb.word(FONT14_DESC + DESC_TABLE) != 0:
        raise ValueError("font descriptor is not the original one")
    struct.pack_into("<H", eb.d, eb.foff(FONT14_DESC), flags | 0x20)
    eb.put_word(FONT14_DESC + DESC_TABLE, table_va + 8 - eb.data_va)
    # R_MIPS_32, word in segment 1 (data), value relative to segment 1
    eb.append_reloc(FONT14_DESC + DESC_TABLE - eb.data_va, 2 | (1 << 8) | (1 << 16))

    for va, w, orig in code_patches():
        eb.put_word(va, w, orig)
    if hd:
        n = hd_patches(eb)
        print("4x text: page %d of the font (offset 0x%X), dispatchers %s"
              % (HD_PAGE, HD_PAGE * PAGE_BYTES, ", ".join("%d words at 0x%X" % (k, c[3]) for k, c in zip(n, CALLBACKS))))

    os.makedirs(out, exist_ok=True)
    eboot_out = os.path.join(out, "EBOOT.BIN")
    open(eboot_out, "wb").write(eb.d)
    json.dump({"info": info, "glyph_base": G0, "table_vaddr": table_va, "codes": ["%04X" % c for c in codes],
               "advance": widths}, open(os.path.join(out, "vwf_widths.json"), "w"), indent=1)
    samples = [s.replace("…", chr(0x7F)) for s in vwf_font.SAMPLES]
    vwf_font.preview(os.path.join(out, "vwf_preview.png"), glyphs, widths, samples)
    if hd:
        vwf_font.hd_preview(os.path.join(out, "vwf_preview_hd.png"), hd_glyphs, widths, samples)
    print("glyph slots %d-%d, %s" % (G0, G0 + 95, info))
    print("wrote", eboot_out, "and", font_out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--eboot", required=True)
    ap.add_argument("--table-va", default="auto", help="vaddr of 776 free bytes, or 'auto' (<eboot>.json)")
    ap.add_argument("--font", default=os.path.join("work", "source", "dat", "data", "extra", "gpsp3_font14.fnt"))
    ap.add_argument("--out", default=os.path.join("work", "output", "vwf"))
    ap.add_argument("--weight", type=int, default=vwf_font.DEFAULT_WEIGHT)
    ap.add_argument("--ttf", default=DEFAULT_TTF)
    ap.add_argument("--ttf-index", type=int, default=0)
    ap.add_argument("--no-hd", action="store_true", help="native 14 px glyphs only (no 4x page)")
    a = ap.parse_args()
    if a.table_va == "auto":
        tva = json.load(open(a.eboot + ".json"))["reserved_vaddr"]
        if not tva:
            sys.exit("no reserved space in %s.json: run eboot_insert.py --reserve 1024" % a.eboot)
    else:
        tva = int(a.table_va, 16)
    build(a.eboot, tva, a.font, a.out, a.weight, a.ttf, a.ttf_index, hd=not a.no_hd)


if __name__ == "__main__":
    main()
