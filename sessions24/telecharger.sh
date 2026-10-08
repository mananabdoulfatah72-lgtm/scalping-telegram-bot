#!/usr/bin/env bash
# Telecharge les prix minute (Dukascopy, prix acheteur, UTC) d'un instrument, 2012 - aujourd'hui, 24 h sur 24.
# Usage : bash sessions24/telecharger.sh <code dukascopy>. Lance par .github/workflows/donnees-sessions.yml.
set -u
inst="$1"
mkdir -p brut
npm install -g dukascopy-node@latest >/dev/null 2>&1
for y in $(seq 2012 2026); do
  fin="$((y + 1))-01-01"
  [ "$y" -eq 2026 ] && fin=$(date -u +%F)
  for essai in 1 2 3 4; do
    echo "== $inst $y (essai $essai)"
    if dukascopy-node -i "$inst" -from "$y-01-01" -to "$fin" -t m1 -f csv -dir brut -fn "${inst}_${y}" \
         -bs 5 -bp 1000 -r 10 -rp 5000 -re -ch; then
      break
    fi
    echo "ECHEC $inst $y, nouvelle tentative dans 90 s"
    sleep 90
  done
  ls -la "brut/${inst}_${y}.csv" 2>/dev/null || echo "pas de fichier pour $inst $y"
done
