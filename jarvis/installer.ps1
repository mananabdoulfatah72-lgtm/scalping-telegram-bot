# Installe Jarvis sous Windows 10 ou 11 : Python 3.12 si besoin, un environnement à part, les modules, les modèles
# de voix, la configuration et un raccourci sur le Bureau. Lancé par installer.bat (double-clic).
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"          # la barre de progression rend les téléchargements très lents
try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
$journal = Join-Path ([Environment]::GetFolderPath("Desktop")) "installation_jarvis.txt"
try { Start-Transcript -Path $journal -Force | Out-Null } catch { }
try {
Write-Host "=== Installation de Jarvis ===" -ForegroundColor Cyan
$ici = Split-Path -Parent $MyInvocation.MyCommand.Path
$base = Join-Path $env:LOCALAPPDATA "Jarvis"
$venv = Join-Path $base "venv"
$donnees = Join-Path $env:APPDATA "Jarvis"
New-Item -ItemType Directory -Force -Path $base, $donnees | Out-Null

# Programme Python lancé sans s'arrêter sur ses messages d'avertissement (Windows PowerShell 5.1 prend chaque ligne
# écrite sur la sortie d'erreur pour une erreur fatale). Renvoie le code de sortie.
function Calme([string]$exe, [string[]]$arguments) {
    $ancien = $ErrorActionPreference; $ErrorActionPreference = "Continue"
    try { & $exe @arguments 2>$null | Out-Host } finally { $ErrorActionPreference = $ancien }
    return $LASTEXITCODE
}

# 1. Python 3.12 (ou 3.11)
function Trouver-Python {
    foreach ($v in @("3.12", "3.11")) {
        try {
            $ancien = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            $p = & py "-$v" -c "import sys; print(sys.executable)" 2>$null
            $ErrorActionPreference = $ancien
            if ($LASTEXITCODE -eq 0 -and $p) { return "$p".Trim() }
        } catch { $ErrorActionPreference = "Stop" }
    }
    foreach ($c in @("$env:LOCALAPPDATA\Programs\Python\Python312\python.exe", "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
                     "$env:ProgramFiles\Python312\python.exe", "$env:ProgramFiles\Python311\python.exe")) {
        if (Test-Path $c) { return $c }
    }
    return $null
}
$python = Trouver-Python
if (-not $python) {
    Write-Host "Installation de Python 3.12 (une seule fois, quelques minutes)..."
    $ok = $false
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Calme "winget" @("install", "--id", "Python.Python.3.12", "--silent", "--scope", "user", "--accept-package-agreements", "--accept-source-agreements") | Out-Null
        $python = Trouver-Python
    }
    if (-not $python) {                           # pas de winget (ou échec) : l'installateur officiel de python.org
        $fichier = Join-Path $env:TEMP "python-3.12.10-amd64.exe"
        Invoke-WebRequest "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe" -OutFile $fichier -UseBasicParsing
        Start-Process $fichier -ArgumentList "/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_launcher=1" -Wait
        $python = Trouver-Python
    }
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $python) { throw "Python introuvable après l'installation : redémarre le PC et relance l'installation." }
}
Write-Host "Python : $python"

# 2. Environnement de Jarvis et modules
if (-not (Test-Path (Join-Path $venv "Scripts\python.exe"))) { Calme $python @("-m", "venv", $venv) | Out-Null }
$py = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Impossible de créer l'environnement de Jarvis dans $venv." }
Calme $py @("-m", "pip", "install", "--upgrade", "pip", "--quiet") | Out-Null
Write-Host "Modules de base (quelques minutes)..."
$ancien = $ErrorActionPreference; $ErrorActionPreference = "Continue"
& $py -m pip install -e $ici --quiet                # erreurs affichées : utiles si ça échoue
$code = $LASTEXITCODE; $ErrorActionPreference = $ancien
if ($code -ne 0) { throw "Installation des modules de base impossible (voir le journal sur le Bureau)." }
$groupes = [ordered]@{
    "voix" = @("sounddevice", "faster-whisper", "openwakeword", "webrtcvad-wheels", "pyttsx3", "piper-tts");
    "Windows (son précis)" = @("pycaw", "comtypes");
    "Google (agenda, Gmail)" = @("google-api-python-client", "google-auth-oauthlib");
    "OBS" = @("obsws-python"); "appels Twilio" = @("twilio"); "navigateur" = @("playwright");
    "carte NVIDIA" = @("nvidia-ml-py")
}
foreach ($g in $groupes.Keys) {
    foreach ($m in $groupes[$g]) {
        Write-Host "  $g : $m"
        if ((Calme $py @("-m", "pip", "install", $m, "--quiet")) -ne 0) {
            Write-Host "    (échec : $m ne sera pas disponible)" -ForegroundColor Yellow
        }
    }
}

