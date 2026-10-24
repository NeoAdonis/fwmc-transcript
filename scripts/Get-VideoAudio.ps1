[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Url,
    [string]$OutputDirectory = 'audio',
    [switch]$DownloadVideo,
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

# Use the same yt-dlp options as the Python scripts, without changing the working
# directory so that relative paths still work
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$previousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = (@((Join-Path $scriptDirectory '../src'), $env:PYTHONPATH) | Where-Object { $_ }) -join [IO.Path]::PathSeparator
try {
    # Windows PowerShell mangles embedded double quotes, so the code only uses
    # single quotes
    $code = 'import sys; from common.media import get_video_audio; sys.exit(0 if get_video_audio(sys.argv[1], sys.argv[2], sys.argv[3] == ''true'') else ''Some downloads failed; see the errors above.'')'
    $downloadVideoArgument = if ($DownloadVideo) { 'true' } else { 'false' }
    & python -c $code $Url $OutputDirectory $downloadVideoArgument
}
finally {
    $env:PYTHONPATH = $previousPythonPath
}
