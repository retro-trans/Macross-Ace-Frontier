# Macross Ace Frontier — English patch

Fan translation of the PSP game *Macross Ace Frontier* (ULJS-00158, v1.02) into English. The patch is
distributed as an xdelta file that you apply to your own disc image. This repository contains translation text,
glossaries, layout metadata and tools; disc images, extracted game data and Japanese working files are excluded.

## Applying the patch

Use [Retro Trans](https://github.com/retro-trans/retro-trans-tools/releases/latest) for automatic patching:

1. Open **Automatic**, click **Refresh catalog**, and browse to your original Japanese ISO.
2. Select the **Macross Ace Frontier** English patch.
3. Leave **Target** on **Latest**, choose a new output filename, and apply the patch. Retro Trans downloads the
   matching patch and verifies the resulting image.

See the [release notes](https://github.com/retro-trans/Macross-Ace-Frontier/releases) for changes, known
limitations and supported upgrade paths.

For manual patching:

1. Dump your own Japanese UMD to an ISO. Full patches apply to the original release (Redump v1.02):
   - `Macross Ace Frontier (Japan).iso`, 646,938,624 bytes
   - SHA-256 `58e0020ebf971462fc033f24cc5fe2cbac06ed7ca1416a39302d396611ca4f1f`

   The "PSP the Best" reprint (v2.00, ULJS-19029) is a different image and is not supported yet.
2. Download `MacrossAceFrontier-English-<version>.xdelta` from
   [Releases](https://github.com/retro-trans/Macross-Ace-Frontier/releases/latest).
3. Apply it with xdelta3 (or any VCDIFF tool such as Delta Patcher):

   ```bash
   xdelta3 -d -s "Macross Ace Frontier (Japan).iso" MacrossAceFrontier-English-<version>.xdelta "Macross Ace Frontier English <version>.iso"
   ```

4. Compare the output SHA-256 with the release notes or `BUILD-MANIFEST.json`, then play it in PPSSPP. Boot it
   fresh and load a normal save: save states made with the Japanese image or an older patch keep the old text in
   memory.

The patched image carries a decrypted EBOOT. PPSSPP and custom firmware ISO drivers load it; official firmware
without custom firmware does not.

## What is translated

- Menus, help text, system messages, unit, weapon and pilot descriptions, skills, titles, the sound test
- Era prologue and epilogue narration, mission titles, briefings and objectives, in-mission tutorial lines
- Text drawn into textures (menus, buttons, HUD banners, mission title cards; the official series logos are kept)
- **English subtitles for the in-mission radio voice**, which has no text in the original game
- A proportional English font (GenEi LateGo) with a built-in 4x glyph page, so text stays sharp when PPSSPP
  renders at 2x–4x without a texture pack

The work was ported from the sister project
[Macross Ultimate Frontier](https://github.com/retro-trans/Macross-Ultimate-Frontier) (same engine, sequel):
its glossary, identical translated strings, the font patch, the texture redraw and the voice subtitle system.

## Repository layout

- `docs/` — format notes, the VWF and voice subtitle ports, translation briefs and the release guide
- `tools/` — dump, insert, font, subtitle, texture, build and porting tools
- `work/glossary/` — researched names and terms every translation must follow
- `work/translation/en/` — the English text (`*.en.json`): the corpus, its 80-row slices and the voice subtitles
- `work/ui/` — font widths, texture redraw layout; screenshots stay local
- `work/fonts/` — the GenEi LateGo font and its licence

## Build it

Put your original ISO in the project root as `Macross Ace Frontier (Japan).iso` and extract its data as
described in [the format notes](docs/formats.md). Then:

```text
python tools/build_iso.py <version> --voice-subs work/translation/en/voice/voice_subs.en.json
python tools/relayout_iso.py "Macross Ace Frontier (Japan).iso" "work/output/Macross Ace Frontier (EN <built>).iso" "work/output/Macross Ace Frontier (EN <version>).iso" --write
```

The full command lines for each version are in the [changelog](CHANGELOG.md), and
[the release guide](docs/RETRO_TRANS_RELEASES.md) covers packaging. The Japanese working files
(`work/translation/**/*.json` without `.en`) are generated locally from your own disc and are never committed;
`tools/corpus_slice.py export` and `tools/strip_jp.py` write the English-only copies.

## Credits

GenEi LateGo © okoneya.jp, SIL Open Font License 1.1 (`work/fonts/GenEiLatin_LICENSE.txt`).

## License

Translation text and tools: [MIT](LICENSE). The font keeps its own licence (SIL OFL 1.1). The game and its assets
belong to Bandai Namco Games / Artdink and the respective Macross rights holders. Bring your own disc image; this
license does not cover the game or its assets.
