#!/bin/bash

# Usage: get_morning_audio.sh [-u url] [-o output_directory] [-v]
#   -u  Playlist or video URL (default: the FWMC Morning playlist)
#   -o  Output directory (default: morning/audio at the repository root)
#   -v  Download the video along with the audio

script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
url='https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS'
output_directory="$script_directory/../morning/audio"
args=()

while getopts ':u:o:v' option; do
    case "$option" in
        u) url="$OPTARG" ;;
        o) output_directory="$OPTARG" ;;
        v) args+=(-v) ;;
        *)
            echo "Usage: $0 [-u url] [-o output_directory] [-v]" >&2
            exit 1
            ;;
    esac
done

bash "$script_directory/get_video_audio.sh" -o "$output_directory" "${args[@]}" "$url"
