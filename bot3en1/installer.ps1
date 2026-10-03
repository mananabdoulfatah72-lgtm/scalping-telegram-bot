# Installe le bot 3 en 1 dans Quantower (Windows). Lance par installer.bat (double-clic).
$ErrorActionPreference = "Stop"
Write-Host "Bot 3 en 1 : installation dans Quantower" -ForegroundColor Cyan
# 1. Quantower et sa bibliotheque
$racines = @("C:\Quantower", "$env:USERPROFILE\Quantower", "$env:LOCALAPPDATA\Quantower", "$env:ProgramFiles\Quantower", "D:\Quantower") | Where-Object { Test-Path $_ }
$dll = $racines | ForEach-Object { Get-ChildItem -Path $_ -Recurse -Filter "TradingPlatform.BusinessLayer.dll" -ErrorAction SilentlyContinue } |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $dll) { throw "Quantower introuvable. Installe Quantower (lien dans le guide), lance-le une fois, puis relance ce script." }
$bin = $dll.DirectoryName
$base = $racines | Where-Object { $bin.StartsWith($_) } | Select-Object -First 1
Write-Host "Quantower trouve : $bin"
# 2. Kit .NET 8 (pour compiler), installe une seule fois
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue) -or -not ((dotnet --list-sdks) -match "^8\.")) {
    Write-Host "Installation du kit .NET 8 (une seule fois)..."
    winget install --id Microsoft.DotNet.SDK.8 --silent --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}
# 3. Compilation
dotnet build "$PSScriptRoot\Bot3en1.Quantower\Bot3en1.Quantower.csproj" -c Release -p:QuantowerBin="$bin" -nologo
if ($LASTEXITCODE -ne 0) { throw "La compilation a echoue : envoie la fenetre a Claude." }
# 4. Copie dans les strategies de Quantower et dossier des donnees
$dest = Join-Path $base "Settings\Scripts\Strategies\Bot3en1"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item "$PSScriptRoot\Bot3en1.Quantower\bin\Release\net8.0\Bot3en1.dll" $dest -Force
New-Item -ItemType Directory -Force -Path "C:\Bot3en1" | Out-Null
Write-Host "Installe dans $dest" -ForegroundColor Green
Write-Host "Redemarre Quantower, puis : menu Strategies > Strategies manager > Bot 3 en 1 (voir le guide)."
