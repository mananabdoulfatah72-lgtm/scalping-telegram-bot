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
