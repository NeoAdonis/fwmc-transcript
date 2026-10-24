[CmdletBinding()]
param(
    [string]$CondaEnvironment = 'whisperx',
    [string]$AudioDirectory = 'audio',
    [string]$OutputDirectory = 'transcripts',
    [string]$Model = 'large-v2',
    [switch]$IncludeNoPrompt
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

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location (Join-Path $scriptDirectory "../src")
$arguments = @('--audio_dir', $AudioDirectory, '--output_dir', $OutputDirectory, '--model', $Model)
if ($IncludeNoPrompt) {
    $arguments += '--include_no_prompt'
}
& python -m morning.create_transcript @arguments
Pop-Location
