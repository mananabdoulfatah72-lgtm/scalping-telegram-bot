# Tournoi 9 : une troisième source, sur d'autres marchés

La zone de bruit (NQ, intraday) et le RSI(2) (NQ, plusieurs jours, achat après une baisse) jouent tous
les deux le Nasdaq. Une troisième source vraiment indépendante devrait venir d'**autres marchés** :
or, pétrole, euro, obligations américaines. Demande de l'utilisateur du 2 octobre 2026.

## Règles (fixées le 2 octobre 2026, avant tout calcul)

### Données et exécution

- **Barres journalières Databento** (`fonds/donnees/futures_1d.csv.gz`), séance CME complète, juin 2010
  - septembre 2026. Rendements continus sans saut d'échéance (`fonds/sources.py futures40`). Les
  indicateurs sont calculés sur la série continue obtenue à partir de ces rendements.
- **Décision à la clôture de la séance, exécutée à ce prix** (ordre « trade at settlement »), plus
  1 tick de glissement et 1 $ par ordre. Position gardée d'une clôture à la suivante. Un passage
  d'échéance en position coûte un aller-retour.
- **Contrats** :
  - or : micro MGC, 10 $ le point, tick 0,1 ;
  - pétrole : micro MCL, 100 $ le point, tick 0,01 ;
  - euro : micro M6E, 12 500 $ le point, tick 0,0001 ;
  - obligation 10 ans : ZN standard, 1 000 $ le point, tick 1/64. Il n'existe pas de micro ZN.
- Achat et vente : sur ces marchés, rien ne justifie de n'acheter que, comme sur les actions.

### Les stratégies (13 essais)

| # | Stratégie | Règle | Marchés | Source |
|---|---|---|---|---|
| 1 | RSI(2) symétrique | achat si clôture > moyenne des 200 et RSI(2) < 10, sortie quand clôture > moyenne des 5 ; vente si clôture < moyenne des 200 et RSI(2) > 90, sortie quand clôture < moyenne des 5 | or, pétrole, euro, ZN | Connors, Alvarez (2008) |
| 2 | Double 7 symétrique | achat si clôture > moyenne des 200 et plus bas des 7 clôtures, sortie au plus haut des 7 ; l'inverse à la vente | or, pétrole, euro, ZN | Connors, Alvarez (2009) |
| 3 | Rebond de 5 jours symétrique | variation du jour dans les 10 % les plus basses des 252 précédentes : achat 5 séances ; dans les 10 % les plus hautes : vente 5 séances | or, pétrole, euro, ZN | inversion à court terme |
| 4 | Fin de mois des obligations | achat du ZN à la clôture de l'avant-dernière séance du mois, vente à la clôture de la dernière | ZN | Hartley, Schwarz (2019) |

Le dernier jour de bourse du mois est déterminé par le calendrier (jours ouvrés hors jours fériés de
la Bourse), sans regarder les données futures.

### Le tri (comme le tournoi 8)

1. **Exploration 2011-2022**, sans charger les années suivantes. Deux conditions :
   - t ≥ 2 sur les rendements quotidiens nets ;
   - battre 95 % de 1 000 placements au hasard des mêmes trades (même sens, même durée).
2. **Coffre 2023 - septembre 2026, ouvert une seule fois** pour les survivants :
   - t ≥ seuil de Bonferroni pour m survivants ;
   - au moins 3 années positives sur 4.
3. **Avec la zone et le RSI(2)** pour un survivant qui passe :
   - corrélations ;
   - Sharpe du mélange au même risque ;
   - challenge Phidias avec 3 sources (f × coussin / √3 chacune, au moins 1 micro), comparé aux
     2 sources actuelles.
4. Mesures descriptives pour chaque essai : Sharpe, perte maximale pour 1 contrat, temps en position,
   trades, trades gagnants, gain moyen, perte moyenne.
5. Les 13 essais sont inscrits dans `fonds/essais.csv`. Rien n'est ajouté ni changé après avoir vu
   les résultats.

## Résultats (2 octobre 2026) : aucun survivant, coffre non ouvert

`tournoi9.py` → `exploration9.txt`, `exploration9.csv`. Tests : `test_tournoi9.py`, 5 contrôles passés
(rendements sans saut d'échéance, aucun regard vers le futur, fin de mois au calendrier, trade à la
main, placements au hasard fidèles).

Détail d'exécution précisé en codant, sans voir de résultat : les séances courtes des jours fériés de
la Bourse (le CME ouvre parfois) sont fusionnées avec la séance suivante, pour garder une décision par
vraie séance. Les variations journalières de plus de 50 % (pétrole sous zéro, avril 2020) sont
neutralisées, comme dans `fonds/`.

| Stratégie | Or | Pétrole | Euro | ZN |
|---|---|---|---|---|
| RSI(2) symétrique | t −0,61 | t +0,66 | t −0,16 | t +0,25 |
| Double 7 symétrique | t −0,07 | t −1,12 | t +1,06 (bat 90,5 % du hasard) | t +0,24 |
| Rebond de 5 jours symétrique | t −0,92 | t −0,61 | t −0,85 | t −1,19 |
| Fin de mois des obligations | — | — | — | t +0,07 |

**Aucun des 13 essais n'atteint t ≥ 2.** Le retour vers la moyenne de quelques jours, qui marche sur
le Nasdaq (RSI(2), tournoi 8), ne marche pas sur l'or, le pétrole, l'euro ni les obligations. L'effet
de fin de mois des obligations n'apparaît pas sur le ZN en 2011-2022.

**Et la tendance ?** C'est la famille qui marche sur ces marchés, mais elle a déjà été étudiée
(`tendance/`) : Sharpe négatif sur 2023-2026 (−0,16), et sur un compte de 50 000 $ les contrats micro
sont trop gros (sans eux, Sharpe 0,16). Elle ne convient pas comme troisième source pour le challenge.
