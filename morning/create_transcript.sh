#!/bin/bash

# Define the Conda environment
conda_environment="${1:-whisperx}"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "conda not found. Please make sure that Anaconda/Miniconda is properly installed." >&2
    exit 1
fi

# Activate the Conda environment
if ! conda_base="$(conda info --base)"; then
    echo "Could not determine the Conda base directory." >&2
    exit 1
fi
# shellcheck source=/dev/null
source "$conda_base/etc/profile.d/conda.sh"
if ! conda activate "$conda_environment"; then
    echo "Could not activate the Conda environment '$conda_environment'." >&2
    exit 1
fi

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Python not found. Please make sure that Python is properly installed in the Conda environment '$conda_environment'." >&2
    conda deactivate
    exit 1
fi

# Check if WhisperX is available
if ! command -v whisperx &> /dev/null; then
    echo "WhisperX not found. Please make sure that WhisperX is installed in the Conda environment '$conda_environment'." >&2
    conda deactivate
    exit 1
fi

python -m morning.create_transcript "${@:2}"
