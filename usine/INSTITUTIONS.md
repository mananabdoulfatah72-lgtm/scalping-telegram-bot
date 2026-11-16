# Ce que font les logiciels des institutions, et ce qu'on en a tiré pour ton compte (16 novembre 2026)

## D'où viennent les preuves, et pourquoi pas REA

Les logiciels internes des grands fonds (Citadel, Renaissance, Two Sigma, Man AHL…) ne sont distribués à personne.
- REA ne lit que des fichiers présents sur ton PC.
- Se procurer ces logiciels autrement serait un vol de secrets d'affaires.

Ce qui est public, c'est le code que des institutions ou leurs praticiens publient eux-mêmes. On le lit en source, avec
les commentaires, ce qui vaut mieux qu'une reconstruction par REA. Trois projets ont été clonés et lus le 16 novembre :

| Projet | Qui | Version lue | Ce que c'est |
|---|---|---|---|
| pysystemtrade | Rob Carver (ancien de Man AHL d'après ses livres ; le dépôt dit seulement que c'est « son propre moteur de backtest et de trading ») | commit `bbf5cf8`, 2 nov. 2026 | Système complet de trading de futures, du backtest à la production (Interactive Brokers) |
| NautilusTrader | Nautech Systems | commit `33492c8`, 16 nov. 2026 | Plateforme de trading : moteur de risque, exécution, rapprochement |
| LEAN | QuantConnect | commit `29b8082`, 16 nov. 2026 | Moteur de backtest et de trading |

**Ce que je ne sais pas :** si les grands fonds utilisent en interne exactement ces mécanismes. Ce sont des logiciels
publics écrits par des praticiens ; les systèmes internes ne sont pas publics.

## Leurs fonctions, ce que ton système a déjà, ce qui manquait

### 1. La taille suit le risque, jamais un nombre de contrats fixe

**Chez eux (pysystemtrade).**
- `systems/positionsizing.py`, ligne 128 : `subsystem_position_raw = vol_scalar * forecast / avg_abs_forecast`.
- Ligne 201 : `vol_scalar = cash_vol_target / instr_value_vol`.
- Lignes 491 - 493 : objectif de risque annuel en dollars = capital × pourcentage de volatilité visé / 100.
- `sysdata/config/defaults.yaml` : `percentage_vol_target: 16.0` (ligne 221), `average_absolute_forecast: 10.0`
  (ligne 143), `forecast_cap: 20.0` (ligne 141).
- **La logique :** la position est calculée pour que chaque marché risque une part fixe du capital, corrigée par sa
  volatilité. Quand le marché s'agite ou que le capital baisse, la taille baisse d'elle-même.

**Chez toi.** Le frein du Bot 3 en 1 fait la même chose avec le seul capital qui compte chez Bulenox : le coussin
au-dessus du plancher.
- `bot3en1/Bot3en1.Core/RegleCompte.cs`, lignes 11 - 18 (branche `claude/optimistic-ptolemy-xs24ra`) : coussin = solde
  − plancher ; la zone passe sur 1 MES quand le coussin est sous 2 500 − 750 = 1 750 $.

**Mesuré aujourd'hui** (`pupitre.py`, test R de [REGLES.md](REGLES.md) ; 2 927 séances, 2015 → 25 septembre 2026) :

| Depuis une marge de 700 $ | Comptes perdus en 22 séances | En 250 séances |
|---|---|---|
| P0 : sans frein | 41,4 % | 64,5 % |
| P1 : frein actuel (zone sur MES) | **25,1 %** | 61,8 % |
| P2 : frein, et secours Supertrend aussi sur MES | **16,2 %** | 59,6 % |

- **Le frein actuel (P1) protège ton mois :** 41 % de comptes perdus sans lui, 25 % avec.
- **Il a un prix sur un Master neuf :** sur 250 séances, 42,4 % de comptes perdus contre 38,5 % sans frein. Sur MES, la
  zone gagne beaucoup moins (+9,2 $ par séance tradée, contre +30,8 $ sur MNQ), donc le compte remonte plus lentement.
- **P2 n'est pas recommandée par la règle fixée avant le calcul.** Sur un Master neuf et 250 séances, le premier retrait
  passe de 51,7 % à 44,1 %, soit 7,6 points de moins, au-delà des 2 points permis.
