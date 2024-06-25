[CmdletBinding()]
param(
    [string]$TranscriptsFolder = "transcripts",
    [string]$SummariesFolder = "summaries"
)


$SummaryIndex = @()
$SummaryTable = @()

$SummaryIndex += "| 🗓️ Date |     | 📺 Episode |     | 📄 Summary | 🔤 Transcript |"
$SummaryIndex += "| ------ | --- | --------- | --- | --------- | ------------ |"

$QuestionSummary = @("# Daily questions", "")

foreach ($TranscriptSubfolder in (Get-ChildItem -Path $TranscriptsFolder -Directory)) {
    $EmojiList = Get-Content -Path './config/emojis.csv' | ConvertFrom-Csv
    $Summary = Get-Content -Path (Join-Path -Path $TranscriptSubfolder.FullName -ChildPath "summary.md")
    $NewSummary = @()
    $Metadata = Get-Content -Path (Join-Path -Path $TranscriptSubfolder.FullName -ChildPath "metadata.json") | ConvertFrom-Json
    $EpisodeName = if ($Metadata.isSpecial) { $Metadata.episode } else { "Episode #$($Metadata.episode)" }
    $TranscriptPath = "$TranscriptsFolder/$($TranscriptSubfolder.Name)/transcript.vtt"
    $EpisodeLink = "https://youtu.be/$($Metadata.id)"
    $SummaryIndex += "| $($Metadata.date) | $($Metadata.dayOfWeek.SubString(0, 3)) | [$EpisodeName]($EpisodeLink) | $($Metadata.description) | [Summary]($SummariesFolder/$($TranscriptSubfolder.Name).md) | [Transcript]($TranscriptPath) |"
    $SummaryTable += [PSCustomObject]@{
        'Date'        = $Metadata.date
        'Episode'     = $EpisodeName
        'Title'       = $Metadata.title
        'Description' = $Metadata.description
        'Illustrator' = $Metadata.illustrator
        'Link'        = $EpisodeLink
    }
    $EpisodeQuestion = ""
    foreach ($Line in $Summary) {
        if ($Line -match '^(#+) (.*)$') {
            $HeaderLevel = $Matches[1]
            $Header = $CurrentSection = $Matches[2]
            $Emoji = "🎞️"
            foreach ($EmojiEntry in $EmojiList) {
                if ($Header -match $EmojiEntry.Pattern) {
                    $Emoji = $EmojiEntry.Emoji
                    break
                }
            }
            # TODO: Make this configurable if needed
            if ($HeaderLevel -ne "###" -and $EpisodeName -ne "friday the 13th")
            {
                $Header = "$Emoji $Header"
            }
            
            if ($Header -match '^(.*) \((\d+):(\d+)\)$') {
                $Timestamp = "[$($Matches[2]):$($Matches[3])]($($EpisodeLink)?t=$($Matches[2])m$($Matches[3])s)"
                $Line = "$HeaderLevel $($Matches[1]) ($Timestamp)"
                if ($CurrentSection -match '^Introduction') {
                    $Line = "# $EpisodeName (start: $Timestamp)"
                }
            }
        }
        elseif ($CurrentSection -match '^Question of the Day') {
            $EpisodeQuestion += $Line
        }
        $NewSummary += $Line
    }
    # Skip Episode #0 as no question was asked
    if ($EpisodeQuestion -and $EpisodeName -ne "Episode #0") {
        # Replace the author's name with a generic name
        $EpisodeQuestion = $EpisodeQuestion.Trim() -replace '^\[[^\]]+\]\([^\)]+\)', 'A Ruffian'
        # Remove all other links
        $EpisodeQuestion = $EpisodeQuestion -replace '\[([^\]]+)\]\([^\)]+\)', '$1'
        $QuestionSummary += @("## $EpisodeName", "", ($EpisodeQuestion -replace '\s+', ' ').Trim(), "")
    }
    $NewSummary | Set-Content -Path (Join-Path -Path $SummariesFolder -ChildPath "$($TranscriptSubfolder.Name).md")
}

$SummaryIndex | Set-Content -Path "index.md"
$SummaryTable | Sort-Object -Property 'Date' | Export-Csv -Path "index.csv"
$QuestionSummary | Set-Content -Path "questions.md"
