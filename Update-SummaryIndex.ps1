$Transcripts = Get-ChildItem -Path "transcript" -Directory
$SummaryIndex = @()
$SummaryTable = @()

foreach ($TranscriptSubfolder in $Transcripts) {
    $Metadata = Get-Content -Path (Join-Path -Path $TranscriptSubfolder.FullName -ChildPath "metadata.json") | ConvertFrom-Json
    $EpisodeName = if ($Metadata.isSpecial) { $Metadata.episode } else { "Episode $($Metadata.episode)" }
    $SummaryIndex += "- $($Metadata.date) ($($Metadata.dayOfWeek.SubString(0, 2))): [$EpisodeName](https://youtu.be/$($Metadata.id)) - [Summary](./transcript/$($TranscriptSubfolder.Name)/summary.md)"
    $SummaryTable += [PSCustomObject]@{
        'Date'        = $Metadata.date
        'Episode'     = $EpisodeName
        'Title'       = $Metadata.title
        'Description' = $Metadata.description
        'Illustrator' = $Metadata.illustrator
        'Link'        = "https://youtu.be/$($Metadata.id)"
    }
}

$SummaryIndex | Set-Content -Path "index.md"
$SummaryTable | Sort-Object -Property 'Date' | Export-Csv -Path "index.csv"
