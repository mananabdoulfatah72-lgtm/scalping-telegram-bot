# Tournoi 10 : de nouvelles progressions sur le NQ

Demande de l'utilisateur du 2 octobre 2026 : chercher d'autres sources de gain sur le Nasdaq, en plus de la
zone de bruit (intraday) et du RSI(2) (plusieurs jours). Ce tournoi ne reprend **aucune** famille déjà
testée : stratégies intraday (tournois 1 à 7), tournant du mois et veille de la Fed (`fonds/`), veille de
jour férié, IBS, Double 7, rebond de 5 jours (`tournoi8/`), nuit sans condition (`nuit/`), effets de
calendrier (`tournoi2/`), tendance multi-marchés (`tendance/`), order flow (`orderflow/`, `filtre_h1/`).

## Règles (fixées le 2 octobre 2026, avant tout calcul)

### Données et exécution

- Comme `tournoi8/` : minutes Databento du NQ (`intraday/`), 2011 - septembre 2026, une décision par
  séance 10 minutes avant la fin (15 h 50), indicateurs sur la clôture de 15 h 49, exécution à l'ouverture
  de la minute de décision. Position fermée à la dernière décision d'un contrat. Frais : 1 $ par ordre
  et 1 tick de glissement par ordre (1,5 point de NQ par aller-retour).
- **VIX** (CBOE, quotidien, `evolution2/donnees/`) : pour une décision du jour t, on n'utilise que le VIX
  **jusqu'à la clôture de la veille** (t − 1). Aucun chiffre du jour même.
- Achat seulement, sauf mention contraire.

### Les stratégies (6 sur le NQ ; les mêmes sur l'ES à titre descriptif)

| # | Stratégie | Règle | Source |
|---|---|---|---|
| T1 | **VIX tendu** | NQ au-dessus de sa moyenne de 200 séances, et VIX au moins 5 % au-dessus de sa moyenne de 10 jours, 3 jours de suite (jusqu'à la veille) : achat. Sortie quand le RSI(2) du NQ dépasse 65. | Connors, Alvarez (2009), « VIX Stretches » |
| T2 | **RSI du VIX** | NQ au-dessus de sa moyenne de 200, RSI(2) du VIX de la veille au-dessus de 90, ouverture du VIX de la veille au-dessus de sa clôture de l'avant-veille, RSI(2) du NQ sous 30 : achat. Sortie quand le RSI(2) du NQ dépasse 65. | Connors, Alvarez (2009), « VIX RSI » |
| T3 | **Mardi de rebond** | le lundi, si la clôture de 15 h 49 est sous celle de la séance précédente : achat à 15 h 50, vente à la décision suivante. | « Turnaround Tuesday » (Connors, Alvarez 2009 ; Cross 1973 pour l'effet lundi) |
| T4 | **Nuit après une fin de séance en baisse** | si le mouvement 14 h 49 → 15 h 49 est dans les 20 % les plus bas des 252 séances d'avant : achat à 15 h 50, vente à l'ouverture de 9 h 30 le lendemain. | Boyarchenko, Larsen, Whelan (2023), « The Overnight Drift » (la nuit sans condition a été rejetée dans `nuit/`) |
| T5 | **Nouveau plus haut de 252 séances** | si la clôture de 15 h 49 dépasse toutes celles des 252 séances d'avant : en position pendant les 20 séances suivantes (un nouveau plus haut prolonge). | George, Hwang (2004) ; Li, Yu (2012) pour l'indice |
| T6 | **Achat permanent piloté par la volatilité** | toujours acheteur ; exposition = variance de référence / variance des 22 derniers rendements quotidiens, plafonnée à 2. Variance de référence = médiane des variances passées (sans regarder l'avenir). Frais payés sur chaque changement d'exposition. | Moreira, Muir (2017), « Volatility-Managed Portfolios » |

### Le tri

1. **Exploration 2011-2022**, comme `tournoi8/` :
   - T1 à T5 : t ≥ 2 sur les rendements quotidiens nets, **et** battre 95 % de 1 000 placements au hasard
     des mêmes trades (mêmes durées ; pour T4, mêmes nuits en nombre, à des dates tirées au hasard).
   - T6 : alpha contre l'achat permanent simple (régression des rendements quotidiens de T6 sur ceux de
     l'achat permanent), **t de l'alpha ≥ 2**. C'est le test de l'article.
2. **Coffre 2023 - septembre 2026, ouvert une seule fois** pour les survivants : t (ou t de l'alpha pour
   T6) au moins égal au seuil de Bonferroni pour m survivants, et résultat positif au moins 3 années
   sur 4.
3. Publié pour chaque essai : Sharpe, perte maximale pour 1 MNQ, temps en position, nombre de trades,
   **corrélation quotidienne avec le RSI(2) et avec la zone de bruit** (une source utile doit être peu liée
   aux deux).
4. Les 6 essais sont inscrits dans `fonds/essais.csv`. Rien ne sera ajouté ou changé après avoir vu les
   résultats.

## Résultats de l'exploration 2011-2022 (2 octobre 2026) : `exploration10.txt`

| Stratégie (NQ) | t | Bat le hasard | Trades | $ pour 1 MNQ | Corrélation RSI(2) / zone | Verdict |
|---|---|---|---|---|---|---|
| T1 VIX tendu | 1,45 | 82,0 % | 90 | +4 674 | +0,50 / −0,04 | éliminé |
| T2 RSI du VIX | 0,77 | 54,4 % | 53 | +986 | +0,60 / −0,06 | éliminé |
| T3 Mardi de rebond | **2,09** | **94,4 %** | 239 | +6 793 | +0,15 / +0,02 | éliminé de justesse (seuil 95 %) |
| T4 Nuit après une fin de séance en baisse | 0,49 | 55,9 % | 568 nuits | +827 | +0,05 / −0,10 | éliminé |
| T5 Nouveau plus haut de 252 séances | 1,47 | 16,3 % | 51 | +5 608 | +0,40 / −0,11 | éliminé (le hasard fait mieux) |
| T6 Achat piloté par la volatilité | alpha t = 0,89 | | | | +0,41 / −0,07 | éliminé (Sharpe 0,73 contre 0,75 pour l'achat simple) |

- **Aucun survivant.** Le coffre 2023-2026 n'est pas ouvert.
- Le mardi de rebond est le seul à frôler les deux seuils, avec une corrélation faible au RSI(2) et à la
  zone. Sur l'ES (descriptif seulement) : t = 2,20, bat le hasard 97 %. Il est éliminé selon la règle
  fixée d'avance. S'il devait être repris, ce serait comme nouvelle idée, testée sur d'autres données.
- Les deux stratégies sur le VIX ressemblent beaucoup au RSI(2) (corrélation de 0,5 à 0,6) : même quand
  elles gagnent, elles n'apportent pas une source vraiment nouvelle.

## Seconde chance pour le mardi de rebond (décidée le 2 octobre 2026, après l'exploration, avant de lire 2023-2026)

L'utilisateur ne veut pas écarter une stratégie qui frôle les seuils. Le mardi de rebond (T3) est donc testé
une fois sur **2023 - septembre 2026**, années jamais lues pour lui. Comme ce test est décidé **après** avoir
vu l'exploration, la barre est plus haute que pour un coffre normal :
- t ≥ 2 (au lieu de 1,65 pour un seul survivant) ;
- battre 95 % de 1 000 placements au hasard des mêmes trades ;
- résultat positif au moins 3 années sur 4.

Même s'il passe, ce sera une preuve plus faible qu'un survivant normal : il entrerait en suivi virtuel, pas
dans le compte.
