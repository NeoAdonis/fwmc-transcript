"""Tests for the morning.create_transcript script."""

import json
import os

import pytest

# Importing the script loads WhisperX, which is installed separately.
create_transcript = pytest.importorskip("morning.create_transcript")

REGULAR_TITLE = "【FUWAMOCO MORNING】episode 181 🐾 #FWMCMORNING"
SPECIAL_TITLE = "【FUWAMOCO MORNING】BAU-lentine's day 🐾 #FWMCMORNING"
DESCRIPTION = [
    "last FWMC morning until fuwawa is back from the hospital ✨️",
    "lovely illustration by @A_LoneKM9581 💕",
    "jingle by @Sarina_A_Elysia ♪",
]


def write_episode(
    audio_dir, date, title=REGULAR_TITLE, description=None, video_id="2Q_Z4PVnMdk"
):
    """Write the title and description files of an episode, like get_audio.py."""
    episode_dir = audio_dir / date
    episode_dir.mkdir(parents=True)
    (episode_dir / f"{date}.title").write_text(
        f"{video_id}\n{title}\n", encoding="utf-8"
    )
    lines = DESCRIPTION if description is None else description
    (episode_dir / f"{date}.description").write_text(
        "".join(f"{line}\n" for line in lines), encoding="utf-8"
    )
    return episode_dir


def get_metadata(tmp_path, date="20260320", **kwargs):
    """Write an episode and return its metadata."""
    episode_dir = write_episode(tmp_path, date, **kwargs)
    return create_transcript.get_metadata(str(episode_dir), date)


# parse_args


def test_parse_args_defaults(monkeypatch):
    """The default arguments match the morning directory layout."""
    monkeypatch.setattr("sys.argv", ["create_transcript.py"])
    args = create_transcript.parse_args()
    assert args.audio_dir == "audio"
    assert args.output_dir == "transcripts"
    assert args.model == "large-v2"
    assert args.include_no_prompt is False


# get_metadata


def test_get_metadata_regular_episode(tmp_path):
    """Regular episodes are numbered, with metadata from the title and description."""
    assert get_metadata(tmp_path) == {
        "id": "2Q_Z4PVnMdk",
        "title": REGULAR_TITLE,
        "episode": "181",
        "isSpecial": False,
        "date": "2026-03-20",
        "dayOfWeek": "Friday",
        "description": DESCRIPTION[0],
        "illustrator": "A_LoneKM9581",
    }


@pytest.mark.parametrize(
    ("title", "episode"),
    [
        (SPECIAL_TITLE, "BAU-lentine's day"),
        ("【FUWAMOCO 1st Anniversary】Special Morning 🐾", "FUWAMOCO 1st Anniversary"),
        ("Untitled special 🐾", "???"),
    ],
)
def test_get_metadata_special_episode(tmp_path, title, episode):
    """Episodes without a number are special, named after the title if possible."""
    metadata = get_metadata(tmp_path, title=title)
    assert metadata["episode"] == episode
    assert metadata["isSpecial"] is True


def test_get_metadata_multiline_description(tmp_path):
    """Description lines before the illustration credit are joined."""
    metadata = get_metadata(
        tmp_path, description=["first line", "second line", *DESCRIPTION[1:]]
    )
    assert metadata["description"] == "first line second line"


@pytest.mark.parametrize(
    ("credit", "illustrator"),
    [
        ("lovely illustration by @MILKURIEM 💕", "MILKURIEM"),
        ("illustration by @name!", "name"),
        ("illustration by some_artist", "some_artist"),
    ],
)
def test_get_metadata_illustrator(tmp_path, credit, illustrator):
    """The illustrator is taken from the credit line, without trailing symbols."""
    metadata = get_metadata(tmp_path, description=["description", credit])
    assert metadata["illustrator"] == illustrator


def test_get_metadata_default_illustrator(tmp_path):
    """Without an illustration credit, the illustrator is the FUWAMOCO designer."""
    metadata = get_metadata(tmp_path, description=["first line", "second line"])
    assert metadata["illustrator"] == "rswxx"
    assert metadata["description"] == "first line second line"


@pytest.mark.parametrize(
    ("date", "warned"), [("20260316", False), ("20260320", False), ("20260321", True)]
)
def test_get_metadata_unexpected_day(tmp_path, capsys, date, warned):
    """Episodes aired on days other than Monday, Wednesday or Friday are warned."""
    get_metadata(tmp_path, date=date)
    assert ("unexpected day" in capsys.readouterr().out) == warned


