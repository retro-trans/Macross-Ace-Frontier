# Voice-clip subtitles

During missions the characters talk over the radio: a portrait (the "cut-in") opens and a voice clip plays. The
game has no text for these lines. Since v0.2.0 the patched game shows an English subtitle while each clip plays.

Ported from Macross Ultimate Frontier (MUF) 0.7.0 (`../Macross Ultimate Frontier/docs/voice_subtitles.md`): same
storage, same hooks, same layout. Ace Frontier's EBOOT is older code, so the routines were found again (see "EBOOT
hooks"), and the hook code lives in reserved room instead of unused routines.

Status (v0.2.0, 2026-10-16): working in PPSSPP (OpenGL, 4x) in the first mission (see "Testing"). Not tried on
real hardware.

## Results

| | Clips |
| --- | --- |
| Voice clips | 6,711 (plus 1 sound effect, `fold_out`) |
| **With an English subtitle** | **5,375** |
| Silent placeholder clips (no voice in the game) | 1,130 |
| Sound but no words (shouts, grunts, laughs; Whisper or translator) | 190 (+4 repeats of such clips) |
| Era prologue narration (already English text on screen) | 12 |

**6,545 of the 6,711 voice clips are byte-identical to MUF clips.** Their transcripts (after MUF's retry pass) and
MUF's reviewed English were reused: 5,231 subtitles. The other 166 clips (Vrlitwhai Kridanik's whole set, 151 clips,
plus a few Hayao, Gavil, Basara, Mylene and Max lines) were transcribed here and translated in 2 slices of 80 rows
(`work/translation/en/voice/slices/`): 144 subtitles. Most are the same line recorded again, so each slice row shows
the MUF clip with the same id as a reference. Flags on the slice rows: `whisper_doubt` 42, `no_subtitle` 16,
`uncertain` 13, `kept_omission` 1; every flagged row has an English note.

## Pipeline

| Step | Tool | Output |
| --- | --- | --- |
| 1. Reuse MUF transcripts of identical clips | `tools/voice_transcribe.py --reuse "../Macross Ultimate Frontier"` | `work/source/voice/transcripts.json` (local: Japanese), `reused_from` |
| 2. Transcribe the rest | `tools/voice_transcribe.py` (faster-whisper large-v3, CUDA), then `--retry` | same file |
| 3. Flag silent clips (peak below -60 dB) | `tools/voice_transcribe.py --silence` | same file, flag `silent` |
| 4. Work file: speaker, missions, transcript, MUF English | `tools/voice_rows.py` | `work/translation/en/voice/voice.json` (local) |
| 5. Translate in 80-row slices | agents, `docs/voice_translation_brief.md`, `tools/voice_slice.py show/check` | `work/translation/en/voice/slices/vslice_NNN.en.json` |
| 6. Unify names | `tools/voice_fix_names.py` | the slices (no change was needed in 0.2.0) |
| 7. Collect the lines | `tools/voice_subs_export.py` | `work/translation/en/voice/voice_subs.en.json` |
| 8. Append each line to its clip | `tools/voice_subs_at3.py` | overlay `data/sound/voice/<clip>.at3` |
| 9. EBOOT hooks that read and draw the line | `tools/voice_subs_patch.py` | patched `EBOOT.BIN` |

Steps 8 and 9 run inside `tools/build_iso.py` with `--voice-subs <file>` (`--voice-placeholder` shows each clip's id
instead, to test the hooks).

Whisper runs in the venv of the MUF project (Python 3.11, CUDA, RTX 3070 Ti):

```bash
"../Macross Ultimate Frontier/work/source/whisper_venv/Scripts/python" tools/voice_transcribe.py
```

The 166 clips took 92 s, the retry pass (13 clips) 9 s. Hotwords: `work/source/voice/hotwords.txt` (copied from MUF,
local).

## The clips

`data/sound/voice/` in `macross.dat` holds 6,712 ATRAC3 clips `v<prefix>_<num>.at3`. Each has a 48-byte lip-sync
file `data/sound/vad/<clip>.vad`: u32 length in frames at 60 fps, u16 at +6 = 2 (the step), then mouth keys.

`<prefix>` is the face id of the cut-in portrait. `work/translation/en/voice/speakers.en.json` names the 39 speakers
(copied from MUF): four operators (`o0_of0` Yuu, `o0_of1` Claire, `o0_om0` Itsuki, `os_mis` Misa), four custom
pilots (`p0_of0/of1/om0/om1`) and 31 named characters. Clip numbers mean the same as in MUF: 000-020 launch,
100-198 combat, 300-371 skills and results, 600-699 story lines, 900-905 the era prologue narration, 1000+ operator
mission lines.

630 of the clips are also members of the `cv_*` fileset bundles (18 per character, played from memory). Those copies
are not changed: `tools/muf_archive.py` uses overlay files under `data/sound/voice/` for `macross.dat` only
(`DAT_ONLY`), so the bundles do not grow. The hook reads the `macross.dat` copy.

