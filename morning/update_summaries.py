"""Generate and update formatted episode summaries, and update index file with the
latest summaries and questions of the day."""

import argparse
import csv
import json
import os
import re
from datetime import datetime
from datetime import timezone as datetime_timezone

# Define constants
EMOJI_FILE = "config/emojis.csv"
NO_EMOJI_EPISODES = ["friday the 13th"]
HEADER_REGEX = re.compile(r"(#+) (.*)\n")
LAST_UPDATED_REGEX = re.compile(r"^Last updated: [^\r\n]*", re.IGNORECASE)
TIMESTAMP_REGEX = re.compile(r"(.*) \((\d+):(\d+)\)")
CURRENT_TIME_STRING = datetime.now(datetime_timezone.utc).strftime("%Y-%m-%d %H:%M")
LAST_UPDATED_STRING = f"Last updated: {CURRENT_TIME_STRING} UTC"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate and update formatted episode summaries, and update index"
        + "file with the latest summaries and questions of the day."
    )
    parser.add_argument(
        "--transcripts_dir",
        type=str,
        default="transcripts",
        help="Path to the transcripts directory",
    )
    parser.add_argument(
        "--summaries_dir",
        type=str,
        default="summaries",
        help="Path to the summaries directory",
    )
    return parser.parse_args()


def load_metadata(subfolder_path):
    """Load the metadata for the episode."""
    with open(
        os.path.join(subfolder_path, "metadata.json"), "r", encoding="utf-8"
    ) as f:
        metadata = json.load(f)
    metadata["name"] = (
        metadata["episode"]
        if metadata.get("isSpecial")
        else f"Episode #{metadata['episode']}"
    )
    metadata["link"] = f"https://youtu.be/{metadata['id']}"
    return metadata


def format_episode_filename(transcript_subdir, metadata):
    """Format the episode filename."""
    return re.sub(
        r"[^a-zA-Z0-9_]",
        "",
        re.sub(
            r"\s+",
            "_",
            str.replace(
                f"{transcript_subdir} {metadata['episode']}",
                "あさモコ",
                "ASAMOCO",
            ),
        ),
    )


def format_header_line(emoji_list, header_level, header, episode_name, episode_link):
    """Format the header line with the appropriate emoji and timestamp."""

    line = f"{header_level} {header}"
    emoji = ""
    if header_level != "###" and episode_name.lower() not in NO_EMOJI_EPISODES:
        emoji = "🎞️"
        for emoji_entry in emoji_list:
            if re.search(emoji_entry["Pattern"], header, re.IGNORECASE):
                emoji = emoji_entry["Emoji"]
                break

    timestamp_match = TIMESTAMP_REGEX.fullmatch(header)
    if timestamp_match:
        ts_text = f"{timestamp_match.group(2)}:{timestamp_match.group(3)}"
        ts_link = (
            f"{episode_link}?"
            + f"t={timestamp_match.group(2)}m{timestamp_match.group(3)}s"
        )
        timestamp = f"[{ts_text}]({ts_link})"
        if header.lower().startswith("introduction"):
            header_level = "#"
            emoji = ""
            header = f"{episode_name} (start: {timestamp})"
        else:
            header = f"{timestamp_match.group(1)} ({timestamp})"

    if emoji != "":
        emoji = f"{emoji} "
    line = f"{header_level} {emoji}{header}\n"

    return line


def process_summary(
    emoji_list,
    summary,
    episode_name,
    episode_link,
):
    """Process the summary file and add timestamps to the headers."""

    new_summary = []
    episode_question = ""
    skip_front_matter = False
    current_section = ""

    for line in summary:
        if line == "---\n":
            skip_front_matter = not skip_front_matter
            continue

        if skip_front_matter:
            continue

        header_match = HEADER_REGEX.fullmatch(line)
        if header_match:
            header_level = header_match.group(1)
            header = current_section = header_match.group(2)
            line = format_header_line(
                emoji_list,
                header_level,
                header,
                episode_name,
                episode_link,
            )
        elif current_section.lower().startswith("question of the day"):
            episode_question += line
            # Remove all links and formatting from the question
            episode_question = re.sub(
                r"\[([^\]]+)\]\([^\)]+\)", r"\1", episode_question
            )
            episode_question = re.sub(
                r"\*\*(\w[^\*]+)\*\*([.,]?)", r'"\1\2"', episode_question
            )
            episode_question = re.sub(
                r"\*(\w[^\*]+)\*([.,]?)", r'"\1\2"', episode_question
            )

        new_summary.append(line)

    # Remove all empty lines at the beginning of the summary
    while new_summary and new_summary[0].isspace():
        new_summary.pop(0)

    return new_summary, episode_question


