# Variable-width font (VWF) and 4x text

Ported from Macross Ultimate Frontier (`../Macross Ultimate Frontier/docs/vwf.md`): same glyphs (GenEi LateGo v2,
drawn at 4x and downsampled), same proportional mode, same 4x page idea. Ace Frontier has an older version of the
text code, so the addresses, the descriptor layout and the 4x mechanism differ. Built by `tools/vwf_build.py`.

Status (2026-10-16, v0.1.0): works in PPSSPP (OpenGL, 4x rendering) from the boot to the first mission: menu help
bar, character and operator select, era narration, mission select, the wrapped briefing, confirm dialogs, mission
load. Not tried on real hardware.

## Build order

The width table needs 776 bytes of free, file-backed memory and Ace Frontier has no unused function that large.
`tools/eboot_insert.py --reserve 1024` leaves zeroed room in the gap it opens for the English text (it writes the
address to `<out>.json`), and `vwf_build.py` runs on that output:

```bash
python tools/eboot_insert.py --reserve 1024 --out work/output/build/EBOOT.ins.bin work/translation/en/insert.json
```

```bash
python tools/vwf_build.py --eboot work/output/build/EBOOT.ins.bin --out work/output/build/vwf
```

`tools/build_iso.py` runs both, with `--reserve 3072` since 0.2.0: the 2 KB after the width table hold the
voice-subtitle hooks (`docs/voice_subtitles.md`).

## Data

| Item | Ace Frontier | (MUF) |
| --- | --- | --- |
| font14 descriptor (0x48 bytes) | 0x2A2B64 | 0x3FAE20 (0x54 bytes) |
| bearing-table pointer | descriptor +0x28 | +0x24 |
| group offsets / codes | +0x20 → 0x2A2A58 / +0x24 → 0x29F404 | +0x1C / +0x20 |
| ASCII → Shift-JIS table | 0x241CCC | 0x347E4C |
| glyph slots | 1210–1305 (codes 0x9F82–0xE772), unused by every AF string | same |

The descriptor gets flag 0x20 and a pointer to the table; the pointer gets a new R_MIPS_32 relocation (word and
value in segment 1).

## Code patches

| AF | MUF | Change |
| --- | --- | --- |
| 0xF3AB8 | 0x159B84 | printer: single-byte advance → bearing-table code at 0xF3774 |
| 0xF3C28 | 0x159D18 | printer: single-byte glyph drawn full size, not ×0.8 |
| 0xF3D34 | 0x159ED4 | printer: `(` `[` drawn at the pen |
| 0xF37F0 | 0x1598C8 | printer: space uses the table |
| 0xF3B48, 0xF3B50 | 0x159C2C/34 | printer: ASCII table covers 0x20–0x7F |
| 0xF30E8, 0xF30B0 | 0x15917C, 0x159144 | string width 0xF3014: single-byte chars and space use the table |
| 0xF3468, 0xF332C | 0x1594FC, 0x1593C0 | line truncation 0xF32E8: same |

The routines were matched with `tools/port_match.py` / `tools/port_align.py` (masked instruction alignment). Width
and truncation are identical to MUF except the descriptor offset. The printer is 54 % similar; every patched site
was checked by hand. MUF's `{` `}` patch has no counterpart (AF has no such path). AF has no separate glyph-array
drawer (MUF's lock-on label path), so that part of the port does not apply.

## 4x text

The font loader (0xF1F58) sizes the font texture's page table from the file: pages of 448×448 px
(100,352 bytes), `ceil(rows / 32)`. The original font has 4 pages. `vwf_build.py` pads the file to 4 pages and
appends a fifth page with the 96 glyphs at 4x (56 px cells, 8 per row, two CLUT layers as in the main atlas):
501,760 bytes in all. The loader picks the new page up by itself.

The glyph draw callback 0xF2160 (called through a pointer by the printer) picks the page with
`glyph / (per_row × rows × 2)`, the layer with `glyph & 1`, and the texture cell from descriptor +0x08/+0x0C/+0x10.
Its first two words now branch to a dispatcher at 0xF270C (inside the unreferenced function 0xF26B4, found with
`tools/find_caves.py`, 73 relocation-free words; it uses 47). For an English glyph of the 14 px font the dispatcher
saves descriptor +0x08..+0x14, sets the cell to 56, cells per row and rows per page to 8, calls the callback body
with glyph `4 × 128 + local` (page 4, same layer), and restores the fields. The sprite's screen size comes from the
text size, so layout is unchanged and only the texture detail grows.

A second callback, 0xF7AA4, draws a glyph plus an outline made of offset half-cells (texture coordinates also
from descriptor +0x08..+0x14). The menu help bar uses it. It has its own dispatcher (47 words at 0xE6B4C, inside
the unreferenced function 0xE6A74, frame 0x60 / ra at 0x54) since 0.1.2. Its "half a cell + 1 texel" pieces become
"half + 1/4 native texel" at 4x, which is not visible.

## Limits

- Glyphs sit on whole native pixels: a 1 px rounding step shows as a small gap at 4x ("Vario us").
- Only ASCII is proportional. Text drawn into textures is not affected (see the changelog's known issues).
