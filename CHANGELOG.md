# Changelog

## [0.2.1] - 2026-10-16 (first public release)

Same game content as 0.2.0, in the original disc layout.

### Added
- Public repository files: `README.md`, `CONTRIBUTING.md`, `LICENSE` (MIT for text and tools),
  `docs/RETRO_TRANS_RELEASES.md` (game ID `macross-ace-frontier`, edition `ULJS00158`), following the
  Macross Ultimate Frontier repository.

### Build
- `work/output/Macross Ace Frontier (EN v0.2.1).iso`: `python tools/relayout_iso.py "Macross Ace Frontier (Japan).iso"
  "work/output/Macross Ace Frontier (EN v0.2.0).iso" "work/output/Macross Ace Frontier (EN v0.2.1).iso" --write`.
  647,364,608 bytes (original 646,938,624), SHA-256
  `90ee13f53f598231cb6b40f9337d1bd06c42d0492e5c66ee9b097d03ba944993`. 70 of 72 files moved by up to 208 sectors;
  all 72 match 0.2.0.
- Booted in PPSSPP to the main menu and the campaign load screen (the moved archives load). 0.2.0, with the same
  files, was played into the first mission with radio subtitles.
- Release assets built with Retro Trans Tools (`docs/RETRO_TRANS_RELEASES.md`); metadata in `docs/releases/0.2.1/`.

## [0.2.0] - 2026-10-16 (test build, not released)

### Added
- **English subtitles for the in-mission radio voice.** The cut-in voice lines had no text anywhere in the game.
  The patched game now shows an English line under the cut-in while each clip plays: in the pre-mission intro
  camera, over the "Mission Start" and "Enemy Appeared" banners, and in flight with the HUD. Ported from Macross
  Ultimate Frontier 0.7.0; details, numbers and limits in `docs/voice_subtitles.md`.
  - **5,375 of the 6,711 voice clips have a subtitle.** The rest have nothing to show: 1,130 silent placeholder
    clips, 190 shouts, grunts and laughs without words (plus 4 repeats of such clips), and 12 era prologue
    narration clips whose text is already on screen.
  - **6,545 clips are byte-identical to Ultimate Frontier clips**, so their transcripts and MUF's reviewed English
    were reused (5,231 subtitles). The other 166 clips (all of Vrlitwhai Kridanik's 151, plus a few Hayao, Gavil,
    Basara, Mylene and Max lines) were transcribed with faster-whisper large-v3 on the GPU (92 s, plus a retry
    pass) and translated in 2 slices of 80 rows (`work/translation/en/voice/slices/`, brief
    `docs/voice_translation_brief.md`), with the MUF clip of the same id shown as a reference (most are the same
    line recorded again): 144 subtitles. Slice flags: `whisper_doubt` 42, `uncertain` 13, `no_subtitle` 16,
    `kept_omission` 1, each with a note. Speaker map: `work/translation/en/voice/speakers.en.json` (39 speakers).
    Transcripts stay local (`work/source/voice/`, Japanese).
  - **Storage:** each line is appended to the end of its own clip in `macross.dat` (after the RIFF data, which is
    unchanged). The 630 copies of voice clips inside the `cv_*` fileset bundles are left as they are
    (`tools/muf_archive.py` `DAT_ONLY`), so no memory is added.
  - **EBOOT hooks** (`tools/voice_subs_patch.py`): the two calls that load a clip's lip-sync file (0x12CD2C,
    0x12ED70) also read the line from the clip's tail; the cut-in step call in the mission's 2D layer (0xDD3FC) now
    also draws it. All AF routines were matched to MUF's with `tools/port_match.py` and checked by hand. Same layout
    as MUF: VWF 12 px, white with a dark shadow, centred at (240, 228), nearest sprite depth; the line follows the
    lip-sync counter, plus 24 frames. The code (253 words), buffers and config sit in 2 KB of zeroed room that
    `tools/eboot_insert.py --reserve 3072` now leaves after the VWF width table; no new relocations.
