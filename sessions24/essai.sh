#!/usr/bin/env bash
# Essai court : ou et sous quel nom dukascopy-node ecrit ses fichiers (resultats en annotations GitHub).
set -u
mkdir -p brut
npm install -g dukascopy-node@latest >/dev/null 2>&1
echo "::warning::version $(npm ls -g dukascopy-node 2>/dev/null | grep dukascopy | tr -d ' ')"
dukascopy-node -i eurusd -from 2013-01-02 -to 2013-01-04 -t m1 -f csv -dir brut -fn eurusd_2013 -bs 5 -bp 1000 -r 10 -rp 5000 -re -ch > sortie.txt 2>&1
echo "::warning::code $? ; sortie : $(tail -c 600 sortie.txt | tr '\n' ' ')"
echo "::warning::fichiers : $(find . -name '*.csv' -newer sessions24/essai.sh 2>/dev/null | grep -v node_modules | head -20 | tr '\n' ' ')"
f=$(find . -name '*.csv' -newer sessions24/essai.sh 2>/dev/null | grep -v node_modules | head -1)
[ -n "$f" ] && echo "::warning::debut de $f : $(head -c 300 "$f" | tr '\n' ' ')"
dukascopy-node --help > aide.txt 2>&1
echo "::warning::aide : $(grep -iE 'file-name|directory|-fn|-dir' aide.txt | tr '\n' ' ' | head -c 800)"
