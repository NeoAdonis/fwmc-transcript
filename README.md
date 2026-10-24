# 🐾 FUWAMOCO Transcripts Repository

This repository contains scripts to generate automatic transcripts and summaries of [FUWAMOCO](https://www.youtube.com/@FUWAMOCOch) content, starting with FWMC Morning.

This is a fan-made project. Its contents follow the [hololive production Derivative Works Guidelines](https://hololivepro.com/en/terms/) set forth by Cover Corp.

> [!NOTE]
> The transcripts in this repository are initially generated with speech recognition software, and the summaries are drafted with the help of an LLM-based assistant. As a result, they may contain errors that don't reflect the original content. If you notice significant errors, feel free to submit corrections or open an issue.

## 🌅 FUWAMOCO Morning

[FUWAMOCO Morning](https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS) is an online, short-format morning show hosted by the fuzzy and fluffy guard dog sisters [FUWAMOCO](https://www.youtube.com/@FUWAMOCOch). The show aims to bring a smile to everyone's face and help them start the day on the right paw!

- 📅 Schedule: every **F**riday, **W**ednesday and **M**onday (aka **F**U**W**A**M**OCO) at 8:00 AM Pacific Time.
- 🎶 Jingle by [Sarina](https://twitter.com/Sarina_A_Elysia/status/1695163342699081980).
- ▶️ Playlist: <https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS>
- 📤 Submissions:
  - Question Of The Day: [#helpFWMC](https://twitter.com/hashtag/helpFWMC)
  - Other corners (Pero Sighting, Doggie Of The Day, Today I Went On A Walk...): [#FWMCMORNING](https://twitter.com/hashtag/FWMCMORNING)

An index of all FWMC Morning episodes, summaries and transcripts is available at [`morning/index.md`](./morning/index.md).

## ⚒️ Building

Some files in this repository are generated automatically:

1. Media and its metadata are downloaded from YouTube, and the audio is converted to WAV for easier processing.
1. The audio is transcribed with automatic speech recognition, plus some workarounds to make the initial transcript as accurate as possible.
1. A basic summary is created. From there, an LLM/RAG tool can be used to summarize the transcript and help write the initial draft.
1. A formatted summary is generated from the basic summary and the episode metadata.
1. An index of all summaries is generated.

### Prerequisites

- [Bun](https://bun.sh/) or [Node.js](https://nodejs.org/)
- [FFmpeg](https://ffmpeg.org/)
- Python 3.13, or optionally [Miniforge](https://conda-forge.org/download/) to manage Python environments. The project targets the latest Python version supported by WhisperX.

On Windows, you can install all of them with [WinGet](https://learn.microsoft.com/windows/package-manager/).

## 🔰 Quick start

### Install prerequisites on Windows

[Make sure that WinGet is installed](https://learn.microsoft.com/windows/package-manager/winget/), then run the following:

```text
winget install Oven-sh.Bun
winget install Gyan.FFmpeg
winget install CondaForge.Miniforge3
```

### Install prerequisites on Linux

If you don't use conda, make sure that Python 3.13 is installed before creating an environment.

Install Bun or Node.js from your distribution's package manager, or follow the instructions on the [Bun](https://bun.com/docs/installation#macos-and-linux) or [Node.js](https://nodejs.org/en/download) websites.

### Set up a conda environment

1. On PowerShell, initialize conda: `conda init powershell`
1. Create the environment with the base packages: `conda env create --file environment.yml`
1. Activate the environment: `conda activate transcripts`
1. Continue with the WhisperX installation.

### Set up a venv

1. Create the environment:
    - Python: `python3.13 -m venv transcripts`
    - uv: `uv venv --python 3.13 venv/transcripts`
1. Activate the environment:
    - PowerShell: `.\transcripts\Scripts\Activate.ps1`
    - Bash: `source ./transcripts/bin/activate`
1. Install the base packages: `pip install -r requirements_0_base.txt`
1. Continue with the WhisperX installation.

### Install WhisperX

1. Install PyTorch: `pip install -r requirements_1_torch_cu128_<platform>.txt` (or `requirements_1_torch_cpu_<platform>.txt` if you don't have an NVIDIA GPU).
1. Install WhisperX: `pip install -r requirements_2_whisperx.txt`
1. On Linux, if you get an error like `ImportError: libctranslate2-d3638643.so.4.4.0: cannot enable executable stack as shared object requires`, run `./scripts/workaround_libctranslate2_clear-execstack.sh` to clear the conflicting `GNU_STACK` executable flag from the library (see <https://github.com/OpenNMT/CTranslate2/issues/1849>).
1. On Linux, if you get an error like `Could not load library libcudnn_ops_infer.so.8`, install cuDNN 11. Alternatively, install `nvidia-cudnn-cu11` with pip and add its libraries to `LD_LIBRARY_PATH` (e.g. `export LD_LIBRARY_PATH="$VIRTUAL_ENV/lib/python3.x/site-packages/nvidia/cublas/lib:$VIRTUAL_ENV/lib/python3.x/site-packages/nvidia/cudnn/lib:$LD_LIBRARY_PATH"`).

### Install linters

To lint and type-check the code, install the linters in your environment: `pip install -r requirements_3_optional_linters.txt`. Alternatively, you can use them externally, such as through a global install (e.g. `uv tool install ruff`), an editor extension or a package manager (e.g. `apt`, `pacman`).

To lint Markdown files with [markdownlint](https://github.com/DavidAnson/markdownlint-cli2), install it from the repository root with `npm ci` (or `bun install --frozen-lockfile`), then run `npm run lint` (or `bun run lint`). The FWMC Morning validation script also runs it.

## 🎶 FUWAMOCO songs

Lyrics, fanchants and other content related to their songs:

- Born to be "BAU"DOL☆★ (🎼 [lyrics: `songs/baudol.md`](./songs/baudol.md))
- Lifetime Showtime (🎼 [lyrics: `songs/ltst.md`](./songs/ltst.md))
- side by side ["NEKOPARA After: La Vraie Famille" Ending Theme] (🎼 [lyrics: `songs/sidebyside.md`](./songs/sidebyside.md))

## ✨ Thanks

- Cover Corp.: For hololive and for giving FUWAMOCO a chance to shine.
- Dylan Mendes, Kami-bako: For the timestamps in each video's comment section; they were a useful resource to find sections and compare them against my own timestamps.
- FUWAMOCO: For their content and for being an inspiration to many, including myself!
