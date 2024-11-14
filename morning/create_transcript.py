"""Create transcripts for FUWAMOCO Morning episodes."""

import argparse
import json
import os
import re
from datetime import datetime

import torch
import whisperx

from common import asr, printer, transcript
from common.media import convert_to_wav

# Define constants
FILE_BASE_NAME = "audio"
CONVERT_BASE_NAME = "audio_converted"
NEW_BASE_NAME = "transcript"
PROMPT_FILE = "config/transcript-prompt.txt"
HIGHLIGHTS_FILE = "config/highlights.csv"
REPLACEMENTS_FILE = "config/replacements.csv"
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
        type=str,
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


def get_metadata(root, dir_basename):
    """Get metadata for the episode from the title and description files"""
    title_file_path = os.path.join(root, f"{dir_basename}.title")
    description_file_path = os.path.join(root, f"{dir_basename}.description")
    with open(title_file_path, "r", encoding="utf-8") as f:
        title_file_content = f.readlines()
    with open(description_file_path, "r", encoding="utf-8") as f:
        description_file_content = f.readlines()

    title = title_file_content[1].strip()
    episode = "???"

    patterns = [
        r"【FUWAMOCO MORNING】\s*episode (\d+)",
        r"【FUWAMOCO MORNING】\s*([\w\s\-']+)",
        r"【([^】]+)】",
    ]
    for pattern in patterns:
        m = re.search(pattern, title, re.IGNORECASE)
        if m:
            episode = m.group(1).strip()
            break

    description = description_file_content[0].strip()
    illustrator = "rswxx"  # Icomochi, FUWAMOCO designer
    for line in description_file_content[1:]:
        if "illust" in line:
            if "@" in line:
                illustrator = line.split("@")[1].split()[0]
            elif "illustration by" in line:
                illustrator = line.split("illustration by")[1].split()[0]
            m = re.match(r"([\w_\-]*)", illustrator)
            if m:
                illustrator = m.group(1)
            break
        description += " " + line.strip()

    metadata = {
        "id": title_file_content[0].strip(),
        "title": title,
        "episode": episode,
        "isSpecial": not episode.isdigit(),
        "date": datetime.strptime(dir_basename, "%Y%m%d").strftime("%Y-%m-%d"),
        "dayOfWeek": datetime.strptime(dir_basename, "%Y%m%d").strftime("%A"),
        "description": description,
        "illustrator": illustrator,
    }

    if metadata["dayOfWeek"] not in ["Monday", "Wednesday", "Friday"]:
        printer.print_warning(
            f"Episode aired on an unexpected day ({metadata['dayOfWeek']}). "
            + "Maybe a bug?",
            dir_basename,
        )

    return metadata


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

    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    args = parse_args()

    model = None
    model_no_prompt = None
    align_model = None
    align_metadata = None

    replacements = transcript.fetch_patterns(REPLACEMENTS_FILE)
    highlights = transcript.fetch_patterns(HIGHLIGHTS_FILE)

    # Iterate through the audio files in the source directory
    for root, _, files in os.walk(args.audio_dir):
        for file in files:
            if file.startswith(FILE_BASE_NAME):
                audio_path = os.path.join(root, file)
                if audio_path.endswith((".wave", ".wav")):
                    continue
                dir_basename = os.path.basename(os.path.dirname(audio_path))
                new_output_dir = os.path.join(args.output_dir, dir_basename)

                metadata = get_metadata(root, dir_basename)

                if not os.path.exists(new_output_dir):
                    os.makedirs(new_output_dir)

                with open(
                    os.path.join(new_output_dir, "metadata.json"), "w", encoding="utf-8"
                ) as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)

                if os.path.exists(os.path.join(new_output_dir, f"{NEW_BASE_NAME}.vtt")):
                    continue

                print(f"Transcribing '{audio_path}'...")

                # Convert audio files for easier transcription
                convert_to_wav(audio_path, CONVERT_BASE_NAME)
                audio_path = os.path.join(root, f"{CONVERT_BASE_NAME}.wav")

                # Load transcription models (if not already loaded)
                if model is None:
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

                # Transcript with prompt to create a more accurate transcript
                asr.transcribe_audio(
                    audio_path, model, align_model, align_metadata, new_output_dir
                )

                # Transcript without prompt can be used to fix potential errors when using prompt
                if args.include_no_prompt:
                    new_output_dir_no_prompt = os.path.join(new_output_dir, "noprompt")
                    if not os.path.exists(new_output_dir_no_prompt):
                        os.makedirs(new_output_dir_no_prompt)
                    if model_no_prompt is None:
                        model_no_prompt = whisperx.load_model(args.model, DEVICE)
                    asr.transcribe_audio(
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
                    printer.print_error("Transcript file not found", new_output_dir)
                    continue

                transcript.fix_mistakes(replacements, new_output_dir, transcript_file)
                transcript.highlight_ambiguities(
                    highlights, new_output_dir, transcript_file
                )

                if os.path.exists(os.path.join(new_output_dir, "summary.md")):
                    continue

                create_summary_draft(metadata, new_output_dir)


if __name__ == "__main__":
    main()
