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
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
$kitLocal = Join-Path $env:LOCALAPPDATA "Microsoft\dotnet"     # kit installe par le script de Microsoft (sans winget)
if (Test-Path (Join-Path $kitLocal "dotnet.exe")) { $env:Path = "$kitLocal;" + $env:Path }
function Kit-Present([int]$v) {
    if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) { return $false }
    return [bool]((dotnet --list-sdks) -match "^$v\.")
}
function Assurer-Kit([int]$v) {
    if (Kit-Present $v) { return }
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Installation du kit .NET $v (une seule fois, quelques minutes)..."
        $ancien = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        try { winget install --id "Microsoft.DotNet.SDK.$v" --silent --accept-package-agreements --accept-source-agreements | Out-Host }
        finally { $ErrorActionPreference = $ancien }
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        if (Test-Path (Join-Path $kitLocal "dotnet.exe")) { $env:Path = "$kitLocal;" + $env:Path }
        if (Kit-Present $v) { return }
    }
    # pas de winget (Windows Server 2022 des serveurs loues, par exemple) ou echec : script officiel de Microsoft
    Write-Host "Installation du kit .NET $v avec le script de Microsoft (une seule fois, quelques minutes)..."
    $script = Join-Path $env:TEMP "dotnet-install.ps1"
    $ProgressPreference = "SilentlyContinue"
    try { Invoke-WebRequest "https://dot.net/v1/dotnet-install.ps1" -OutFile $script -UseBasicParsing }
    catch { Invoke-WebRequest "https://raw.githubusercontent.com/dotnet/install-scripts/main/src/dotnet-install.ps1" -OutFile $script -UseBasicParsing }
    & $script -Channel "$v.0" -InstallDir $kitLocal -NoPath
    $env:Path = "$kitLocal;" + $env:Path
    if (-not (Kit-Present $v)) { throw "le kit .NET $v n'a pas pu etre installe" }
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
    # FluxNQ (bot order flow) : compile a part ; s'il echoue, le bot 3 en 1 reste installe
    $flux = "$PSScriptRoot\Flux.Quantower\Flux.Quantower.csproj"
    if (Test-Path $flux) {
        Remove-Item -Recurse -Force "$PSScriptRoot\Flux.Quantower\obj", "$PSScriptRoot\Flux.Quantower\bin" -ErrorAction SilentlyContinue
        $ancien = $ErrorActionPreference; $ErrorActionPreference = "Continue"
        dotnet restore $flux -p:TargetFramework=$tfm -p:QuantowerBin="$($p.Bin)" | Out-Host
        dotnet build $flux -c Release --no-restore -p:TargetFramework=$tfm -p:QuantowerBin="$($p.Bin)" -nologo | Out-Host
        $codeFlux = $LASTEXITCODE
        $ErrorActionPreference = $ancien
        if ($codeFlux -eq 0) {
            $destFlux = Join-Path $p.Base "Settings\Scripts\Strategies\FluxNQ"
            New-Item -ItemType Directory -Force -Path $destFlux | Out-Null
            Copy-Item "$PSScriptRoot\Flux.Quantower\bin\Release\$tfm\FluxNQ.dll" $destFlux -Force
            Write-Host "FluxNQ installe dans $destFlux" -ForegroundColor Green
        } else {
            Write-Host "ATTENTION : FluxNQ n'a pas compile (le bot 3 en 1 est bien installe). Envoie installation_bot3en1.txt a Claude." -ForegroundColor Yellow
        }
    }
}
New-Item -ItemType Directory -Force -Path "C:\Bot3en1" | Out-Null
Write-Host "Redemarre la plateforme, puis : menu Strategies > Strategies manager > Bot 3 en 1, Export transactions NQ ou FluxNQ (voir le guide)."
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