# 3. Modèles : mot de réveil, transcription, voix
Write-Host "Modèle du mot de réveil « Hey Jarvis »..."
Calme $py @("-c", "import openwakeword.utils as u; u.download_models(['hey_jarvis'])") | Out-Null
Write-Host "Modèle de transcription (environ 500 Mo, une seule fois : patiente quelques minutes)..."
Calme $py @("-c", "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8'); print('  prêt')") | Out-Null
Write-Host "Essai de la carte graphique pour la transcription..."
Calme $py @("-c", "from jarvis.voix.reconnaissance import cuda_utilisable; print('  transcription sur la carte graphique' if cuda_utilisable('small') else '  transcription sur le processeur')") | Out-Null
$dossierVoix = Join-Path $donnees "voix"
New-Item -ItemType Directory -Force -Path $dossierVoix | Out-Null
$voixChoisie = ""
foreach ($v in @(@("fr_FR-tom-medium", "fr/fr_FR/tom/medium"), @("fr_FR-siwis-medium", "fr/fr_FR/siwis/medium"))) {
    $nom = $v[0]; $url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/$($v[1])/$nom"
    try {
        if (-not (Test-Path (Join-Path $dossierVoix "$nom.onnx"))) {
            Write-Host "Voix $nom..."
            Invoke-WebRequest "$url.onnx" -OutFile (Join-Path $dossierVoix "$nom.onnx") -UseBasicParsing
            Invoke-WebRequest "$url.onnx.json" -OutFile (Join-Path $dossierVoix "$nom.onnx.json") -UseBasicParsing
        }
        $voixChoisie = $nom; break
    } catch { Write-Host "  voix $nom indisponible" -ForegroundColor Yellow }
}

# 4. Configuration
$config = Join-Path $donnees "config.toml"
if (-not (Test-Path $config)) {
    $texte = Get-Content (Join-Path $ici "config.exemple.toml") -Raw -Encoding UTF8
    if ($voixChoisie) { $texte = $texte -replace 'voix_piper = "fr_FR-tom-medium"', "voix_piper = `"$voixChoisie`"" }
    [IO.File]::WriteAllText($config, $texte, (New-Object Text.UTF8Encoding $false))
    Write-Host "Configuration créée : $config" -ForegroundColor Green
}

# 5. Raccourcis
$lanceur = Join-Path $ici "lancer.bat"
$shell = New-Object -ComObject WScript.Shell
$raccourci = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Desktop")) "Jarvis.lnk"))
$raccourci.TargetPath = $lanceur; $raccourci.WorkingDirectory = $ici; $raccourci.WindowStyle = 7
$raccourci.IconLocation = "$env:SystemRoot\System32\shell32.dll,170"; $raccourci.Save()
$reponse = Read-Host "Lancer Jarvis automatiquement à l'ouverture de Windows ? (o/n)"
if ($reponse -match "^[oOyY]") {
    $demarrage = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath("Startup")) "Jarvis.lnk"))
    $demarrage.TargetPath = $lanceur; $demarrage.WorkingDirectory = $ici; $demarrage.WindowStyle = 7; $demarrage.Save()
}

if (Test-Path (Join-Path $env:APPDATA "Claude")) {
    $reponse = Read-Host "Claude Desktop est installé : lui donner les outils de Jarvis (serveur MCP) ? (o/n)"
    if ($reponse -match "^[oOyY]") { Calme $py @("-m", "jarvis", "--claude-desktop") | Out-Null }
}

# 6. Bilan
Write-Host ""
Calme $py @("-m", "jarvis", "--verifier") | Out-Null
Write-Host ""
Write-Host "C'est installé. Ouvre la configuration pour mettre ta clé (ou installe Claude Code) :" -ForegroundColor Green
Write-Host "  $config"
Start-Process notepad.exe $config
Write-Host "Puis double-clique sur « Jarvis » sur le Bureau."
} catch {
    Write-Host "ERREUR : $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Le journal complet est sur le Bureau : installation_jarvis.txt"
} finally {
    try { Stop-Transcript | Out-Null } catch { }
    Read-Host "Appuie sur Entrée pour fermer"
}
