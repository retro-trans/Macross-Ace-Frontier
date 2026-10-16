# Redrawing the text in textures (v0.1.1, 2026-10-16)

```bash
python tools/redraw_images.py
```

This redraws the Japanese text drawn into game textures (GIM) in English. The tool and `tools/gim.py` were
ported from the Macross Ultimate Frontier project (same engine and texture format). It reads the rows in
`work/translation/en/images/img_*.json` (gitignored: they hold the Japanese) and the layout in
`work/ui/redraw_layout.json`, and writes:

| Output | What |
| --- | --- |
| `work/output/redraw/overlay/data/...gim` | The re-encoded textures, for `muf_archive.py repack --overlay` (gitignored) |
| `work/ui/redraw_preview/sheet_*.png` | Before/after contact sheets of every texture, after palette reduction (gitignored) |
| `work/ui/redraw_preview/report.json` | Per text item: the text drawn, font size, horizontal squeeze, whether a short form was used (no Japanese) |
| `work/ui/redraw_preview/shared_text.json` | Which textures share text (no Japanese) |

The list of every redrawn texture with its English (no Japanese) is `work/ui/redraw_textures.json`.

`--only <part of a path>` redraws a few textures into `work/ui/redraw_preview/_only/`; `--no-write` skips the
GIM files. `tools/build_iso.py` runs it as step 3b into the build overlay (`--no-images` leaves it out).

## Finding the textures

1. `python tools/gim.py dir <folder> work/ui/gim_png/<top>_<folder> --sheet` decodes every GIM (and every
   GIM inside a `.gfp` pack) under `data/menu`, `data/script` and `data/cockpit` to PNG with contact sheets
   (`work/ui/gim_png/`, gitignored). 2,706 files.
2. Each texture was compared with the Ultimate Frontier disc: 662 are byte-identical to a MUF texture (619 at
   the same path, 43 moved) and 124 more have identical pixels. For those, MUF's review stands (it read every
   MUF texture): its rows and layout specs were imported (`img_muf.json`, the `files` entries marked `_from`).
3. The other 1,920 were reviewed again, on packed sheets, after dropping what cannot be shown:
   - `a2a_*.gim` (178): the layout editor's preview pictures ("A2A dummy"), not drawn by the game;
   - 37 textures that no `.a2a` layout, script or EBOOT string names (`*_dummy.gim`, leftovers);
   - the 248 loading stills `mac00009`–`mac00256` (mecha renders and anime frames: the text in them, such as
     a weapon caption, chalkboard names or the Nyan-Nyan seals, is part of the frame and is kept);
   - the 107 mission title cards and their English subtitles (below).
4. Four agents read the rest (`docs/image_translation_brief.md`): Japanese, English, and the measured glyph box,
   plate, background kind, colour and alignment of every line (`img_A` hangar, `img_B` gallery and settings,
   `img_C` other menus, `img_D` HUD and cockpit).

## Mission title cards

The 107 `script/fesrat_m/*_title.gim` cards (480×48, white heavy gothic with a dark edge) are matched to their
mission titles by image: every short mission/title string of the corpus is rendered and compared with the card's
glyph mask (cards are reused across sub-missions, so the EBOOT neighbour of a mission ID is not always its
title). All 107 matches were checked by eye; one (`m7_160`) was set by hand. The English is the corpus /
glossary title (`img_titles.json`). One rule draws them all (style `title`, box `[4, 5, 472, 37]`).

## Loading tip cards

`menu/load/mac00001`–`mac00005` are the "Yuu and Itsuki's MAF Primer" dialogue cards (four) and the co-op
play card. They are transcribed and translated in `img_tips.json` (`card`: title, lines with speaker and
colour, "Next" line) and typeset by `tipcard()`:

- Cards 1–4: speaker column at x 101, colon at x 133, text from x 139 to 446, one line every 14 px from y 52;
  title at y 16; "Next - ..." at y 262. Card 5: headings and bullets at the y positions in its spec (`geom.ys`).
- The English keeps the Japanese line positions, so the dashed separators stay. Size 10 (or less, so that no
  line needs more than 20 % squeeze); colours white, yellow, green, orange for quoted terms (`[o]...[/]`),
  and the card 5 heading colours, all with a black edge.
- Erasing: in each line band, pixels of the text colours that touch the black edge are inpainted, only over the
  line's own run of lettering (so the portraits next to the text are not touched), then a soft dark shade is
  laid under the old and the new lines.
