# Project overview for coding agents (and curious humans)

This project contains Python scripts to generate automatic transcriptions, as well as summaries, for [FUWAMOCO](https://www.youtube.com/@FUWAMOCOch) content, starting with FWMC Morning. It also hosts the resulting transcripts, summaries and indexes, plus lyrics for some of their songs. It's a fan made project, so its contents must follow the [hololive production Derivative Works Guidelines](https://hololivepro.com/en/terms/) (see [`CONTRIBUTING.md`](./CONTRIBUTING.md)).

## Design philosophy

- Worse is better: Prioritize simplicity and ease of implementation over complexity and completeness.
- DRY (Don't Repeat Yourself) and AHA (Avoid Hasty Abstractions): Avoid redundancy by reusing code wherever possible without adding unnecessary abstraction.
- Testing: TODO (testing guidelines and tooling will be updated soon).
- Refactor freely: Although the project has been around for a while, there are no strong signs of heavy usage that would warrant backward compatibility, so prefer a clean reimplementation over patching, as long as it respects the principles above. Point out any breaking changes to the scripts' command-line options or file formats.
- Code as the source of truth: The code, including its docstrings, is its own primary documentation; keep docstrings up to date when changing it. If there are any inconsistencies between other documentation and the code, the code should be considered the source of truth.

## Coding conventions

Follow the style conventions in [`STYLE.md`](./STYLE.md), especially for code comments and written content. In short:

- The project uses the default Ruff style, so `ruff format` (with the appropriate flags, e.g. `--check`) can both fix and verify formatting. The formatter doesn't sort imports; use `ruff check --select I --fix` for that.
- Use `ruff check` to check for common mistakes and non-idiomatic code.
- Comments follow PEP 8: a single space after the `#`, two spaces before an inline comment, complete sentences. The formatter doesn't wrap comments, so keep them within the 88-character line limit manually.
- Docstrings follow PEP 257: triple double quotes and a brief summary line ending with a period.
- In written content (transcripts, summaries, documentation), use proper capitalization for talent names, hyphenate Japanese honorifics (e.g., Moco-chan) and don't introduce intentional misspellings.

## Commits

- Coding agents shouldn't create commits on their own, only when explicitly asked by the user.
- Follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification and the 50/72 rule, as described in [`STYLE.md`](./STYLE.md).
- If possible, use a tool such as Cocogitto (`cog check`, `cog verify`) to validate commit messages.
- Don't add AI attribution trailers (e.g. "Co-Authored-By", "Generated with") to commits or PR descriptions; they clutter permanent history and can read as product promotion. This isn't opposition to transparency about AI use.

## Code structure

The Python source code lives in `src/`, which must be in the module search path: run the scripts as modules from `src/` (e.g. `python -m morning.update_summaries`). pytest and mypy are already configured for it in `pyproject.toml`. The FWMC Morning scripts change to the `morning/` directory at the repository root, so their default paths are relative to it.

Shared code, relative to `src/common/`:

- `asr.py`: automatic speech recognition with WhisperX.
- `asrtransform.py`: experimental post-processing of ASR output, such as fixing repeated captions.
- `media.py`: media download (yt-dlp) and conversion to WAV (FFmpeg).
- `transcript.py`: transcript validation, conversion to LRC, and detection or replacement of common mistakes.
- `printer.py`: helpers to print errors, warnings and highlighted text.
- `time.py`: conversion helpers between timestamps and `timedelta`.

FWMC Morning scripts, relative to `src/morning/`:

- `create_transcript.py`: transcribes downloaded episodes into `morning/transcripts/`, including their metadata and a summary draft.
- `fix_captions.py`: experimental script to fix repeated captions in existing transcripts.
- `transcript_to_lrc.py`: converts transcripts to LRC files to feed them to an LLM with `morning/summary-prompt.md`.
- `update_summaries.py`: generates the formatted summaries in `morning/summaries/` and updates `morning/index.md`, `morning/index.csv` and `morning/questions.txt`.
- `validate_docs.py`: validates the structure and content of transcripts, summaries and metadata, and lints all Markdown files with markdownlint.

Shell scripts, relative to `scripts/`:

- `get_morning_audio.sh` (and its PowerShell counterpart, `Get-MorningAudio.ps1`): downloads the audio, title and description of FWMC Morning episodes into `morning/audio/` (ignored by Git) with `get_video_audio.sh`.
- `new_morning_transcript.sh` (and its PowerShell counterpart, `New-MorningTranscript.ps1`): convenience wrapper around `create_transcript.py`.
- `get_video_audio.sh`, `convert_to_wav.sh` (and their PowerShell counterparts, `Get-VideoAudio.ps1` and `ConvertTo-Wav.ps1`): call `get_video_audio()` and `convert_to_wav()` from `media.py`, so yt-dlp and FFmpeg get the same options as in the Python scripts.
- `workaround_libctranslate2_clear-execstack.sh`: workaround for a CTranslate2 loading error on Linux (see `README.md`).

FWMC Morning data, relative to `morning/`:

- `config/`: data used by the scripts.
  - `transcript-prompt.txt`: initial prompt for WhisperX with frequently used words and phrases. `prompt-notes.md` explains what should be included in it.
  - `replacements.csv`: patterns for common transcription mistakes and their replacements.
  - `highlights.csv`: patterns for ambiguous words that should be reviewed manually.
  - `emojis.csv`: patterns to pick an emoji for each summary heading.
- `transcripts/<YYYYMMDD>/`: one directory per episode, with its `metadata.json`, `transcript.vtt` and `summary.md`. This is the source that should be edited.
- `summaries/<YYYYMMDD>_<episode>.md`: formatted summaries generated by `update_summaries.py`; don't edit them by hand.
- `index.md`, `index.csv`, `questions.txt`: indexes generated by `update_summaries.py`; don't edit them by hand.
- `summary-prompt.md`: prompt to draft a summary from a transcript with an LLM.

Songs, relative to `songs/`: lyrics, fanchants and other content related to FUWAMOCO songs, one Markdown file per song.

Markdown linting, relative to the repository root:

- `package.json`, `package-lock.json`: markdownlint-cli2 and its custom rules, installed with `npm ci` (or `bun install --frozen-lockfile`). `npm run lint` (or `bun run lint`) lints and fixes all Markdown files.
- `.markdownlint-cli2.jsonc`: shared configuration, including the proper names list. Configuration files in subdirectories merge with it to override rules for their files:
  - `.github/`: templates don't start with a heading.
  - `songs/`: lyrics use stylized names, so proper names aren't checked.
  - `morning/transcripts/`: summaries start with a second-level heading and use custom search-and-replace rules, such as timestamps in headings.

Tests, relative to `tests/`:

- `unit/`: unit tests that mirror the layout of `src/`, with one `test_<module>.py` file per module (e.g. `unit/common/test_media.py` for `src/common/media.py`).
- `integration/`: reserved for future integration tests.

Run `pytest --cov` from the repository root to measure test coverage of `src/` with pytest-cov (configured in `pyproject.toml`).
