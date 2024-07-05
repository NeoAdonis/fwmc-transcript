[CmdletBinding()]
param(
    [string]$TranscriptPath = './transcripts'
)


Get-ChildItem -Path $TranscriptPath -Recurse | Where-Object { $_.Name -eq "metadata.json" } | ForEach-Object {
    $Metadata = Get-Content $_.FullName | ConvertFrom-Json
    if ($Metadata.episode -eq '???') {
        Write-Host "$($_.FullName) Episode name/number not set" -ForegroundColor Red
    }
    if ($Metadata.episode -match '^\d+$' -and $Metadata.isSpecial) {
        Write-Host "$($_.FullName) Numbered episode marked as special" -ForegroundColor Red
    }
}

Get-ChildItem -Path $TranscriptPath -Directory | ForEach-Object {
    $summaryPath = Join-Path -Path $_.FullName -ChildPath "summary.md"
    if (-not (Test-Path -Path $summaryPath)) {
        Write-Host "$($_.FullName) No summary file found" -ForegroundColor Red
    }
}

& npm run lint-summaries

# TODO: Replace with markdownlint custom rules
Get-ChildItem -Path $TranscriptPath -Recurse | Where-Object { $_.Name -eq "summary.md" } | ForEach-Object {
    $length = (Get-Content $_.FullName | Measure-Object -Character).Characters
    $relativePath = [System.IO.Path]::GetRelativePath((Get-Location), $_.FullName)
    if ($length -gt 4000) {
        Write-Host "$($relativePath) - File too long ($length characters)"
    }
    $content = Get-Content $_.FullName
    $newContent = ''
    $titles = @()
    $i = 0
    foreach ($line in $content) {
        $i++
        # Check for duplicate titles
        if ($line -match '^## ') {
            $line -match '^## (.*) \(' | Out-Null
            $title = $Matches[1]
            if ($title) {
                if ($titles -contains $title) {
                    Write-Host "$($relativePath):$i Duplicate title: $title"
                }
                else {
                    $titles += $title
                }
            }
        }

        $newContent += $line + "`n"
    }

    # Check for missing introduction
    if ($titles -notcontains 'Introduction') {
        $newContent = "## Introduction (5:00)`n`n" + $newContent
        Write-Host "$($relativePath) Missing introduction"
    }
}