## Where the line is stored

At the end of its own clip, after the RIFF data, in `macross.dat`:

```
... RIFF ATRAC3 clip ... | part 1 NUL [part 2 NUL ...] | u16 len | u16 parts | "SB"
```

`len` counts all parts with their NULs. The RIFF size field is not changed, so the player never reads the tail.
Voice clips sit on 0x8000 boundaries in `macross.dat`. Nothing is loaded into memory except the 0xB8 bytes the
hook reads.

## EBOOT hooks (`tools/voice_subs_patch.py`)

| Routine | AF | MUF | Match |
| --- | --- | --- | --- |
| exact-size file read | 0xFD4 | 0x21A00 | 24/24 words |
| path normalise | 0x158E0 | 0x37C60 | 24/24 |
| `macross.dat` index lookup (container, offset, size, packed) | 0x18320 | 0x3A9B8 | identical |
| read at an offset (path, buf, offset, size, mode) | 0x16F0C | 0x39560 | same body; AF waits for a pending async read first |
| lip-sync slot 0 load (`jal` replaced) | 0x12CD2C | 0x1A0A14 | same code; slot 0 at 0x14147EC |
| lip-sync slot 1 load (`jal` replaced) | 0x12ED70 | 0x1A38E4 | same code |
| lip-sync frame counter | 0x12BBA4 | 0x1A0AD0 | 16/16; counters at slot 0 - 8 / - 4 |
| mission 2D layer, cut-in step call (`jal` replaced) | 0xDD3FC (in 0xDD3D0) | 0x140D68 | same code |
| cut-in module step | 0x12B5B8 | 0x1A024C | 23/24 |
| text routine | 0xF435C | 0x15ABC0 | same prologue and arguments |
| `"data/sound/voice/"` | 0x26FC94 | 0x3947A0 | |

Found with `tools/port_match.py` and checked by hand with `tools/disasm.py`; the `.vad` format strings
(`data/sound/vad/%s.vad`) and the call arguments (`a2 = 0x30`) are the same.

**Read.** Both `.vad` loads go to READ_HOOK. It makes the same call, then builds `data/sound/voice/<clip>.at3`,
normalises it, looks it up in the `macross.dat` index and reads the last 0xB8 bytes. With an `SB` tail it keeps a
pointer to the line and its number of parts for that slot.

**When.** The game counts a slot's frames only while its clip plays. A slot's line shows while its counter runs
and for 24 frames after. Part i of n shows from i/n of the clip on.

**Draw.** The cut-in step call in the mission's 2D layer goes to DRAW_HOOK: it runs the step, then draws the line
with the game's text routine twice, a black shadow 1 px down-right, then white. Same parameters as MUF: centre
(240, 228), alignment 0, 12 px VWF, box 232 px, line step 13 px, depth 0xFFFF. They are 9 config words at
`CFG`, so a layout can be tried live through the PPSSPP debugger.

**Space used.** Ace Frontier has no unused routine large enough (the VWF port already took the two that were). So
`tools/eboot_insert.py --reserve 3072` leaves zeroed room in the gap it opens between `.data` and `.bss`: the VWF
width table takes the first 1 KB, this patch the next 2 KB (in 0.2.0: READ_HOOK 136 words at 0x2A73C0, DRAW_HOOK
117 words at 0x2A7600, buffers and state at 0x2A7800, config at 0x2A79A8). The gap is file-backed data, zero in the
EBOOT, so nothing shows before the first clip; the PSP does not forbid running code there. The three replaced
words are `jal` with an R_MIPS_26 relocation, which stays valid for the new target; the new code carries no
relocation (it finds its load address with `bal`).

## Length

At 12 px the box holds about 38 characters per line. A line is wrapped to 232 px with the VWF advances, at most 3
lines per part; a longer line becomes 2-3 parts. The whole line must fit in 178 bytes (`voice_slice.py check`).
In 0.2.0 one line is shown in parts.

## Limits

- Only clips the mission script queues get a subtitle. Clips played another way (menus, the character select voice
  samples, the era prologue) do not; the prologue already shows English text.
- Two lines spoken at once show one subtitle, slot 0 first. Parts follow the clip at even steps.
- The AF read routine waits while another asynchronous file read is pending (MUF's does not). No stutter was seen
  in PPSSPP; not measured on hardware.
- With the game's "2D Display" option off, whether subtitles still show was not checked.
- Transcription errors the translators could not settle are flagged `whisper_doubt` / `uncertain` in the slices
  (Vrlitwhai's set had many garbled transcripts).
- Not tested on real hardware.

## Testing

PPSSPP (portable copy in `work/local/ppsspp`, OpenGL, 4x), driven with `tools/ppsspp_ctl.py`. A placeholder build
(`--voice-placeholder`) showed the clip id under the cut-ins in the first mission's intro camera, over the
"Mission Start" banner and with the flight HUD. The 0.2.0 build was then played into the same mission (see the
changelog). Screenshots: `work/ui/screens_0.2.0/` (local).
