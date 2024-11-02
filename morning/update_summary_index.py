import builtins
import csv
import json
import re
import os
from datetime import datetime
from datetime import timezone as datetime_timezone


def open_with_default_encoding(file, mode="r", encoding="utf-8", **kwargs):
    return builtins._open(file, mode, encoding=encoding, **kwargs)


builtins._open = builtins.open
builtins.open = open_with_default_encoding

transcripts_folder = "transcripts"
summaries_folder = "summaries"

summary_index = []
summary_table = []

last_updated_string = f"Last updated: {datetime.now(datetime_timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC"

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
        with open("config/emojis.csv", "r") as csvfile:
            emoji_list = list(csv.DictReader(csvfile))

        with open(os.path.join(subfolder_path, "summary.md"), "r") as f:
            summary = f.readlines()

        new_summary = []

        with open(os.path.join(subfolder_path, "metadata.json"), "r") as f:
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
                re.sub(
                    "あさモコ",
                    "ASAMOCO",
                    f"{transcript_subfolder} {metadata['episode']}",
                ),
            ),
        )

        summary_index.append(
            f"| {metadata['date']} | {metadata['dayOfWeek'][:3]} | [{episode_name}]({episode_link}) | {metadata['description']} | [Summary]({summaries_folder}/{summary_base_name}.md) | [Transcript]({transcript_path}) |"
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

        episode_question = ""
        skip_front_matter = False
        current_section = ""

        for line in summary:
            if skip_front_matter:
                if re.match(r"^---$", line):
                    skip_front_matter = False
                continue
            elif re.match(r"^---$", line):
                skip_front_matter = True
                continue

            header_match = re.match(r"^(#+) (.*)$", line)
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

                timestamp_match = re.match(r"^(.*) \((\d+):(\d+)\)$", header)
                if timestamp_match:
                    timestamp = f"[{timestamp_match.group(2)}:{timestamp_match.group(3)}]({episode_link}?t={timestamp_match.group(2)}m{timestamp_match.group(3)}s)"
                    line = f"{header_level} {timestamp_match.group(1)} ({timestamp})\n"
                    if re.match(r"^Introduction", current_section):
                        line = f"# {episode_name} (start: {timestamp})\n"
            elif re.match(r"^Question of the Day", current_section, re.IGNORECASE):
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
        while new_summary and re.match(r"^\s*$", new_summary[0]):
            new_summary.pop(0)

        with open(
            os.path.join(summaries_folder, f"{summary_base_name}.md"),
            "w",
        ) as f:
            f.writelines(new_summary)

current_index = []
with open("index.md", "r") as f:
    current_index = f.readlines()

current_index = [
    re.sub(r"^Last updated: .*$", last_updated_string, line) for line in current_index
]

if "\n".join(current_index) != "\n".join(summary_index):
    with open("index.md", "w") as f:
        f.writelines(f"{line}\n" for line in summary_index)

    with open("index.csv", "w") as csvfile:
        fieldnames = ["Date", "Episode", "Title", "Description", "Illustrator", "Link"]
        writer = csv.DictWriter(
            csvfile, fieldnames=fieldnames, lineterminator="\n", quoting=csv.QUOTE_ALL
        )
        writer.writeheader()
        for row in sorted(summary_table, key=lambda x: x["Date"]):
            writer.writerow(row)

    print("Index updated")
else:
    print("No changes to index")

current_questions = []
with open("questions.txt", "r") as f:
    current_questions = f.readlines()

current_questions = [
    re.sub(r"Last updated: .*$", last_updated_string, line)
    for line in current_questions
]

if "\n".join(current_questions) != "\n".join(question_summary):
    with open("questions.txt", "w") as f:
        f.writelines(f"{line}\n" for line in question_summary)
    print("Questions summary updated")
else:
    print("No changes to questions summary")