# clean_transcript_files


def test_clean_transcript_files(monkeypatch, tmp_path):
    """New transcripts replace the old ones, keeping other files."""
    # List the new transcript before the old one, which used to remove it after
    # renaming it
    listdir = os.listdir
    monkeypatch.setattr(create_transcript.os, "listdir", lambda p: sorted(listdir(p)))
    (tmp_path / "transcript.vtt").write_text("old", encoding="utf-8")
    (tmp_path / "transcript.lrc").write_text("old", encoding="utf-8")
    (tmp_path / "audio_converted.vtt").write_text("new", encoding="utf-8")
    (tmp_path / "metadata.json").write_text("{}", encoding="utf-8")
    create_transcript.clean_transcript_files(str(tmp_path))
    assert sorted(os.listdir(tmp_path)) == ["metadata.json", "transcript.vtt"]
    assert (tmp_path / "transcript.vtt").read_text(encoding="utf-8") == "new"


# create_summary_draft


@pytest.mark.parametrize(
    ("title", "episode_line"),
    [
        (REGULAR_TITLE, "episode: 181"),
        (SPECIAL_TITLE, 'episode: "BAU-lentine\'s day"'),
    ],
)
def test_create_summary_draft(tmp_path, title, episode_line):
    """The draft has the front matter and the default sections."""
    metadata = get_metadata(tmp_path / "audio", title=title)
    create_transcript.create_summary_draft(metadata, str(tmp_path))
    summary = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert summary.splitlines() == [
        "---",
        episode_line,
        "date: 2026-03-20",
        'link: "https://youtu.be/2Q_Z4PVnMdk"',
        "wip: true",
        "---",
        "",
        "## Sections",
        "",
        *create_transcript.DEFAULT_SECTION_NAMES,
    ]
    assert summary.endswith("\n")  # Markdown files end with a single newline.


# main


@pytest.fixture
def fake_asr(monkeypatch):
    """Replace audio conversion and transcription with fakes and record the calls."""
    calls = {
        "convert": [],
        "load_model": [],
        "load_align_model": [],
        "transcribe": [],
        "fix_repeats": [],
    }

    def convert_to_wav(path, new_base_name):
        calls["convert"].append(path)
        wav_path = os.path.join(os.path.dirname(path), f"{new_base_name}.wav")
        with open(wav_path, "wb") as f:
            f.write(b"RIFF")

    def load_model(*_args, **kwargs):
        calls["load_model"].append(kwargs)
        return f"model {len(calls['load_model'])}"

    def load_align_model(**kwargs):
        calls["load_align_model"].append(kwargs)
        return "align model", {"language": "en"}

    def transcribe_audio(audio_path, model, _align_model, _align_meta, _device, out):
        calls["transcribe"].append((audio_path, model, out))
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        with open(os.path.join(out, f"{base_name}.vtt"), "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nHallo hallo BAU BAU\n")

    monkeypatch.setattr(create_transcript, "convert_to_wav", convert_to_wav)
    monkeypatch.setattr(create_transcript.whisperx, "load_model", load_model)
    monkeypatch.setattr(
        create_transcript.whisperx, "load_align_model", load_align_model
    )
    monkeypatch.setattr(create_transcript.asr, "transcribe_audio", transcribe_audio)

    def fix_repeats(vtt_root, file, audio_path, *_args):
        assert os.path.exists(os.path.join(vtt_root, file))
        assert os.path.exists(audio_path)
        calls["fix_repeats"].append((vtt_root, file, audio_path))
        return False

    monkeypatch.setattr(create_transcript.asrtransform, "fix_repeats", fix_repeats)
    return calls


def run_main(monkeypatch, tmp_path, *extra_args):
    """Run the script on the audio and transcripts directories in tmp_path."""
    monkeypatch.chdir(tmp_path)  # Restore the directory changed by main.
    monkeypatch.setattr(
        "sys.argv",
        [
            "create_transcript.py",
            "--audio_dir",
            str(tmp_path / "audio"),
            "--output_dir",
            str(tmp_path / "transcripts"),
            *extra_args,
        ],
    )
    create_transcript.main()


