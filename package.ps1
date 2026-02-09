# Build and package Digital Reverse Engine Player Edition

Write-Host "Cleaning old build..."
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

Write-Host "Running PyInstaller..."
pyinstaller dre_player.spec

$releaseName = "DigitalReverseEnginePlayer_v1.2.0"
$distPath = "dist/DigitalReverseEnginePlayer"
$zipPath = "$releaseName.zip"

Write-Host "Packaging release..."
if (Test-Path $zipPath) { Remove-Item $zipPath }

Compress-Archive -Path "$distPath\*" -DestinationPath $zipPath

Write-Host "Done!"
Write-Host "Created: $zipPath"