- The gallery thumbnails `picture_s/mac0000N_s.gim` are regenerated from the redrawn cards.

## How a texture is redrawn

For each texture, every item first **erases** its box, then every item **draws** its text:

1. Text: the row's `en` (or one line of it, `line`), or the item's `text`, then its `fallbacks`.
2. Fit (`fit()`): first the font may shrink a little (to 86 %) without squeezing, then the text may be squeezed
   horizontally down to 84 %, at any size down to `min_size`. If the full text cannot fit that way, the short
   forms are tried the same way. Only then is the text squeezed hard (down to `xscale_min`).
3. Render: Noto Sans JP (variable weight, SIL OFL 1.1), drawn at 4x and box-filtered down. Effects are layers
   under the fill: glow (blurred mask), shadow (offset mask), outline (dilated mask). The fill can be a
   vertical gradient. Italic is a shear.
4. Encode: `gim.encode()` quantizes the result back to the texture's own palette size, with an exact
   transparent entry kept for fully transparent pixels (a faint alpha-1 entry once showed as a line at the edge of
   every MUF title card).

### Measured items → spec (`auto_spec()`)

A texture with no `files` entry and no matching rule is laid out from its rows' measured items:

| `bg` | Erase |
| --- | --- |
| `transparent` | `clear` the glyph box grown by 1 px (2 px with an edge or glow), kept inside the plate |
| `flat`, `bands` | `row`: every row takes the colour of a text-free column next to the box |
| `hgrad` / `vgrad` | `plate` / `vplate`: interpolation from the pixels left/right (above/below) of the box |
| `picture` | `inpaint` the pixels near the text colour (and the edge or glow colour) |

The English is drawn into the plate's width (from the old glyphs' left edge for left-aligned text, to their right
edge for right-aligned text, centred on them otherwise) at the old glyphs' height, at size ≈ 0.95 × the glyph
height. A white fill with a coloured glow (the HUD banners) gets a solid 1.3 px coloured edge plus a soft glow,
weight 800. `item_set` in a `files` entry overrides single items (`{"<line>": {...}}`).

### Layout file (`work/ui/redraw_layout.json`)

- `styles`: named presets (from MUF).
- `rules`: glob patterns; the first match is the base (only the title cards use one now).
- `files`: per-texture entries, merged over the rule (imported MUF specs, overrides, tip card 5's geometry).
- `thumbnails`: gallery thumbnail → the still it is made from.

The erase modes (`clear`, `fill`, `row`, `col`, `plate`, `vplate`, `copy`, `inpaint`, `frost`) are those of the
MUF tool; see `tools/redraw_images.py`.

## Result (v0.1.1)

346 textures (351 GIM files with the five tip-card thumbnails), 771 text items; 32 items use a short form,
none overflows. By source:

| Group | Textures | What |
| --- | --- | --- |
| `muf` | 84 | Identical to a MUF texture: system and music menu buttons, unit/face cards, colour edit, record list |
| `titles` | 107 | Mission title cards |
| `D` | 50 | HUD banners `2d_ope_*` (27), `2d_rat_*` (23, four of them counter pieces) |
| `B` | 49 | Gallery record screens, controller config, ID card |
| `C` | 26 | Character stats, name entry, save data, results, pause panel, title copyright, network |
| `A` | 25 | Mission select, record panels in the hangar, hangar headers, pilot status |
| `tips` | 5 | Loading tip cards |

Choices worth knowing:

- Countdown banners: the game draws digits between `2d_rat_19` ("Last") and `2d_rat_20` / `2d_rat_42` /
  `2d_rat_29` ("min" / "sec" / "tgt", squeezed into 16 px), so it reads "Last 5 min".
- Missile counter in the record panels: the 10^8 / 10^4 separators became "x100M" / "x10K", the last unit "shots".
- The record panels are mock-ups with dummy values and a dummy mission name ("Roy Focker Assassination"); the
  game draws the real values over them.
- `gal_record_list_base` and its six highlight labels: same box and size, offsets (+6, +6/35/64/93/122/151)
  measured from the old glyphs, so the bright label covers the dim one exactly (checked in game).

## Tested in game (PPSSPP, v0.1.1)

Screenshots in `work/ui/screens_0.1.1/` (local): title copyright, save data, character stats, name entry,
operator select, mission select (weather / time / time limit, Sortie, Info), player tab, record tab (overall
and campaign), "First Step" title card, pause menu and info panel, "Enemy Appeared" banner.

Not seen in game yet: tip cards, gallery, settings and controller config, network rooms, results screens.
