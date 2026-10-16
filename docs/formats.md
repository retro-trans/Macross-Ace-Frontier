# Data formats: Macross Ace Frontier (PSP, ULJS-00158, Japan v1.02)

Ace Frontier runs on the same engine as Macross Ultimate Frontier. The MUF project documents the formats in
detail (`../Macross Ultimate Frontier/docs/formats.md`). This page lists only what was checked on Ace Frontier
and where it differs.

## Disc

`Macross Ace Frontier (Japan).iso`, 646,938,624 bytes, CRC32 `fba3dbe1` = Redump v1.02 (the original release,
also listed without a version tag on some sites). The "PSP the Best" v2.00 (ULJS-19029) is a different image;
patches made for one will not apply to the other.

| File | Size |
| --- | --- |
| `PSP_GAME/SYSDIR/EBOOT.BIN` | 3,618,544 (encrypted `~PSP`) |
| `PSP_GAME/USRDIR/macross.idx` | 414,391 |
| `PSP_GAME/USRDIR/macross.dat` | 293,699,584 |
| `PSP_GAME/USRDIR/fileset.dat` | 158,612,400 |
| `PSP_GAME/USRDIR/data/movie/*.pmf`, `data/sound/bgm/*.at3` | plain ISO files |

## Extracting

```bash
python -I tools/muf_archive.py extract work/source/iso/USRDIR work/source/dat
python -I tools/dump_text.py
```

Copy the three USRDIR files and `EBOOT.BIN` out of the ISO into `work/source/iso/` first. Extraction takes about
1.5 minutes: 9,398 files in macross.dat, 984 filesets with 31,436 members, 21,295 unique files.

Differences from MUF, both handled in the copied tools:

- **fileset.dat head order.** The PIDX head of `fileset.dat` lists the same 984 fileset records as the index,
  but in a different order. `muf_archive.py extract` and `repack` match them by their original (offset, size,
  count). A repack of the unchanged tree is byte-identical to the disc files.
- **FES 3.00.** Mission scripts are `FES 3.00` (MUF: 3.04). The string pool pointer is at the same header
  offset (0x12), so `dump_text.py` accepts both.
- **No menu CSVs.** There is no `data/menu/text/`. Menu text, names, mission titles, briefings, profiles,
  skills and songs are all in the EBOOT.

## EBOOT

Decrypted the same way as MUF: a portable PPSSPP copy (`work/local/ppsspp/`, `installed.txt` removed,
`DumpFileTypes = 3` in `memstick/PSP/SYSTEM/ppsspp.ini`) boots the ISO and writes
`memstick/PSP/SYSTEM/DUMP/ULJS00158_EBOOT.BIN` (3,618,544 bytes, `\x7FELF`). The copy is kept at
`work/source/eboot/EBOOT.dec.bin` (gitignored). `python -I tools/dump_eboot.py` finds 1,824 Japanese strings
(46,624 characters) and writes `work/source/text/eboot_strings.json`.

Main tables (file offsets in the decrypted EBOOT):

| Offset | Content |
| --- | --- |
| 0x22C6D8 | system messages (save, load, ranks display) |
| 0x24E9C8 | pilot table: named pilots, player slots, generic AI profiles (0x78-byte records) |
| 0x258FD0 | unit / object table (units, ship parts, mission objects) |
| 0x25AE3C | mission titles, briefings and objectives |
| 0x264488 | stages and weapons |
| 0x266B08 | unit names with descriptions |
| 0x26B378 | operator names, then skills (0x26C664) and epilogue lines |
| 0x26E1E0 | factions, series titles, BGM list |
| 0x26EDE8 | operator profiles |
| 0x277E28 | sound test (title + credits) |
| 0x27B954 | ranks, faction tabs and character profiles |
| 0x27D400 | pilot titles (称号) and unlock conditions |

## Text dump

| File | Entries | Content |
| --- | --- | --- |
| `eboot_strings.json` | 1,824 | everything listed above |
| `fes_strings.json` | 121 | mission script strings (objectives, tutorial lines) |
| `locate_names.json` | 297 | mission unit lists: display name, unit, pilot id |

All three contain Japanese and stay in `work/source/` (gitignored).

## Reuse from MUF

770 of the 1,881 different AF strings are character-for-character identical to a string MUF has already
translated (`ui_insert.json`, `dialogue.json`, `internal_labels.json`, `ui.json`). They are mostly short:
names, menu labels, ranks, skills, songs. The glossary seed used them for names; the UI translation can use them
as a translation memory.
