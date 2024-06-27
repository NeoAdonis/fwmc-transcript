[CmdletBinding()]
param(
    [string]$URL = 'https://www.youtube.com/playlist?list=PLf4O_VcbYo27DpnCJZXRsxov6_DD2Q1NS',
    [string]$OutputFolder = 'audio',
    [switch]$DownloadVideo = $false
)


..\common\Get-VideoAudio -URL $URL -OutputFolder $OutputFolder -DownloadVideo:$DownloadVideo

# Find the first time when there's a blank line after a non-blank line in the description files, then keep only the lines before that
Get-ChildItem -Path $OutputFolder -Filter "*.description" -Recurse | ForEach-Object {
    $DescriptionPath = $_.FullName
    $Content = Get-Content -Path $DescriptionPath
    for ($i = 1; $i -lt $Content.Length; $i++) {
        if ($Content[$i - 1] -ne '' -and $Content[$i] -eq '') {
            $Content[0..($i - 1)] | Set-Content -Path $DescriptionPath
            break
        }
    }
}

# Alternative method to find the first time when there's a specific header in the description files, then keep only the lines before that
# $Headers = @(
#     'Get your paws on hololive English -Advent- merchandise!',
#     'Submit your spooky stories here! 🎃🍬',
#     'Submit your Christmas memories here! 🎁',
#     'Mococo Abyssgard Birthday Celebration 2024 Goods! 🐾💖',
#     'Fuwawa Abyssgard Birthday Celebration 2024 Goods! 🐾💙',
#     '(∪･ω･∪ ♡：：：：：：：：：：：：：：：：♡ ∪･ω･∪)'
# )
# Get-ChildItem -Path $OutputFolder -Filter "*.description" -Recurse | ForEach-Object {
#     $DescriptionPath = $_.FullName
#     $Content = Get-Content -Path $DescriptionPath
#     $LowestIndex = $Content.Length
#     foreach ($Header in $Headers) {
#         $HeaderIndex = $Content.IndexOf($Header)
#         if ($HeaderIndex -ge 0) {
#             $LowestIndex = [math]::Min($LowestIndex, $HeaderIndex)
#         }
#     }
#     if ($LowestIndex -lt $Content.Length) {
#         $Content[0..($LowestIndex - 1)] | Set-Content -Path $DescriptionPath
#     }
# }
