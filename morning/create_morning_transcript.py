"""Create transcripts for FUWAMOCO Morning episodes."""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime
from termcolor import colored
from common.convert_to_wav import convert_to_wav

# Define constants
INTRODUCTION_PATTERN = "Hallo hallo BAU BAU"
FILE_BASE_NAME = "audio"
CONVERT_BASE_NAME = "audio_converted"
NEW_BASE_NAME = "transcript"
DEFAULT_SECTION_NAMES = [
    "- Introduction",
    "- Pero Sighting",
    "- Mococo Pup Talk",
    "- Doggie Of The Day",
    "- Today I Went On A Walk",
    "- Question Of The Day",
    "- Next Stream & Schedule",
    "- Thanks & Extra Special Ruffians",
]

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Validate the structure and content of the transcripts and metadata files."
)
parser.add_argument(
    "--source_folder",
    type=str,
    default="audio",
    help="Path to the source directory",
)
parser.add_argument(
    "--output_folder",
    type=str,
    default="transcripts",
    help="Path to the output directory",
)
parser.add_argument(
    "--model",
    type=bool,
    default=(
        "large-v2"  # This model *seems* to work better than "large-v3" for FUWAMOCO Morning
    ),
    help="Whisper model to use for transcription",
)
parser.add_argument(
    "--prompt_path",
    type=str,
    default="config/transcript-prompt.txt",
    help="Path to the transcript prompt file",
)
parser.add_argument(
    "--include_no_prompt",
    type=bool,
    default=False,
    help="True if the transcript without prompt should be included, False otherwise",
)
args = parser.parse_args()

source_folder = args.source_folder
output_folder = args.output_folder
model = args.model
prompt_path = args.prompt_path
include_no_prompt = args.include_no_prompt

# Read the transcript prompt from the specified file
with open(prompt_path, "r", encoding="utf-8") as f:
    transcript_prompt = f.read()

