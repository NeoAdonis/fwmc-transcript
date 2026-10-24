#!/bin/bash

# Usage: get_video_audio.sh [-o output_directory] [-v] url
#   -o   Output directory (default: audio)
#   -v   Download the video along with the audio
#   url  YouTube playlist or video URL

output_directory='audio'
download_video=false

usage() {
    echo "Usage: $0 [-o output_directory] [-v] url" >&2
    exit 1
}

while getopts ':o:v' option; do
    case "$option" in
        o) output_directory="$OPTARG" ;;
        v) download_video=true ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))

if [[ $# -ne 1 ]]; then
    usage
fi
url="$1"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Python not found. Please make sure that Python is installed and the right environment is activated." >&2
    exit 1
fi

# Use the same yt-dlp options as the Python scripts, without changing the working
# directory so that relative paths still work
script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$script_directory/../src${PYTHONPATH:+:$PYTHONPATH}" python -c '
import sys
from common.media import get_video_audio
if not get_video_audio(sys.argv[1], sys.argv[2], sys.argv[3] == "true"):
    sys.exit("Some downloads failed; see the errors above.")
' "$url" "$output_directory" "$download_video"
