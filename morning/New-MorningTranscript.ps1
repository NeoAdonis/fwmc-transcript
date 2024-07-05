[CmdletBinding()]
param(
    [string]$SourceFolder = 'audio',
    [string]$OutputFolder = 'transcripts',
    [string]$WhisperXEnvironment = 'whisperx',
    [string]$Model = 'large-v2', # This model *seems* to work better than "large-v3" for FUWAMOCO Morning
    [string]$PromptPath = './config/transcript-prompt.txt',
    [switch]$IncludeNoPrompt = $false
)


# Prompt to use to help WhisperX with the transcription
$TranscriptPrompt = Get-Content -Path $PromptPath -Raw

$FileBaseName = 'audio'
$NewBaseName = 'transcript'

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    Write-Host "conda not found. Please make sure that Anaconda/Miniconda is properly installed." -ForegroundColor Red
    throw 'conda not found'
}

& conda activate $WhisperXEnvironment

if (-not (Get-Command whisperx -ErrorAction SilentlyContinue)) {
    Write-Host "WhisperX not found. Please make sure that WhisperX is installed in the Conda environment '$WhisperXEnvironment'." -ForegroundColor Red
    & conda deactivate
    throw 'whisperx not found'
}

foreach ($Audio in (Get-ChildItem -Path $SourceFolder -Filter "$FileBaseName.wav" -Recurse)) {
    $ParentFolderName = $Audio.Directory.Name
    $NewOutputFolder = Join-Path -Path $OutputFolder -ChildPath $ParentFolderName

    $TitleFileContent = Get-Content -Path (Join-Path -Path $Audio.Directory.FullName -ChildPath "$ParentFolderName.title")
    $DescriptionFileContent = @(Get-Content -Path (Join-Path -Path $Audio.Directory.FullName -ChildPath "$ParentFolderName.description"))

    $Title = $TitleFileContent[1]
    $Episode = switch -regex ($Title) {
        '^【FUWAMOCO MORNING】\s*episode (\d+)' {
            $Matches[1]
            continue
        }
        '^【FUWAMOCO MORNING】\s*([\w\s\p{P}]+)' {
            $Matches[1].Trim()
            continue
        }
        # Do not confuse the circle brackets with the square ones
        '^【([^】]+)】' {
            $Matches[1]
            continue
        }
        default {
            '???'
        }
    }
    $Description = $DescriptionFileContent[0]
    $Illustrator = 'rswxx' # Icomochi, FUWAMOCO designer
    for ($i = 1; $i -lt $DescriptionFileContent.Count; $i++) {
        if ($DescriptionFileContent[$i] -match '\billust') {
            $Illustrator = $DescriptionFileContent[$i] -replace '.*@(\w+).*', '$1'
            break
        }
        $Description += " " + $DescriptionFileContent[$i]
    }

    $Metadata = [PSCustomObject]@{
        'id'          = $TitleFileContent[0]
        'title'       = $Title
        'episode'     = $Episode
        'isSpecial'   = $Episode -notmatch '^\d+$' # Every episode is special, but they're more special when they're non-numbered one-offs
        'date'        = [datetime]::ParseExact($ParentFolderName, 'yyyyMMdd', $null).ToString('yyyy-MM-dd')
        'dayOfWeek'   = [datetime]::ParseExact($ParentFolderName, 'yyyyMMdd', $null).DayOfWeek.ToString()
        'description' = $Description
        'illustrator' = $Illustrator
    }

    if ($Metadata.dayOfWeek -notin @([DayOfWeek]::Monday, [DayOfWeek]::Wednesday, [DayOfWeek]::Friday)) {
        Write-Host "Episode aired on an unexpected day ($($Metadata.dayOfWeek)). Maybe a bug?" -ForegroundColor Yellow
    }

    if (-not (Test-Path -Path $NewOutputFolder)) {
        New-Item -Path $NewOutputFolder -ItemType Directory | Out-Null
    }

    $Metadata | ConvertTo-Json | Set-Content -Path (Join-Path -Path $NewOutputFolder -ChildPath 'metadata.json')

    if (Test-Path -Path (Join-Path -Path $NewOutputFolder -ChildPath "$NewBaseName.vtt")) {
        continue
    }

    Write-Host "Transcribing '$Audio'..."

    # Transcript with prompt to create a more accurate transcript
    & whisperx --model $Model --batch_size 16 -o $NewOutputFolder --output_format vtt --verbose False --language en --initial_prompt $TranscriptPrompt $Audio.FullName 

    # Transcript without prompt can be used to fix potential errors when using the prompt
    if ($IncludeNoPrompt.IsPresent) {
        $NewOutputFolderNoPrompt = Join-Path -Path $NewOutputFolder -ChildPath 'noprompt'
        if (-not (Test-Path -Path $NewOutputFolderNoPrompt)) {
            New-Item -Path $NewOutputFolderNoPrompt -ItemType Directory | Out-Null
        }
        & whisperx --model $Model --batch_size 16 -o $NewOutputFolderNoPrompt --output_format vtt --verbose False --language en $Audio.FullName
    }

    Get-ChildItem -Path $NewOutputFolder -Recurse | Where-Object { $_.BaseName -eq $NewBaseName } | ForEach-Object { Remove-Item -Path $_.FullName }
    Get-ChildItem -Path $NewOutputFolder -Recurse | Where-Object { $_.BaseName -eq $FileBaseName } | ForEach-Object { Rename-Item -Path $_.FullName -NewName ($NewBaseName + $_.Extension) }

    $TranscriptFile = Get-ChildItem -Path $NewOutputFolder | Where-Object { $_.BaseName -eq $NewBaseName } | Select-Object -First 1
    if (-not $TranscriptFile) {
        Write-Host "Transcript file not found in '$NewOutputFolder'." -ForegroundColor Red
        continue
    }

    # Fix common mistakes in the transcript
    $TranscriptContent = Get-Content -Path $TranscriptFile.FullName -Raw
    Get-Content -Path './config/replacements.csv' | ConvertFrom-Csv | ForEach-Object {
        $TranscriptContent = $TranscriptContent -replace $_.Pattern, $_.Replacement
    }
    $TranscriptContent | Set-Content -Path $TranscriptFile.FullName -NoNewline

    # Detect and highlight potential mistakes that might actually be correct for manual review
    $TranscriptContent = $TranscriptContent -split '\r?\n'
    Get-Content -Path './config/highlights.csv' | ConvertFrom-Csv | ForEach-Object {
        $Reason = $_.Reason
        $TranscriptContent | Select-String -Pattern $_.Pattern -AllMatches -Context 1 | ForEach-Object {
            $LineNumber = $_.LineNumber
            Write-Host "$TranscriptFile@$LineNumber - $Reason" -ForegroundColor Yellow
            Write-Host $_.ToEmphasizedString('')
        }
    }

    if ($TranscriptContent -notmatch 'Hello,? hello,? BAU BAU') {
        Write-Host "$TranscriptFile - Potential missing introduction" -ForegroundColor Yellow
    }

    if (Test-Path -Path (Join-Path -Path $NewOutputFolder -ChildPath "summary.md")) {
        continue
    }

    $SummaryDraft = @(
        "---",
        "episode: $(if ($Metadata.isSpecial) { $Metadata.episode | ConvertTo-Json } else { $Metadata.episode })",
        "date: $($Metadata.date)",
        "wip: true",
        "---",
        "",
        "## Sections",
        "",
        "- Introduction",
        "- Pero Sighting",
        "- Mococo Pup Talk",
        "- Doggie Of The Day",
        "- Today I Went On A Walk",
        "- Question Of The Day",
        "- Next Stream & Schedule",
        "- Thanks & Extra Special Ruffians"
    )

    $SummaryDraft | Set-Content -Path (Join-Path -Path $NewOutputFolder -ChildPath "summary.md")
}

& conda deactivate
