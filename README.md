# 🐾 FUWAMOCO Transcripts Repository

This repo holds a set of scripts for automatic transcription, as well as summaries, for [FUWAMOCO](https://www.youtube.com/@FUWAMOCOch) content, starting with FWMC Morning.

This is a fan made project. The contents in this repository follow the [hololive production Derivative Works Guidelines](https://hololivepro.com/en/terms/) set forth by Cover Corp.

> [!NOTE]
> In its initial state, the transcriptions provided in this repository were generated automatically using speech recognition software. The summaries were created aided by a large language model virtual assistant. As a result, there may be inaccuracies or errors in these documents that are not representative of the original content. If you notice significant errors, feel free to submit corrections or raise issues through the repository's issue tracker.

## 🌅 FUWAMOCO Morning

[FUWAMOCO Morning](https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS) is an online, short-format morning show hosted by the fuzzy and fluffy guard dog sisters [FUWAMOCO](https://www.youtube.com/@FUWAMOCOch). Their aim with this show is to bring a smile to everyone's face and to help them start the day on the right paw!

- 📅 Schedule: every **F**riday, **W**ednesday and **M**onday (aka **F**U**W**A**M**OCO) at 8:00 hrs. US Pacific Time.
- 🎶 Jingle by [Sarina](https://twitter.com/Sarina_A_Elysia/status/1695163342699081980).
- ▶️ Playlist: https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS
- 📤 Submissions:
    - Question Of The Day: [#helpFWMC](https://twitter.com/hashtag/helpFWMC)
    - Other corners (Pero Sighting, Doggie Of The Day, Today I Went On A Walk...): [#FWMCMORNING](https://twitter.com/hashtag/FWMCMORNING)

An index of all FWMC Morning episodes, summaries and transcripts can be found at [`morning/index.md`](./morning/index.md).

## ⚒️ Building

Some of the files here are generated automatically.

1. Media is extracted directly from YouTube along with its metadata. Audio is converted into .wav format for easier processing.
1. Audio is automatically transcribed using a mix of automatic speech recognition plus some manual workarounds to provide the most accurate transcript possible from the get-go.
1. A basic summary is created. A LLM/RAG tool can be leveraged to to summarize the information from the transcript and help with the initial draft.
1. Using the basic summary and metadata from each media, a fancier summary document can be created programatically.
1. An index of all summaries can be automatically generated.

### Prerequisites

- [PowerShell 7+](https://learn.microsoft.com/en-us/powershell/scripting/overview)
- [Node.js](https://nodejs.org/en)
- [Miniconda](https://docs.anaconda.com/free/miniconda/)
- [WhisperX](https://github.com/m-bain/whisperX)
- [FFmpeg](https://ffmpeg.org/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

If using Windows, you can install all these prerequisites with [WinGet](https://learn.microsoft.com/windows/package-manager/).

## ✨ Thanks

- Cover Corp.: For hololive and for giving FUWAMOCO a chance to shine through.
- Dylan Mendes, Kami-bako: For the timestamps in each video's comments sections; it was an useful resource to easily find sections and compare against my own timestamps.
- FUWAMOCO: For their content and for being an inspiration to many, including myself!
