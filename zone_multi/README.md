# Zone de bruit sur plusieurs marchés (bot de challenge plus régulier)

## Règles (fixées le 29 septembre 2026, avant de télécharger les données)

Objectif : rendre le bot de challenge plus régulier en appliquant la zone de bruit (Zarattini, Aziz et
Barbon ; `intraday/strategies.py`) à plusieurs marchés à la fois. Sur NQ seul : t = 2,55. Sur ES seul :
t = −1,0.

**Marchés, fixés maintenant et tous gardés dans le portefeuille quel que soit leur résultat** (contrat
micro, $ par point, tick) :

| Marché | Micro | Séance utilisée (New York) | $ par point | Tick |
|---|---|---|---|---|
| Nasdaq 100 (NQ) | MNQ | 9 h 30 - 16 h | 2 | 0,25 |
| S&P 500 (ES) | MES | 9 h 30 - 16 h | 5 | 0,25 |
| Russell 2000 (RTY) | M2K | 9 h 30 - 16 h | 5 | 0,10 |
| Dow Jones (YM) | MYM | 9 h 30 - 16 h | 0,5 | 1 |
| Or (GC) | MGC | 8 h 20 - 13 h 30 | 10 | 0,10 |
| Pétrole (CL) | MCL | 9 h - 14 h 30 | 100 | 0,01 |
| Euro (6E) | M6E | 8 h 20 - 15 h | 12 500 | 0,0001 |

- **Règles identiques à NQ, sans rien ajuster par marché** :
  - moyenne sur 14 séances ;
  - un contrôle toutes les 30 minutes après l'ouverture de la séance, jusqu'à 30 minutes avant la fin ;
  - sortie si le prix repasse la limite de la zone ou le prix moyen du jour (VWAP) ;
  - tout est fermé à la fin de la séance.
- Une séance est complète si la première et la dernière minute sont présentes et qu'il manque au plus
  20 minutes. Pas de trade le jour d'un changement d'échéance.
- Frais : 1 $ par ordre et 1 tick de glissement par ordre (comme pour NQ).
- Données : Databento GLBX.MDP3, ohlcv-1m, contrat le plus échangé (`.v.0`), depuis 2011 si le coût le
  permet (même période pour tous les marchés).

**Portefeuille** : chaque marché reçoit le même risque. Son gain du jour pour 1 micro est divisé par son
écart-type des 60 séances précédentes, connu la veille. Le portefeuille est la moyenne de ces gains, puis
il est ramené au risque de NQ seul pour comparer.

**Critères** (plus stricts que d'habitude, puisqu'environ 85 essais ont déjà été faits) :
- t du portefeuille ≥ 3 ;
- gain positif sur 2011-2014, 2015-2019 et 2020-2026 ;
- Sharpe du portefeuille supérieur à celui de NQ seul.

**Si les critères sont remplis** : bot coussin sur les règles Topstep, Apex et Phidias. Chaque marché
reçoit un budget f × coussin / √(nombre de marchés) et prend un nombre entier de micros. Le pire moment
du jour est la somme des pires moments de chaque marché, ce qui est prudent. On mesure la réussite en
12 mois, avec 2 comptes au plus, par rapport au bot sans avantage, puis ce que rapporte le compte
financé. f vaut 0,15, 0,25 ou 0,35.

Essai inscrit dans `fonds/essais.csv` : 1 portefeuille et 6 nouveaux marchés. Aucun marché ne sera retiré
ni ajouté après les résultats.

**Précision avant le calcul (29 septembre, données reçues, résultats pas encore vus)**
- Le plafond de coût a fait commencer les 5 nouveaux marchés en **janvier 2016**. Le Russell (RTY) ne
  démarre qu'en **juillet 2017** : avant, il se traitait sur une autre bourse (ICE).
- Le portefeuille et sa comparaison avec NQ seul portent donc sur **2016-2026**, avec deux sous-périodes :
  2016-2019 et 2020-2026. Le Russell entre dans le portefeuille dès qu'il existe.
- Les critères sont inchangés : t ≥ 3, positif dans chaque sous-période, Sharpe supérieur à NQ seul sur
  la même période.

## Résultats (`analyse.py`, `resultats.txt`, `resultats_brut.txt`) : rejeté

| Marché | Jours de trade | Net par jour (1 micro), toute la période disponible* | t | Avant frais 2016-2026 (t) |
|---|---|---|---|---|
| NQ | 2 326 | +8,55 $ | +2,55 | +18,62 $ (+3,80) |
| ES | 2 382 | −1,83 $ | −0,99 | +6,61 $ (+2,51) |
| Russell (RTY) | 1 426 | −4,50 $ | −2,59 | +0,27 $ (+0,16) |
| Dow (YM) | 1 592 | −5,18 $ | −2,64 | −0,33 $ (−0,17) |
| Or (GC) | 1 329 | −6,91 $ | −2,19 | −0,66 $ (−0,21) |
| Pétrole (CL) | 1 536 | −4,99 $ | −2,58 | +0,94 $ (+0,49) |
| Euro (6E) | 1 592 | −7,70 $ | −9,48 | +0,12 $ (+0,16) |

\* NQ et ES : 2011-2026 ; sur 2016-2026, NQ fait +13,86 $ (t +2,82) et ES −0,49 $ (t −0,19). Les autres
marchés : 2016 (Russell : 2017) - 2026.

**Portefeuille à risque égal (2016-2026) : Sharpe −1,45, t −4,78**, contre Sharpe 0,86 pour NQ seul.
Négatif dans les deux sous-périodes. Critères non remplis : pas de challenge simulé.

- La cassure de la zone de bruit ne gagne, avant frais, que sur les deux grands indices américains
  (NQ et ES). Sur les 5 autres marchés, elle est à zéro avant frais : les frais la rendent perdante.
- Ajouter des marchés rend donc le bot **plus mauvais**, pas plus régulier : les marchés ajoutés n'ont
  pas d'avantage. Le bot reste sur NQ seul.
- Mise en garde sur NQ : sur 7 marchés, un seul tient, et surtout depuis 2020 (t +3,39 ; t −2,28 en
  2011-2015). Cela ressemble davantage à un effet propre au Nasdaq de ces dernières années qu'à une
  règle générale. Son avantage futur est donc incertain, et le robot en argent virtuel le dira.

### Revue du code (niveau maximal)

Vérifié correct :
- heures de séance, changement d'heure et horodatage Databento ;
- valeur du point et tick de chaque micro, formule des frais ;
- changements d'échéance (le pétrole change 12 fois par an, sans aller-retour) ;
- précision des prix de l'euro ;
- aucune journée extrême ne tire le résultat.

Défauts relevés, venant du code copié de `intraday/` ou propres aux marchés plus calmes :
- des allers-retours comptés quand une position est coupée puis reprise dans le même sens au même prix ;
- un dernier contrôle 10 minutes avant la fin sur l'or et l'euro ;
- 14 séances perdues après un jour sans première minute ;
- des jours joués sur l'ancienne échéance, qui ne s'échange presque plus.

Corrigés tous ensemble, ils déplacent les t de 0,1 à 0,4 point et **aucun marché ne devient positif**.
Le verdict ne change pas. `resultats.txt` contient maintenant aussi les chiffres avant frais (produits
par `analyse.py`).
