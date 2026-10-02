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
- Historique, refait le 1er octobre 2026 avec les règles Phidias publiques (`zone_retrait/` sur la
  branche de recherche) : sur 24 mois, environ 160 $ reçus par an, pour 1,1 challenge payé par an à
  164 $. Rien n'est reçu dans 79 % des départs. Ce n'est pas un revenu (voir « Retraits » plus bas).

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

## Taille : 1 MNQ minimum (1er octobre 2026)

L'ancienne règle arrondissait à 0 MNQ quand la marge avant la limite passait sous environ 1 400 $. Le
compte ne tradait plus, donc ne remontait plus, et restait bloqué : c'est ce qui arrivait en octobre
2025 au compte financé rejoué, et c'est pour cela que tant de tentatives « n'avaient pas fini ». À la
demande de l'utilisateur, le robot garde maintenant **au moins 1 MNQ** :
nombre de MNQ = max(1, arrondi inférieur de 0,15 × marge / risque d'un MNQ).

Effet mesuré avec le code du robot (`zone_taille/` sur la branche de recherche). Zone seule, règles
Phidias du robot, un départ par semaine, chaque départ suivi 12 mois :

| | Départs 2011-2021, ancienne | Départs 2011-2021, nouvelle | Départs 2023-2025, ancienne | Départs 2023-2025, nouvelle |
|---|---|---|---|---|
| challenge validé en 12 mois | 21 % | 32 % | 42 % | 67 % |
| challenges commencés (chacun se paie) | 1,23 | 1,85 | 1,00 | 1,88 |
| comptes perdus | 0,23 | 0,85 | 0 | 0,88 |
| séances gelées à 0 MNQ, sur 252 | 113 | 0 | 123 | 0 |
| reçu en 12 mois, moyenne | 29 $ | 48 $ | 83 $ | 83 $ |
| départs qui ne reçoivent rien | 97 % | 95 % | 93 % | 93 % |

- **Le gel disparaît, et le challenge passe beaucoup plus souvent.**
- **En échange, plus de comptes sautent.** Il faut en moyenne près d'un challenge payant de plus par an.
- **L'argent reçu ne bouge presque pas.** Partir de 50 000 $, monter au-dessus de 52 600 $ avec 1 ou
  2 MNQ, puis respecter la règle des 30 % pour retirer, prend le plus souvent plus de 12 mois.
  C'est la prochaine limite, plus que la stratégie.

Rejeu unique depuis le 30 décembre 2022 :
- **Ancienne règle :** challenge réussi le 8 juin 2023, puis compte financé gelé.
- **Nouvelle règle :** même challenge réussi. Le compte financé trade jusqu'au 23 janvier 2026, où il
  saute. Le challenge suivant est à +3 494 $ fin septembre 2026.
- Aucun retrait dans les deux cas.

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

## Retraits : règles corrigées, gestion inchangée (1er octobre 2026)

Le robot supposait un retrait tous les 21 jours, sans plafond. D'après les sources publiques d'octobre
2026 (le site de Phidias est bloqué depuis l'environnement de calcul, donc à vérifier), le compte
financé 50K Fundamental fonctionne ainsi :
- retrait possible après 10 jours qualifiants depuis le dernier retrait (jours à au moins +150 $) ;
- de 500 $ à 2 000 $ par retrait, sur ce qui dépasse 52 600 $ ;
- meilleure journée ≤ 30 % du gain depuis le dernier retrait ;
- 80 % pour toi ;
- challenge à 164 $ (souvent moins avec un code promo).

Le robot suit maintenant ces règles.

L'utilisateur voulait retirer plus. 128 gestions ont été essayées (`zone_retrait/`), avec des règles
fixées avant le calcul :
- taille du challenge ;
- taille du compte financé, avant et après le blocage de la limite ;
- marge gardée après un retrait.

**Aucune ne gagne de l'argent de façon fiable** :

| Départs suivis 24 mois | Reçu par an | Challenges payés par an | Gain net par an (164 $ le challenge) | Départs sans rien |
|---|---|---|---|---|
| 2011-2020, gestion actuelle | 61 $ | 1,49 | −184 $ | 85 % |
| 2011-2020, meilleure des 128 | 80 $ | 1,49 | −164 $ | 87 % |
| 2023-2024, gestion actuelle | 158 $ | 1,09 | −22 $ | 79 % |
| 2023-2024, meilleure du passé | 109 $ | 1,09 | −70 $ | 79 % |

- La gestion actuelle est déjà dans le haut de la grille (5e sur 128). La médiane des 128 fait −497 $
  par an. Prendre plus de risque fait sauter plus de comptes qu'il ne rapporte de retraits.
- Avec un challenge à 65,60 $ (code promo), une gestion plus agressive (f = 0,25 au challenge et
  avant blocage) gagnait +126 $ par an sur 2011-2020. Mais sur 2023-2024 elle fait moins bien que
  l'actuelle : +27 $ contre +86 $ par an.

**Pourquoi.** Le frein n'est pas la gestion, c'est l'avantage. La zone gagne en moyenne 11,5 $ par
séance pour 1 MNQ, avec un écart-type de 202 $ (Sharpe annuel 0,9 sur 2023-2026, 0,3 sur 2011-2020).
Avant le moindre retrait, il faut monter de 2 600 $ sans jamais reculer de 2 500 $. Ensuite il faut
10 jours à +150 $, alors qu'à 1 MNQ, seuls 14 % des séances y arrivent. Avec un tel avantage, le
compte saute à peu près aussi souvent qu'il arrive au premier retrait. Pour retirer vraiment plus, il
faut une stratégie au rapport gain/risque nettement meilleur, ou plusieurs sources de gain peu liées
qui tradent ensemble.

## Juger le virtuel : règle fixée le 1er octobre 2026

**Ce que le virtuel peut prouver, et ce qu'il ne peut pas.** Sur le rejeu 2023-2026, la zone gagne en
moyenne **+11,5 $ par séance pour 1 MNQ**, avec un écart-type de **202 $** par séance. Pour prouver
l'avantage en direct (t ≥ 2), il faudrait environ **1 200 séances, soit 5 ans**. Quelques mois de
virtuel ne prouvent donc pas que la stratégie gagne. Ils vérifient deux choses :
1. le robot fait exactement ce que fait le backtest (même code, `une_journee`) ;
2. rien n'est cassé : données, marché qui change, glissement plus fort que prévu.

**Voyant** (calculé chaque jour par `voyant()` dans `robot.py`, affiché sur la page et dans le message
Telegram). Gain cumulé pour 1 MNQ depuis le départ, après n séances, comparé à la fourchette du
backtest, moyenne × n − z × 202 × √n :

| Voyant | Condition | Sens |
|---|---|---|
| vert | au-dessus de la ligne des 25 % (z = 0,674) | fourchette normale |
| orange | entre la ligne des 5 % (z = 1,645) et celle des 25 % | bas de la fourchette, arrive 1 fois sur 5 par hasard ; pas une alerte |
| rouge | sous la ligne des 5 % | alerte |

**Bilans à 60 puis 120 séances** (60 séances : vers le 21 décembre 2026) :
- **rouge → arrêter le suivi et chercher la cause** (données, glissement, changement du marché) avant
  tout argent réel ;
- sinon → continuer jusqu'au bilan suivant.

Ligne des 5 % : environ **−1 890 $ pour 1 MNQ après 60 séances**, **−2 270 $ après 120 séances**.

**Avant de payer un challenge**, deux conditions :
- le voyant n'est pas rouge au bilan de 60 séances, et le glissement réel est conforme, mesuré sur
  un compte démo avec les alertes TradingView (`tradingview/GUIDE.md`) ;
- la simulation du challenge donne un gain attendu nettement positif après le prix des challenges.
  Avec la zone seule, ce n'est pas le cas : environ 160 $ reçus par an pour 1,1 challenge payé à
  164 $. Une deuxième stratégie validée est cherchée (tournoi des stratégies de plusieurs jours sur la
  branche de recherche).

## Telegram

Le résumé du matin part sur Telegram si le secret `TELEGRAM_TOKEN` existe :
- **conversation** : secret `CHAT_ID` s'il existe ;
- sinon, la **première conversation privée qui a écrit au bot**, trouvée automatiquement (`getUpdates`)
  puis gardée d'un passage à l'autre par le cache de GitHub Actions (fichier `.telegram_chat`, jamais
  commité ni affiché dans les journaux, le dépôt étant public).

Il suffit d'envoyer une fois un message au bot (par exemple `/start`) : le passage suivant du robot le
trouve. Telegram ne garde les messages que 24 heures ; si le robot passe plus tard, renvoyer un message.
Le robot de tendance fait de même.

## Second moteur dans le compte : RSI(2) sur le NQ (depuis le 1er octobre 2026)

Seul survivant du tournoi des stratégies de plusieurs jours (`tournoi8/` sur la branche de recherche,
règles fixées avant calcul, contrôle par dates tirées au hasard, coffre 2023-2026 ouvert une fois).

**Règle (Connors, Alvarez 2008), achat seulement, 1 décision par séance à 15 h 50 New York :**
- **achat** si la clôture de 15 h 49 est au-dessus de la moyenne des 200 clôtures et que le RSI de
  Wilder sur 2 clôtures est sous 10 ;
- **vente** quand la clôture dépasse la moyenne des 5 clôtures ;
- exécution à l'ouverture de 15 h 50, position gardée la nuit et le week-end ;
- position fermée à la dernière décision d'un contrat ;
- jours fériés de la Bourse ignorés, décision 10 minutes avant la fin les jours courts.

**Chiffres de la recherche (1 MNQ) :**
- exploration 2011-2022 : t 2,40 ;
- coffre 2023-2026 : t 1,95, Sharpe 1,01, +11 098 $, 4 années positives ;
- corrélation avec la zone ≈ 0 ; Sharpe du mélange 1,31 contre 0,90 pour la zone seule.
- Limites : passé de justesse, 40 trades dans le coffre, une partie du gain récent vient de la hausse
  du marché.

**Dans le compte virtuel :**
- chaque source reçoit f × coussin / √2 de risque (f = 0,15, au moins 1 MNQ), pour les décisions à
  partir du 1er octobre 2026. Le risque d'un MNQ du RSI(2) est l'écart-type de ses gains les jours en
  position sur les 252 séances d'avant ;
- une taille plus grande a été testée (`zone_deux/`) et ne fait pas mieux sur le contrôle 2023-2024.

**Résultats attendus, rejeu du challenge, départs 2023-2024 suivis 24 mois :**

| | Gain net par an | Rien reçu |
|---|---|---|
| Zone + RSI(2) | **+254 $** | 27 % des départs |
| Zone seule | −22 $ | 79 % des départs |

**Contrôle :** sur les minutes 2011-2026 de la recherche, la fonction `rsi2()` du robot redonne
exactement la série du tournoi : 3 950 séances, mêmes gains, mêmes pires moments.

**Chaque matin**, la page et le message donnent la consigne du soir : en position, le prix de vente ;
sinon, la fourchette de prix où l'on achèterait à 15 h 50. Le voyant reste celui de la zone (règle
ci-dessus) ; le journal montre les deux sources séparément.

## Filtre order flow H1 : le delta des 30 dernières minutes (depuis le 2 octobre 2026)

Étude : `orderflow/` sur la branche de recherche (transactions du NQ, avril à octobre 2026). Parmi tous
les outils d'order flow testés, un seul passe le coffre : **ne prendre un trade de la zone que si le delta
des 30 dernières minutes va dans son sens**. Le delta, ce sont les contrats achetés au prix vendeur moins
les contrats vendus au prix acheteur, sur les 30 minutes qui finissent à la clôture de la minute du signal.

| Période | Trades de zone | Gardés | Écartés | Écart | t |
|---|---|---|---|---|---|
| Exploration (avril - juillet) | 76 | 61 trades, +9,24 pt | 15 trades, −41,25 pt | +50,5 pt | 1,68 |
| Coffre (août - 1er octobre) | 23 | 18 trades, +67,40 pt | 5 trades, −35,15 pt | +102,6 pt | 2,34 |

Sur les 6 mois, la zone passe de +982 à +1 777 points (environ +1 590 $ pour 1 MNQ). Le filtre marche aussi
avec un delta sur 15, 45, 60 ou 90 minutes, pas sur 5 ou 10. **Mais il repose sur 20 trades écartés en tout.**
L'effet réel est sans doute plus petit.

Dans le robot :
- Chaque matin, pour chaque trade de zone joué depuis le 1er octobre 2026, le robot achète à Databento les
  transactions des 30 minutes avant le signal (schéma `trades`, NQ.v.0) et note le delta, gardé ou écarté,
  dans `robot/filtre_delta.csv`. Il a été vérifié hors ligne qu'il prend les mêmes 23 décisions que le
  test du coffre.
- **Budget accepté par l'utilisateur : 1 $ par mois.** Au plus 0,25 $ par fenêtre ; au-delà du budget du
  mois, le trade est noté « non mesuré » et compté comme gardé.
- **Suivi à part** : le compte virtuel garde la zone d'origine, pour ne pas changer la règle de jugement en
  cours de route. Le message Telegram, `TABLEAU_DE_BORD.md` et la page donnent la zone seule et la zone
  filtrée. Au bilan (60 séances), on décide si le filtre entre dans le compte.
- **En direct sur ta plateforme** : à chaque signal de la zone, regarder le delta cumulé des 30 dernières
  minutes. S'il va contre le trade, ne pas le prendre.
