# Filtre delta : variante « zone neutre » (règles fixées le 19 octobre 2026, avant tout calcul)

Demande de l'utilisateur, 19 octobre 2026. En une semaine, deux gros mouvements de la zone ont été écartés par le filtre
delta H1 alors que le delta des 30 minutes était presque nul :
- 16 octobre 2026, vente de 10 h (New York) : delta +72 sur environ 93 000 contrats (0,08 %), +447,75 points ratés ;
- 19 octobre 2026, achat de 11 h 30 : delta −60, le prix a ensuite monté (pas encore mesuré).

Question : un delta presque nul doit-il vraiment écarter un trade ?

## Règle testée (une seule)

**Variante N1** : un trade de zone est gardé si le signe du delta des 30 minutes va dans son sens (filtre H1 actuel),
**ou** si le delta est presque nul : |achats − ventes| < **1 %** de (achats + ventes) sur les mêmes 30 minutes.
Seuil de 1 % proposé à l'utilisateur avant tout calcul et fixé ici. Fenêtre : la même que le bot (les 30 barres
d'une minute qui finissent à la clôture de la minute du signal).

## Données

1. **Databento**, 1er avril - 2 octobre 2026 : les 99 trades de zone de `orderflow/zone_avril_septembre_2026.csv`
   (colonne `delta30` = delta ÷ volume des 30 minutes). C'est la période où le filtre H1 a été trouvé : elle sert ici
   à mesurer, pas à régler (le seuil est déjà fixé).
2. **Rithmic** (export de l'utilisateur, `filtre_h1/donnees_rithmic/transactions_NQZ6_rithmic.csv`) : seulement les
   séances après le 2 octobre 2026 (avant, ce sont les mêmes jours que Databento).
3. Le 19 octobre 2026 ne peut pas être mesuré tant que ses transactions ne sont pas exportées.

## Mesures (publiées dans tous les cas)

- Trades « repêchés » : écartés par H1, gardés par N1 (|delta| < 1 %) ; nombre et gain moyen en points.
- Total en points sur chaque période : zone sans filtre, filtre H1, variante N1 ; gardés contre écartés (t de Welch)
  pour H1 et N1.
- Descriptif seulement, sans décision : seuils 0,5 %, 2 % et 3 % ; trades écartés par H1 coupés en « delta fort »
  (≥ 1 %) et « delta faible » (< 1 %).

## Décision (fixée maintenant)

N1 remplace le filtre H1 dans le bot **seulement si** :
1. au moins **10 trades repêchés** sont mesurés au total ;
2. leur gain moyen est **positif** ;
3. N1 fait au moins aussi bien que H1 sur la période Databento **et** sur la période après le 2 octobre.

Avec moins de 10 trades repêchés : **pas de décision**, le bot ne change pas, et l'étude est relancée quand de
nouvelles séances sont exportées (même règle, même seuil).
