# Quelle stratégie automatiser sur le Master Bulenox (14 novembre 2026)

Situation : solde 51 000 $, plancher 49 200 $. Le premier retrait devient possible à 53 600 $.
**Règle d'inactivité de Bulenox : 5 jours de trading sans trade, et le Master est perdu** (`chantier/REGLES.md` de
`claude/loving-mccarthy-u21aw6`).

Même simulateur pour les deux bots (machine v6, `st_zone.py`), même historique de 2011 au 13 novembre 2026 (minutes
NQ propres), 1 MNQ, départ à chaque séance, 250 séances (environ un an). La zone est rejouée par son moteur C#
(`Bot3en1.Replay`, réglages actuels C2 + Q1, sans le filtre delta qui n'existe pas avant 2026) : 1 753 trades sur
15 ans, **aucun trade dans 60 % des séances**. Supertrend ne trade pas dans 3 % des séances seulement (demi-journées).

| Stratégie, plancher suivi en temps réel | 53 600 $ atteint | Perdu par le plancher | Perdu par l'inactivité |
|---|---|---|---|
| Supertrend 1 MNQ, limite 400 $ (départs 2011+ / 2023+) | 44 % / 45 % | 56 % / 55 % | 0 % |
| Bot 3 en 1 seul, 1 MNQ (2011+ / 2023+) | 7 % / 0 % | 1 % / 2 % | **92 % / 98 %** |
| Bot 3 en 1 si le compte est gardé actif par ailleurs (2011+ / 2023+) | **66 %** / 47 % | 23 % / 41 % | — |

Plancher suivi en fin de journée : à 1 à 6 points près, mêmes conclusions.

- La dernière ligne suppose un trade de secours qui garde le compte actif et ne coûte rien. Le secours d'une heure
  du chantier (1 MES de 8 h à 9 h, heure de Paris, après 2 jours sans trade) faisait −0,7 $ en moyenne, avec un pire
  résultat de −513 $. **Il faut l'accord écrit de Bulenox**, qui refuse l'« activité artificielle ».
- Depuis 2023, la zone est moins bonne : 2024 et 2025 ont été de mauvaises années pour elle. Sur les départs depuis
  2023, elle ne fait guère mieux que Supertrend.
- Avec le frein (zone sur 1 MES quand la marge passe sous 1 750 $), le chantier trouvait moins de comptes perdus mais
  des retraits plus lents (`chantier/resultats/situation.txt`).
