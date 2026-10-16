# Translation brief: Macross Ace Frontier (v0.1.0)

Read `BASE_RULES.md` first; its rules apply in full. This page adds what is specific to this game. The sister
project **Macross Ultimate Frontier** (same engine, sequel) has been translated already; this game reuses its
glossary and, where the Japanese is identical, its translations.

## Work file and your output

- `work/translation/en/corpus.json`: **one row per distinct Japanese string** of the whole game (menus, system
  messages, mission titles, briefings and objectives, unit and weapon names and descriptions, skills, titles,
  profiles, era narration, sound test, in-mission script lines, mission unit names). Each row lists every place it
  occurs (`occ`), so it is translated once. Rows are in game order: neighbours are the same menu, list or scene.
  **Do not edit corpus.json.**
- `python tools/corpus_slice.py show <N> --context 10` prints your slice. `~` marks context rows, `<NL>` a newline.
  Each row shows its group, status and limit:
  - `box~NNNpx`: the width the line should fit, measured in pixels at 14 px text with the game's English font.
  - `WRAP ...`: the text is re-wrapped at build time (see below).
  - `MAX_BYTES=n`: a fixed-size field (pilot table, a few buffers). The English must fit in n bytes (ASCII = 1).
  - `xK`: the string is used K times.
- Rows with `status: tm` are prefilled from the Ultimate Frontier translation. **Review them**: keep them, or fix them
  if they are wrong for this game or contradict the glossary.
- Write `work/translation/en/slices/slice_NN.en.json` (NN = two digits) with Python
  `json.dump(obj, f, ensure_ascii=False, indent=1)`, including **every** row of the slice, prefilled ones too:

```json
{"slice": 3, "rows_in_slice": 80, "rows_examined": 80,
 "rows": [{"id": "u0412", "en": "...", "flags": [], "notes": ""}],
 "report": {"uncertain": [], "kept_omission": [], "missing_glossary": [], "unfinished": []}}
```

- **No Japanese anywhere in the slice file** (it goes to git). Notes describe the Japanese in English; use romaji
  only when you must.
- Run `python tools/corpus_slice.py check <N>` and fix every ERROR. Warnings are widths and line counts: follow
  "Fitting" below. `python tools/corpus_slice.py width "text"` measures a line.
- `flags`: `uncertain`, `kept_omission`, `name_missing`, `unfinished`, `reflow` (you deliberately changed the number
  of line breaks of a non-WRAP row), `overflow` (still too long after compressing; say so in notes).

## Line breaks

All text in this game uses real newline characters (`"\n"` in JSON). Never write a literal backslash-n.

- **Normal rows:** keep the same number of lines as the Japanese, broken at a natural point. Menu messages such as
  "Save the data?<NL>..." keep their shape.
- **WRAP rows** (mission briefings, unit descriptions, pilot and operator profiles): the Japanese is hard-wrapped at
  a fixed character count, often in the middle of a word. Ignore its breaks. Write
  - `title_lines=0`: one paragraph, **no newlines**;
  - `title_lines=1` (unit descriptions): the unit name, one newline, then the description as one paragraph.
  The build wraps the paragraph at the box width. The check tells you how many lines it will take; it must not
  exceed `max_lines`.

## Fitting

Write the full line first (BASE_RULES), run the check, then compress what is over: abbreviate, use shorter words,
drop filler. Never drop the end of a sentence or a fact. The `box` widths of UI labels are estimates from the
Japanese width; a label up to the warning is fine, and a little over is acceptable for short labels if the meaning
needs it (flag `uncertain` and say so). Briefings, descriptions and profiles must fit their `max_lines`.

## Character set

Shift-JIS only. Use plain ASCII wherever possible. Also allowed and kept as they are: `…` `☆` `♪` `×` `○` `△` `□`
`→` `←` `↑` `↓`, the Roman numerals `Ⅱ` `Ⅲ`, Greek `α` `γ`, and icon glyphs such as `⑳` (it draws the "Duo" logo
after "Memory Stick": write "Memory Stick⑳"). No `é`, `ō`, `ö`, em dash. Use `-` or `--`.
Full-width letters and digits become ASCII: `ＶＦ－２５Ｆ` → `VF-25F`, `ＳＰ` → `SP`.
Do not write a literal `{` (it starts a colour code).

