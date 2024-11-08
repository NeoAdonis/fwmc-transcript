[CmdletBinding()]
param(
    [string]$CondaEnvironment = 'whisperx',
    [string]$Url = 'https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS',
    [string]$OutputDirectory = 'audio',
    [switch]$DownloadVideo
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

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $scriptDirectory "..")
& python -m morning.get_audio --url $Url --output_dir $OutputDirectory --download_video $DownloadVideo
Set-Location $scriptDirectory
