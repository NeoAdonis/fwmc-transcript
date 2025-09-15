# 🐾 FUWAMOCO Transcripts Repository

This repo contains scripts to generate automatic transcriptions, as well as summaries, for [FUWAMOCO](https://www.youtube.com/@FUWAMOCOch) content, starting with FWMC Morning.

This is a fan made project. The contents in this repository follow the [hololive production Derivative Works Guidelines](https://hololivepro.com/en/terms/) set forth by Cover Corp.

> [!NOTE]
> In its initial state, the transcriptions provided in this repository were generated automatically using speech recognition software. The summaries were created aided by a large language model virtual assistant. As a result, there may be inaccuracies or errors in these documents that are not representative of the original content. If you notice significant errors, feel free to submit corrections or raise issues through the repository's issue tracker.

## 🌅 FUWAMOCO Morning

[FUWAMOCO Morning](https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS) is an online, short-format morning show hosted by the fuzzy and fluffy guard dog sisters [FUWAMOCO](https://www.youtube.com/@FUWAMOCOch). Their aim with this show is to bring a smile to everyone's face and to help them start the day on the right paw!

- 📅 Schedule: every **F**riday, **W**ednesday and **M**onday (aka **F**U**W**A**M**OCO) at 8:00 hrs. US Pacific Time.
- 🎶 Jingle by [Sarina](https://twitter.com/Sarina_A_Elysia/status/1695163342699081980).
- ▶️ Playlist: <https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS>
- 📤 Submissions:
  - Question Of The Day: [#helpFWMC](https://twitter.com/hashtag/helpFWMC)
  - Other corners (Pero Sighting, Doggie Of The Day, Today I Went On A Walk...): [#FWMCMORNING](https://twitter.com/hashtag/FWMCMORNING)

An index of all FWMC Morning episodes, summaries and transcripts can be found at [`morning/index.md`](./morning/index.md).

## ⚒️ Building

Some of the files here are generated automatically.

1. Media is extracted directly from YouTube along with its metadata. Audio is converted into .wav format for easier processing.
1. Audio is automatically transcribed using a mix of automatic speech recognition plus some manual workarounds to provide the most accurate transcript possible from the get-go.
1. A basic summary is created. A LLM/RAG tool can be leveraged to summarize the information from the transcript and help with the initial draft.
1. Using the basic summary and metadata from each media, a fancier summary document can be created programmatically.
1. An index of all summaries can be automatically generated.

### Prerequisites

- [Bun](https://bun.sh/) or [Node.js](https://nodejs.org/)
- [FFmpeg](https://ffmpeg.org/)
- Optional: [Miniforge](https://conda-forge.org/download/) to handle virtual Python environments.
- Otherwise, make sure that Python 3.12 is installed.

If using Windows, you can install all these prerequisites with [WinGet](https://learn.microsoft.com/windows/package-manager/).

## 🔰 Quick start

### Install prerequisites in Windows

[Make sure that WinGet is installed](https://learn.microsoft.com/windows/package-manager/winget/), then run the following:

```text
winget install Oven-sh.Bun
winget install Gyan.FFmpeg
winget install CondaForge.Miniforge3
```

### Install prerequisites in Linux

WhisperX requires Python 3.12. Make sure that such version is installed on your system before creating an environment.

You can install Bun or Node.js from your distro package manager, or directly by following the instructions on the [Bun](https://bun.com/docs/installation#macos-and-linux) or [Node.js](https://nodejs.org/en/download) download websites.

### Set up Miniconda environment

1. If using PowerShell, init Miniconda: `conda init powershell`
1. Create environment with some base packages: `conda env create --file environment.yml`
1. Activate environment: `conda activate transcripts`
1. Proceed with WhisperX installation.

### Set up venv

1. Create environment: `python3.12 -m venv transcripts`
1. Activate environment:
    - PowerShell: `.\transcripts\Scripts\Activate.ps1`
    - Bash: `source ./transcripts/bin/activate`
1. Install base packages: `pip install -r requirements_0_base.txt`
1. Proceed with installation of other packages.

### Install WhisperX

1. Install requirements: `pip install -r requirements_1_torch_cu129.txt` (use `requirements_1_torch_cpu_<platform>.txt` instead if you don't have an Nvidia GPU)
1. Install WhisperX: `pip install -r requirements_2_whisperx.txt`
1. On Linux, if you encounter an error similar to `ImportError: libctranslate2-d3638643.so.4.4.0: cannot enable executable stack as shared object requires`, run `./workaround_libctranslate2_clear-execstack.sh` to clear conflicting `GNU_STACK` executable flag from the library; see <https://github.com/OpenNMT/CTranslate2/issues/1849>.
1. On Linux, if you encounter an error similar to `Could not load library libcudnn_ops_infer.so.8`, downgrade Torch: `pip install -r requirements_1_torch_cu118.txt`; see <https://github.com/m-bain/whisperX/issues/967>. Ignore any dependency conflicts coming from WhisperX.

## 🎶 FUWAMOCO songs

A compilation of lyrics, fanchants & other content related to their songs.

- Born to be "BAU"DOL☆★ (🎼 [lyrics: `songs/baudol.md`](./songs/baudol.md))
- Lifetime Showtime (🎼 [lyrics: `songs/ltst.md`](./songs/ltst.md))
- side by side ["NEKOPARA After: La Vraie Famille" Ending Theme] (🎼 [lyrics: `songs/sidebyside.md`](./songs/sidebyside.md))

## ✨ Thanks

- Cover Corp.: For hololive and for giving FUWAMOCO a chance to shine through.
- Dylan Mendes, Kami-bako: For the timestamps in each video's comments sections; it was a useful resource to easily find sections and compare against my own timestamps.
- FUWAMOCO: For their content and for being an inspiration to many, including myself!
