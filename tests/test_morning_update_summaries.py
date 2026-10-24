"""Tests for the morning.update_summaries script."""

import csv
import json
import os

import pytest

from morning import update_summaries

LINK = "https://youtu.be/nMl8WQ1Iuls"
EMOJIS = [
    {"Pattern": r"\bPero\b", "Emoji": "🐶"},
    {"Pattern": r"\bsighting\b", "Emoji": "❌"},  # Only the first match is used.
    {"Pattern": r"^Question of the day\b", "Emoji": "❓"},
]


def write_episode(transcripts_dir, date, episode, summary, is_special=False):
    """Write the metadata and summary of an episode, like create_transcript.py."""
    episode_dir = transcripts_dir / date
    episode_dir.mkdir(parents=True)
    metadata = {
        "id": f"id{date}",
        "title": f"【FUWAMOCO MORNING】episode {episode}",
        "episode": episode,
        "isSpecial": is_special,
        "date": f"{date[:4]}-{date[4:6]}-{date[6:]}",
        "dayOfWeek": "Monday",
        "description": f"Description of {episode}",
        "illustrator": "rswxx",
    }
    (episode_dir / "metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    (episode_dir / "summary.md").write_text(summary, encoding="utf-8")
    return episode_dir


def summary_for(date, question):
    """Return a short summary with front matter and a question of the day."""
    return (
        f"---\nepisode: 1\ndate: {date}\nwip: true\n---\n\n"
        "## Introduction (01:02)\n\nHallo hallo BAU BAU!\n\n"
        f"## Question of the Day (10:20)\n\n{question}\n"
    )


# parse_args


def test_parse_args_defaults(monkeypatch):
    """The default arguments match the morning directory layout."""
    monkeypatch.setattr("sys.argv", ["update_summaries.py"])
    args = update_summaries.parse_args()
    assert args.transcripts_dir == "transcripts"
    assert args.summaries_dir == "summaries"


# load_metadata


@pytest.mark.parametrize(
    ("episode", "is_special", "name"),
    [("123", False, "Episode #123"), ("friday the 13th", True, "friday the 13th")],
)
def test_load_metadata(tmp_path, episode, is_special, name):
    """The episode name and link are added to the metadata."""
    episode_dir = write_episode(tmp_path, "20231013", episode, "", is_special)
    metadata = update_summaries.load_metadata(str(episode_dir))
    assert metadata["episode"] == episode
    assert metadata["name"] == name
    assert metadata["link"] == "https://youtu.be/id20231013"


# format_episode_filename


@pytest.mark.parametrize(
    ("episode", "filename"),
    [
        ("123", "20231229_123"),
        ("special episode in space", "20231229_special_episode_in_space"),
        ("BAU-lentine's day", "20231229_BAUlentines_day"),
        ("あさモコLIVE", "20231229_ASAMOCOLIVE"),
    ],
)
def test_format_episode_filename(episode, filename):
    """Filenames only have letters, numbers and underscores."""
    assert (
        update_summaries.format_episode_filename("20231229", {"episode": episode})
        == filename
    )


# format_header_line


@pytest.mark.parametrize(
    ("header", "line"),
    [
        ("Pero Sighting (06:53)", f"## 🐶 Pero Sighting ([06:53]({LINK}?t=06m53s))\n"),
        (
            "Valentine Merch (13:08)",
            f"## 🎞️ Valentine Merch ([13:08]({LINK}?t=13m08s))\n",
        ),
        ("Pero Sighting", "## 🐶 Pero Sighting\n"),
    ],
)
def test_format_header_line(header, line):
    """Headers get the first matching emoji, or a default one, and a timestamp link."""
    assert (
        update_summaries.format_header_line(EMOJIS, "##", header, "Episode #1", LINK)
        == line
    )


def test_format_header_line_introduction():
    """The introduction becomes the title, with the start of the episode."""
    line = update_summaries.format_header_line(
        EMOJIS, "##", "Introduction (05:02)", "Episode #1", LINK
    )
    assert line == f"# Episode #1 (start: [05:02]({LINK}?t=05m02s))\n"


def test_format_header_line_subsection():
    """Subsections don't get an emoji."""
    line = update_summaries.format_header_line(
        EMOJIS, "###", "Pero (06:53)", "Episode #1", LINK
    )
    assert line == f"### Pero ([06:53]({LINK}?t=06m53s))\n"


def test_format_header_line_no_emoji_episode():
    """Some episodes don't use emojis at all."""
    line = update_summaries.format_header_line(
        EMOJIS, "##", "Pero Sighting (06:53)", "Friday the 13th", LINK
    )
    assert line == f"## Pero Sighting ([06:53]({LINK}?t=06m53s))\n"


# process_summary


def test_process_summary():
    """The front matter and leading blank lines are removed, and headers formatted."""
    summary = summary_for("2024-02-14", "A question.").splitlines(keepends=True)
    new_summary, _ = update_summaries.process_summary(
        EMOJIS, summary, "Episode #1", LINK
    )
    assert new_summary == [
        f"# Episode #1 (start: [01:02]({LINK}?t=01m02s))\n",
        "\n",
        "Hallo hallo BAU BAU!\n",
        "\n",
        f"## ❓ Question of the Day ([10:20]({LINK}?t=10m20s))\n",
        "\n",
        "A question.\n",
    ]


@pytest.mark.parametrize(
    ("text", "question"),
    [
        ("A Ruffian asks\nabout *ears*.", 'A Ruffian asks\nabout "ears."\n'),
        ("Asked about **wanko soba**, yes.", 'Asked about "wanko soba," yes.\n'),
        ("Ask [Pero](https://x.com/pero).", "Ask Pero.\n"),
    ],
)
def test_process_summary_question(text, question):
    """The question of the day is extracted without links or formatting."""
    summary = summary_for("2024-02-14", text).splitlines(keepends=True)
    _, episode_question = update_summaries.process_summary(
        EMOJIS, summary, "Episode #1", LINK
    )
    # The blank line after the header is part of the question
    assert episode_question == f"\n{question}"


# refresh_file


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_refresh_file_unchanged(tmp_path, newline):
    """Files that only differ in the last updated time aren't rewritten."""
    path = tmp_path / "index.md"
    content = newline.join(["Title", "Last updated: 2020-01-01 00:00 UTC", ""])
    path.write_bytes(content.encode())
    new_content = ["Title", update_summaries.LAST_UPDATED_STRING]
    assert update_summaries.refresh_file(str(path), new_content) is False
    assert path.read_bytes() == content.encode()


@pytest.mark.parametrize("newline", ["\n", "\r\n"])
def test_refresh_file_changed(tmp_path, newline):
    """Changed files are rewritten, keeping their line endings."""
    path = tmp_path / "index.md"
    path.write_bytes(f"Title{newline}Old row{newline}".encode())
    assert update_summaries.refresh_file(str(path), ["Title", "New row"]) is True
    assert path.read_bytes() == f"Title{newline}New row{newline}".encode()


# main


@pytest.fixture
def morning_dir(monkeypatch, tmp_path):
    """Set up a morning directory in tmp_path and make main() run in it."""
    monkeypatch.chdir(tmp_path)
    # main() changes to the script directory, which has the real files
    monkeypatch.setattr(update_summaries.os, "chdir", lambda _: None)
    (tmp_path / "config").mkdir()
    with open(tmp_path / "config" / "emojis.csv", "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Pattern", "Emoji"])
        writer.writeheader()
        writer.writerows(EMOJIS)
    (tmp_path / "summaries").mkdir()
    (tmp_path / "index.md").write_text("old\n", encoding="utf-8")
    (tmp_path / "questions.txt").write_text("old\n", encoding="utf-8")
    write_episode(
        tmp_path / "transcripts", "20230731", "0", summary_for("2023-07-31", "None.")
    )
    write_episode(
        tmp_path / "transcripts",
        "20240214",
        "BAU-lentine's day",
        summary_for("2024-02-14", "What's your favorite chocolate?"),
        is_special=True,
    )
    monkeypatch.setattr("sys.argv", ["update_summaries.py"])
    return tmp_path


