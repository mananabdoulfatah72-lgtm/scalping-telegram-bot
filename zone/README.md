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

## Second moteur en test : rebond après forte baisse (1er octobre 2026)

Ajouté à la demande de l'utilisateur. La recherche (`zone_sources/` sur la branche de recherche,
piste S4) l'a trouvé comme la seule nouvelle source qui améliore les trois périodes. Son apport n'est
pas prouvé statistiquement (t de la différence avec la zone seule : 1,44, contre 2,33 exigé). C'est ce
suivi en argent virtuel qui doit le juger.

Règle : le lendemain d'une séance dont le mouvement ouverture → clôture est dans les 10 % les plus bas
des 252 valeurs précédentes, achat à l'ouverture de 9 h 30 et sortie à la clôture (15 h 59), en plus de
la zone et à la même taille. La séance de référence est la dernière séance complète du même contrat.
Pas d'achat un jour de fête, de demi-séance ou de changement de contrat. Environ 24 jours par an.

Contrôle : rejoué sur 2023-2026, le robot donne exactement les gains de la recherche. Pour 1 MNQ, la
zone seule fait 10 668 $, la zone plus le rebond 18 758 $ :

| Année | 2023 | 2024 | 2025 | 2026 (à fin septembre) |
|---|---|---|---|---|
| Zone + rebond, 1 MNQ | +3 923 $ | +3 886 $ | +8 451 $ | +2 498 $ |

Le tableau de bord et le message Telegram annoncent l'achat la veille au soir. Pas encore dans le script
TradingView. Si les deux moteurs tradent le même compte en réel, un achat du rebond et une vente de la
zone le même jour se compensent en partie : le gain total reste la somme des deux.

Les chiffres historiques du haut de cette page (39 % de challenges réussis, 680 $ par an) sont ceux de
la zone seule : ils n'ont pas été refaits avec le rebond.
