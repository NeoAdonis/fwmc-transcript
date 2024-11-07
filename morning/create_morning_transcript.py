"""Create transcripts for FUWAMOCO Morning episodes."""

import argparse
import json
import os
import re
from datetime import datetime
import torch
import whisperx
from common import printer
from common.media import convert_to_wav

# Define constants
INTRODUCTION_PATTERN = "Hallo hallo BAU BAU"
FILE_BASE_NAME = "audio"
CONVERT_BASE_NAME = "audio_converted"
NEW_BASE_NAME = "transcript"
PROMPT_FILE = "config/transcript-prompt.txt"
HIGHLIGHTS_FILE = "config/highlights.csv"
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
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 16


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Validate the structure and content of the transcripts and metadata files."
    )
    parser.add_argument(
        "--audio_dir",
        type=str,
        default="audio",
        help="Path to the directory containing the audio files",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="transcripts",
        help="Path to the directory to save the transcripts",
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
        "--include_no_prompt",
        type=bool,
        default=False,
        help="True if the transcript without prompt should be included, False otherwise",
    )
    args = parser.parse_args()
    return args


def get_metadata(root, parent_folder_name):
    """Get metadata for the episode from the title and description files"""
    title_file_path = os.path.join(root, f"{parent_folder_name}.title")
    description_file_path = os.path.join(root, f"{parent_folder_name}.description")
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
        "date": datetime.strptime(parent_folder_name, "%Y%m%d").strftime("%Y-%m-%d"),
        "day_of_week": datetime.strptime(parent_folder_name, "%Y%m%d").strftime("%A"),
        "description": description,
        "illustrator": illustrator,
    }

    if metadata["day_of_week"] not in ["Monday", "Wednesday", "Friday"]:
        printer.print_warning(
            parent_folder_name,
            f"Episode aired on an unexpected day ({metadata['day_of_week']}). "
            + "Maybe a bug?",
        )

    return metadata


def transcribe_audio(audio_path, model, align_model, align_metadata, new_output_dir):
    """Transcribe the audio file using the specified model"""
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, BATCH_SIZE, language="en")
    result = whisperx.align(
        result["segments"],
        align_model,
        align_metadata,
        audio,
        DEVICE,
        return_char_alignments=False,
    )

    writer = whisperx.utils.get_writer("vtt", new_output_dir)
    writer(result, audio_path)


def clean_transcript_files(new_output_dir):
    """Clean up the transcript files"""
    for file in os.listdir(new_output_dir):
        if file.startswith(NEW_BASE_NAME):
            os.remove(os.path.join(new_output_dir, file))
        elif file.startswith(CONVERT_BASE_NAME):
            os.rename(
                os.path.join(new_output_dir, file),
                os.path.join(
                    new_output_dir,
                    f"{NEW_BASE_NAME}{os.path.splitext(file)[1]}",
                ),
            )


def fix_transcript_mistakes(transcript_file, new_output_dir):
    """Fix common mistakes in the transcript"""
    with open(
        os.path.join(new_output_dir, transcript_file), "r", encoding="utf-8"
    ) as f:
        transcript_content = f.read()
    transcript_lines = transcript_content.splitlines()
    with open("./config/replacements.csv", "r", encoding="utf-8") as f:
        replacements = [line.strip().split(",") for line in f.readlines()]
    for pattern, replacement, warning in replacements:
        if warning == "Y":
            for i, line in enumerate(transcript_lines):
                if re.search(pattern, line, re.IGNORECASE):
                    printer.print_with_highlight(
                        f"{transcript_file}:{i+1}",
                        f'Replaced with "{replacement}"',
                        line,
                        pattern,
                    )
        transcript_content = re.sub(
            pattern, replacement, transcript_content, flags=re.IGNORECASE
        )
    with open(
        os.path.join(new_output_dir, transcript_file), "w", encoding="utf-8"
    ) as f:
        f.write(transcript_content)


