"""Tests for the common.transcript module."""

import re
from pathlib import Path

import pytest
import termcolor

from common import transcript

REL_PATH = "20230731/transcript.vtt"

REPLACEMENTS_HEADER = "Pattern,Replacement,Warning\n"
HIGHLIGHTS_HEADER = "Pattern,Reason\n"

INTRO_CUES = [
    ("00:04:58.275", "00:05:00.901", "Hallo hallo BAU BAU!"),
    ("00:05:00.921", "00:05:05.309", "It's time for FUWAMOCO Morning!"),
    ("00:05:05.769", "00:05:09.382", "<i>FUWAMOCO Morning hajimaru yo!</i>"),
    (
        "00:05:22.396",
        "00:05:26.879",
        "And today, we're your hosts\nof FUWAMOCO Morning!",
    ),
]


@pytest.fixture(autouse=True)
def no_color(monkeypatch):
    """Disable colors so that printed diagnostics are plain text."""
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    termcolor.can_colorize.cache_clear()
    yield
    termcolor.can_colorize.cache_clear()


@pytest.fixture
def cwd(tmp_path, monkeypatch):
    """Change to a temporary directory and return it."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


def vtt_content(cues):
    """Return a transcript in WhisperX's layout for (start, end, text) cues."""
    blocks = [f"{start} --> {end}\n{text}" for start, end, text in cues]
    return "WEBVTT\n\n" + "\n\n".join(blocks) + "\n"


def write_file(path, content):
    """Write content to a file as UTF-8 without newline translation."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content.encode("utf-8"))
    return path


def write_vtt(directory, cues):
    """Write a transcript for cues into an episode directory and return its path."""
    return write_file(directory / REL_PATH, vtt_content(cues))


def timing_lines(cues):
    """Return the 1-based line number of each cue's timing line."""
    numbers = []
    line = 3
    for _, _, text in cues:
        numbers.append(line)
        line += 1 + len(text.split("\n")) + 1
    return numbers


def fetch(directory, content, name="patterns.csv"):
    """Write a CSV file of patterns and read it with fetch_patterns."""
    path = write_file(directory / name, content)
    return transcript.fetch_patterns(str(path))


# validate