def refresh_file(filename, new_content):
    """Refresh a file with new content if it has changed."""
    current_content = []
    line_terminator = "\n"
    with open(filename, "r", encoding="utf-8", newline="") as f:
        current_content = f.readlines()
        if "\r\n" in current_content[0]:
            line_terminator = "\r\n"
    current_content = [
        LAST_UPDATED_REGEX.sub(LAST_UPDATED_STRING, line) for line in current_content
    ]
    new_content = [f"{line}{line_terminator}" for line in new_content]
    if current_content != new_content:
        with open(filename, "w", encoding="utf-8", newline="") as f:
            f.writelines(f"{line}" for line in new_content)
        return True
    return False


def refresh_summary_index(summary_index, summary_table):
    """Refresh the summary index with the latest episode summaries."""
    was_updated = refresh_file("index.md", summary_index)
    if was_updated:
        with open("index.csv", "w", encoding="utf-8", newline="") as csvfile:
            fieldnames = [
                "Date",
                "Episode",
                "Title",
                "Description",
                "Illustrator",
                "Link",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in sorted(summary_table, key=lambda x: x["Date"]):
                writer.writerow(row)
    return was_updated


def refresh_questions_file(question_summary):
    """Refresh the questions file with the latest questions of the day."""
    return refresh_file("questions.txt", question_summary)


def main():
    """Update index file with the latest episode summaries and questions of the day."""

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    args = parse_args()

    summary_index = [
        "# 🌅 FUWAMOCO Morning Episode Summaries",
        "",
        LAST_UPDATED_STRING,
        "",
        "<!-- markdownlint-disable-file MD044 -->",
        "| 🗓️ Date |     | 📺 Episode |     | 📄 Summary | 🔤 Transcript |",
        "| ------ | --- | --------- | --- | --------- | ------------ |",
    ]
    summary_table = []
    question_summary = [
        "FUWAMOCO Morning Questions of the Day",
        "",
        LAST_UPDATED_STRING,
    ]

    with open(EMOJI_FILE, "r", encoding="utf-8", newline="") as csvfile:
        emoji_list = list(csv.DictReader(csvfile))

    for transcript_subdir in os.listdir(args.transcripts_dir):
        subfolder_path = os.path.join(args.transcripts_dir, transcript_subdir)
        if os.path.isdir(subfolder_path):
            with open(
                os.path.join(subfolder_path, "summary.md"), "r", encoding="utf-8"
            ) as f:
                summary = f.readlines()

            metadata = load_metadata(subfolder_path)

            summary_base_name = format_episode_filename(transcript_subdir, metadata)

            summary_index.append(
                f"| {metadata['date']} | "
                + f"{metadata['dayOfWeek'][:3]} | "
                + f"[{metadata['name']}]({metadata['link']}) | "
                + f"{metadata['description']} | "
                + f"[Summary]({args.summaries_dir}/{summary_base_name}.md) | "
                + f"[Transcript]({args.transcripts_dir}"
                + f"/{transcript_subdir}/transcript.vtt) |"
            )

            summary_table.append(
                {
                    "Date": metadata["date"],
                    "Episode": metadata["name"],
                    "Title": metadata["title"],
                    "Description": metadata["description"],
                    "Illustrator": metadata["illustrator"],
                    "Link": metadata["link"],
                }
            )

            new_summary, episode_question = process_summary(
                emoji_list,
                summary,
                metadata["name"],
                metadata["link"],
            )

            # Skip Episode #0 as no question was asked
            if episode_question and metadata["episode"] != "0":
                question_summary.append("")
                question_summary.append(
                    f"{metadata['name']} — "
                    + re.sub(r"\s+", " ", episode_question).strip()
                )

            with open(
                os.path.join(args.summaries_dir, f"{summary_base_name}.md"),
                "w",
                encoding="utf-8",
            ) as f:
                f.writelines(new_summary)

    if refresh_summary_index(summary_index, summary_table):
        print("Index updated")
    else:
        print("No changes to index")

    if refresh_questions_file(question_summary):
        print("Questions summary updated")
    else:
        print("No changes to questions summary")


if __name__ == "__main__":
    main()