def test_main_creates_transcripts(monkeypatch, tmp_path, fake_asr):
    """Each episode gets its metadata, transcript and summary draft."""
    for date in ("20260318", "20260320"):
        episode_dir = write_episode(tmp_path / "audio", date)
        (episode_dir / "audio.opus").touch()
    run_main(monkeypatch, tmp_path)

    for date in ("20260318", "20260320"):
        output_dir = tmp_path / "transcripts" / date
        assert sorted(os.listdir(output_dir)) == [
            "metadata.json",
            "summary.md",
            "transcript.vtt",
        ]
        metadata = json.loads((output_dir / "metadata.json").read_text("utf-8"))
        assert metadata["date"] == f"{date[:4]}-{date[4:6]}-{date[6:]}"
        transcript = (output_dir / "transcript.vtt").read_text(encoding="utf-8")
        assert "Hallo hallo BAU BAU" in transcript
        # The converted audio is removed after transcribing
        assert not (tmp_path / "audio" / date / "audio_converted.wav").exists()
    # Models are loaded only once
    assert len(fake_asr["load_model"]) == 1
    assert len(fake_asr["load_align_model"]) == 1
    assert len(fake_asr["transcribe"]) == 2


def test_main_skips_existing_transcripts(monkeypatch, tmp_path, fake_asr):
    """Existing transcripts aren't transcribed again, but their metadata is updated."""
    episode_dir = write_episode(tmp_path / "audio", "20260320")
    (episode_dir / "audio.opus").touch()
    output_dir = tmp_path / "transcripts" / "20260320"
    output_dir.mkdir(parents=True)
    (output_dir / "transcript.vtt").write_text("edited", encoding="utf-8")
    (output_dir / "metadata.json").write_text("{}", encoding="utf-8")
    run_main(monkeypatch, tmp_path)

    assert fake_asr["convert"] == []
    assert fake_asr["transcribe"] == []
    assert (output_dir / "transcript.vtt").read_text(encoding="utf-8") == "edited"
    metadata = json.loads((output_dir / "metadata.json").read_text("utf-8"))
    assert metadata["id"] == "2Q_Z4PVnMdk"
    assert not (output_dir / "summary.md").exists()


def test_main_keeps_existing_summary(monkeypatch, tmp_path, fake_asr):
    """An existing summary isn't replaced by a draft."""
    episode_dir = write_episode(tmp_path / "audio", "20260320")
    (episode_dir / "audio.opus").touch()
    output_dir = tmp_path / "transcripts" / "20260320"
    output_dir.mkdir(parents=True)
    (output_dir / "summary.md").write_text("edited", encoding="utf-8")
    run_main(monkeypatch, tmp_path)

    assert len(fake_asr["transcribe"]) == 1
    assert (output_dir / "summary.md").read_text(encoding="utf-8") == "edited"


def test_main_ignores_other_files(monkeypatch, tmp_path, fake_asr):
    """Only audio files are transcribed, not WAV files or other downloads."""
    episode_dir = write_episode(tmp_path / "audio", "20260320")
    (episode_dir / "audio_converted.wav").touch()
    (episode_dir / "video.mp4").touch()
    (episode_dir / "thumbnail.webp").touch()
    run_main(monkeypatch, tmp_path)

    assert fake_asr["transcribe"] == []
    assert not (tmp_path / "transcripts").exists()


def test_main_fixes_repeats(monkeypatch, tmp_path, fake_asr):
    """Repeats are fixed in the new transcript, using the downloaded audio."""
    episode_dir = write_episode(tmp_path / "audio", "20260320")
    (episode_dir / "audio.m4a").touch()
    run_main(monkeypatch, tmp_path)

    assert fake_asr["fix_repeats"] == [
        (
            str(tmp_path / "transcripts" / "20260320"),
            "audio_converted.vtt",
            str(episode_dir / "audio.m4a"),
        )
    ]


def test_main_include_no_prompt(monkeypatch, tmp_path, fake_asr):
    """With --include_no_prompt, a second transcript is made without the prompt."""
    episode_dir = write_episode(tmp_path / "audio", "20260320")
    (episode_dir / "audio.opus").touch()
    run_main(monkeypatch, tmp_path, "--include_no_prompt")

    output_dir = tmp_path / "transcripts" / "20260320"
    assert [model for _, model, _ in fake_asr["transcribe"]] == ["model 1", "model 2"]
    assert "initial_prompt" in fake_asr["load_model"][0]["asr_options"]
    assert "asr_options" not in fake_asr["load_model"][1]
    assert (output_dir / "noprompt").is_dir()
    assert os.listdir(output_dir / "noprompt")