def test_main_writes_summaries(morning_dir):
    """Each episode gets a formatted summary."""
    update_summaries.main()
    assert sorted(os.listdir(morning_dir / "summaries")) == [
        "20230731_0.md",
        "20240214_BAUlentines_day.md",
    ]
    summary = (morning_dir / "summaries" / "20240214_BAUlentines_day.md").read_text(
        encoding="utf-8"
    )
    assert summary.startswith(
        "# BAU-lentine's day (start: [01:02](https://youtu.be/id20240214?t=01m02s))\n"
    )


def test_main_writes_indexes(morning_dir, capsys):
    """The index files list every episode, and the questions skip episode 0."""
    update_summaries.main()
    assert "Index updated" in capsys.readouterr().out

    index = (morning_dir / "index.md").read_text(encoding="utf-8").splitlines()
    assert index[2] == update_summaries.LAST_UPDATED_STRING
    # The row order is checked by test_main_sorts_episodes
    assert sorted(index[-2:]) == [
        (
            "| 2023-07-31 | Mon | [Episode #0](https://youtu.be/id20230731) | "
            "Description of 0 | [Summary](summaries/20230731_0.md) | "
            "[Transcript](transcripts/20230731/transcript.vtt) |"
        ),
        (
            "| 2024-02-14 | Mon | [BAU-lentine's day](https://youtu.be/id20240214) | "
            "Description of BAU-lentine's day | "
            "[Summary](summaries/20240214_BAUlentines_day.md) | "
            "[Transcript](transcripts/20240214/transcript.vtt) |"
        ),
    ]

    with open(morning_dir / "index.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert [row["Episode"] for row in rows] == ["Episode #0", "BAU-lentine's day"]
    assert rows[1]["Link"] == "https://youtu.be/id20240214"

    questions = (morning_dir / "questions.txt").read_text(encoding="utf-8")
    assert questions.splitlines()[-1] == (
        "BAU-lentine's day — What's your favorite chocolate?"
    )
    assert "Episode #0" not in questions


def test_main_without_changes(morning_dir, capsys):
    """A second run doesn't change the index files."""
    update_summaries.main()
    index = (morning_dir / "index.md").read_bytes()
    capsys.readouterr()
    update_summaries.main()
    output = capsys.readouterr().out
    assert "No changes to index" in output
    assert "No changes to questions summary" in output
    assert (morning_dir / "index.md").read_bytes() == index


@pytest.mark.xfail(strict=True, reason="Episodes are listed in os.listdir() order")
def test_main_sorts_episodes(morning_dir, monkeypatch):
    """Episodes are listed by date, whatever order the file system uses."""
    listdir = os.listdir
    monkeypatch.setattr(
        update_summaries.os, "listdir", lambda p: sorted(listdir(p), reverse=True)
    )
    update_summaries.main()
    index = (morning_dir / "index.md").read_text(encoding="utf-8")
    assert index.index("2023-07-31") < index.index("2024-02-14")
