#!/usr/bin/env bash
# Refait les rejeux bruts de resultats/rejeu/ (voir rejeu_periode.py). Il faut le SDK .NET 8 et les branches extraites :
#   OP = claude/optimistic-ptolemy-xs24ra (bot3en1/ a jour, audit/donnees/, flux/veille.py), KB = claude/keen-babbage-r686cl.
# Minutes du NQ : zone/robot/nq_1min.csv.gz de main (mis a jour chaque soir par GitHub Actions).
set -e
MIN=${1:?minutes du NQ}; DEBUT=2026-10-13; FIN=${2:-2026-11-11}; DOS=$(dirname "$0")/resultats/rejeu; B=$OP/bot3en1
python3 -c "import pandas as p; d=p.read_csv('$OP/audit/donnees/transactions_NQZ6_13-30oct.csv'); d[['jour','minute','achats','ventes']].to_csv('$DOS/agresseurs.csv', index=False)"
for p in Bot3en1 Supertrend; do dotnet build -c Release $B/$p.Replay > /dev/null; done
R="dotnet $B/Bot3en1.Replay/bin/Release/net8.0/Bot3en1.Replay.dll"
env SANS_FILTRE=1 SANS_RETOUR=1 Q1=1 CONTRAT_CALENDRIER=1 $R $MIN - $DEBUT $FIN > $DOS/bot_actuel_sans_delta.txt
env SANS_FILTRE=1 CONTRAT_CALENDRIER=1 $R $MIN - $DEBUT $FIN > $DOS/bot_origine_sans_delta.txt
env CASSURE=1 VOLUME=1 VOLMULT=1 SANS_TARDIVE=1 COURIR=1 SANS_FILTRE=1 CONTRAT_CALENDRIER=1 $R $MIN - $DEBUT $FIN > $DOS/bot_regle_26oct.txt
env CASSURE=1 VOLUME=1 VOLMULT=1 SANS_TARDIVE=1 COURIR=1 SANS_FILTRE=1 SANS_SORTIE=1 STOP=70 CONTRAT_CALENDRIER=1 $R $MIN - $DEBUT $FIN > $DOS/bot_regle_27oct.txt
env SANS_RETOUR=1 Q1=1 CONTRAT_CALENDRIER=1 $R $MIN $DOS/agresseurs.csv $DEBUT 2026-10-30 > $DOS/bot_actuel_avec_delta.txt
env CONTRAT_CALENDRIER=1 $R $MIN $DOS/agresseurs.csv $DEBUT 2026-10-30 > $DOS/bot_origine_avec_delta.txt
dotnet $B/Supertrend.Replay/bin/Release/net8.0/Supertrend.Replay.dll $MIN $DOS/supertrend_trades.csv
# W1 et XGBoost : un petit programme qui compile W1.Core (ou XGBoost.Core) avec son modele embarque et ecrit bot.Trades
# (jour,sens,m_in,m_out,entree,sortie,proba,entraine_jusqua) ; meme total que W1.Replay depuis le 13 octobre (+6 152 $, 27 trades).
(cd $OP && DEBUT_SUIVI=$DEBUT KB=$KB python3 flux/veille.py $MIN && cp flux/veille/journal.csv $DOS/veille_journal.csv)
for f in zone/robot/journal.csv:zone tendance/robot/journal.csv:tendance tendance/robot/journal_melange.csv:melange version7/robot/journal.csv:version7; do
  git show origin/main:${f%%:*} > $DOS/robot_${f##*:}.csv; done
python3 $(dirname "$0")/rejeu_periode.py $MIN
