#!/usr/bin/env bash
# Telecharge les prix minute par minute (Dukascopy) du S&P 500 et du Nasdaq 100 depuis 2014.
# Lance par .github/workflows/donnees-intraday.yml (Dukascopy n'est pas joignable ailleurs).
# Dukascopy limite le debit (erreur 429) : petits lots, pauses, reessais et cache.
set -u
mkdir -p brut
npm install -g dukascopy-node@latest >/dev/null 2>&1
for inst in usa500idxusd usatechidxusd; do
  for y in $(seq 2014 2026); do
    fin="$((y + 1))-01-01"
    [ "$y" -eq 2026 ] && fin=$(date -u +%F)
    for essai in 1 2 3 4; do
      echo "== $inst $y (essai $essai)"
      if dukascopy-node -i "$inst" -from "$y-01-01" -to "$fin" -t m1 -f csv -dir brut -fn "${inst}_${y}" \
           -bs 3 -bp 1500 -r 10 -rp 5000 -re -ch; then
        break
      fi
      echo "ECHEC $inst $y, nouvelle tentative dans 90 s"
      sleep 90
    done
    ls -la "brut/${inst}_${y}.csv" 2>/dev/null || echo "pas de fichier pour $inst $y"
  done
done