- **Pour ta situation seule (700 $ de marge), P2 fait mieux** : 16 % de comptes perdus dans le mois au lieu de 25 %,
  pour un gain moyen de +131 $ au lieu de +169 $. C'est une lecture après coup, pas le verdict de la règle.
- **P2 demande une modification du bot Supertrend.** Il compte ses pertes en MNQ, à 2 $ par point du NQ
  (`bot3en1/Supertrend.Quantower/SupertrendStrategy.cs`, ligne 347 : `Taille * (2 * bot.Position * (dernierPrix -
  bot.Entree) - 3.0)`). Sur MES, sa limite de 400 $ serait donc fausse.

### 2. Des états de trading : actif, réduction seule, arrêt

**Chez eux.**
- NautilusTrader, `docs/concepts/execution/index.md`, lignes 283 - 291 : `ACTIVE` (tout est permis), `REDUCING`
  (seulement des ordres qui réduisent la position), `HALTED` (plus aucun nouvel ordre). Le moteur de risque refuse les
  ordres selon l'état : `crates/risk/src/engine/mod.rs`, lignes 1070 - 1071.
- pysystemtrade, `sysobjects/production/override.py`, lignes 8 - 16 : `Close`, `No trading`, `Reduce only`, `No override`.

**Chez toi.** Le fichier `STOP` (`C:\Bot3en1\STOP`, `C:\SupertrendNQ\STOP`) est l'état « arrêt » : la position est
fermée et le bot ne reprend plus ([RISQUE.md](RISQUE.md)).

**Pas d'ajout.** L'état « réduction seule » ne sert pas chez Bulenox : 5 séances sans trade, et le compte est perdu.

### 3. Des contrôles avant chaque ordre, et une coupure sur la perte

