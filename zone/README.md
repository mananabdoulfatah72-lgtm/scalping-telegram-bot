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

## Second moteur suivi à part : rebond après forte baisse (1er octobre 2026)

Ajouté à la demande de l'utilisateur. La recherche (`zone_sources/` sur la branche de recherche,
piste S4) l'a trouvé comme la seule nouvelle source qui améliore les trois périodes. Son apport n'est
pas prouvé statistiquement.

Règle : le lendemain d'une séance dont le mouvement ouverture → clôture est dans les 10 % les plus bas,
achat de 1 MNQ à l'ouverture de 9 h 30 et sortie à la clôture (15 h 59).
- La séance de référence est la dernière séance complète, quel que soit le contrat.
- Le seuil est le 10e centile des 252 valeurs précédentes de cette référence, une valeur par séance.
  Après une séance incomplète, la même référence compte deux fois, comme dans la recherche.
- Pas d'achat un jour de fête ou de demi-séance (connus d'avance).
- Environ 24 achats par an.

**Version exécutable.** La revue de code a montré que la piste S4 écartait les jours de changement de
contrat, ce qu'on ne peut pas savoir la veille. Le robot aurait donc annoncé des achats que le
backtest ne comptait pas : 7 depuis 2017, pour −1 880 $ par MNQ. Le robot prend maintenant chaque
achat qu'il annonce. Contrôle jour par jour sur 2011-2026 : 0 écart entre l'annonce de la veille et le
trade du lendemain. Cela change les chiffres (NQ, 1 MNQ, frais réels) :

| | Piste S4 (recherche) | Version exécutable |
|---|---|---|
| Rebond seul, 2023-2026 | +8 089 $ | +6 420 $ |
| Zone + rebond, t 2023-2026 (zone seule : 2,00) | 2,04 | 1,91 |
| t de l'apport du rebond, 2023-2026 | 1,44 | 1,21 |
| Rebond seul, 2011-2022 | +6 428 $ | +6 871 $ |

**D'où vient le gain** (version exécutable, 1 MNQ) : de deux krachs suivis d'un rebond. 2020 (Covid)
rapporte +6 408 $ et 2025 (droits de douane, avril) +6 568 $. Les 14 autres années réunies ne font
qu'environ +300 $. Un seul jour, le 9 avril 2025 (pause des droits de douane), rapporte +4 119 $. Les
pires jours sont lourds pour un compte de challenge : −1 066 $ le 17 juin 2026, et six jours à plus de
−780 $ depuis fin 2021.

**Pourquoi hors du compte de challenge.** Rejoué sur 2023-2026 avec la taille du robot, le compte avec
le rebond passe le challenge, mais le compte financé tombe à 0 MNQ dès novembre 2023 et n'en sort plus.
La zone seule tient jusqu'en octobre 2025. Le compte virtuel joue donc la zone seule, exactement comme
avant (contrôle : journal identique sur 2023-2026). Le rebond est annoncé et compté à part, pour
1 MNQ : colonne `gain_rebond_1_mnq` du journal, ligne à part du tableau de bord.

Le tableau de bord et le message Telegram annoncent l'achat le matin de la séance, vers 7 h 35 heure
de Paris (au plus tard 14 h 35 si les données de Databento sont en retard). Le rebond n'est pas dans le
script TradingView.

**À savoir sur la taille, avec ou sans rebond.** La règle de taille arrondit à 0 MNQ quand la marge
avant la limite passe sous environ 1 400 $ : le compte ne trade plus, donc ne remonte plus, et reste
bloqué. C'est ce qui arrive en octobre 2025 au compte financé rejoué, et c'est pour cela que tant de
tentatives « n'ont pas fini » dans l'historique.

## Tableau de bord en direct

Page : https://claude.ai/artifact/J3yAQvPZtmSHhY74Xf4mVv (privée ; partage depuis le menu de la page).
- Compte virtuel : solde, objectif, marge avant la limite, taille du lendemain.
- Niveaux de la séance, avec les heures de Paris et le prochain contrôle en direct.
- Rebond suivi à part.
- Courbe du robot comparée à la fourchette attendue par le backtest.
- Backtest 2023-2026 et journal.

`zone/tableau/construire.py` fabrique la page à partir de `zone/robot/` et de
`zone/tableau/reference.json` (rejeu 2023-2026 pour 1 MNQ). Une routine Claude la reconstruit et la
republie chaque jour de semaine vers 14 h 50 (Paris), après le passage du robot et avant l'ouverture
de New York.
