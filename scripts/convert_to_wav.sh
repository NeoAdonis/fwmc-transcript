#!/bin/bash

# Usage: convert_to_wav.sh [-s start_from] [-e end_at] path [new_base_name]
#   -s  Start timestamp (e.g. 00:01:30)
#   -e  End timestamp (e.g. 01:02:03)
#   path           Audio file to convert
#   new_base_name  Base name of the WAV file, written next to the source file
#                  (default: audio_converted)

start_from=''
end_at=''

usage() {
    echo "Usage: $0 [-s start_from] [-e end_at] path [new_base_name]" >&2
    exit 1
}

while getopts ':s:e:' option; do
    case "$option" in
        s) start_from="$OPTARG" ;;
        e) end_at="$OPTARG" ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))

if [[ $# -lt 1 || $# -gt 2 ]]; then
    usage
fi
path="$1"
new_base_name="${2:-audio_converted}"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Python not found. Please make sure that Python is installed and the right environment is activated." >&2
    exit 1
fi

# Use the same FFmpeg parameters as the Python scripts, without changing the
# working directory so that relative paths still work
script_directory="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$script_directory/../src${PYTHONPATH:+:$PYTHONPATH}" python -c '
import sys
from common.media import convert_to_wav
convert_to_wav(*sys.argv[1:])
' "$path" "$new_base_name" "$start_from" "$end_at"
