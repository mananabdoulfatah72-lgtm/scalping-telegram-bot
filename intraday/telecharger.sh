#!/usr/bin/env bash
# Telecharge les prix minute par minute (Dukascopy) du S&P 500 et du Nasdaq 100 depuis 2012.
# Lance par .github/workflows/donnees-intraday.yml (Dukascopy n'est pas joignable ailleurs).
set -u
mkdir -p brut
npm install -g dukascopy-node@latest >/dev/null 2>&1
echo "== test sur une semaine"
dukascopy-node -i usa500idxusd -from 2024-03-04 -to 2024-03-05 -t m1 -f csv -dir brut -fn test || true
head -3 brut/test.csv || true
for inst in usa500idxusd usatechidxusd; do
  for y in $(seq 2012 2026); do
    fin="$((y + 1))-01-01"
    [ "$y" -eq 2026 ] && fin=$(date -u +%F)
    echo "== $inst $y"
    dukascopy-node -i "$inst" -from "$y-01-01" -to "$fin" -t m1 -f csv -dir brut -fn "${inst}_${y}" \
      -bs 20 -bp 300 -r 5 || echo "ECHEC $inst $y"
    ls -la "brut/${inst}_${y}.csv" 2>/dev/null || echo "pas de fichier pour $inst $y"
  done
done
