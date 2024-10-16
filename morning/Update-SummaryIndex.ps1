[CmdletBinding()]
param(
    [string]$TranscriptsFolder = "transcripts",
    [string]$SummariesFolder = "summaries"
)


$SummaryIndex = @()
$SummaryTable = @()

$LastUpdatedString = "Last updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm' -AsUTC) UTC"

$SummaryIndex += @("# 🌅 FUWAMOCO Morning Episode Summaries", "")
$SummaryIndex += @($LastUpdatedString, "")
$SummaryIndex += "| 🗓️ Date |     | 📺 Episode |     | 📄 Summary | 🔤 Transcript |"
$SummaryIndex += "| ------ | --- | --------- | --- | --------- | ------------ |"

$QuestionSummary = @("FUWAMOCO Morning Questions of the Day", "", $LastUpdatedString)

foreach ($TranscriptSubfolder in (Get-ChildItem -Path $TranscriptsFolder -Directory)) {
    $EmojiList = Get-Content -Path './config/emojis.csv' | ConvertFrom-Csv
    $Summary = Get-Content -Path (Join-Path -Path $TranscriptSubfolder.FullName -ChildPath "summary.md")
    $NewSummary = @()
    $Metadata = Get-Content -Path (Join-Path -Path $TranscriptSubfolder.FullName -ChildPath "metadata.json") | ConvertFrom-Json
    $EpisodeName = if ($Metadata.isSpecial) { $Metadata.episode } else { "Episode #$($Metadata.episode)" }
    $TranscriptPath = "$TranscriptsFolder/$($TranscriptSubfolder.Name)/transcript.vtt"
    $EpisodeLink = "https://youtu.be/$($Metadata.id)"
    $SummaryBaseName = "$($TranscriptSubfolder.Name) $($Metadata.episode)" -replace 'あさモコ', 'ASAMOCO' -replace '\s+', '_' -replace '[^a-zA-Z0-9_]', ''
    $SummaryIndex += "| $($Metadata.date) | $($Metadata.dayOfWeek.SubString(0, 3)) | [$EpisodeName]($EpisodeLink) | $($Metadata.description) | [Summary]($SummariesFolder/$SummaryBaseName.md) | [Transcript]($TranscriptPath) |"
    $SummaryTable += [PSCustomObject]@{
        'Date'        = $Metadata.date
        'Episode'     = $EpisodeName
        'Title'       = $Metadata.title
        'Description' = $Metadata.description
        'Illustrator' = $Metadata.illustrator
        'Link'        = $EpisodeLink
    }
    $EpisodeQuestion = ""
    $SkipFrontMatter = $false
    foreach ($Line in $Summary) {
        if ($SkipFrontMatter) {
            if ($Line -match '^---$') {
                $SkipFrontMatter = $false
            }
            continue
        }
        elseif ($Line -match '^---$') {
            $SkipFrontMatter = $true
            continue
        }
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
        # Remove all links to minimize file size
        $EpisodeQuestion = $EpisodeQuestion -replace '\[([^\]]+)\]\([^\)]+\)', '$1'
        $EpisodeQuestion = $EpisodeQuestion -replace '\*\*(\w[^\*]+)\*\*([.,]?)', '"$1$2"'
        $EpisodeQuestion = $EpisodeQuestion -replace '\*(\w[^\*]+)\*([.,]?)', '"$1$2"'
        $QuestionSummary += @("", "$EpisodeName — $(($EpisodeQuestion -replace '\s+', ' ').Trim())")
    }
    # Remove all empty lines at the beginning of the summary
    while ($NewSummary[0] -match '^\s*$') {
        $NewSummary = $NewSummary[1..$NewSummary.Count]
    }
    # Save the summary
    $NewSummary | Set-Content -Path (Join-Path -Path $SummariesFolder -ChildPath "$SummaryBaseName.md")
}

$CurrentIndex = Get-Content -Path "index.md"
$CurrentIndex = $CurrentIndex -replace '^Last updated: .*$', $LastUpdatedString
if (($CurrentIndex -join "`n") -ne ($SummaryIndex -join "`n")) {
    $SummaryIndex | Set-Content -Path "index.md"
    $SummaryTable | Sort-Object -Property 'Date' | Export-Csv -Path "index.csv"
    Write-Host "Index updated"
}
else {
    Write-Host "No changes to index"
}

$CurrentQuestions = (Get-Content -Path "questions.txt") -replace 'Last updated: .*$', $LastUpdatedString
if (($CurrentQuestions -join "`n") -ne ($QuestionSummary -join "`n")) {
    $QuestionSummary | Set-Content -Path "questions.txt"
    Write-Host "Questions summary updated"
}
else {
    Write-Host "No changes to questions summary"
}
