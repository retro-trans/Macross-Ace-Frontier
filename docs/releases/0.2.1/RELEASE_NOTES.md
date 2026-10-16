English fan translation of **Macross Ace Frontier** for PSP (**ULJS-00158**, v1.02), including English subtitles for the in-mission radio voice.

### Apply

**Recommended:** Use the latest [Retro Trans](https://github.com/retro-trans/retro-trans-tools) app. Click **Refresh catalog**, open **Automatic**, select your original Japanese ISO, choose **0.2.1** (or **Latest**), and select a new output filename. The app downloads the matching patch and verifies the result.

**Manual patching:** [DeltaPatcher](https://github.com/marco-calautti/DeltaPatcher) and [xdelta3](https://github.com/jmacd/xdelta) accept the same asset:

| Your source image | Patch |
| --- | --- |
| Original Japanese ISO (v1.02) | `MacrossAceFrontier-English-0.2.1.xdelta` |

```text
xdelta3 -d -s "Macross Ace Frontier (Japan).iso" MacrossAceFrontier-English-0.2.1.xdelta "Macross Ace Frontier English 0.2.1.iso"
```

Original Japanese ISO (Redump v1.02): 646,938,624 bytes; SHA-256 `58e0020ebf971462fc033f24cc5fe2cbac06ed7ca1416a39302d396611ca4f1f`. The "PSP the Best" reprint (v2.00, ULJS-19029) is a different image and is not supported by this release.

Release output: 647,364,608 bytes; SHA-256 `90ee13f53f598231cb6b40f9337d1bd06c42d0492e5c66ee9b097d03ba944993`.

The exact source, output and patch hashes are in `BUILD-MANIFEST.json`. `VALIDATION.json` records the patch round trip, and `SHA256SUMS.txt` covers the downloads. Manual patchers require the unpacked ISO.

### What's included

This is the first public release.

* **Menus and help:** the main, single-player, network and option menus, help bars, system and save messages, unit, weapon, pilot and operator descriptions, skills, player titles, records and the sound test. 1,824 distinct strings in all.
* **Story text:** prologue and epilogue narration for every era (SDF, Plus, 7, Frontier), mission titles (episode titles use the official English), objectives and briefings, and in-mission objectives and tutorial lines.
* **Radio voice subtitles:** the in-mission radio cut-ins have no text in the original game. Each clip was transcribed and translated, and the patched game shows the English line under the cut-in while it plays. 5,375 of the 6,711 clips have a subtitle; the rest are silent placeholders, shouts without words, or narration already shown as text.
* **Textures:** 346 textures with Japanese text are redrawn in English (menus, buttons and labels, HUD banners, mission title cards, loading tips). The official series logos keep their original designs.
* **Font:** a proportional English font (GenEi LateGo) with its own 4x glyph page. In PPSSPP at 2x–4x rendering, game text is drawn sharp without a texture pack.

This project was ported from the sister project [Macross Ultimate Frontier](https://github.com/retro-trans/Macross-Ultimate-Frontier) (same engine, sequel), reusing its glossary, its translation of identical strings, its font patch, texture redraw and voice subtitle system. See the [changelog](https://github.com/retro-trans/Macross-Ace-Frontier/blob/main/CHANGELOG.md).

### Release status

**This is an early build. Further proofreading and full in-game playtesting are needed.** File and patch verification shows that the intended data is included and that the patch reproduces the release image. It does not certify emulator or console behavior. In PPSSPP, the menus, a new campaign through character and operator select, the era narration, the mission list and briefing, and the first mission (intro, radio subtitles) were checked. Most missions have not been played with this build.

Known limitations:

* Only voice clips that the mission script plays are subtitled. Voices played elsewhere (menus, character select samples) are not. The parts of a long subtitle advance at even steps through the clip, not with the phrasing.
* Letter spacing in text drawn at sizes other than the font's native 14 px can be uneven by up to one pixel.
* Some redrawn screens (tip cards, gallery, settings, network rooms, results) were checked in preview images only, not in game.
* The 4x font is designed for emulators at 2x resolution or higher. At native 1x resolution the same glyphs are scaled down.
* The image carries a decrypted EBOOT. PPSSPP and custom firmware ISO drivers load it; official firmware without custom firmware does not. Real hardware has not been tried.

**Boot the patched ISO fresh and load a normal save.** Save states keep the old text, fonts and textures in memory.

### How it was translated

This is a **machine translation**, produced with large language models and then reviewed and edited using scene context and a researched glossary. Names and terms follow the [Macross Wiki](https://macross.fandom.com) and avoid Robotech names. Most radio clips are identical to Macross Ultimate Frontier's and reuse its reviewed subtitles; the remaining clips were transcribed locally with Whisper large-v3 (faster-whisper), and uncertain readings are marked in the sources. Human proofreading and playtesting are welcome.

### Acknowledgements

* **GenEi LateGo** © okoneya.jp, used for the English glyphs (SIL Open Font License 1.1; the licence is in the repository).
* **PPSSPP**, whose PRX decryption and debugger were used for the EBOOT tools and testing.
* **Whisper** (OpenAI) and **faster-whisper**, used to transcribe the radio voice.

### Source code

Translation text, glossaries and tools are available in the [project repository](https://github.com/retro-trans/Macross-Ace-Frontier). GitHub's source archives contain the repository snapshot at the release tag. Use the `.xdelta` asset to patch the game.

### Contribute

Bug reports, proofreading and playtesting are welcome at **[discord.gg/MssepShjmB](https://discord.gg/MssepShjmB)**.

No complete game images are included. Apply the patch to your own disc image.