- New tools: `voice_transcribe.py` (with `--reuse` for clips identical to MUF's and `--silence` for silent
  placeholders), `voice_rows.py`, `voice_slice.py`, `voice_fix_names.py`, `voice_subs_export.py`,
  `voice_subs_at3.py`, `voice_subs_patch.py`.
- `tools/build_iso.py`: `--voice-subs <file>` (and `--voice-placeholder` to show clip ids); the EBOOT reserve is
  now 3 KB.

### Build
- `work/output/Macross Ace Frontier (EN v0.2.0).iso`: `python tools/build_iso.py 0.2.0 --work
  work/output/build_0.2.0 --voice-subs work/translation/en/voice/voice_subs.en.json` (log
  `work/output/build_0.2.0.log`). 1,103,310,848 bytes, SHA-256
  `D6947BBC0885581E859E88F03B4A0D3FCEC866574F5A9437E63E756EF3F23F06`. Otherwise the same text and textures as 0.1.2.
- Checked in PPSSPP (OpenGL, 4x) from a new campaign into "First Step" with Claire as operator
  (`work/ui/screens_0.2.0/`, local): intro cut-ins (Claire, the player, both at once), Claire's two-line report over
  the "Mission Start" banner and then with the HUD, "Enemy reinforcements." with the "Enemy Appeared" banner, and a
  partner bark in flight. A placeholder build (clip ids) was checked first with Yuu as operator.
- The placeholder ISO shows each clip's id (e.g. `vp0_om0_102`) instead of English. It was first left in
  `work/output` as `(EN v0.2.0-ph).iso` and got loaded by mistake, so it now lives in `work/output/test/` as
  `PLACEHOLDER clip ids - do not play (EN v0.2.0-ph).iso`. The 0.2.0 ISO itself is unchanged; it carries
  "I'll make it work!" for `vp0_om0_102` (`work/ui/screens_0.2.0/02_intro_pilot.png`). It has the same byte size as
  0.1.2 because the lines fit in the 0x8000-byte padding after each clip in `macross.dat`.

### Known
- Only clips that the mission script queues are subtitled; voices played elsewhere (menus, character select
  samples) are not.
- Parts of a long line advance at even steps of the clip, not with the phrasing (one line in 0.2.0 has parts).
- Only the first mission was played. Not tried on real hardware. Whether subtitles show with the "2D Display"
  option off was not checked.
- Vrlitwhai's new recordings transcribed poorly; the uncertain readings are flagged in the slices and are worth a
  listen.

## [0.1.2] - 2026-10-16 (test build, not released)

### Fixed
- **4x text for outlined/shadowed text.** The menu help bar (and any other text drawn through the second glyph
  callback 0xF7AA4, which draws a glyph plus an outline from offset half-cells) used the native 14 px glyphs scaled
  up, so it looked blurry at 2x/4x. That callback now has its own dispatcher (47 words at 0xE6B4C, inside the
  unreferenced function 0xE6A74), the same one as the main callback. `tools/vwf_build.py` wraps both from the
  `CALLBACKS` list.

### Build
- `work/output/Macross Ace Frontier (EN v0.1.2).iso`: `python tools/build_iso.py 0.1.2`. 1,103,310,848 bytes,
  SHA-256 `6F85FF26760976D2218C7454E80A9BB154F5A279F161B5209E905C54819651EB`. Same text and textures as 0.1.1.
- Checked in PPSSPP (OpenGL, 4x): the main menu help bar is now sharp (`work/ui/screens_0.1.2/compare_bar.png`,
  0.1.1 above, 0.1.2 below).

### Known
- Letter spacing at sizes other than 14 px is still uneven by up to one native pixel (per-letter rounding).

## [0.1.1] - 2026-10-16 (test build, not released)

The Japanese text drawn into textures is redrawn in English (`docs/image_redraw.md`).