def highlight_mistakes(transcript_file, new_output_dir):
    """Highlight potential mistakes in the transcript"""
    with open(
        os.path.join(new_output_dir, transcript_file), "r", encoding="utf-8"
    ) as f:
        transcript_content = f.read()
    transcript_lines = transcript_content.splitlines()
    # Detect and highlight potential mistakes that might actually be correct
    # for manual review
    if INTRODUCTION_PATTERN not in transcript_content:
        printer.print_warning(transcript_file, "Potential missing introduction")

    with open(HIGHLIGHTS_FILE, "r", encoding="utf-8") as f:
        highlights = [line.strip().split(",") for line in f.readlines()]
    for pattern, reason in highlights:
        for i, line in enumerate(transcript_lines):
            if re.search(pattern, line, re.IGNORECASE):
                printer.print_with_highlight(
                    f"{transcript_file}:{i+1}", reason, line, pattern
                )


def create_summary_draft(metadata, new_output_dir):
    """Create a draft of the summary file"""

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

    with open(os.path.join(new_output_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary_draft))


def main():
    """Create transcripts for FUWAMOCO Morning episodes."""

    args = parse_args()

    # Load transcription models
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        model = whisperx.load_model(
            args.model,
            DEVICE,
            asr_options={
                "initial_prompt": f.read(),
            },
        )
    align_model, align_metadata = whisperx.load_align_model(
        language_code="en", device=DEVICE
    )
    if args.include_no_prompt:
        model_no_prompt = whisperx.load_model(model, DEVICE)

    # Iterate through the audio files in the source directory
    for root, _, files in os.walk(args.audio_dir):
        for file in files:
            if file.startswith(FILE_BASE_NAME):
                audio_path = os.path.join(root, file)
                if audio_path.endswith((".wave", ".wav")):
                    continue
                parent_folder_name = os.path.basename(os.path.dirname(audio_path))
                new_output_dir = os.path.join(args.output_dir, parent_folder_name)

                metadata = get_metadata(root, parent_folder_name)

                if not os.path.exists(new_output_dir):
                    os.makedirs(new_output_dir)

                with open(
                    os.path.join(new_output_dir, "metadata.json"), "w", encoding="utf-8"
                ) as f:
                    json.dump(metadata, f, indent=4)

                if os.path.exists(os.path.join(new_output_dir, f"{NEW_BASE_NAME}.vtt")):
                    continue

                print(f"Transcribing '{audio_path}'...")

                # Convert audio files for easier transcription
                convert_to_wav(audio_path, CONVERT_BASE_NAME)
                audio_path = os.path.join(root, f"{CONVERT_BASE_NAME}.wav")

                # Transcript with prompt to create a more accurate transcript
                transcribe_audio(
                    audio_path, model, align_model, align_metadata, new_output_dir
                )

                # Transcript without prompt can be used to fix potential errors when using prompt
                if args.include_no_prompt:
                    new_output_dir_no_prompt = os.path.join(new_output_dir, "noprompt")
                    if not os.path.exists(new_output_dir_no_prompt):
                        os.makedirs(new_output_dir_no_prompt)
                    transcribe_audio(
                        audio_path,
                        model_no_prompt,
                        align_model,
                        align_metadata,
                        new_output_dir_no_prompt,
                    )

                os.remove(audio_path)

                clean_transcript_files(new_output_dir)

                transcript_file = next(
                    (
                        f
                        for f in os.listdir(new_output_dir)
                        if f.startswith(NEW_BASE_NAME)
                    ),
                    None,
                )
                if not transcript_file:
                    printer.print_warning(new_output_dir, "Transcript file not found")
                    continue

                fix_transcript_mistakes(transcript_file, new_output_dir)
                highlight_mistakes(transcript_file, new_output_dir)

                if os.path.exists(os.path.join(new_output_dir, "summary.md")):
                    continue

                create_summary_draft(metadata, new_output_dir)


if __name__ == "__main__":
    main()
