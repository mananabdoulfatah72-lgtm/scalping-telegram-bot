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
