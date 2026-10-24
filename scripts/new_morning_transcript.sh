#!/bin/bash

# Usage: new_morning_transcript.sh [-a audio_directory] [-o output_directory] [-m model] [-n]
#   -a  Audio directory (relative to the morning directory)
#   -o  Output directory (relative to the morning directory)
#   -m  WhisperX model
#   -n  Include the transcript without prompt

audio_directory='audio'
output_directory='transcripts'
model='large-v2'
include_no_prompt=false

while getopts ':a:o:m:n' option; do
    case "$option" in
        a) audio_directory="$OPTARG" ;;
        o) output_directory="$OPTARG" ;;
        m) model="$OPTARG" ;;
        n) include_no_prompt=true ;;
        *)
            echo "Usage: $0 [-a audio_directory] [-o output_directory] [-m model] [-n]" >&2
            exit 1
            ;;
    esac
done

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Python not found. Please make sure that Python is installed and the right environment is activated." >&2
    exit 1
fi

# Check if WhisperX is available
if ! command -v whisperx &> /dev/null; then
    echo "WhisperX not found. Please make sure that WhisperX is installed in the active environment." >&2
    exit 1
fi

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_directory/../src" || exit 1

args=(--audio_dir "$audio_directory" --output_dir "$output_directory" --model "$model")
if [[ "$include_no_prompt" == true ]]; then
    args+=(--include_no_prompt)
fi

python -m morning.create_transcript "${args[@]}"
