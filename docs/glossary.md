# Glossary

Version 0.1.0 (2026-10-16). Files live in `work/glossary/`:

| File | Contents |
|---|---|
| `characters.json` | 101 characters: 20 playable pilots, 4 player-pilot slots, 4 operators, 4 AI/enemy pilots, plus supporting cast |
| `mecha.json` | 112 units, 12 packs, 9 families (incl. Super / Strike / Armored Valkyrie), 16 mission objects |
| `organizations.json` | 52 militaries, factions, squadrons, bands and fleets |
| `locations.json` | 24 planets, cities and ships-as-places |
| `terms.json` | lore, game-system terms, series titles, **songs**, **skills**, **ranks**, **missions** |
| `gaps.json` | Output of `tools/glossary_check.py`: every name the game uses and how it matched |

## Where it came from

The glossary was seeded from the **Macross Ultimate Frontier** project (`../Macross Ultimate Frontier`,
glossary 0.1.0). MUF is the sequel on the same engine and its cast is mostly a superset of Ace Frontier's.
The seed:

- kept every entry from a series that Ace Frontier covers (SDF Macross, DYRL, Plus, 7, Frontier) and every
  entry that the AF text names (this keeps Roy, Nora, D.D. Ivanov and Shin Kudo from Macross Zero);
- dropped 25 entries that AF never names: the MUF-only originals Yui, Luis and Pinon, and the Macross II,
  VF-X2, Dynamite 7 and other Zero cast;
- renamed MUF's `in_game` field to `muf_role` and added `af_role` and `af_uses`;
- added AF-only entries: magazine cameos, mission objects, songs, skills, ranks and mission titles. Where MUF
  had already translated the same Japanese string, its English was reused (status `muf`).

The four player pilots have **no default names in AF**. The game calls the slots パイロット男Ａ/男Ｂ/女Ａ/女Ｂ
(Male Pilot A/B, Female Pilot A/B). MUF later named them Yuuto Kagura, Gary Murdoch, Miyuki Shirakawa and
Hilda V. Bergen; the Macross Wiki lists those names on the AF page. Their entries keep MUF's personality notes
for voice work, but AF text must not use the names.

## Spelling policy

Same as MUF, so the two patches read alike:

1. **Macross Wiki (macross.fandom.com) wins** for names. Where the wiki contradicts itself, the entry is
   `needs_check` and `notes` explains the choice.
2. **No Robotech names.** They are in `avoid` lists.
3. **Given name first** for Japanese names (Alto Saotome, Hikaru Ichijyo). Chinese-order names keep the surname
   first (Lynn Minmay).
4. **No macrons or umlauts:** the game font has no glyphs for them. Shin Kudo, VB-6 Konig Monster.
5. **Episode titles:** a mission named after an anime episode uses the official English episode title
   (Wikipedia episode lists). Where MUF already chose a wording for the same title, MUF's wording wins and the
   Wikipedia form is in `refers_to`.
6. **Songs:** MUF's English title when MUF had the song, else the Macross Wiki article title (often romanised,
   e.g. *Totsugeki Love Heart*), else the title as written when it is already English.

Decided in MUF and not to be reopened: Vrlitwhai Kridanik, Quamzin Kravshera, Milia Fallyna Jenius, Jeffrey
Wilder. MUF's translation also settled Hoilie, Golg Boddole Zer (full title form) / Boddole Zer, and Shin Kudo.

## Fields

- `en`: the canonical spelling. Empty means not decided yet; see `status`.
- `ja`, `ja_aliases`: the Japanese forms. `ja_aliases` holds the short and variant forms AF uses
  (マックス, ミリア・ファリーナ, ゴルグ・ボドルザー, クラン・クラン（マイクローン）...). The checker matches both.
- `avoid`: spellings the proofreading script must replace with `en` (case-sensitive).
- `gender`: from the wiki. `unknown` means use neutral wording. Never infer gender from a name.
- `af_role`: pilot (playable) / pilot table (AI or enemy) / operator / player pilot slot / mentioned / not seen.
- `af_uses`: how many AF text entries contain the name. 0 does not mean unused: AF also has voice clips.
- `status`: `verified` / `decided` / `muf` / `wiki` / `episode` / `term` / `as_written` / `provisional` /
  `needs_check` / `needs_research` / `open`.

## AF naming notes

- **Valkyrie variants:** unit labels add （Ｆ） for the DYRL film version and （Ａ） for the armored version.
  ＶＦ－１Ａ（Ｆ） 一条機 is the Super Valkyrie, ＶＦ－１Ｓ（Ｆ） the Strike Valkyrie, ＶＦ－１Ｊ（Ａ） the Armored
  Valkyrie.
- **VF-17:** AF calls both VF-17D and VF-17S "ナイトメア" (Nightmare). Translate what the game says.
- **Milia** has three playable versions: SDF-era "Milia Fallyna" (before marriage), "Milia (Micronian)" and
  Macross 7 mayor "Milia (7)". **Max** has the SDF pilot and "Max (7)". **Klan** has a Micronian version.
- **Guld** is misspelled ガルド・ボア・ボーマン in one unit list. Translate it as Guld Goa Bowman.
- **Battle Frontier**'s profile calls the Frontier fleet the "21st" New Macross-class fleet. Check this before
  translating it (most sources say 25th).

## Open items

| Item | Status | What is needed |
|---|---|---|
| ＶＳＦ (Sharon Apple's affiliation tab) | needs_research | Expansion not on the wiki. Keep "VSF" until found |
| 半身マクロス (mission object, parts 01-10) | needs_research | Find the mission that uses it |
| 空戦ポッド, 重攻撃機 | needs_research | MUF names them "Air Combat Pod" / "Heavy Attack Craft"; canon unit not identified |
| フロンティア行政府 | needs_research | English name of the Frontier civil government |
| バカタール加藤, 倉西編集長 | provisional | Magazine-staff cameos in the password missions; romanisation and magazine |
| 7 song / BGM titles | open | 嵐の中で輝いて, 架空の空, ゼントラ艦隊, 艦隊戦, 灼熱の脱出, ハーフムーンラブ, 宇宙を駆ける |
| 5 skills | open | ダッシュプラス, チャフ, 修理, ミサイル落とし, スピリチア吸収 (translate with the UI) |
| 47 mission titles | open | Game originals; translate with the UI |
| 26 characters | needs_check | Inherited from MUF unchanged (minor Macross 7 / F cast) |

## Checking against the game text

```bash
python tools/dump_text.py
python tools/glossary_check.py
```

`glossary_check.py` reads the AF name tables from the decrypted EBOOT (pilot table 0x24E9C8, unit/object
table 0x259044) plus the mission scripts and unit lists, and writes `work/glossary/gaps.json`. Current result:
characters 2 gaps (both editor labels, 未使用 and 施設), mecha 0 gaps, objects 0 gaps. The organization list is
mined from prose and is mostly noise. See [formats.md](formats.md) for where the text lives.

## Sources

- AF on the Macross Wiki: https://macross.fandom.com/wiki/Macross_Ace_Frontier (cast, original characters,
  password missions)
- Episode titles: Wikipedia lists for
  [SDF Macross](https://en.wikipedia.org/wiki/List_of_The_Super_Dimension_Fortress_Macross_episodes),
  [Macross 7](https://en.wikipedia.org/wiki/List_of_Macross_7_episodes) and
  [Macross Frontier](https://en.wikipedia.org/wiki/List_of_Macross_Frontier_episodes)
- Character facts: the per-character wiki pages linked in each entry (inherited from MUF)
