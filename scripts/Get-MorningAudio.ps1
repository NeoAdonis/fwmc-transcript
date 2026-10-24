[CmdletBinding()]
param(
    [string]$CondaEnvironment = 'whisperx',
    [string]$Url = 'https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS',
    [string]$OutputDirectory = (Join-Path $PSScriptRoot '../morning/audio'),
    [switch]$DownloadVideo
)

& (Join-Path $PSScriptRoot 'Get-VideoAudio.ps1') $Url -OutputDirectory $OutputDirectory -DownloadVideo:$DownloadVideo -CondaEnvironment $CondaEnvironment
