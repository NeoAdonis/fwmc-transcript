$TranscriptsPath = "transcripts"
$SummariesPath = "summaries"
$Transcripts = Get-ChildItem -Path "transcripts" -Directory
$SummaryIndex = @()
$SummaryTable = @()

$SummaryIndex += "| Date |     | Episode | Summary | Transcript |"
$SummaryIndex += "| ---- | --- | ------- | ------- | ---------- |"

foreach ($TranscriptSubfolder in $Transcripts) {
    $EmojiList = Get-Content -Path './config/emojis.csv' | ConvertFrom-Csv
    $Summary = Get-Content -Path (Join-Path -Path $TranscriptSubfolder.FullName -ChildPath "summary.md")
    $NewSummary = @()
    $Metadata = Get-Content -Path (Join-Path -Path $TranscriptSubfolder.FullName -ChildPath "metadata.json") | ConvertFrom-Json
    $EpisodeName = if ($Metadata.isSpecial) { $Metadata.episode } else { "Episode $($Metadata.episode)" }
    $SummaryIndex += "| $($Metadata.date) | $($Metadata.dayOfWeek.SubString(0, 3)) | 📺 [$EpisodeName](https://youtu.be/$($Metadata.id)) | 📄 [Summary](./$SummariesPath/$($TranscriptSubfolder.Name).md) | 🔤 [Transcript](./$TranscriptsPath/$($TranscriptSubfolder.Name)/transcript.vtt) |"
    $SummaryTable += [PSCustomObject]@{
        'Date'        = $Metadata.date
        'Episode'     = $EpisodeName
        'Title'       = $Metadata.title
        'Description' = $Metadata.description
        'Illustrator' = $Metadata.illustrator
        'Link'        = "https://youtu.be/$($Metadata.id)"
    }
    foreach ($Line in $Summary) {
        if ($Line -match '^(#+) (.*)$') {
            $HeaderLevel = $Matches[1]
            $Header = $Matches[2]
            $Emoji = $EmojiList | ForEach-Object {
                if ($Header -match $_.Pattern) {
                    return $_.Emoji
                }
            }
            if (-not $Emoji) {
                $Emoji = "🎞️"
            }
            # TODO: Make this configurable if needed
            if ($HeaderLevel -ne "###" -and $EpisodeName -ne "friday the 13th")
            {
                $Header = "$Emoji $Header"
            }
            
            if ($Header -match '^(.*) \((\d+):(\d+)\)$') {
                $Timestamp = "[$($Matches[2]):$($Matches[3])](https://youtu.be/$($Metadata.id)?t=$($Matches[2])m$($Matches[3])s)"
                $Line = "$HeaderLevel $($Matches[1]) ($Timestamp)"
                if ($Header -match '^📺 Introduction') {
                    $Line = "# $EpisodeName (start: $Timestamp)"
                }
            }
        }
        $NewSummary += $Line
    }
    $NewSummary | Set-Content -Path (Join-Path -Path $SummariesPath -ChildPath "$($TranscriptSubfolder.Name).md")
}

$SummaryIndex | Set-Content -Path "index.md"
$SummaryTable | Sort-Object -Property 'Date' | Export-Csv -Path "index.csv"
