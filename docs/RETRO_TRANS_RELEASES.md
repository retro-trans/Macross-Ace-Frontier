# Retro Trans release packaging

Macross Ace Frontier follows the
[Retro Trans release standard](https://github.com/retro-trans/retro-trans-tools/blob/main/docs/RELEASE_STANDARD.md).
Stable identity: game ID `macross-ace-frontier`, platform `PSP`, edition `ULJS00158`, language `en`.
Never reuse a version for different bytes; a corrected image is a new `0.x.y`.

The supported source is the original release, Redump v1.02 (646,938,624 bytes, SHA-256
`58e0020ebf971462fc033f24cc5fe2cbac06ed7ca1416a39302d396611ca4f1f`). The "PSP the Best" v2.00 (ULJS-19029) is
a different image; supporting it would need its own edition and patch row.

## Release image

The title screen shows the version (`tools/title_tag.py`, bottom-right). It must match the release version, so
build the image that will be re-laid out with that version painted, under a separate test name:

```text
python tools/build_iso.py <version>-build --title-version <version> --voice-subs work/translation/en/voice/voice_subs.en.json
```

`tools/build_iso.py` appends every file that outgrew its sectors at the end of the image (a 1.1 GB test ISO), and
the new data sits too far from the original bytes for xdelta to match. Release images are re-laid out first:

```text
python tools/relayout_iso.py "Macross Ace Frontier (Japan).iso" "work/output/Macross Ace Frontier (EN <version>-build).iso" "work/output/Macross Ace Frontier (EN <version>).iso"
python tools/relayout_iso.py ... --write
```

The tool keeps the original file order, shifts later files by whole 32 KB blocks where a file grew, rewrites the
directory records and volume size, and verifies every file against the built ISO. The game opens files by path,
so the moved files load as before. Boot the re-laid-out image in PPSSPP before packaging.

## Build and validate

Check out Retro Trans Tools under the ignored `work/local/` and write the private builder configuration there
(it holds local paths):

```json
{
  "game_id": "macross-ace-frontier",
  "game_name": "Macross Ace Frontier",
  "platform": "PSP",
  "version": "<version>",
  "source_commit": "<full commit of this repository at the release tag>",
  "patches": [
    {
      "patch": "MacrossAceFrontier-English-<version>.xdelta",
      "edition": "ULJS00158",
      "language": "en",
      "source_version": "original",
      "source_format": "iso",
      "target_format": "iso",
      "source": "<original ISO>",
      "target": "<release ISO>"
    }
  ]
}
```

Add an upgrade row (`source_version` = the previous published version, source = that exact published image)
for every later release. Then build and validate (run from the Retro Trans Tools checkout, or install it):

```text
python -m retro_trans.release build work/local/release-<version>.json --out work/release/<version>
python -m retro_trans.release validate work/release/<version>
```

The builder encodes each patch, decodes it again and compares the complete target. Only the patches,
`BUILD-MANIFEST.json`, `VALIDATION.json` and `SHA256SUMS.txt` are release assets. Never upload an ISO, extracted
game data or the private configuration. Copy the three metadata files to `docs/releases/<version>/`.

## Publish and confirm discovery

Tag the release commit `v<version>`. Stage a draft release, upload the patches, `VALIDATION.json` and
`SHA256SUMS.txt`, upload `BUILD-MANIFEST.json` last, check the uploaded sizes and hashes, then publish. Notes
follow the sibling releases: Apply, changes, release status, included content, how it was translated,
acknowledgements (GenEi LateGo, SIL OFL 1.1), Source code and Contribute.

After publishing, run **Refresh patch catalog** in Retro Trans Tools Actions with
`repository=retro-trans/Macross-Ace-Frontier` (or wait for the hourly run) and confirm the release appears
in the public catalog.

Packaging and catalog checks verify patch application, not in-game behaviour. Keep runtime limitations explicit
in the notes.
