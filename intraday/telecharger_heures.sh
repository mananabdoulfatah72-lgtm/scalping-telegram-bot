#!/usr/bin/env bash
# Telecharge les prix heure par heure (Dukascopy) du S&P 500 et du Nasdaq 100 depuis 2014.
# Beaucoup plus rapide que les minutes : Dukascopy stocke les heures par mois (1 requete par mois).
set -u
mkdir -p brut_h
npm install -g dukascopy-node@latest >/dev/null 2>&1
fin=$(date -u +%F)
for inst in usa500idxusd usatechidxusd; do
  for essai in 1 2 3 4 5; do
    echo "== $inst (essai $essai)"
    if dukascopy-node -i "$inst" -from 2014-01-01 -to "$fin" -t h1 -f csv -dir brut_h -fn "$inst" \
         -bs 2 -bp 1500 -r 10 -rp 4000 -re -ch; then
      break
    fi
    sleep 60
  done
  ls -la "brut_h/$inst.csv" || true
done
