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
        Write-Host "$($relativePath) - File too long ($length characters)."
    }
    $content = Get-Content $_.FullName
    $newContent = ''
    $contentChanged = $false
    $titles = @()
    $i = 0
    foreach ($line in $content) {
        $i++

        $errorYouTubeLinkUnshortened = $false
        foreach ($match in [regex]::Matches($line, '\bhttps:\/\/(?:www\.)youtube\.com\/watch\?([^\b]+)\b')) {
            $errorYouTubeLinkUnshortened = $true
            $newLink = ''
            foreach ($param in $match.Groups[1].Value.Split('&')) {
                switch -regex ($param) {
                    '^v=' {
                        $newLink = "https://youtu.be/$($param.Substring(2))" + $newLink
                        continue
                    }
                    '^t=' {
                        $newLink += "?$param"
                        continue
                    }
                    # Ignore other parameters
                }
            }
            $line = $line.Replace($match.Value, $newLink)
        }
        if ($errorYouTubeLinkUnshortened) {
            $contentChanged = $true
            Write-Host "$($_.Name):$i YouTube links should be shortened; fixed."
        }

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

    if ($titles -notcontains 'Introduction') {
        $newContent = "## Introduction (5:00)`n`n" + $newContent
        $contentChanged = $true
        Write-Host "$($relativePath) Missing Introduction; attempted to fix."
    }

    if ($contentChanged) {
        # $newContent | Set-Content $_.FullName -NoNewline
    }
}
