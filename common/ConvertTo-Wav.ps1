[CmdletBinding()]
param(
    [string]$Path,
    [string]$NewBaseName = 'audio_converted'
)


$ParentFolder = Split-Path -Path $Path -Parent
$ConvertedAudio = Join-Path $ParentFolder "$NewBaseName.wav"
if (-not (Test-Path -Path $ConvertedAudio)) {
    & ffmpeg -v warning -i $Path -vn -acodec pcm_s16le -ar 44100 -ac 2 $ConvertedAudio
}
