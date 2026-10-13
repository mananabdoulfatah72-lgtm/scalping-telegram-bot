# Telecharge Jarvis depuis GitHub (seulement son dossier, moins de 1 Mo), puis lance l'installation.
# A coller dans PowerShell (menu Demarrer > taper PowerShell > Entree) :
#   irm https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/refs/heads/claude/keen-babbage-r686cl/jarvis/telecharger.ps1 | iex
# Recoller la meme ligne plus tard met Jarvis a jour (la configuration est gardee).
# (Texte sans accents : il passe tel quel dans toutes les versions de PowerShell.)
& {
    $ErrorActionPreference = "Stop"
    $ProgressPreference = "SilentlyContinue"
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
    $depot = "mananabdoulfatah72-lgtm/scalping-telegram-bot"
    $branche = "claude/keen-babbage-r686cl"
    $dest = if ($env:JARVIS_DESTINATION) { $env:JARVIS_DESTINATION } else { Join-Path $env:USERPROFILE "Jarvis" }
    try {
        Write-Host "=== Jarvis : telechargement ===" -ForegroundColor Cyan
        $arbre = Invoke-RestMethod "https://api.github.com/repos/$depot/git/trees/${branche}?recursive=1" -UseBasicParsing -Headers @{ "User-Agent" = "jarvis-installateur" }
        $fichiers = @($arbre.tree | Where-Object { $_.type -eq "blob" -and $_.path.StartsWith("jarvis/") })
        if ($fichiers.Count -lt 10) { throw "la liste des fichiers de Jarvis est introuvable sur GitHub" }
        $n = 0
        foreach ($f in $fichiers) {
            $n++
            $cible = Join-Path $dest $f.path.Substring(7)
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $cible) | Out-Null
            Invoke-WebRequest "https://raw.githubusercontent.com/$depot/refs/heads/$branche/$($f.path)" -OutFile $cible -UseBasicParsing
            Write-Host ("`r  fichier {0} sur {1}" -f $n, $fichiers.Count) -NoNewline
        }
        Write-Host ""
        Write-Host "Jarvis est telecharge dans $dest" -ForegroundColor Green
        if ($env:JARVIS_TELECHARGER_SEULEMENT) { return }
        $py = Join-Path $env:LOCALAPPDATA "Jarvis\venv\Scripts\python.exe"
        if ((Test-Path $py) -and (Test-Path (Join-Path $env:APPDATA "Jarvis\config.toml"))) {
            # deja installe : mise a jour rapide (modules eventuellement nouveaux), configuration gardee
            Write-Host "Mise a jour des modules (moins d'une minute)..."
            $ancien = $ErrorActionPreference; $ErrorActionPreference = "Continue"
            & $py -m pip install -e $dest --quiet 2>$null | Out-Null
            $ErrorActionPreference = $ancien
            Write-Host "Jarvis est a jour. Ferme-le s'il tourne (fenetre noire), puis double-clique sur Jarvis sur le Bureau." -ForegroundColor Green
            return
        }
        Write-Host "Installation (10 a 20 minutes la premiere fois)..."
        powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $dest "installer.ps1")
    } catch {
        Write-Host "ERREUR : $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Verifie la connexion internet, puis recolle la ligne dans PowerShell."
    }
}
