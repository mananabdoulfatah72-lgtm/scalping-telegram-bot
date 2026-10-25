#!/bin/bash
# Version 5 (README.md) : machines B, B2, D sur les caches complets (vrai, bruit, signe ; graines 11 a 16).
PY=/tmp/claude-0/-home-user-scalping-telegram-bot/4861520c-7c70-542c-a1db-763e9dd91dac/scratchpad/venv/bin/python
cd /home/user/scalping-telegram-bot/scalping
date
$PY vague5.py B B2 D >> resultats/v5/machine.log 2>&1
date
