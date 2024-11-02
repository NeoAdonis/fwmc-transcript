[CmdletBinding()]
param(
    [string]$CondaEnvironment = 'whisperx'
)

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "conda not found. Please make sure that Anaconda/Miniconda is properly installed." -ForegroundColor Red
    throw 'conda not found'
}

& conda activate $CondaEnvironment

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found. Please make sure that Python is properly installed in the Conda environment '$CondaEnvironment'." -ForegroundColor Red
    & conda deactivate
    throw 'python not found'
}

if (-not (Get-Command whisperx -ErrorAction SilentlyContinue)) {
    Write-Host "WhisperX not found. Please make sure that WhisperX is installed in the Conda environment '$CondaEnvironment'." -ForegroundColor Red
    & conda deactivate
    throw 'whisperx not found'
}

& python create_morning_transcript.py
