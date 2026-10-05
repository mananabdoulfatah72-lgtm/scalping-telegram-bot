# Installe le bot 3 en 1 et l'export des transactions dans Quantower et/ou Optimus Flow (une version de Quantower),
# sous Windows. Lance par installer.bat (double-clic, ou glisser le dossier de la plateforme sur installer.bat).
param([string]$Dossier = "")
$ErrorActionPreference = "Stop"
Write-Host "Bot 3 en 1 : installation dans Quantower / Optimus Flow" -ForegroundColor Cyan
# 1. Plateformes installees et leur bibliotheque
$noms = @("Quantower", "Optimus Flow", "OptimusFlow")
$lieux = @("C:\", "D:\", $env:USERPROFILE, $env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)},
           "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Documents") | Where-Object { $_ }
$racines = @(foreach ($l in $lieux) { foreach ($n in $noms) { Join-Path $l $n } })
if ($Dossier) { $racines = @($Dossier.Trim('"')) + $racines }
$racines = @($racines | Where-Object { Test-Path $_ } | Select-Object -Unique)
if ($racines.Count -eq 0) {
    $Dossier = Read-Host "Quantower / Optimus Flow introuvable. Colle le chemin de son dossier d'installation (ex. C:\Optimus Flow)"
    $racines = @($Dossier.Trim('"') | Where-Object { $_ -and (Test-Path $_) })
}
$plateformes = @(foreach ($r in $racines) {
    $d = Get-ChildItem -Path $r -Recurse -Filter "TradingPlatform.BusinessLayer.dll" -ErrorAction SilentlyContinue |
         Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($d) {
        # dossier d'installation = celui qui contient TradingPlatform\<version>\bin
        $base = if ($d.DirectoryName -match '^(.*)\\TradingPlatform\\[^\\]+\\bin$') { $Matches[1] } else { $r }
        [pscustomobject]@{ Base = $base; Bin = $d.DirectoryName }
    }
}) | Sort-Object Bin -Unique
if (-not $plateformes) { throw "Bibliotheque introuvable. Lance Quantower ou Optimus Flow une fois, puis relance ce script." }
# 2. Kit .NET 8 (pour compiler), installe une seule fois
if (-not (Get-Command dotnet -ErrorAction SilentlyContinue) -or -not ((dotnet --list-sdks) -match "^8\.")) {
    Write-Host "Installation du kit .NET 8 (une seule fois)..."
    winget install --id Microsoft.DotNet.SDK.8 --silent --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
}
# 3. Pour chaque plateforme : compilation contre sa bibliotheque, copie dans ses strategies
foreach ($p in $plateformes) {
    Write-Host "Plateforme trouvee : $($p.Base)"
    dotnet build "$PSScriptRoot\Bot3en1.Quantower\Bot3en1.Quantower.csproj" -c Release --no-incremental -p:QuantowerBin="$($p.Bin)" -nologo
    if ($LASTEXITCODE -ne 0) { throw "La compilation a echoue : envoie la fenetre a Claude." }
    $dest = Join-Path $p.Base "Settings\Scripts\Strategies\Bot3en1"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item "$PSScriptRoot\Bot3en1.Quantower\bin\Release\net8.0\Bot3en1.dll" $dest -Force
    Write-Host "Installe dans $dest" -ForegroundColor Green
}
New-Item -ItemType Directory -Force -Path "C:\Bot3en1" | Out-Null
Write-Host "Redemarre la plateforme, puis : menu Strategies > Strategies manager > Bot 3 en 1 ou Export transactions NQ (voir le guide)."
