#!/bin/bash
# Exploration complete (README.md, version 4) : machines B, B2, D (vrai, bruit, signe), puis parties A et C, puis selection.
PY=/tmp/claude-0/-home-user-scalping-telegram-bot/4861520c-7c70-542c-a1db-763e9dd91dac/scratchpad/venv/bin/python
cd /home/user/scalping-telegram-bot/scalping
date
$PY machine.py B B2 D > resultats/machine.log 2>&1
date
$PY partie_a.py > resultats/partie_a.log 2>&1
date
$PY appris.py exploration > resultats/appris.log 2>&1
date
$PY coffre.py exploration > resultats/exploration.log 2>&1
date
