# Brief: text drawn into textures (v0.1.1)

Read `BASE_RULES.md` and `docs/translation_brief.md` first; their rules apply. This page is for the Japanese that
is drawn into the game's GIM textures (button labels, panel headers, HUD banners), which the text patch cannot
reach. The textures are redrawn in English by `tools/redraw_images.py` (`docs/image_redraw.md`). Your job is to
find every texture that shows Japanese, transcribe it, give the English, and measure where it is drawn.

## Your files

- `work/ui/gim_png/_tasks/task_<G>.json`: your textures. For each one: `file` (path under `work/source/dat/`;
  a `.gfp` pack adds `#NN`), `size`, and `muf_rows`: the row the Ultimate Frontier project wrote for the texture
  at the same path, when there was one (`muf_same_path`: "pixels identical" or "differs"). It is a hint only:
  Ace Frontier's texture is usually a different drawing, so check the Japanese and the layout yourself.
- `sheets`: packed review sheets `work/ui/gim_png/_tasks/<G>_NNN.png`, each listing the files it shows. Small
  textures are enlarged 2x or 3x on the sheets.
- Full-size PNGs: `work/ui/gim_png/<top>_<folder>/<path with __ for subfolders>.png`, e.g.
  `data/menu/hangar/han_m_info_info_base.gim` → `work/ui/gim_png/menu_hangar/han_m_info_info_base.gim.png`,
  `data/menu/gallery/picture_s/x.gim` → `work/ui/gim_png/menu_gallery/picture_s__x.gim.png`,
  `data/cockpit/gfp/p0_of0_l.gfp#03` → `work/ui/gim_png/cockpit_gfp/p0_of0_l.gfp_03.png`.
  Use the Read tool to view a PNG; crop and enlarge with Python (PIL) when the text is small.

Look at every sheet and open the full PNG of every texture that may contain Japanese. Report Japanese only (kana,
kanji, full-width text that reads as Japanese). Ignore English already in the art, pictures with no text, and the
official series logos ("MACROSS ACE FRONTIER", the small katakana line under that logo, the "マクロス7",
"MACROSSⅡ", "MACROSS F" title logos): they are kept.

## Output: `work/translation/en/images/img_<G>.json`

This file may contain Japanese (it is gitignored). Write it with
`json.dump(obj, f, ensure_ascii=False, indent=1)`:

```json
{"group": "A", "sheets_viewed": 9, "textures_in_task": 186, "textures_with_japanese": 40,
 "rows": [{"file": "data/menu/hangar/han_m_info_info_base.gim", "size": [256, 64],
           "jp": "天候\n時刻\n制限時間", "en": "Weather\nTime\nTime Limit",
           "kind": "caption", "style": "white bold on dark blue plates",
           "items": [{"line": 0, "box": [3, 2, 30, 13], "plate": [1, 1, 40, 15], "bg": "flat",
                      "color": [255, 255, 255], "align": "center", "fallbacks": ["Wthr"]}],
           "notes": "", "flags": []}],
 "report": {"uncertain": [], "missing_glossary": [], "notes": []}}
```

- One row per texture that has Japanese. `jp` and `en` hold one line per separate piece of text, in reading order
  (top to bottom, then left to right), joined with `\n`. A two-line label that is one phrase stays one line in
  `jp` with a real newline only if the game shows it as two lines; then say so in `notes`.
- `items`: one per line of `jp`, in the same order (`line` = its index):
  - `box`: `[x, y, w, h]` in texture pixels, the bounding box of the old Japanese glyphs (measure it from the
    full PNG with Python: pixels that differ from the background around them).
  - `plate`: the area that can be erased and drawn into: the box plus the free space around it up to the next
    graphic (frame line, icon, other label). The English is fitted into the plate, so it is usually wider than the
    box. Never let it overlap an icon or another label.
  - `bg`: what is under the text: `transparent` (alpha 0 around the glyphs), `flat` (one colour), `hgrad` /
    `vgrad` (gradient across / down), `bands` (horizontal stripes or scanlines, same along a row), `picture`.
  - `color`: the main fill colour of the glyphs `[r, g, b]`; add `"outline": [r, g, b]` or `"glow": [r, g, b]` if
    the glyphs have a dark edge or a glow, `"gradient": [[r,g,b], [r,g,b]]` for a top-to-bottom metallic fill,
    `"italic": true` if slanted.
  - `align`: `left`, `center` or `right`, as the Japanese is placed.
  - `fallbacks`: shorter English forms, best first, for when the full text does not fit.
- `kind`: button label, menu title, banner, caption, message, map label, cockpit HUD, other.
- `flags`: `uncertain` (cannot read the Japanese for sure, or unsure of the meaning), `mockup` (the texture looks
  like a design mock-up with dummy values; still list it), `numbers` (a counter word or unit drawn next to digits
  that the game draws: explain in `notes` what should replace it).
- Black/white, on/off, normal/light variants (`_b`/`_w`, `_on`/`_off`, `_light`) are separate textures: list each,
  with the same English and the same item layout where the art is the same.

## English

- Fit the drawn area: buttons and labels are short Title Case ("Sortie", "Details", "Time Limit"). Do not hesitate
  to abbreviate (BASE_RULES), but give the full form in `en` when it fits the plate and the short forms in
  `fallbacks`.
- Reuse the game's own wording. The menu text is already translated in `work/translation/en/corpus.json`
  (`jp` → `en`, groups `ui`, `title`, `mission`, `skill`, `rank`): search it for the same or a similar term and use
  its English. Names, units, songs, mission titles: `work/glossary/*.json`.
- The Ultimate Frontier hint (`muf_rows`) shows how the sister game worded the same label. Reuse it when it says the
  same thing and the glossary agrees.
- Pilot stats are, in this order: Stamina, Shooting, Melee, Defense, Speed, Focus, Awakening; their 3-letter forms
  are STA SHT MEL DEF SPD FOC AWK.
- Do not soften or drop meaning. A counter word after a number (位, 発, 機, 回) becomes the English that reads
  right after the digits ("1st" or "#1", "shots", "units", "times"); say what you chose.

## Report (in the file's `report`, no Japanese there)

Sheets viewed vs sheets in task, textures with Japanese, the calls you were unsure of, terms missing from the
glossary. Your final message: the same counts and anything the redraw needs to know (textures that share text,
labels too long for their plate, mock-ups).
