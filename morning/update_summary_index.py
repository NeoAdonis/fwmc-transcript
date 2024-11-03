"""Update the index.md file with the latest episode summaries and questions of the day"""

import argparse
import csv
import json
import re
import os
from datetime import datetime
from datetime import timezone as datetime_timezone


# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Validate the structure and content of the transcripts and metadata files."
)
parser.add_argument(
    "--transcripts_folder",
    type=str,
    default="transcripts",
    help="Path to the transcripts directory",
)
parser.add_argument(
    "--summaries_folder",
    type=str,
    default="transcripts",
    help="Path to the transcripts directory",
)
args = parser.parse_args()

transcripts_folder = args.transcripts_folder
summaries_folder = args.summaries_folder

summary_index = []
summary_table = []

current_time_string = datetime.now(datetime_timezone.utc).strftime("%Y-%m-%d %H:%M")
last_updated_string = f"Last updated: {current_time_string} UTC"

summary_index.append("# 🌅 FUWAMOCO Morning Episode Summaries")
summary_index.append("")
summary_index.append(last_updated_string)
summary_index.append("")
summary_index.append("| 🗓️ Date |     | 📺 Episode |     | 📄 Summary | 🔤 Transcript |")
summary_index.append("| ------ | --- | --------- | --- | --------- | ------------ |")

question_summary = ["FUWAMOCO Morning Questions of the Day", "", last_updated_string]

for transcript_subfolder in os.listdir(transcripts_folder):
    subfolder_path = os.path.join(transcripts_folder, transcript_subfolder)
    if os.path.isdir(subfolder_path):
        with open("config/emojis.csv", "r", encoding="utf-8") as csvfile:
            emoji_list = list(csv.DictReader(csvfile))

        with open(
            os.path.join(subfolder_path, "summary.md"), "r", encoding="utf-8"
        ) as f:
            summary = f.readlines()

        new_summary = []

        with open(
            os.path.join(subfolder_path, "metadata.json"), "r", encoding="utf-8"
        ) as f:
            metadata = json.load(f)

        episode_name = (
            metadata["episode"]
            if metadata.get("isSpecial")
            else f"Episode #{metadata['episode']}"
        )
        transcript_path = f"{transcripts_folder}/{transcript_subfolder}/transcript.vtt"
        episode_link = f"https://youtu.be/{metadata['id']}"
        summary_base_name = re.sub(
            r"[^a-zA-Z0-9_]",
            "",
            re.sub(
                r"\s+",
                "_",
                str.replace(
                    f"{transcript_subfolder} {metadata['episode']}",
                    "あさモコ",
                    "ASAMOCO",
                ),
            ),
        )

        summary_index.append(
            f"| {metadata['date']} | "
            + f"{metadata['dayOfWeek'][:3]} | "
            + f"[{episode_name}]({episode_link}) | "
            + f"{metadata['description']} | "
            + f"[Summary]({summaries_folder}/{summary_base_name}.md) | "
            + f"[Transcript]({transcript_path}) |"
        )

        summary_table.append(
            {
                "Date": metadata["date"],
                "Episode": episode_name,
                "Title": metadata["title"],
                "Description": metadata["description"],
                "Illustrator": metadata["illustrator"],
                "Link": episode_link,
            }
        )

        header_regex = re.compile(r"(#+) (.*)\n")
        timestamp_regex = re.compile(r"(.*) \((\d+):(\d+)\)")

        episode_question = ""
        skip_front_matter = False
        current_section = ""

        for line in summary:
            if skip_front_matter:
                if line == "---\n":
                    skip_front_matter = False
                continue
            elif line == "---\n":
                skip_front_matter = True
                continue

            header_match = header_regex.fullmatch(line)
            if header_match:
                header_level = header_match.group(1)
                header = current_section = header_match.group(2)
                emoji = "🎞️"
                for emoji_entry in emoji_list:
                    if re.search(emoji_entry["Pattern"], header, re.IGNORECASE):
                        emoji = emoji_entry["Emoji"]
                        break
                # TODO: Make this configurable if needed
                if header_level != "###" and episode_name != "friday the 13th":
                    header = f"{emoji} {header}"

                timestamp_match = timestamp_regex.fullmatch(header)
                if timestamp_match:
                    ts_text = f"{timestamp_match.group(2)}:{timestamp_match.group(3)}"
                    ts_link = (
                        f"{episode_link}?"
                        + f"t={timestamp_match.group(2)}m{timestamp_match.group(3)}s"
                    )
                    timestamp = f"[{ts_text}]({ts_link})"
                    line = f"{header_level} {timestamp_match.group(1)} ({timestamp})\n"
                    if current_section.lower().startswith("introduction"):
                        line = f"# {episode_name} (start: {timestamp})\n"
            elif current_section.lower().startswith("question of the day"):
                episode_question += line

            new_summary.append(line)

        # Skip Episode #0 as no question was asked
        if episode_question and episode_name != "Episode #0":
            # Remove all links to minimize file size
            episode_question = re.sub(
                r"\[([^\]]+)\]\([^\)]+\)", r"\1", episode_question
            )
            episode_question = re.sub(
                r"\*\*(\w[^\*]+)\*\*([.,]?)", r'"\1\2"', episode_question
            )
            episode_question = re.sub(
                r"\*(\w[^\*]+)\*([.,]?)", r'"\1\2"', episode_question
            )
            question_summary.append("")
            question_summary.append(
                f"{episode_name} — {re.sub(r'\s+', ' ', episode_question).strip()}"
            )

        # Remove all empty lines at the beginning of the summary
        while new_summary and new_summary[0].isspace():
            new_summary.pop(0)

        with open(
            os.path.join(summaries_folder, f"{summary_base_name}.md"),
            "w",
            encoding="utf-8",
        ) as f:
            f.writelines(new_summary)

current_index = []
with open("index.md", "r", encoding="utf-8") as f:
    current_index = f.readlines()

current_index = [
    re.sub(r"^Last updated: .*$", last_updated_string, line) for line in current_index
]

if "\n".join(current_index) != "\n".join(summary_index):
    with open("index.md", "w", encoding="utf-8") as f:
        f.writelines(f"{line}\n" for line in summary_index)

    with open("index.csv", "w", encoding="utf-8") as csvfile:
        fieldnames = ["Date", "Episode", "Title", "Description", "Illustrator", "Link"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(summary_table, key=lambda x: x["Date"]):
            writer.writerow(row)

    print("Index updated")
else:
    print("No changes to index")

current_questions = []
with open("questions.txt", "r", encoding="utf-8") as f:
    current_questions = f.readlines()

current_questions = [
    re.sub(r"Last updated: .*$", last_updated_string, line)
    for line in current_questions
]

if "\n".join(current_questions) != "\n".join(question_summary):
    with open("questions.txt", "w", encoding="utf-8") as f:
        f.writelines(f"{line}\n" for line in question_summary)
    print("Questions summary updated")
else:
    print("No changes to questions summary")