def test_validate_valid_file_prints_nothing(cwd, capsys):
    """A transcript with ordered, touching and multi-line captions is valid."""
    cues = [
        *INTRO_CUES,
        ("00:05:26.879", "00:05:30.000", "Touching the previous caption."),
    ]
    transcript.validate(str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("00:00:10.000", "00:00:05.000"),  # Reversed.
        ("00:00:05.000", "00:00:05.000"),  # Zero length.
    ],
)
def test_validate_first_caption_not_ending_after_start(cwd, capsys, start, end):
    """The first caption is reported if it doesn't end after it starts."""
    cues = [(start, end, "Hallo hallo BAU BAU!"), *INTRO_CUES[1:]]
    transcript.validate(str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == (
        f"{REL_PATH}:3 Caption doesn't end after it starts\n"
    )


@pytest.mark.parametrize(
    ("start", "end"),
    [
        ("00:05:40.000", "00:05:35.000"),  # Reversed.
        ("00:05:40.000", "00:05:40.000"),  # Zero length.
    ],
)
def test_validate_later_caption_not_ending_after_start(cwd, capsys, start, end):
    """A later caption that doesn't end after it starts points to its timing line."""
    cues = [
        *INTRO_CUES,
        (start, end, "Bad timing."),
        ("00:05:50.000", "00:05:55.000", "Good timing."),
    ]
    transcript.validate(str(write_vtt(cwd, cues)))
    line = timing_lines(cues)[4]
    assert line == 16
    assert capsys.readouterr().out == (
        f"{REL_PATH}:{line} Caption doesn't end after it starts\n"
    )


def test_validate_overlap_after_multiline_caption(cwd, capsys):
    """An overlapping caption is reported at its timing line after multi-line cues."""
    cues = [
        *INTRO_CUES,
        ("00:05:26.878", "00:05:30.000", "Starts 1 ms too early."),
    ]
    transcript.validate(str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == (
        f"{REL_PATH}:16 Caption overlaps with the previous one\n"
    )


def test_validate_reports_every_error_in_order(cwd, capsys):
    """Each invalid caption gets its own error, in file order."""
    cues = [
        ("00:00:01.000", "00:00:01.000", "Zero length."),
        ("00:00:02.000", "00:00:04.000", "Fine."),
        ("00:00:03.000", "00:00:05.000", "Overlaps."),
        ("00:00:06.000", "00:00:07.000", "Fine again."),
    ]
    transcript.validate(str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == (
        f"{REL_PATH}:3 Caption doesn't end after it starts\n"
        f"{REL_PATH}:9 Caption overlaps with the previous one\n"
    )


# check_repeats


def test_check_repeats_two_identical_captions_print_nothing(cwd, capsys):
    """Exactly two identical captions in a row aren't reported."""
    cues = [
        ("00:00:01.000", "00:00:02.000", "BAU BAU!"),
        ("00:00:02.000", "00:00:03.000", "BAU BAU!"),
        ("00:00:03.000", "00:00:04.000", "Something else."),
        ("00:00:04.000", "00:00:05.000", "BAU BAU!"),
    ]
    transcript.check_repeats(str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == ""


def test_check_repeats_run_at_start(cwd, capsys):
    """A run of three at the start is reported from its first start to last end."""
    cues = [
        ("00:00:01.000", "00:00:02.000", "BAU BAU!"),
        ("00:00:02.500", "00:00:03.000", "BAU BAU!"),
        ("00:00:03.500", "00:00:04.250", "BAU BAU!"),
        ("00:00:05.000", "00:00:06.000", "Something else."),
    ]
    transcript.check_repeats(str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == (
        f"{REL_PATH}:3 Repeated caption from 00:00:01.000 to 00:00:04.250\nBAU BAU!\n"
    )


def test_check_repeats_run_at_end_after_multiline_caption(cwd, capsys):
    """A run at the end of the file points to its first caption's timing line."""
    cues = [
        *INTRO_CUES,
        ("00:05:30.000", "00:05:31.000", "Thank you."),
        ("00:05:31.000", "00:05:32.000", "Thank you."),
        ("00:05:32.000", "00:05:33.000", "Thank you."),
        ("00:05:33.000", "00:05:34.500", "Thank you."),
    ]
    transcript.check_repeats(str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == (
        f"{REL_PATH}:16 Repeated caption from 00:05:30.000 to 00:05:34.500\n"
        "Thank you.\n"
    )


def test_check_repeats_multiple_runs(cwd, capsys):
    """Each run of three or more identical captions is reported once."""
    cues = [
        ("00:00:01.000", "00:00:02.000", "Ruff!"),
        ("00:00:02.000", "00:00:03.000", "Ruff!"),
        ("00:00:03.000", "00:00:04.000", "Ruff!"),
        ("00:00:04.000", "00:00:05.000", "Ruff!"),
        ("00:00:05.000", "00:00:06.000", "Pero."),
        ("00:00:06.000", "00:00:07.000", "Pero."),
        ("00:00:07.000", "00:00:08.000", "Hallo."),
        ("00:00:08.000", "00:00:09.000", "Hallo."),
        ("00:00:09.000", "00:00:10.000", "Hallo."),
        ("00:00:10.000", "00:00:11.000", "Bye."),
    ]
    transcript.check_repeats(str(write_vtt(cwd, cues)))
    line = timing_lines(cues)[6]
    assert capsys.readouterr().out == (
        f"{REL_PATH}:3 Repeated caption from 00:00:01.000 to 00:00:05.000\n"
        "Ruff!\n"
        f"{REL_PATH}:{line} Repeated caption from 00:00:07.000 to 00:00:10.000\n"
        "Hallo.\n"
    )


def test_check_repeats_non_consecutive_captions_print_nothing(cwd, capsys):
    """Identical captions separated by a different one don't form a run."""
    cues = [
        ("00:00:01.000", "00:00:02.000", "BAU BAU!"),
        ("00:00:02.000", "00:00:03.000", "BAU BAU!"),
        ("00:00:03.000", "00:00:04.000", "Ruff!"),
        ("00:00:04.000", "00:00:05.000", "BAU BAU!"),
    ]
    transcript.check_repeats(str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == ""


# fetch_patterns


def test_fetch_patterns_reads_rows_and_compiles_regex(tmp_path):
    """Each row keeps its columns and gets a case-insensitive compiled Regex."""
    rows = fetch(
        tmp_path,
        REPLACEMENTS_HEADER
        + "\\bbow[ -]bow\\b,BAU BAU,N\n"
        + '"H[ae]ll?o,? h[ae]ll?o,? BAU BAU",Hallo hallo BAU BAU,N\n',
    )
    assert [{k: v for k, v in row.items() if k != "Regex"} for row in rows] == [
        {"Pattern": "\\bbow[ -]bow\\b", "Replacement": "BAU BAU", "Warning": "N"},
        {
            "Pattern": "H[ae]ll?o,? h[ae]ll?o,? BAU BAU",
            "Replacement": "Hallo hallo BAU BAU",
            "Warning": "N",
        },
    ]
    for row in rows:
        assert isinstance(row["Regex"], re.Pattern)
        assert row["Regex"].pattern == row["Pattern"]
        assert row["Regex"].flags & re.IGNORECASE
    assert rows[0]["Regex"].search("BOW-BOW")
    assert rows[1]["Regex"].search("hello, HELLO BAU BAU")


def test_fetch_patterns_keeps_extra_columns(tmp_path):
    """Columns other than Pattern are kept as they are."""
    rows = fetch(
        tmp_path, HIGHLIGHTS_HEADER + "\\bAyami\\b,'Ayamy'\n\\bMoomin\\b,'Mumei'\n"
    )
    assert [row["Reason"] for row in rows] == ["'Ayamy'", "'Mumei'"]
    assert set(rows[0]) == {"Pattern", "Reason", "Regex"}


def test_fetch_patterns_header_only_returns_empty_list(tmp_path):
    """A CSV file with only a header has no patterns."""
    assert fetch(tmp_path, REPLACEMENTS_HEADER) == []


# fix_mistakes


def test_fix_mistakes_chains_replacements_in_order(cwd, capsys):
    """Unflagged replacements apply in order, each to the previous result."""
    rows = fetch(
        cwd,
        REPLACEMENTS_HEADER
        + "\\bbow[ -]bow\\b,BAU BAU,N\n"
        + '"H[ae]ll?o,? h[ae]ll?o,? BAU BAU",Hallo hallo BAU BAU,N\n',
    )
    path = write_vtt(cwd, [("00:04:58.275", "00:05:00.901", "hello, hello BOW-BOW!")])
    assert transcript.fix_mistakes(rows, str(path)) is True
    assert path.read_bytes().decode() == vtt_content(
        [("00:04:58.275", "00:05:00.901", "Hallo hallo BAU BAU!")]
    )
    assert capsys.readouterr().out == ""


def test_fix_mistakes_order_matters(cwd):
    """A replacement doesn't see the output of replacements listed after it."""
    rows = fetch(
        cwd,
        REPLACEMENTS_HEADER
        + '"H[ae]ll?o,? h[ae]ll?o,? BAU BAU",Hallo hallo BAU BAU,N\n'
        + "\\bbow[ -]bow\\b,BAU BAU,N\n",
    )
    path = write_vtt(cwd, [("00:04:58.275", "00:05:00.901", "hello, hello bow bow!")])
    assert transcript.fix_mistakes(rows, str(path)) is True
    assert path.read_bytes().decode() == vtt_content(
        [("00:04:58.275", "00:05:00.901", "hello, hello BAU BAU!")]
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Hashtag, hashtag FUWAMOCO", "Hashtag #FUWAMOCO"),
        ("use hashtag hashtag fwmc please", "use hashtag #fwmc please"),
    ],
)
def test_fix_mistakes_substitutes_groups(cwd, text, expected):
    """Replacements refer to capture groups as $n."""
    rows = fetch(
        cwd,
        REPLACEMENTS_HEADER + '"\\b(H|h)ashtag,? hashtag,? (\\w+)",$1ashtag #$2,N\n',
    )
    path = write_vtt(cwd, [("00:00:01.000", "00:00:02.000", text)])
    assert transcript.fix_mistakes(rows, str(path)) is True
    assert path.read_bytes().decode() == vtt_content(
        [("00:00:01.000", "00:00:02.000", expected)]
    )


def test_fix_mistakes_applies_to_every_text_line(cwd):
    """Replacements apply to all text lines, including multi-line captions."""
    rows = fetch(cwd, REPLACEMENTS_HEADER + "\\bbow[ -]bow\\b,BAU BAU,N\n")
    cues = [
        ("00:00:01.000", "00:00:02.000", "Bow wow? No, bow bow!"),
        ("00:00:02.000", "00:00:03.000", "first line\nand BOW-BOW, bow bow"),
    ]
    path = write_vtt(cwd, cues)
    assert transcript.fix_mistakes(rows, str(path)) is True
    assert path.read_bytes().decode() == vtt_content(
        [
            ("00:00:01.000", "00:00:02.000", "Bow wow? No, BAU BAU!"),
            ("00:00:02.000", "00:00:03.000", "first line\nand BAU BAU, BAU BAU"),
        ]
    )


def test_fix_mistakes_skips_timing_lines(cwd):
    """Lines with timings stay untouched even if a pattern matches them."""
    rows = fetch(cwd, REPLACEMENTS_HEADER + "\\b00\\b,zero-zero,N\n")
    path = write_vtt(cwd, [("00:00:01.000", "00:00:02.000", "Score: 00 to 00")])
    assert transcript.fix_mistakes(rows, str(path)) is True
    assert path.read_bytes().decode() == vtt_content(
        [("00:00:01.000", "00:00:02.000", "Score: zero-zero to zero-zero")]
    )


def test_fix_mistakes_flagged_prints_warning(cwd, capsys):
    """A flagged replacement warns with the new line, then shows the original."""
    rows = fetch(cwd, REPLACEMENTS_HEADER + "\\bPerro\\b,Pero,Y\n")
    cues = [
        *INTRO_CUES,
        ("00:05:30.000", "00:05:31.000", "perro is cute"),
        ("00:05:31.000", "00:05:32.000", "Nothing here."),
        ("00:05:32.000", "00:05:33.000", "Perro again, Perro!"),
    ]
    path = write_vtt(cwd, cues)
    assert transcript.fix_mistakes(rows, str(path)) is True
    assert capsys.readouterr().out == (
        f'{REL_PATH}:17 Replaced with "Pero is cute"\n'
        "perro is cute\n"
        f'{REL_PATH}:23 Replaced with "Pero again, Pero!"\n'
        "Perro again, Perro!\n"
    )
    assert path.read_bytes().decode() == vtt_content(
        [
            *INTRO_CUES,
            ("00:05:30.000", "00:05:31.000", "Pero is cute"),
            ("00:05:31.000", "00:05:32.000", "Nothing here."),
            ("00:05:32.000", "00:05:33.000", "Pero again, Pero!"),
        ]
    )


def test_fix_mistakes_skip_flagged(cwd, capsys):
    """With skip_flagged, flagged rows are skipped silently and others still apply."""
    rows = fetch(
        cwd,
        REPLACEMENTS_HEADER
        + "\\bbow[ -]bow\\b,BAU BAU,N\n"
        + "\\bPerro\\b,Pero,Y\n"
        + "\\bMococo-chan,Moco-chan,Y\n",
    )
    path = write_vtt(
        cwd, [("00:00:01.000", "00:00:02.000", "Perro, bow bow, Mococo-chan")]
    )
    assert transcript.fix_mistakes(rows, str(path), skip_flagged=True) is True
    assert path.read_bytes().decode() == vtt_content(
        [("00:00:01.000", "00:00:02.000", "Perro, BAU BAU, Mococo-chan")]
    )
    assert capsys.readouterr().out == ""


def test_fix_mistakes_skip_flagged_only_flagged_rows(cwd, capsys):
    """With skip_flagged and only flagged matches, nothing changes."""
    rows = fetch(cwd, REPLACEMENTS_HEADER + "\\bPerro\\b,Pero,Y\n")
    path = write_vtt(cwd, [("00:00:01.000", "00:00:02.000", "Perro is cute")])
    before = path.read_bytes()
    assert transcript.fix_mistakes(rows, str(path), skip_flagged=True) is False
    assert path.read_bytes() == before
    assert capsys.readouterr().out == ""


def test_fix_mistakes_no_change_leaves_file_untouched(cwd, capsys):
    """Without matches, the file keeps its bytes, including CRLF endings."""
    rows = fetch(
        cwd,
        REPLACEMENTS_HEADER + "\\bbow[ -]bow\\b,BAU BAU,N\n\\bPerro\\b,Pero,Y\n",
    )
    content = vtt_content(INTRO_CUES).replace("\n", "\r\n").encode()
    path = cwd / REL_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(content)
    assert transcript.fix_mistakes(rows, str(path)) is False
    assert path.read_bytes() == content
    assert capsys.readouterr().out == ""


def test_fix_mistakes_rewrites_with_lf_and_final_newline(cwd):
    """A changed transcript is rewritten with LF endings and a final newline."""
    rows = fetch(cwd, REPLACEMENTS_HEADER + "\\bbow[ -]bow\\b,BAU BAU,N\n")
    path = cwd / REL_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(
        b"WEBVTT\r\n\r\n00:00:01.000 --> 00:00:02.000\r\nbow bow\r\n\r\n"
        b"00:00:02.000 --> 00:00:03.000\r\nThe end."
    )
    assert transcript.fix_mistakes(rows, str(path)) is True
    assert path.read_bytes() == (
        b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nBAU BAU\n\n"
        b"00:00:02.000 --> 00:00:03.000\nThe end.\n"
    )


# highlight_ambiguities


def test_highlight_ambiguities_prints_matching_lines(cwd, capsys):
    """Each matching line prints an info message and the line, in file order."""
    rows = fetch(cwd, HIGHLIGHTS_HEADER + "\\bMoomin\\b,'Mumei'\n")
    cues = [
        *INTRO_CUES,
        ("00:05:30.000", "00:05:31.000", "Is that MOOMIN?"),
        ("00:05:31.000", "00:05:32.000", "Moomins aren't matched."),
        ("00:05:32.000", "00:05:33.000", "Line one\nMoomin and Moomin"),
    ]
    transcript.highlight_ambiguities(rows, str(write_vtt(cwd, cues)))
    assert capsys.readouterr().out == (
        f"{REL_PATH}:17 Potential ambiguity: 'Mumei'\n"
        "Is that MOOMIN?\n"
        f"{REL_PATH}:24 Potential ambiguity: 'Mumei'\n"
        "Moomin and Moomin\n"
    )


def test_highlight_ambiguities_several_rows(cwd, capsys):
    """Every row reports its own matching lines with its reason."""
    rows = fetch(cwd, HIGHLIGHTS_HEADER + "\\bAyami\\b,'Ayamy'\n\\bMoomin\\b,'Mumei'\n")
    cues = [
        ("00:04:58.275", "00:05:00.901", "Hallo hallo BAU BAU!"),
        ("00:05:01.000", "00:05:02.000", "Thanks, Moomin!"),
        ("00:05:02.000", "00:05:03.000", "Ayami drew this."),
    ]
    transcript.highlight_ambiguities(rows, str(write_vtt(cwd, cues)))
    lines = capsys.readouterr().out.splitlines()
    pairs = sorted(zip(lines[::2], lines[1::2], strict=True))
    assert pairs == [
        (f"{REL_PATH}:10 Potential ambiguity: 'Ayamy'", "Ayami drew this."),
        (f"{REL_PATH}:7 Potential ambiguity: 'Mumei'", "Thanks, Moomin!"),
    ]


def test_highlight_ambiguities_nothing_to_report(cwd, capsys):
    """A transcript with the introduction and no matches prints nothing."""
    rows = fetch(cwd, HIGHLIGHTS_HEADER + "\\bMoomin\\b,'Mumei'\n")
    transcript.highlight_ambiguities(rows, str(write_vtt(cwd, INTRO_CUES)))
    assert capsys.readouterr().out == ""


def test_highlight_ambiguities_missing_introduction(cwd, capsys):
    """A transcript without the introduction gets a warning without line number."""
    rows = fetch(cwd, HIGHLIGHTS_HEADER + "\\bMoomin\\b,'Mumei'\n")
    path = write_vtt(cwd, INTRO_CUES[1:])
    transcript.highlight_ambiguities(rows, str(path))
    assert capsys.readouterr().out == f"{REL_PATH} Potential missing introduction\n"


def test_highlight_ambiguities_missing_introduction_with_matches(cwd, capsys):
    """The introduction warning is printed alongside the highlights."""
    rows = fetch(cwd, HIGHLIGHTS_HEADER + "\\bMoomin\\b,'Mumei'\n")
    cues = [("00:00:01.000", "00:00:02.000", "Hello, Moomin!")]
    transcript.highlight_ambiguities(rows, str(write_vtt(cwd, cues)))
    out = capsys.readouterr().out
    highlight = f"{REL_PATH}:4 Potential ambiguity: 'Mumei'\nHello, Moomin!\n"
    intro = f"{REL_PATH} Potential missing introduction\n"
    assert out in (highlight + intro, intro + highlight)


# to_lrc


def test_to_lrc_writes_file_next_to_transcript(cwd):
    """The LRC file has the transcript's name and the .lrc extension."""
    path = write_vtt(cwd, INTRO_CUES)
    result = transcript.to_lrc(str(path))
    expected = cwd / "20230731" / "transcript.lrc"
    assert Path(result).resolve() == expected.resolve()
    assert expected.read_bytes().decode() == (
        "[04:58.27]Hallo hallo BAU BAU!\n"
        "[05:00.92]It's time for FUWAMOCO Morning!\n"
        "[05:05.76]FUWAMOCO Morning hajimaru yo!\n"
        "[05:22.39]And today, we're your hosts of FUWAMOCO Morning!\n"
    )


@pytest.mark.parametrize(
    ("start", "expected"),
    [
        ("00:00:00.000", "[00:00.00]"),
        ("00:00:00.009", "[00:00.00]"),
        ("00:05:07.977", "[05:07.97]"),
        ("00:59:59.999", "[59:59.99]"),
    ],
)
def test_to_lrc_truncates_hundredths(cwd, start, expected):
    """Start times are written as mm:ss.xx with truncated hundredths."""
    path = write_vtt(cwd, [(start, "01:00:00.000", "Text")])
    result = transcript.to_lrc(str(path))
    assert Path(result).read_bytes().decode() == f"{expected}Text\n"


def test_to_lrc_removes_tags_and_decodes_entities(cwd):
    """Tags are removed and entities decoded, also in multi-line captions."""
    cues = [
        ("00:00:01.000", "00:00:02.000", "Time for the Q&amp;A!"),
        ("00:00:02.000", "00:00:03.000", "<i>I love you,</i>\n<i>Moco-chan</i> &lt;3"),
    ]
    result = transcript.to_lrc(str(write_vtt(cwd, cues)))
    assert Path(result).read_bytes().decode() == (
        "[00:01.00]Time for the Q&A!\n[00:02.00]I love you, Moco-chan <3\n"
    )


def test_to_lrc_overwrites_existing_file(cwd):
    """An existing LRC file is replaced."""
    path = write_vtt(cwd, [("00:00:01.000", "00:00:02.000", "Hallo hallo BAU BAU!")])
    write_file(cwd / "20230731" / "transcript.lrc", "[00:00.00]Old\n" * 50)
    result = transcript.to_lrc(str(path))
    assert Path(result).read_bytes().decode() == "[00:01.00]Hallo hallo BAU BAU!\n"
