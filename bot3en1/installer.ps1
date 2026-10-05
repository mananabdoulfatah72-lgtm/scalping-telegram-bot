# Installe le bot 3 en 1 et l'export des transactions dans Quantower et/ou Optimus Flow (une version de Quantower),
# sous Windows. Lance par installer.bat (double-clic, ou glisser le dossier de la plateforme sur installer.bat).
param([string]$Dossier = "")
$ErrorActionPreference = "Stop"
# tout ce qui s'affiche est aussi ecrit sur le bureau, pour pouvoir l'envoyer meme si la fenetre se ferme
$journal = Join-Path ([Environment]::GetFolderPath("Desktop")) "installation_bot3en1.txt"
try { Start-Transcript -Path $journal -Force | Out-Null } catch { }
try {
Write-Host "Bot 3 en 1 : installation dans Quantower / Optimus Flow" -ForegroundColor Cyan
# 1. Plateformes installees et leur bibliotheque
$noms = @("Quantower", "Optimus Flow", "OptimusFlow")
$lieux = @("C:\", "D:\", $env:USERPROFILE, $env:LOCALAPPDATA, $env:ProgramFiles, ${env:ProgramFiles(x86)},
           "$env:USERPROFILE\Desktop", "$env:USERPROFILE\Documents") | Where-Object { $_ -and (Test-Path $_) }
# pas de Join-Path ici : il plante si un lecteur (ex. D:) n'existe pas
$racines = @(foreach ($l in $lieux) { foreach ($n in $noms) { $l.TrimEnd('\') + '\' + $n } })
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
# 2. Kit .NET de la bonne version (Quantower et Optimus Flow recents sont en .NET 10), installe une seule fois
function Assurer-Kit([int]$v) {
    $ok = $false
    if (Get-Command dotnet -ErrorAction SilentlyContinue) { $ok = [bool]((dotnet --list-sdks) -match "^$v\.") }
    if (-not $ok) {
        Write-Host "Installation du kit .NET $v (une seule fois, quelques minutes)..."
        winget install --id "Microsoft.DotNet.SDK.$v" --silent --accept-package-agreements --accept-source-agreements | Out-Host
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
    }
}
$projet = "$PSScriptRoot\Bot3en1.Quantower\Bot3en1.Quantower.csproj"
# 3. Pour chaque plateforme : compilation contre sa bibliotheque et sa version de .NET, copie dans ses strategies
foreach ($p in $plateformes) {
    Write-Host "Plateforme trouvee : $($p.Base)"
    $tfm = "net8.0"
    $cfg = Get-ChildItem -Path $p.Bin -Filter "*.runtimeconfig.json" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cfg) {
        try { $t = (Get-Content $cfg.FullName -Raw | ConvertFrom-Json).runtimeOptions.tfm; if ($t -match '^net\d+\.\d+$') { $tfm = $t } } catch { }
    }
    $code = 1
    for ($essai = 0; $essai -lt 2 -and $code -ne 0; $essai++) {
        if ($essai -eq 1) {
            # la bibliotheque demande une version plus recente de .NET (erreur CS1705) : on la lit dans l'erreur
            $v = [regex]::Matches(($sortie -join "`n"), "System\.Runtime, Version=(\d+)\.0\.0\.0") | ForEach-Object { [int]$_.Groups[1].Value }
            $max = ($v | Measure-Object -Maximum).Maximum
            if (-not $max -or "net$max.0" -eq $tfm) { break }
            $tfm = "net$max.0"
            Write-Host "La plateforme demande $tfm : nouvel essai"
        }
        Write-Host "Version de .NET utilisee : $tfm"
        Assurer-Kit ([int]($tfm -replace '^net(\d+)\..*$', '$1'))
        Remove-Item -Recurse -Force "$PSScriptRoot\Bot3en1.Quantower\obj", "$PSScriptRoot\Bot3en1.Quantower\bin" -ErrorAction SilentlyContinue
        dotnet restore $projet -p:TargetFramework=$tfm -p:QuantowerBin="$($p.Bin)" | Out-Host
        dotnet build $projet -c Release --no-restore -p:TargetFramework=$tfm -p:QuantowerBin="$($p.Bin)" -nologo | Tee-Object -Variable sortie | Out-Host
        $code = $LASTEXITCODE
    }
    if ($code -ne 0) { throw "La compilation a echoue : envoie le fichier installation_bot3en1.txt a Claude." }
    $dest = Join-Path $p.Base "Settings\Scripts\Strategies\Bot3en1"
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item "$PSScriptRoot\Bot3en1.Quantower\bin\Release\$tfm\Bot3en1.dll" $dest -Force
    Write-Host "Installe dans $dest" -ForegroundColor Green
}
New-Item -ItemType Directory -Force -Path "C:\Bot3en1" | Out-Null
Write-Host "Redemarre la plateforme, puis : menu Strategies > Strategies manager > Bot 3 en 1 ou Export transactions NQ (voir le guide)."
Write-Host "INSTALLATION TERMINEE" -ForegroundColor Green
}
catch {
    Write-Host ""
    Write-Host "ERREUR : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Envoie a Claude le fichier installation_bot3en1.txt qui est sur ton bureau." -ForegroundColor Yellow
}
finally {
    try { Stop-Transcript | Out-Null } catch { }
}
