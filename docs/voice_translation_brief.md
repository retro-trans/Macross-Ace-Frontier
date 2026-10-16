# Voice-clip subtitle translation brief

Read `BASE_RULES.md` first, then the "Names", "Gender" and "Quality bar" parts of `docs/translation_brief.md`. Those rules apply in full. This page adds what is specific to the voice clips.

## What you are translating

Ace Frontier shares most of its voice clips with Macross Ultimate Frontier (MUF): 6,545 of its 6,711 voice clips are byte-identical to MUF clips and take MUF's reviewed English. **Only the other clips are in the slices** (two slices). Most of them are the same line recorded again: same clip id, about the same length. For those, `show` prints a `ref:` line with the MUF clip's transcript and its English. Use it as a strong hint, not as the answer: the AF clip may say something a bit different, and either transcript may be the misheard one. Where the AF line is clearly the same, keep the MUF English (consistency with the shared clips); where it differs, translate what the AF clip says.

During missions, characters talk over the radio. Each line is a voice clip shown with the speaker's portrait (a "cut-in"). The game has no text for these lines, so we transcribed every clip with Whisper (speech recognition). The patched game now shows your English as a subtitle under the cut-in while the clip plays (`docs/voice_subtitles.md`).

**The Japanese you get is a machine transcript, not the script.** It is usually right, but it can contain:
- homophones or wrong kanji (han-tougou doumei "Anti-U.N. Forces" heard as hantou goudoumei, goei "escort" as goen);
- dropped or extra particles, run-together sentences, missing punctuation;
- a mangled name or term (check the glossary and the series);
- for shouts, grunts and non-speech, nonsense or nothing.

Work out what was most plausibly said, using the speaker, the series, the neighbouring rows and the Macross terms, and translate that. Then flag the row:
- `whisper_doubt`: you corrected or guessed at the transcript. Say in `notes`, in English, what you think was misheard (romaji is fine for a word).
- `no_subtitle`: the clip has no words a viewer needs (a pure grunt, a scream, drums, a chant, an unintelligible line). Leave `en` empty.

## Input and output

- Work file (read only): `work/translation/en/voice/voice.json`. Do not edit it.
- Print your slice with `python tools/voice_slice.py show <N>`. Each row shows: row number, clip id, speaker, clip length in seconds, Whisper's own warning flags, the missions whose scripts hold the clip number (a hint only), a skip reason if any, and the transcript.
- Write only your slice file, `work/translation/en/voice/slices/vslice_NNN.en.json` (three digits), UTF-8, with Python `json.dump(..., ensure_ascii=False, indent=1)`:

```json
{"slice": 7, "rows_in_slice": 80, "rows_examined": 80,
 "rows": [
   {"id": "vo0_of0_1000", "en": "Enemy fighters incoming!", "flags": [], "notes": ""}
 ],
 "report": {"uncertain": ["row 532: ..."], "whisper_doubt": ["row 540: ..."],
            "kept_omission": [], "missing_glossary": [], "unfinished": []}}
```

- Every row of your slice must be in `rows`, including skipped ones (give them `"en": ""`).
- Run `python tools/voice_slice.py check <N>` and fix every ERROR. Read the warnings.
- **No Japanese characters anywhere in the slice file.** It is committed to git.
- Allowed flags: `uncertain`, `whisper_doubt`, `no_subtitle`, `kept_omission`, `name_missing`, `unfinished`.

## How the rows are grouped

- **Operators** (`vo0_of0`, `vo0_of1`, `vo0_om0`, `vos_mis`): Ace Frontier has four operators (Yuu, Claire, Itsuki, Misa) who read the same script. Their other clips are shared with MUF, so look them up in `work/translation/en/voice/voice.json` (rows with the same number) when a row needs context. Each keeps their own manner (see `speakers.en.json`): Yuu polite, Claire cool and mature, Itsuki brisk, Misa a crisp officer. Numbers 1000+ are mission lines (objectives, enemy reports, warnings); lower numbers are stock lines (mission start, results, encouragement).
- **Custom pilots** (`vp0_*`): the four selectable pilots. Same situation, four personalities.
- **Named characters** (`vp<series>_<name>`): by series, then speaker, then number. Speaker names are in `work/translation/en/voice/speakers.en.json`.
- Pilot clip numbers mean the same situation for every pilot: 000-020 launch and greetings, 100-198 combat (attacking, taking damage, shooting down, being shot down, warning a partner...), 300-371 skills, partner and results, 600-699 that character's story lines for particular missions.

## Style

- These are radio lines in combat: short, spoken, alive. Write how an English-speaking pilot or operator would say it on the radio. Keep each character's voice (Basara's swagger, Klan's bluster, Max's calm).
- One clip in, one line out. Never merge or split rows.
- Shouts and battle cries: translate them as English battle cries ("Take this!", "Not yet!", "Damn it!"). A clip that is only a grunt or scream gets `no_subtitle`.
- Restore subjects and verbs as BASE_RULES says. Do not soften.
- Names and terms: `work/glossary/`. 統合軍 "U.N. Forces", 新統合軍 "New U.N. Forces", 反統合同盟 "Anti-U.N. Forces", バルキリー "Valkyrie", ゼントラーディ "Zentradi", バジュラ "Vajra", フォールド "fold".
- Never infer gender from a name; use `gender` in `speakers.en.json` and `characters.json`.

## Length

The subtitle box is about 230 px wide (about 38 characters per line) and shows up to three lines at once. A longer line is shown in parts of up to three lines that follow each other while the clip plays. The hard limit is **178 bytes for the whole line**; `check` measures it.

Readers need time: aim for no more than about 15-17 characters per second of the clip (`check` warns above that). A 1-second bark gets a few words; a 5-second operator report can use two lines. Compress the wording when you must, but never drop the end of a sentence.

Write only ASCII. The font also has the ellipsis (…); typographic quotes and dashes are converted. Do not write `{`.

## Report

At the end, report rows examined against rows in each slice, and list the calls you were unsure of (`uncertain`), the transcripts you corrected (`whisper_doubt`), and names missing from the glossary.
