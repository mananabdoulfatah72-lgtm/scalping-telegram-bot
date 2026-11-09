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

## Terminal live (9 novembre 2026) : http://localhost:8765/live

Le même relais sert une deuxième page, faite pour **comprendre ce qui se passe** pendant la séance, comme un terminal
Bloomberg : les marchés, la volatilité, le volume, les nouvelles et le calendrier sur un seul écran, et une lecture en
français qui relie ces chiffres. Elle se met à jour chaque seconde. Aucun ordre n'est passé.

```
Rithmic ──► Quantower ──► Relais NQ ──► http://localhost:8765/live
                             │  NQ, ES et jusqu'à 6 autres contrats, transaction par transaction, de 18 h à 17 h (New York)
                             │  nouvelles (flux RSS), calendrier économique, VIX et cotations (Yahoo, CBOE)
                             └─ journaux des agents, position et solde du compte
```

**Ce que montre la page.**
- **Lecture du marché** : une phrase par sujet, avec un point vert, ambre ou rouge.
  - où en est la séance ; le NQ face à la veille et à son VWAP ;
  - le mouvement des 30 dernières minutes ; la confirmation par l'ES, le Russell et le Dow ;
  - l'activité (volume face à la normale), le flux (achats contre ventes au marché), l'amplitude du jour ;
  - le VIX et sa courbe, les taux à 10 ans et le dollar, les mégacaps ;
  - la prochaine annonce, les nouvelles importantes de l'heure, et le filtre VIX du Bot 3 en 1 pour aujourd'hui.

  C'est une lecture des chiffres affichés, pas un conseil : elle ne prédit rien.
- **Marchés** : chaque contrat de Rithmic, avec sa variation depuis la clôture de la veille, son volume face à la
  normale à la même heure, son delta et sa courbe du jour. Puis le Nasdaq 100 et le S&P 500 au comptant, le taux à 10 ans,
  le dollar et le Bitcoin (Yahoo).
- **Mégacaps** : NVDA, MSFT, AAPL, AMZN, GOOGL, META, AVGO, TSLA, en couleur selon leur variation.
- **Graphique du NQ** :
  - séance US ou depuis 18 h, en 1 ou 5 minutes ;
  - VWAP, clôture de la veille, ES en surimpression si on le demande ;
  - traits pour les annonces du calendrier, losanges rouges pour les nouvelles importantes ;
  - le détail de chaque bougie au survol.
- **Volume et flux** :
  - volume du jour et des 30 dernières minutes face à la normale ;
  - delta depuis 18 h et depuis 9 h 30 ;
  - volume de chaque minute sur 2 heures face au volume habituel, avec le delta cumulé.
- **Gros ordres** : chaque transaction NQ ou ES d'un seul coup au-dessus du seuil réglé (20 NQ, 100 ES par défaut).
- **Volatilité** :
  - VIX, VXN (le VIX du Nasdaq), VIX 9 jours, VIX 3 mois et VVIX ;
  - l'état du filtre VIX du Bot 3 en 1 pour aujourd'hui, d'après les clôtures du CBOE, et ce qu'il deviendrait demain si
    la courbe reste comme elle est à la clôture ;
  - la volatilité réalisée du NQ (30 minutes, 2 heures) face au VXN, l'ATR de 5 minutes, la plage du jour face à la
    moyenne.
- **Calendrier économique** :
  - les annonces américaines fortes et moyennes, et les fortes des autres pays ;
  - heure de Paris et de New York, prévision, précédent, compte à rebours ;
  - la prochaine annonce forte est aussi en haut de la page.
- **Nouvelles** :
  - environ 12 flux gratuits : investingLive (ex-ForexLive, les titres macro les plus rapides), CNBC, MarketWatch, la
    Fed, Yahoo Finance, Seeking Alpha, Investing.com, Nasdaq et Google Actualités en anglais et en français ;
  - étiquettes en français (Fed, Inflation, Emploi, Géopolitique, Mégacaps, IA, Taux, Pétrole, Résultats, Urgent) ;
  - les importantes en rouge, filtres et recherche ;
  - « nouveau » pendant 5 minutes, et un son si tu coches « son des alertes ».
- **Agents et compte** : position MNQ, latent, solde et les dernières lignes des journaux des bots.

**Réglages en plus dans Relais NQ** (tout est facultatif, les valeurs par défaut marchent) :

| Réglage | Quoi mettre |
|---|---|
| ES | **ESZ6** (recommandé : la confirmation et le graphique s'en servent) |
| Marchés 3 à 8 | par exemple **YMZ6**, **RTYZ6**, **CLZ6**, **GCZ6**, **6EZ6**. Vide = pas de ligne. **ZN** n'est pas dans les produits permis par Bulenox : il est peut-être absent de ton abonnement de données |
| Gros ordre NQ / ES | 20 et 100 contrats |
| Nouvelles, calendrier, cotations, clôtures du VIX | ne pas toucher (adresses des sources gratuites) |

**Les limites, à connaître.**
- Les contrats de Rithmic sont en temps réel. Les cotations de Yahoo (VIX, taux, dollar, actions) sont relues chaque
  minute et peuvent avoir quelques minutes de retard. Si Yahoo ne répond plus, le VIX vient du CBOE (cotation différée).
- Les nouvelles sont relues chaque minute : un titre apparaît en général une à deux minutes après sa publication. Ce
  sont des sources gratuites, sans garantie ; la page dit lesquelles répondent.
- Le calendrier vient d'un fichier gratuit de la semaine en cours (relu toutes les 30 minutes) ; le résultat publié
  (« réel ») n'y figure pas toujours.
- La « normale » du volume et de la plage vient des 20 dernières séances que Quantower donne au relais. Sans cet
  historique, le NQ et l'ES utilisent l'historique de la station (séance 9 h 30 - 16 h seulement) ; les autres
  contrats affichent « — ».
- Bulenox interdit les VPN et les VPS : le relais et la page tournent sur ton PC, comme les bots.

**Démo pour s'entraîner** (sans Quantower) : `terminal/live/demo.py` produit la même page, avec un lecteur qui rejoue la
vraie séance du 28 octobre 2026 (jour de la Fed) et un guide pas à pas. Elle est publiée sur claude.ai (page privée « NQ Live
Démo »).

**Testé** dans l'imitation de Quantower (`Relais.TestQuantower`), avec la séance du 2 novembre rejouée transaction par
transaction pour le NQ. Le test utilise :
- l'ES, le Dow et le Russell tirés du NQ, le pétrole et l'or au hasard (dans le test seulement) ;
- des flux RSS et Atom d'essai, dont une nouvelle qui arrive pendant la séance, et une source en panne ;
- un calendrier d'essai, des cotations d'essai et les vraies clôtures du VIX d'octobre.

Tout s'affiche sans erreur, y compris sur téléphone. Les formats des vraies sources ont été vérifiés depuis GitHub
Actions (`terminal/live/sonder_sources.py`).

```
PORT=8788 ESSAIS=$PWD/Relais.TestQuantower/essais LIVE_PAGE=$PWD/Relais.Quantower/live.html \
  dotnet run -c Release --project Relais.TestQuantower -- <dossier vide> <minutes.csv> Relais.Quantower/station-direct.html 2026-11-02 100 90
```
puis ouvrir http://localhost:8788/live pendant qu'il tourne.