### Added
- **Texture redraw.** 346 textures with Japanese text are redrawn: menus, buttons and panel labels, HUD banners,
  107 mission title cards, five loading tip cards (and their gallery thumbnails), the title-screen copyright lines.
  The full list, without Japanese, is `work/ui/redraw_textures.json`.
  - Found by decoding all 2,706 GIM textures under `data/menu`, `data/script` and `data/cockpit`
    (`work/ui/gim_png/`, local). 786 are byte- or pixel-identical to Ultimate Frontier textures; for those MUF's
    review, English and layout are reused (84 textures). The other 1,920 were read again by four agents
    (`docs/image_translation_brief.md`), less the layout editor's dummy previews, unreferenced leftovers and the
    anime loading stills. The cockpit portraits (`.gfp`) and in-scene text in anime frames have no text to change.
  - Mission title cards matched to their titles by image (all 107 checked by eye); English from the corpus and the
    glossary ("First Step", "Ambition on Varauta 4", ...).
  - Tip cards: "Yuu and Itsuki's MAF Primer" (4 dialogue cards) and the co-op play card, translated and typeset
    again with the original colours, on the original line positions.
  - Kept as they are: official series logos (the title logo and its katakana line, era logos, the Macross Plus
    mission tag), the text in the anime loading stills.
  - 32 items use a short form (mostly HUD banners, "Wthr" for weather); none overflows.
- `tools/gim.py` and `tools/redraw_images.py` ported from MUF. The redraw tool now reads every
  `img_*.json`, builds a layout from the measured boxes when a texture has no spec (`auto_spec()`), and typesets the
  AF tip cards. Layout: `work/ui/redraw_layout.json`.
- `tools/build_iso.py`: step 3b runs the redraw into the build overlay before the repack (`--no-images` skips it).

### Build
- `work/output/Macross Ace Frontier (EN v0.1.1).iso`: `python tools/build_iso.py 0.1.1`.
  1,103,310,848 bytes, SHA-256 `7373BA49AA07B47C3FEA1389479581D4319CC7F71A2ED30AFB5B192F52187D0A`.
  351 GIM files written to the overlay (346 textures plus the five tip-card thumbnails).
- Checked in PPSSPP (OpenGL, 4x) from a new game to the first mission (`work/ui/screens_0.1.1/`, local): title
  copyright, save data "Switch Page", character stats STA…AWK, "Enter Name", mission select (Wthr / Time /
  Time Limit, Sortie, Info), player tab "Unit Settings", record panels and list (the highlighted label sits on its
  button), the "First Step" title card, the pause menu and info panel, the "Enemy Appeared" HUD banner.

### Known
- Not seen in game yet: the tip cards (they are not shown on the first loads), gallery, settings and controller
  config, network rooms, results; checked in the preview sheets only.
- The ID-card stat tiles (`setting/dl03.gim`) use an older stat set; two labels are guessed (REA, SEN).
- The rank counter suffix after a game-drawn number (`gal_r_c_rank_deco2`) is a fixed "th".

## [0.1.0] - 2026-10-16 (test build, not released)

First translated build: all game text in English, with Ultimate Frontier's proportional font and 4x text.

### Added
- **Full text translation.** `work/translation/en/corpus.json` holds every distinct Japanese string once
  (1,825 rows, 2,181 places: EBOOT, mission scripts, mission unit lists), built by `tools/build_corpus.py`.
  769 rows were prefilled from the Ultimate Frontier translation (identical Japanese) and reviewed. The rest were
  translated in 19 slices by 12 agents following `docs/translation_brief.md` (slice files in
  `work/translation/en/slices/`, no Japanese). All slices pass `tools/corpus_slice.py check`: 0 errors,
  162 width warnings (estimated boxes, mostly short labels and glossary names; see the slice reports).
  - Briefings, unit descriptions and profiles are hard-wrapped mid-word in Japanese. They are written as one
    paragraph and wrapped at build time to the box width (mission 266 px, unit 434 px, profile 448 px); the checker
    measures the line count.
  - Consistency pass: the large-unit restriction is "(No large units)" everywhere; confirm prompts use "Proceed?".