# Iterate through the audio files in the source folder
for root, dirs, files in os.walk(source_folder):
    for file in files:
        if file.startswith(FILE_BASE_NAME):
            audio_path = os.path.join(root, file)
            if audio_path.endswith((".wave", ".wav")):
                continue
            parent_folder_name = os.path.basename(os.path.dirname(audio_path))
            new_output_folder = os.path.join(output_folder, parent_folder_name)

            title_file_path = os.path.join(root, f"{parent_folder_name}.title")
            description_file_path = os.path.join(
                root, f"{parent_folder_name}.description"
            )

            with open(title_file_path, "r", encoding="utf-8") as f:
                title_file_content = f.readlines()
            with open(description_file_path, "r", encoding="utf-8") as f:
                description_file_content = f.readlines()

            title = title_file_content[1].strip()
            episode = "???"
            if title.startswith("【FUWAMOCO MORNING】"):
                if "episode" in title:
                    episode = title.split("episode")[1].strip()
                else:
                    episode = title.split("】")[1].strip()

            description = description_file_content[0].strip()
            illustrator = "rswxx"  # Icomochi, FUWAMOCO designer
            for line in description_file_content[1:]:
                if "illust" in line:
                    illustrator = line.split("@")[1].split()[0]
                    break
                description += " " + line.strip()

            metadata = {
                "id": title_file_content[0].strip(),
                "title": title,
                "episode": episode,
                "isSpecial": not episode.isdigit(),
                "date": datetime.strptime(parent_folder_name, "%Y%m%d").strftime(
                    "%Y-%m-%d"
                ),
                "day_of_week": datetime.strptime(parent_folder_name, "%Y%m%d").strftime(
                    "%A"
                ),
                "description": description,
                "illustrator": illustrator,
            }

            if metadata["day_of_week"] not in ["Monday", "Wednesday", "Friday"]:
                print(
                    colored(
                        f"Episode aired on an unexpected day ({metadata['day_of_week']}). "
                        + "Maybe a bug?",
                        "red",
                    )
                )

            if not os.path.exists(new_output_folder):
                os.makedirs(new_output_folder)

            with open(
                os.path.join(new_output_folder, "metadata.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(metadata, f, indent=4)

            if os.path.exists(os.path.join(new_output_folder, f"{NEW_BASE_NAME}.vtt")):
                continue

            print(f"Transcribing '{audio_path}'...")

            # Convert audio files for easier transcription
            convert_to_wav(audio_path, CONVERT_BASE_NAME)
            audio_path = os.path.join(root, f"{CONVERT_BASE_NAME}.wav")

            # TODO: Use whisperx module instead of running the command directly
            # Transcript with prompt to create a more accurate transcript
            subprocess.run(
                [
                    "whisperx",
                    "--model",
                    model,
                    "--batch_size",
                    "16",
                    "-o",
                    new_output_folder,
                    "--output_format",
                    "vtt",
                    "--verbose",
                    "False",
                    "--language",
                    "en",
                    "--initial_prompt",
                    transcript_prompt,
                    audio_path,
                ],
                check=True,
            )

            # Transcript without prompt can be used to fix potential errors when using the prompt
            if include_no_prompt:
                new_output_folder_no_prompt = os.path.join(
                    new_output_folder, "noprompt"
                )
                if not os.path.exists(new_output_folder_no_prompt):
                    os.makedirs(new_output_folder_no_prompt)
                subprocess.run(
                    [
                        "whisperx",
                        "--model",
                        model,
                        "--batch_size",
                        "16",
                        "-o",
                        new_output_folder_no_prompt,
                        "--output_format",
                        "vtt",
                        "--verbose",
                        "False",
                        "--language",
                        "en",
                        audio_path,
                    ],
                    check=True,
                )

            os.remove(audio_path)

            for file in os.listdir(new_output_folder):
                if file.startswith(NEW_BASE_NAME):
                    os.remove(os.path.join(new_output_folder, file))
                elif file.startswith(CONVERT_BASE_NAME):
                    os.rename(
                        os.path.join(new_output_folder, file),
                        os.path.join(
                            new_output_folder,
                            f"{NEW_BASE_NAME}{os.path.splitext(file)[1]}",
                        ),
                    )

            transcript_file = next(
                (
                    f
                    for f in os.listdir(new_output_folder)
                    if f.startswith(NEW_BASE_NAME)
                ),
                None,
            )
            if not transcript_file:
                print(
                    colored(
                        f"Transcript file not found in '{new_output_folder}'.", "red"
                    )
                )
                continue

            # Fix common mistakes in the transcript
            with open(
                os.path.join(new_output_folder, transcript_file), "r", encoding="utf-8"
            ) as f:
                transcript_content = f.read()
            transcript_lines = transcript_content.splitlines()
            with open("./config/replacements.csv", "r", encoding="utf-8") as f:
                replacements = [line.strip().split(",") for line in f.readlines()]
            for pattern, replacement, warning in replacements:
                if warning == "Y":
                    for i, line in enumerate(transcript_lines):
                        if re.search(pattern, line, re.IGNORECASE):
                            print(
                                colored(
                                    f'{transcript_file}:{i+1} - Replaced with "{replacement}"',
                                    "yellow",
                                )
                            )
                            print(
                                re.sub(
                                    pattern,
                                    lambda m: colored(m.group(), attrs=["bold"]),
                                    line,
                                )
                            )
                transcript_content = re.sub(
                    pattern, replacement, transcript_content, flags=re.IGNORECASE
                )
            with open(
                os.path.join(new_output_folder, transcript_file), "w", encoding="utf-8"
            ) as f:
                f.write(transcript_content)

            # Detect and highlight potential mistakes that might actually be correct
            # for manual review
            if INTRODUCTION_PATTERN not in transcript_content:
                print(
                    colored(
                        f"{transcript_file} - Potential missing introduction", "yellow"
                    )
                )

            with open("./config/highlights.csv", "r", encoding="utf-8") as f:
                highlights = [line.strip().split(",") for line in f.readlines()]
            for pattern, reason in highlights:
                for i, line in enumerate(transcript_lines):
                    if re.search(pattern, line, re.IGNORECASE):
                        print(colored(f"{transcript_file}:{i+1} - {reason}", "yellow"))
                        print(
                            re.sub(
                                pattern,
                                lambda m: colored(m.group(), attrs=["bold"]),
                                line,
                            )
                        )

            if os.path.exists(os.path.join(new_output_folder, "summary.md")):
                continue

            episode_name = (
                json.dumps(metadata["episode"])
                if metadata["isSpecial"]
                else metadata["episode"]
            )

            summary_draft = [
                "---",
                f"episode: {episode_name}",
                f"date: {metadata['date']}",
                f"link: \"https://youtu.be/{metadata['id']}\"",
                "wip: true",
                "---",
                "",
                "## Sections",
                "",
            ]
            for section_name in DEFAULT_SECTION_NAMES:
                summary_draft.append(section_name)

            with open(
                os.path.join(new_output_folder, "summary.md"), "w", encoding="utf-8"
            ) as f:
                f.write("\n".join(summary_draft))
