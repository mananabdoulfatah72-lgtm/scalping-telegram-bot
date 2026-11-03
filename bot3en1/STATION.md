# Station NQ en direct (3 novembre 2026)

La station du terminal (tous les panneaux sur un seul écran), mais **branchée sur le vrai marché** : Quantower reçoit les
transactions de Rithmic, une petite stratégie, **Relais NQ**, les transmet à une page ouverte dans Chrome ou Edge sur le
même PC. Le relais **ne passe aucun ordre**.

```
Rithmic ──► Quantower ──► stratégie « Relais NQ » ──► http://localhost:8765 ──► Chrome / Edge
                              │  NQ (et ES) transaction par transaction
                              │  position MNQ et solde du compte
                              └─ journaux de Bot 3 en 1 et de Supertrend NQ
```

## Installation

La ligne PowerShell habituelle (elle met aussi à jour les bots) :

```
irm https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/refs/heads/claude/optimistic-ptolemy-xs24ra/bot3en1/telecharger.ps1 | iex
```

Elle compile le relais dans `Settings\Scripts\Strategies\RelaisNQ` et copie la page dans `C:\StationNQ`.

## Chaque jour

1. Quantower ouvert et connecté à Rithmic.
2. Menu Stratégies > Strategies manager > **Relais NQ (station en direct)**, avec ces réglages :

| Réglage | Quoi mettre |
|---|---|
| NQ (prix) | **NQZ6** (le contrat du moment ; NQH7 après le changement d'échéance de décembre) |
| ES (facultatif) | ESZ6 si tu veux le S&P 500 dans les cotations, sinon vide |
| Compte à surveiller | ton compte Bulenox (position et solde réels) |
| MNQ du compte | **MNQZ6** |
| Port local | 8765 |
| Dossier de la station | `C:\StationNQ` |
| Journaux des agents | `C:\Bot3en1;C:\SupertrendNQ` |
| Historique | ne pas toucher |

3. Lance-la (Run), puis ouvre **http://localhost:8765** dans Chrome ou Edge. Le relais peut tourner en même temps que
   Bot 3 en 1 et Supertrend NQ : il ne fait que lire.

## Ce que montre la page

- **Badge** en haut : `DIRECT` (vert) = transactions qui arrivent ; `HORS SÉANCE` = avant 15 h 30 ou après 22 h (Paris) ;
  `PAS DE TRANSACTION` = séance ouverte mais rien depuis 2 minutes (connexion Rithmic ?) ; `COUPÉ` = la page ne reçoit plus
  rien du relais (Quantower ou la stratégie arrêtés). La page se reconnecte toute seule.
- **Graphique 15 minutes** : la bougie en cours se redessine à chaque transaction ; EMA 8 à 89, Bollinger 20-2, RSI,
  MACD, ATR et signal ML sont recalculés à chaque fois sur cette bougie. Les triangles bleus sont les entrées de la règle
  Supertrend recalculée dans la page.
- **Cotations** : dernier prix, variation, VWAP, ligne du Supertrend, zone de bruit, clôture de la veille.
- **Flux des signaux** : les signaux calculés (Supertrend, VWAP, Bollinger, RSI, zone, ML) apparaissent quand leur bougie
  est terminée ; les messages de Bot 3 en 1 et de Supertrend NQ arrivent tels qu'ils les écrivent dans leur journal.
- **Compte et agents** : ta vraie position MNQ, le latent et le solde ; l'état de chaque agent d'après son journal ; la
  règle Supertrend recalculée ici, pour vérifier que l'agent fait bien ce qu'il doit faire.
- **Risque** : ATR, régime de volatilité, signal ML, et le **résultat réel du jour** (solde + latent) face à ta limite.
  La **distance au plancher** est sous le tableau des agents.
- **Reliefs 3D** : ruban des EMA (la boule blanche est le dernier prix), volume par prix des 30 dernières séances
  (aujourd'hui devant, minute par minute) et amplitude des bougies de 15 minutes.
- **Ordres papier** : pour t'entraîner ; remplis au dernier prix, rien n'est envoyé au courtier.

En haut, deux cases que la page garde en mémoire :

- **limite du jour** (400 $ par défaut) : la jauge « jour réel » passe à l'orange puis au rouge en s'en approchant ;
- **plancher** (49 000 $) : il monte tout seul avec ton plus haut solde vu (solde − 2 500 $, jamais au-dessus de 50 100 $),
  comme la règle Option 1 de Bulenox.

Le résultat du jour part du **premier solde vu par la page ce jour-là** : ouvre la page avant ton premier trade.

## À savoir

- Le signal ML (régression logistique, 1 heure) n'est **pas un avantage** : t = 1,21 sur 2014-2026. Il est affiché
  pour information, rien ne trade dessus.
- L'historique (30 séances) vient du robot du dépôt, remplacé par les barres d'une minute de Quantower quand la plateforme
  les donne ; la séance du jour vient des transactions déjà passées, puis du direct.
- La page n'est visible que sur ce PC (adresse 127.0.0.1). Les reliefs 3D et les polices viennent d'internet.

## Vérifications faites

Relais testé dans l'imitation de Quantower (`Relais.TestQuantower`) avec ta séance du 2 novembre rejouée transaction par
transaction, et la page ouverte dans un vrai navigateur :

- la page suit la séance minute par minute, sans erreur, à 1600, 1366 et 390 pixels de large ;
- signal ML, RSI et EMA calculés par la page = ceux du terminal (écart maximal de 0,0005 sur la probabilité) ;
- règle Supertrend recalculée = moteur vérifié (achat à 28 710,25, sortie et vente à 28 662, fermeture à 28 175) ;
- messages de l'agent, position MNQ et solde du compte affichés à leur arrivée ; ordres papier remplis au dernier prix.

Pour refaire le test (dans `bot3en1`) :

```
dotnet run -c Release --project Relais.TestQuantower -- <dossier vide> <minutes.csv> Relais.Quantower/station-direct.html 2026-11-02 300 30
```

puis ouvrir http://localhost:8765 pendant qu'il tourne. La page est produite par `terminal/assembler_direct.py`.
