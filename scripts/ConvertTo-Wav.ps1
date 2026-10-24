[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$Path,
    [Parameter(Position = 1)]
    [string]$NewBaseName = 'audio_converted',
    [string]$StartFrom = '',
    [string]$EndAt = '',
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

# Use the same FFmpeg parameters as the Python scripts, without changing the
# working directory so that relative paths still work
$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$previousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = (@((Join-Path $scriptDirectory '../src'), $env:PYTHONPATH) | Where-Object { $_ }) -join [IO.Path]::PathSeparator
try {
    # Windows PowerShell drops empty arguments and mangles embedded double quotes, so
    # the optional arguments are passed as keyword arguments only when they are set,
    # and the code only uses single quotes
    $code = 'import sys; from common.media import convert_to_wav; convert_to_wav(*sys.argv[1:3], **dict(a.split(''='', 1) for a in sys.argv[3:]))'
    $arguments = @($Path, $NewBaseName)
    if ($StartFrom) {
        $arguments += "start_from=$StartFrom"
    }
    if ($EndAt) {
        $arguments += "end_at=$EndAt"
    }
    & python -c $code @arguments
}
finally {
    $env:PYTHONPATH = $previousPythonPath
}