**Chez eux.**
- NautilusTrader, `docs/concepts/execution/index.md`, lignes 186 - 205 : chaque ordre passe par le moteur de risque
  (taille maximale en notionnel, nombre d'ordres par seconde, ordres « reduce only » qui ne doivent pas grossir la position).
- LEAN, `Algorithm.Framework/Risk/MaximumDrawdownPercentPortfolio.cs`, lignes 41 - 89 : si le portefeuille perd plus de
  5 % (réglage par défaut) depuis son départ ou son plus haut, toutes les positions sont ramenées à zéro.

**Chez toi.**
- Limite de perte du jour : 1 000 $ pour le Bot 3 en 1, 400 $ pour le Supertrend ([RISQUE.md](RISQUE.md)).
- Une seule position à la fois, et la taille est un réglage borné du bot.
- Des stops plus serrés (200 et 300 $) ont été mesurés le 16 novembre : ils ne protègent presque pas le compte et coûtent
  15 à 30 % du gain. Rien à ajouter.

### 4. Le rapprochement : le système vérifie que le courtier a bien ce qu'il croit

**Chez eux.** NautilusTrader, `docs/concepts/execution/reconciliation.md`, lignes 1 - 5 : aligner l'état réel des ordres
et des positions chez le courtier avec l'état interne du système, au démarrage et en continu.

**Chez toi, déjà là.** Le Bot 3 en 1 lit la position du compte et gère les écarts : `Bot3en1Strategy.cs` (branche
`claude/optimistic-ptolemy-xs24ra`).
- Ligne 1001 : position retrouvée sur le compte, le trade en cours est repris.
- Ligne 1023 : position revenue telle quelle après une coupure.
- Ligne 1041 : position fermée hors du bot (à la main ou par le courtier), le bot ne la rouvre pas.

### 5. La mesure du glissement réel : ce qui manquait

**Chez eux.** pysystemtrade, `sysproduction/reporting/data/trades.py`, lignes 143 - 193. Pour chaque ordre :
- `delay` : prix de la décision contre le milieu de la fourchette à l'envoi ;
- `bid_ask` : milieu de la fourchette contre le prix affiché ;
- `execution` : prix affiché contre le prix obtenu.
- Ligne 189 : glissement = sens × (premier prix − second prix), négatif quand c'est contre toi.

**Chez toi, avant aujourd'hui.**
- Le bot écrit l'ordre envoyé (`Bot3en1Strategy.cs`, ligne 1058 : « ordre envoye : achat 1 MNQ (position 0 -> 1) »),
  mais pas le prix obtenu.
- L'usine suppose 1 $ et 1 tick par ordre, soit 3 $ l'aller-retour sur MNQ (`moteur.py`, `COUT`). Personne ne l'avait
  vérifié sur tes vrais ordres.
- **Pourquoi c'est important :** la zone gagne en moyenne +30,8 $ par séance tradée sur MNQ, et son avantage est fin
  (profit factor 1,02 par minute). Chaque tick de glissement en plus par ordre coûte environ 1 $ par trade.

**Construit aujourd'hui : `usine/rapprochement.py`.**
- Il lit le journal du bot et l'export des exécutions de Quantower.
- Il rattache chaque exécution à l'ordre du bot, puis mesure le glissement contre la clôture de la minute de décision du
  NQ, à la façon de pysystemtrade.
- Il signale les ordres sans exécution, et les exécutions sans ordre du bot (trade à la main, autre bot).
- **Testé seulement sur un exemple fabriqué** : les glissements attendus (−2 ticks à l'achat, −1 tick à la vente), l'ordre
  MES sans exécution et l'exécution orpheline sont tous retrouvés.
- **Ce que je ne sais pas :**
  - le nom exact des colonnes de l'export de Quantower : le script les reconnaît par leur nom, et s'arrête en montrant
    l'en-tête s'il en manque une ;
  - le fuseau horaire des heures exportées (celui de l'affichage de Quantower, Paris par défaut) ;
  - l'écart de prix entre MNQ et NQ au même instant : en général 0 ou 1 tick, il s'ajoute au glissement mesuré.

```bash
python usine/rapprochement.py C:\Bot3en1\journal.txt executions.csv --fuseau Europe/Paris
```

## Les pistes lancées aujourd'hui

| Piste | Résultat | Ce que tu fais |
|---|---|---|
| Bande plus large (k de 1,4 à 2,4) | Rejetée à la porte 2 : 13,2 % des permutations font aussi bien (1 % exigé). Le milieu du plateau de l'idée 1 (k = 1,4 ; 30 jours) n'est pas adopté non plus : −848 $ par an contre le réglage du bot (t −1,17), −1 357 $ par an depuis 2023 (`adoption.py`). | Rien : le bot garde k = 1,0 sur 14 jours. |
| Sous le frein, le secours aussi sur MES (test R) | Voir la partie 1 : non recommandée par la règle ; meilleure pour ton mois à 700 $. | À toi de choisir (plus bas). |
| Mesure du glissement réel | Outil prêt, testé sur un exemple fabriqué seulement | Le lancer après quelques séances. |

**Ce qui n'a pas été relancé :** la nuit, les combinaisons, les autres marchés, les tailles plus grandes, les stops serrés,
le filtre VIX. Tous ont déjà été jugés avec des règles fixées d'avance ([rea/PISTES.md](../rea/PISTES.md)).

## Ce qui reste incertain dans les calculs d'aujourd'hui

- **Le prix du S&P aujourd'hui** n'est pas dans le dépôt : il est estimé par 28 500 × S&P / NQ du 25 septembre 2026,
  soit 7 201 points. 1 MES vaut donc environ 36 000 $ de notionnel.
- **Le test R s'arrête au 25 septembre 2026**, dernière séance du fichier du S&P.
- **Sur MES, les décisions sont prises sur le NQ** et appliquées aux minutes du S&P. Les vrais remplissages du MES ne
  sont pas connus.
- **Le plancher.** La porte 5 l'arrête à 50 000 $, alors que le réglage du bot l'arrête à 50 100 $ (`Blocage` = 100).
  Ça ne compte que pour un compte qui a dépassé 52 500 $ environ ; à 700 $ de marge, ça ne change rien.
- **Précisions apparues en codant, avant tout résultat :**
  - le frein est codé comme dans le bot (coussin sous 1 750 $), y compris quand le plancher est arrêté ;
  - le glissement à la limite du jour vaut 1 point de MES, soit 5 $.