## Codes that stay as they are

`%s %d %02d` and other placeholders, button symbols ○ × △ □, `L`/`R` buttons. `%s` in narration and messages is a
player or partner name: never give it a gender.

## Names and terms

`work/glossary/` is the authority (characters, mecha, organizations, locations, terms). Use `en`; never an `avoid`
spelling. `ja_aliases` maps the short forms the game uses (マックス, ミリア・ファリーナ, ゴルグ・ボドルザー...).

- The four player pilots have no names in this game: パイロット男Ａ "Male Pilot A" etc. Do not use the MUF names.
- Decided, not to be reopened: Vrlitwhai Kridanik (ブリタイ), Quamzin Kravshera (カムジン), Milia Fallyna Jenius
  (SDF era before marriage: "Milia Fallyna" or "Milia"), Golg Boddole Zer / Boddole Zer, Gamlin Kizaki, Gepelnitchi,
  Michael Blanc (Michel when the Japanese says ミシェル), Luca Angeloni.
- 統合軍 → "U.N. Forces"; 新統合軍 → "New U.N. Forces"; 反統合同盟(軍) → "Anti-U.N. Forces"; ゼントラーディ軍 →
  "Zentradi forces" / "the Zentradi"; メルトランディ → "Meltrandi"; バロータ軍 → "Varauta Army".
- Mission titles: `terms.json` → `missions`. Status `episode` / `term` / `muf` give the English to use. Status `open`:
  translate the title yourself (keep katakana-English titles as natural English: ファースト・ステップ → "First Step").
- Unit names follow `mecha.json`. In the unit table, `一条機` / `（一条機）` = the pilot's personal unit:
  "VF-1J Valkyrie (Hikaru)". `（Ｆ）` = film (DYRL) version, `（Ａ）` = armored: see mecha.json families.
  `（一般機）` = "(Standard)". AF calls the VF-17 "Nightmare".
- Skills, songs and ranks: `terms.json` → `skills`, `songs`, `ranks`.
- Missing name: translate as well as you can, flag `name_missing`, list it in `report.missing_glossary`.

## Gender

Never infer gender from a name. Use `gender` in characters.json. Anyone not in the glossary, and the player, gets
neutral wording.

## Style by kind of text

| Group | What | Style |
| --- | --- | --- |
| `mission` | Mission title, objective, briefing | Titles in Title Case. Objectives imperative and short ("Destroy all enemies."). Briefings: crisp military briefing voice, past/present tense as the Japanese. |
| `narration` | Era prologue/epilogue, one row = one screen line | Documentary, a little grand. A sentence often runs over several rows: cut the English at the matching point. One row in, one row out. Year in Western digits; "A.D." only where the Japanese starts with 西暦. |
| `profile` | Pilot and operator profiles | Third person, lively. Ends with `（CV：name）` → "(CV: Given Family)", standard romanisation of the real voice actor; flag `uncertain` if unsure of a reading. |
| `unit_desc` | Unit name + description, short catchline rows | Spec-sheet voice. Catchline rows (2 short lines) keep their two lines. |
| `ingame` | Mission script lines: objectives, tutorial | Tutorial lines speak to the player ("Hold L to guard."). Some are an operator speaking: keep the voice. |
| `skill`, `title`, `rank`, `ui`, `stage_weapon`, `sound_test` | Menus, help, system messages, titles, credits | Concise, Title Case for labels and names, full plain sentences for messages ("Save the data?"). Credits: 作品 "Series", 歌 "Vocals", 作詞 "Lyrics", 作曲 "Music", 編曲 "Arrangement"; real people given name first. |
| `pilot_table`, `unit_table`, `locate` | Names | Glossary `en`; pilot table within MAX_BYTES (use a short form if needed). AI profile labels ("ザコ用射撃１格闘２攻撃力３") plainly: "Grunt: Shot 1 Melee 2 Atk 3". |

## Quality bar (from BASE_RULES)

- Restore subjects and verbs that Japanese drops when the context settles them; check who asks whom.
- Full strength: no softening.
- Before each row, settle who speaks to whom and what it answers. Report non-obvious calls in `report.uncertain`.
- Flag every row where you kept an omission (`kept_omission`).
- Report rows examined vs rows in slice.
