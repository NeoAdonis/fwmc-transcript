[CmdletBinding()]
param(
    [string]$TranscriptPath = './transcripts'
)


# Basic metadata checks
Get-ChildItem -Path $TranscriptPath -Recurse | Where-Object { $_.Name -eq "metadata.json" } | ForEach-Object {
    $Metadata = Get-Content $_.FullName | ConvertFrom-Json
    $relativePath = [System.IO.Path]::GetRelativePath((Get-Location), $_.FullName)
    if ($Metadata.episode -eq '???') {
        Write-Host "$($relativePath) - Episode name/number not set" -ForegroundColor Red
    }
    if ($Metadata.episode -match '^\d+$' -and $Metadata.isSpecial) {
        Write-Host "$($relativePath) - Numbered episode marked as special" -ForegroundColor Red
    }
}

# Check for missing summary files
Get-ChildItem -Path $TranscriptPath -Directory | ForEach-Object {
    $summaryPath = Join-Path -Path $_.FullName -ChildPath "summary.md"
    $relativePath = [System.IO.Path]::GetRelativePath((Get-Location), $summaryPath)
    if (-not (Test-Path -Path $summaryPath)) {
        Write-Host "$($relativePath) - No summary file found" -ForegroundColor Red
    }
}

# Check summaries formatting
& npm run lint-summaries

# Check for long summaries
Get-ChildItem -Path $TranscriptPath -Recurse | Where-Object { $_.Name -eq "summary.md" } | ForEach-Object {
    $length = (Get-Content $_.FullName | Measure-Object -Character).Characters
    $relativePath = [System.IO.Path]::GetRelativePath((Get-Location), $_.FullName)
    if ($length -gt 4000) {
        Write-Host "$($relativePath) - File too long ($length characters)" -ForegroundColor Yellow
    }
}