- **VWF + 4x text** (`tools/vwf_build.py`, `docs/vwf.md`): GenEi LateGo v2 glyphs in slots 1210–1305,
  proportional mode for the 14 px font, 10 printer/width/truncation patches ported from MUF, and the 4x glyphs as a
  fifth page of the font file behind a wrapper on the glyph draw callback.
- `tools/eboot_insert.py --reserve N` (room for the VWF width table in the new gap), `tools/build_iso.py`,
  `tools/insert_text.py` (FES 3.00), `tools/iso_patch.py`, `tools/ppsspp_ctl.py` from MUF.
- Porting tools: `tools/port_match.py`, `tools/port_align.py`, `tools/find_caves.py`, `tools/disasm.py`.

### Fixed
- `tools/muf_archive.py repack`: the `fileset.dat` head lists its records in another order than the idx; new
  offsets are now written to the matching record. Repack is byte-identical on an unchanged tree.
- `tools/dump_eboot.py`: two unrelated lone strings far apart were treated as a struct array, which capped the
  rank-display message at 31 bytes (real room: 128). The 4-byte float at 0x2934CC is marked as not text.

### Build
- `work/output/Macross Ace Frontier (EN v0.1.0).iso`: `python tools/build_iso.py 0.1.0`.
  1,103,126,528 bytes, SHA-256 `10A9D7CF50591628092DC3A6AB7D3F96A700FDD19E6E4CD1DD626612E0CB7E1F`.
  EBOOT 3,618,544 → 3,684,088 bytes (one 64 KB gap). 121 FES strings in 41 scripts, 295 unit-list cells.
- Played in PPSSPP (OpenGL, 4x) from boot to the first mission: menus, character and operator select, era
  narration, mission select and wrapped briefing, confirm dialog, mission load and intro camera
  (`work/ui/screens_0.1.0/`, local).

### Known
- Text drawn into textures is still Japanese: stat labels (体力...), 出撃 / 詳細 buttons, 天候 / 時刻 /
  制限時間 labels, the name-entry label, mission title cards, the title-screen copyright line.
- The second glyph callback (0xF7AA4) is not wrapped for 4x text.
- Not played past the first mission's intro; in-mission objectives and tutorial lines not seen yet.
- The ISO is far larger than needed (grown files are appended); `tools/relayout_iso.py` (copied from MUF) is not
  run yet.
- Not tried on real hardware.

## Glossary and tools - 2026-10-16

### Added
- **Glossary 0.1.0** (`work/glossary/`, `docs/glossary.md`). Seeded from the Macross Ultimate Frontier
  glossary, pruned to the Ace Frontier cast, and checked against the AF text:
  - 101 characters (20 playable pilots, 4 player-pilot slots, 4 operators, 4 AI/enemy pilots), 112 units,
    9 families, 16 mission objects, 52 organizations, 24 locations.
  - New in `terms.json`: 46 songs, 24 skills, 18 ranks, 104 mission titles. 45 mission titles are anime
    episode or film titles and use the official English title; 8 reuse MUF's translation.
  - New fields: `af_role`, `af_uses`; MUF's `in_game` is now `muf_role`.
  - Gap check: 0 unmatched units or objects, 2 unmatched character labels (both editor dummies).
  - Open items are listed in `docs/glossary.md`.
- Tools copied from the MUF project and adapted: `muf_archive.py` (fileset head matched by value),
  `dump_text.py` (FES 3.00, no menu CSVs), `glossary_check.py` (AF EBOOT name tables, `ja_aliases`, objects),
  `dump_eboot.py`, `muf_lzss.py`, `strip_jp.py`. `.gitignore` copied from MUF.
- `docs/formats.md`: AF disc, archive and EBOOT notes, and how they differ from MUF.

### Source
- Disc: `Macross Ace Frontier (Japan).iso`, Redump v1.02 (ULJS-00158), 646,938,624 bytes.
- EBOOT decrypted with a portable PPSSPP copy in `work/local/ppsspp/`.
