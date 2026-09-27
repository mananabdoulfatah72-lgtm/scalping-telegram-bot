#!/usr/bin/env bash
# Telecharge les pages du calendrier des reunions du FOMC (site de la Fed) pour en extraire les dates.
set -u
D=fonds/donnees/fomc
mkdir -p "$D"
curl -sSL -A "Mozilla/5.0" --retry 3 -o "$D/fomccalendars.htm" https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm || true
for a in $(seq 2008 2022); do
  curl -sSL -A "Mozilla/5.0" --retry 3 -f -o "$D/fomchistorical$a.htm" "https://www.federalreserve.gov/monetarypolicy/fomchistorical$a.htm" || rm -f "$D/fomchistorical$a.htm"
done
ls -la "$D"
gzip -f "$D"/*.htm
