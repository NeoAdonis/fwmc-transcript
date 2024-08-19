[CmdletBinding()]
param(
    [string]$URL,
    [string]$OutputFolder = (Get-Location),
    [switch]$DownloadVideo = $false
)


if (-not (Test-Path -Path $OutputFolder)) {
    New-Item -Path $OutputFolder -ItemType Directory | Out-Null
}

$DependenciesMet = $true
if (-not (Get-Command yt-dlp -ErrorAction SilentlyContinue)) {
    Write-Host "yt-dlp not found. Please make sure that yt-dlp is installed." -ForegroundColor Red
    $DependenciesMet = $false
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "ffmpeg not found. Please make sure that ffmpeg is installed." -ForegroundColor Red
    $DependenciesMet = $false
}
if (-not $DependenciesMet) {
    throw 'Dependencies not met'
}

# Download best source audio for better transcription and save some metadata
& yt-dlp -q --progress -f 'ba/b' -P $OutputFolder --download-archive (Join-Path $OutputFolder 'archive.txt') --match-filter "!is_live & live_status!=is_upcoming & availability=public" --print-to-file "%(id)s" "%(release_date)s/%(release_date)s.title" --print-to-file "%(title)s" "%(release_date)s/%(release_date)s.title" --write-description -o "description:%(release_date)s/%(release_date)s" --write-thumbnail -o "thumbnail:%(release_date)s/thumbnail" -o "%(release_date)s/audio.%(ext)s" -N 3 $URL

# An additional "NA" folder might have been created for scheduled streams that haven't started yet
Remove-Item -Path (Join-Path -Path $OutputFolder -ChildPath "NA") -Recurse -Force

# yt-dlp appends new info to title files if it exists already; keep only the latest info
Get-ChildItem -Path $OutputFolder -Filter "*.title" -Recurse | ForEach-Object { Get-Content -Path $_.FullName | Select-Object -Last 2 | Set-Content -Path $_.FullName }

# If specified, download smallest video with at least 480p resolution for reference
if ($DownloadVideo) {
    & yt-dlp -q --progress -f 'bv*[height>=480]+ba/b[height>=480]/bv*+ba/b' -S '+size,+br,+res,+fps' -P $OutputFolder -o "%(release_date)s/video.%(ext)s" -N 3 $URL
}
