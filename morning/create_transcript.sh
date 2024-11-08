#!/bin/bash

# Define the Conda environment
conda_environment="${1:-whisperx}"

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "conda not found. Please make sure that Anaconda/Miniconda is properly installed." >&2
    exit 1
fi

# Activate the Conda environment
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$conda_environment"

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