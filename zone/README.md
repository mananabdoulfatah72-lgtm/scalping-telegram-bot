# Robot zone de bruit + challenge Phidias 50K (argent virtuel)

Suit en direct le meilleur bot de challenge trouvé dans l'étude (`challenge/` sur la branche de
recherche) : zone de bruit sur le Nasdaq (MNQ), intraday, taille réduite quand le compte s'approche de
sa limite (f = 0,15). Il passe un challenge Phidias 50K virtuel puis, s'il le réussit, un compte
financé virtuel avec retraits. Tableau de bord : [`robot/TABLEAU_DE_BORD.md`](robot/TABLEAU_DE_BORD.md).

- Données : barres minute NQ de Databento (secret `DATABENTO_API_KEY`), environ 1 centime par jour. Les
  260 séances précédant le départ viennent des données de l'étude.
- Contrôle : rejoué sur 2023-2026, le robot donne, pour 1 MNQ, exactement les mêmes gains jour par jour
  que le backtest. Le challenge est réussi le même jour (7 juin 2023).
- Databento publie les barres minute environ 8 heures après la séance : chaque séance est rejouée le
  lendemain matin (heure de Paris). Pour trader en vrai, il faudrait recevoir les signaux en direct,
  toutes les 30 minutes.
- Historique : une tentative réussit 39 % du temps et saute 4 % du temps. Une fois financé, le compte
  rapporte environ 680 $ par an en moyenne, et rien dans 86 % des cas. Ce n'est pas un revenu.

## Correction du 30 septembre 2026 (données propres, dite V1)

L'autopsie de la zone (`zone_failles/` sur la branche de recherche) a trouvé une faille de calcul.
Les séances incomplètes entraient dans la moyenne des 14 jours et pouvaient servir de « veille » :
jours fériés de la CME arrêtés à 13 h, demi-séances. Désormais, seules les séances complètes comptent,
et la veille est la dernière séance complète du même contrat. C'est corrigé dans `robot.py` et dans le
script TradingView. Le robot corrigé donne exactement le backtest corrigé (2 287 jours de trade, écart
nul).

Effet sur NQ (t des rendements quotidiens nets) :

| Période | Avant | Après |
|---|---|---|
| 2011-2016 | −2,62 | −2,26 |
| 2017-2022 | +2,77 | +2,78 |
| 2023-2026 | +2,01 | +2,00 |

Quatre autres corrections ont été testées, avec des règles fixées avant le calcul :
- un seul trade par jour ;
- filtre GEX ;
- achats seulement ;
- stop sur le VWAP seul.

Aucune ne passe le tri : chacune fait moins bien que la version corrigée sur 2017-2022 ou sur
2023-2026. Les achats seuls font un peu mieux sur 2023-2026 (t 2,07 contre 2,00), mais moins bien sur
2017-2022 (1,97 contre 2,78), et leur écart avec la version corrigée n'est pas significatif. Elles ne
sont pas retenues.

Après la revue de code :
- les niveaux publiés n'annoncent plus de veille prise sur l'ancien contrat : ils disent « pas de
  trade (changement de contrat) », comme le backtest ;
- le script TradingView exige au moins 370 minutes pour compter une séance comme complète, comme le
  robot.
