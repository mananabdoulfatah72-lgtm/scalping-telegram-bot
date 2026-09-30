# Machine évolutive : des stratégies qui naissent, sont testées et meurent (version honnête de SETS)

Inspirée de SETS MACHINE (github.com/Shelpid/sets). Son propre README le dit : c'est « un jouet de
recherche ». Il utilise 100 jours de BTC, dont 30 jours de test réutilisés à chaque génération, et
l'achat simple y gagne plus que les stratégies. Ici, on garde la boucle (observer → muter → tester →
sélectionner → déployer), mais pour un **challenge 50K futures** et avec des contrôles que SETS n'a pas.

## Règles (fixées le 30 septembre 2026, avant tout calcul)

### Données et découpage

Barres de 5 minutes du Nasdaq 100 (NQ) et du S&P 500 (ES), séance de 9 h 30 à 16 h (New York).
Données Databento, 2011-2026, contrats micro MNQ et MES. Trois périodes :

| Période | Dates | Rôle |
|---|---|---|
| Entraînement | 2011 - 2018 | la sélection naturelle (fitness) |
| Validation | 2019 - 2022 | la « porte » : on meurt si on échoue |
| **Coffre** | **2023 - septembre 2026** | **ouvert une seule fois, à la fin, pour les finalistes** |

Pendant l'évolution, le programme **ne charge pas** les données après le 31 décembre 2022 : le coffre
est physiquement hors de portée de la recherche.

### Le génome (9 gènes, 4 espèces)

| Gène | Valeurs | Rôle |
|---|---|---|
| espèce | momentum, retour à la moyenne, cassure de canal, range d'ouverture | logique d'entrée |
| marché | NQ, ES | contrat traité |
| rétrospection L | 6 à 120 barres de 5 min | fenêtre des moyennes, écarts-types, canaux (range d'ouverture : 1 à 12 barres) |
| seuil Z | 0,25 à 3,0 | écart minimal (en écarts-types) pour entrer |
| sens | les deux, achat seul, vente seule | sens autorisés |
| stop | 0,10 % à 1,50 % du prix | perte maximale par trade |
| objectif | 0,10 % à 3,00 % du prix | prise de bénéfice |
| heure de début | 9 h 35 à 14 h 00 | premières entrées permises (dernières à 15 h 00) |
| filtre de volatilité | aucun, jours agités seulement, jours calmes seulement | selon l'amplitude de la veille comparée aux 20 jours d'avant |

Espèces :
- **momentum** : achat si la clôture dépasse sa moyenne de L barres de plus de Z écarts-types, vente
  si elle est en dessous de −Z ;
- **retour à la moyenne** : l'inverse ;
- **cassure de canal** : achat si la clôture dépasse le plus haut des L barres précédentes de Z écarts-
  types, vente sous le plus bas ;
- **range d'ouverture** : même chose avec le plus haut et le plus bas des L premières barres du jour.

La grille avec renforcement de SETS n'est pas reprise. Elle double la mise en perdant, ce qui est
incompatible avec la perte maximale d'un challenge.

### Exécution (pas de triche)

- Le signal est calculé à la clôture de la barre j et exécuté à l'ouverture de la barre j + 1.
- Une seule position à la fois.
- Le stop est vérifié avant l'objectif dans la même barre. Si le prix saute le stop, la sortie se
  fait à l'ouverture de la barre.
- Tout est fermé à 16 h. Pas de trade le jour d'un changement d'échéance ni le lendemain.
- Frais : 1 $ par ordre et 1 tick de glissement par ordre, soit 1,5 point de NQ ou 0,9 point d'ES par
  aller-retour.
- Un test vérifie que modifier une barre future ne change aucun signal passé.

### La boucle (comme SETS)

- 96 stratégies par génération.
- 8 immigrants tirés au hasard.
- 80 descendants : tournoi dans chaque espèce, croisement uniforme, mutation gaussienne (p = 0,18).
- Quotas par espèce : 20 descendants chacune.
- On garde les 4 meilleures, plus la meilleure de chaque espèce.
- 60 générations par graine, 5 graines.

**Fitness** (entraînement 2011-2018) : Sharpe annualisé des rendements quotidiens nets. Si la stratégie
fait moins de 150 trades, sa fitness est réduite en proportion.

**Porte** (validation 2019-2022) : Sharpe ≥ 0,5 et au moins 100 trades.

**Leader affiché** : la meilleure fitness parmi celles qui passent la porte, comme SETS.

### Les contrôles que SETS n'a pas

1. **Évolution sur du bruit.** Même programme, 5 graines, sur des données où, chaque jour, les barres
   de 5 minutes sont mélangées au hasard. La volatilité et le résultat du jour sont conservés, mais
   toute structure intraday exploitable est détruite. Cela mesure ce que la sélection produit **par pur
   hasard**. Le champion réel doit avoir un Sharpe de validation supérieur à celui des 5 champions sur
   bruit.
2. **Finalistes fixés par une règle.** Parmi toutes les stratégies évaluées sur les 5 graines réelles
   avec un Sharpe d'entraînement ≥ 0,5, on retient la meilleure de chaque espèce par Sharpe de
   validation, soit 4 finalistes. Le **champion** est celle des 4 qui a le meilleur Sharpe de
   validation.
3. **Ouverture du coffre, une seule fois.** Le champion passe s'il remplit tout ce qui suit :
   - t ≥ 2,5 sur 2023-2026 (correction pour 4 finalistes) ;
   - gain net positif sur 2023, 2024, 2025 et 2026 ;
   - Sharpe de validation supérieur à celui des 5 champions sur bruit.

   Les 3 autres finalistes sont donnés pour information.
4. **Challenge 50K.** Si le champion passe : bot coussin (Topstep, Apex et Phidias, comme dans
   `challenge/`) sur 2023-2026, comparé au bot zone de bruit et au même bot sans avantage. Puis ce que
   rapporte le compte financé.
5. Registre des essais : toutes les stratégies évaluées sont comptées dans `fonds/essais.csv`.

Suivi en direct : page au style de SETS (réserve génétique, génome du leader, sélection, moteur de
trading), mise à jour pendant les calculs.
