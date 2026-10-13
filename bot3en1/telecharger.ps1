# Telecharge le bot 3 en 1 depuis GitHub (seulement son dossier, environ 150 Ko), puis lance son installation dans
# Quantower (compilation et copie dans Settings\Scripts\Strategies).
# A coller dans PowerShell (menu Demarrer > taper PowerShell > Entree) :
#   irm https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/refs/heads/claude/keen-babbage-r686cl/bot3en1/telecharger.ps1 | iex
# Recoller la meme ligne plus tard met le bot a jour. Ses reglages restent dans Quantower, son etat dans C:\Bot3en1.
# (Texte sans accents : il passe tel quel dans toutes les versions de PowerShell.)
& {
    $ErrorActionPreference = "Stop"
    $ProgressPreference = "SilentlyContinue"
    try { [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12 } catch { }
    $depot = "mananabdoulfatah72-lgtm/scalping-telegram-bot"
    $branche = "claude/keen-babbage-r686cl"
    $dest = if ($env:BOT3EN1_DESTINATION) { $env:BOT3EN1_DESTINATION } else { Join-Path $env:USERPROFILE "Bot3en1-installation" }
    try {
        Write-Host "=== Bot 3 en 1 : telechargement ===" -ForegroundColor Cyan
        $arbre = Invoke-RestMethod "https://api.github.com/repos/$depot/git/trees/${branche}?recursive=1" -UseBasicParsing -Headers @{ "User-Agent" = "bot3en1-installateur" }
        $fichiers = @($arbre.tree | Where-Object { $_.type -eq "blob" -and $_.path.StartsWith("bot3en1/") })
        if ($fichiers.Count -lt 10) { throw "la liste des fichiers du bot est introuvable sur GitHub" }
        $n = 0
        foreach ($f in $fichiers) {
            $n++
            $cible = Join-Path $dest $f.path.Substring(8)
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $cible) | Out-Null
            Invoke-WebRequest "https://raw.githubusercontent.com/$depot/refs/heads/$branche/$($f.path)" -OutFile $cible -UseBasicParsing
            Write-Host ("`r  fichier {0} sur {1}" -f $n, $fichiers.Count) -NoNewline
        }
        Write-Host ""
        Write-Host "Bot telecharge dans $dest" -ForegroundColor Green
        if ($env:BOT3EN1_TELECHARGER_SEULEMENT) { return }
        Write-Host "Ferme Quantower avant de continuer (la bibliotheque du bot doit pouvoir etre remplacee)." -ForegroundColor Yellow
        powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $dest "installer.ps1")
    } catch {
        Write-Host "ERREUR : $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "Verifie la connexion internet, puis recolle la ligne dans PowerShell."
    }
}
