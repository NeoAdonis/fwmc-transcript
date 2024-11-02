import builtins
import json
import os
import re
import subprocess
from datetime import datetime
from termcolor import colored


def open_with_default_encoding(file, mode="r", encoding="utf-8", **kwargs):
    return builtins._open(file, mode, encoding=encoding, **kwargs)


builtins._open = builtins.open
builtins.open = open_with_default_encoding

# Define variables
source_folder = "audio"
output_folder = "transcripts"
model = (
    "large-v2"  # This model *seems* to work better than "large-v3" for FUWAMOCO Morning
)
prompt_path = "config/transcript-prompt.txt"
include_no_prompt = False

# Read the transcript prompt from the specified file
with open(prompt_path, "r") as f:
    transcript_prompt = f.read()

file_base_name = "audio"
convert_base_name = "audio_converted"
new_base_name = "transcript"

# Iterate through the audio files in the source folder
for root, dirs, files in os.walk(source_folder):
    for file in files:
        if file.startswith(file_base_name):
            audio_path = os.path.join(root, file)
            if audio_path.endswith((".wave", ".wav")):
                continue
            parent_folder_name = os.path.basename(os.path.dirname(audio_path))
            new_output_folder = os.path.join(output_folder, parent_folder_name)

            title_file_path = os.path.join(root, f"{parent_folder_name}.title")
            description_file_path = os.path.join(
                root, f"{parent_folder_name}.description"
            )

            with open(title_file_path, "r") as f:
                title_file_content = f.readlines()
            with open(description_file_path, "r") as f:
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
                        f"Episode aired on an unexpected day ({metadata['day_of_week']}). Maybe a bug?",
                        "red",
                    )
                )

            if not os.path.exists(new_output_folder):
                os.makedirs(new_output_folder)

            with open(os.path.join(new_output_folder, "metadata.json"), "w") as f:
                json.dump(metadata, f, indent=4)

            if os.path.exists(os.path.join(new_output_folder, f"{new_base_name}.vtt")):
                continue

            print(f"Transcribing '{audio_path}'...")

            # Convert audio files for easier transcription
            exec(open("../common/get_video_audio.py").read())
            audio_path = os.path.join(root, f"{convert_base_name}.wav")

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
                ]
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
                    ]
                )

            os.remove(audio_path)

            for file in os.listdir(new_output_folder):
                if file.startswith(new_base_name):
                    os.remove(os.path.join(new_output_folder, file))
                elif file.startswith(convert_base_name):
                    os.rename(
                        os.path.join(new_output_folder, file),
                        os.path.join(
                            new_output_folder,
                            f"{new_base_name}{os.path.splitext(file)[1]}",
                        ),
                    )

            transcript_file = next(
                (
                    f
                    for f in os.listdir(new_output_folder)
                    if f.startswith(new_base_name)
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
            with open(os.path.join(new_output_folder, transcript_file), "r") as f:
                transcript_content = f.read()
            transcript_lines = transcript_content.splitlines()
            with open("./config/replacements.csv", "r") as f:
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
            with open(os.path.join(new_output_folder, transcript_file), "w") as f:
                f.write(transcript_content)

            # Detect and highlight potential mistakes that might actually be correct for manual review
            if "Hallo hallo BAU BAU" not in transcript_content:
                print(
                    colored(
                        f"{transcript_file} - Potential missing introduction", "yellow"
                    )
                )

            with open("./config/highlights.csv", "r") as f:
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

            summary_draft = [
                "---",
                f"episode: {json.dumps(metadata['episode']) if metadata['isSpecial'] else metadata['episode']}",
                f"date: {metadata['date']}",
                f"link: \"https://youtu.be/{metadata['id']}\"",
                "wip: true",
                "---",
                "",
                "## Sections",
                "",
                "- Introduction",
                "- Pero Sighting",
                "- Mococo Pup Talk",
                "- Doggie Of The Day",
                "- Today I Went On A Walk",
                "- Question Of The Day",
                "- Next Stream & Schedule",
                "- Thanks & Extra Special Ruffians",
            ]

            with open(os.path.join(new_output_folder, "summary.md"), "w") as f:
                f.write("\n".join(summary_draft))
