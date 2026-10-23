#!/bin/bash

# Usage: get_morning_audio.sh [-u url] [-o output_directory] [-v]
#   -u  Playlist or video URL
#   -o  Output directory (relative to the morning directory)
#   -v  Download the video instead of audio only

url='https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS'
output_directory='audio'
download_video=false

while getopts ':u:o:v' option; do
    case "$option" in
        u) url="$OPTARG" ;;
        o) output_directory="$OPTARG" ;;
        v) download_video=true ;;
        *)
            echo "Usage: $0 [-u url] [-o output_directory] [-v]" >&2
            exit 1
            ;;
    esac
done

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Python not found. Please make sure that Python is installed and the right environment is activated." >&2
    exit 1
fi

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_directory/.." || exit 1

args=(--url "$url" --output_dir "$output_directory")
if [[ "$download_video" == true ]]; then
    args+=(--download_video)
fi

python -m morning.get_audio "${args[@]}"
