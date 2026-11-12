# Chantier des 11 et 12 novembre 2026 : résultats

Règles fixées avant chaque calcul : [`REGLES.md`](REGLES.md) (l'historique git montre que chaque règle a été
enregistrée avant son calcul). Détail de chaque partie : dossier `resultats/`.

## En bref

- **Un atout ressort pour ton challenge : la nuit de secours.** Quand le compte a passé 2 jours de trading sans aucun
  trade, on achète 1 MNQ à 18 h (New York) avec un stop à 0,50 %, et on vend à 9 h 30. En simulation, plus aucun
  compte n'est perdu par la règle d'inactivité et 70 % des Masters atteignent le 3e retrait, contre 0 % pour le bot
  seul.
- **Copier les institutions et les banques ne donne rien.** 10 tests sur leurs positions déclarées à la CFTC : aucun
  ne passe, et tous font moins bien qu'acheter chaque jour sans regarder personne.
- **L'arbitrage n'est pas une solution de rechange.** Sur les futures, il a déjà été testé dans le projet et il perd.
  Polymarket est bloqué en France depuis juillet 2026.
- **Les six modèles du message du 11 novembre sont tués.** Aucun ne gagne sur des données qu'il n'a pas vues.
- **Ce qui tient : la zone de bruit (ton Bot 3 en 1) et la hausse lente du Nasdaq pendant la nuit.**
- **La contre-revue a trouvé un défaut dans mes données de nuit.** Il est corrigé et tous les chiffres de ce rapport
  sont recalculés. Elle a été coupée par la limite d'utilisation : seule la partie « nuit » a été relue par un
  regard indépendant.

Aucun système ne rapporte 847 $ par nuit ni ne transforme 100 $ en 2 981 $ en 45 minutes. Ces récits ne donnent ni
données, ni frais, ni période de contrôle : ils ne peuvent pas être reproduits.

## Le plan pour ton challenge

### 1. La nuit de secours (à faire à la main ou à automatiser)

| | |
|---|---|
| Quand | dès que le compte a passé 2 jours de trading de suite sans aucun trade |
| Entrée | achat de 1 MNQ à 18 h, heure de New York (minuit à Paris) |
| Stop | 0,50 % sous le prix d'entrée : environ 140 points de NQ aujourd'hui, soit −285 $ |
| Sortie | vente à 9 h 30, heure de New York (15 h 30 à Paris), si le stop n'a pas été touché |
| Ensuite | cette nuit compte comme un trade : le compteur d'inactivité repart de zéro |
| Si la marge est sous 1 750 $ | 1 MES au lieu de 1 MNQ : c'est le frein de ton bot |

Trois à quatre semaines par an (mi-mars, fin octobre), New York et Paris n'ont que 5 heures d'écart : l'entrée est
alors à 23 h et la sortie à 14 h 30, heure de Paris.

Ce que ça donne sur un compte Master Bulenox 50K, rejoué de 2017 à octobre 2026 (un compte neuf toutes les
20 séances, 122 comptes) :

| | Atteignent le 3e retrait | Perdus par le plancher | Perdus par l'inactivité |
|---|---|---|---|
| Ton bot seul | 0 % | 0 % | 99 % |
| Ton bot + la nuit de secours | 70 % | 2 % | 0 % |
| Pour comparer : ton bot seul, si la règle d'inactivité n'existait pas | 65 % | 0 % | — |

À savoir avant de l'utiliser :

- **Le chiffre exact est fragile.** Avec un secours plus tardif (après 3 ou 4 jours) ou un stop à 0,75 %, 41 à 63 %
  des comptes atteignent le 3e retrait et 11 à 34 % sont perdus par le plancher. Ce qui ne change jamais : aucun
  compte n'est plus perdu par l'inactivité.
- **Il faut l'accord écrit de Bulenox.** Leur contrat ne compte pas une « activité artificielle destinée uniquement à
  prévenir l'inactivité ». Cette nuit est un vrai trade (15 heures de marché, un vrai risque, un gain moyen de
  14 $ par nuit en test), mais elle est déclenchée par le compteur. Message proposé plus bas.
- **Fais-la d'abord tourner sans argent** pendant quelques semaines : la simulation lit la nuit sur un CFD, pas sur
  le vrai future.
- Le rapport du matin (`systeme/rapport_matin.py`) écrit maintenant la consigne les jours où elle s'applique.

### 2. Ta taille, depuis ta marge actuelle

Solde 50 700 $, plancher 49 300 $, marge 1 400 $. Rejoué depuis chaque séance de 2017 à octobre 2026, sur 120 séances,
règle d'inactivité comptée (`resultats/partie_h3.txt`, descriptif) :

| Cas | Perdu par le plancher | Perdu par l'inactivité | Solde ≥ 53 600 $ (1er retrait possible) | Toujours en vie, sans retrait |
|---|---|---|---|---|
| 1 MNQ, le bot seul | 0 % | 99 % | 1 % | 0 % |
| 1 MNQ, le bot + la nuit de secours | 6 % | 0 % | 31 % | 62 % |
| 2 MNQ, le bot seul | 2 % | 95 % | 3 % | 0 % |
| 2 MNQ, le bot + la nuit de secours | 34 % | 0 % | 49 % | 17 % |

« Frein » compris : tant que la marge est sous 1 750 $, le bot et la nuit passent en demi-taille (1 MES à la place
de 1 MNQ, 1 MNQ à la place de 2). À 4 MNQ, le bot seul perd déjà le compte par le plancher plus d'une fois sur deux
(`resultats/situation.txt`). **Tant que ta marge n'est pas remontée : 1 MNQ au plus.**

### 3. Pour tes trades à la main

- **Le sens.** La seule règle de direction validée sur 15 ans reste la zone de bruit : acheter au-dessus de la bande
  haute, vendre sous la bande basse, ne rien faire entre les deux. Un setup à contre-sens de la zone joue contre le
  seul avantage mesuré du projet.
- **L'heure.** Entre 8 h et 9 h (Paris), à l'ouverture de l'Europe, le NQ monte en moyenne de 7 $ par MNQ
  (3,5 points ; t 4,2 sur 2012 - 2026). C'est trop petit pour être tradé seul une fois les frais payés, mais c'est
  un vent dans le dos des achats et un vent de face pour les ventes à cette heure-là.
- **Le risque.** Avec 1 400 $ de marge, une limite du jour de 1 000 $ veut dire qu'une seule mauvaise journée peut
  coûter le compte. `systeme/garde.py` calcule la taille permise avant chaque ordre et refuse ceux qui pourraient
  toucher le plancher.

### 4. Le message à envoyer à Bulenox

> Hello, I trade a Master 50K account with an automated strategy that can stay flat for several days. To remain
> active, I would like to add a second strategy: buying 1 MNQ at 18:00 ET with a 0.50% stop-loss and closing it at
> 9:30 ET, on the evening that follows two trading days without a trade. It is a real overnight position with its own
> risk. Do you consider it valid trading activity under the inactivity rule, or "artificial activity"? Could you
> confirm in writing? Thank you.

### 5. Pour l'automatiser

La règle tient en quatre lignes dans le bot : un compteur de jours de trading sans trade ; à 18 h (New York), si le
compteur vaut 2 ou plus, un achat au marché avec un stop à 0,50 % ; à 9 h 30, la sortie ; le résultat de la nuit
entame la limite du jour. Je ne l'ai pas écrite dans `bot3en1/` : c'est du code qui passerait de vrais ordres sur
ton compte, à décider avec toi et après la réponse de Bulenox.

## Contre-revue (#ultrareview)

Un relecteur indépendant a recalculé la partie « nuit » avec son propre code, sans lire le mien. Il a été coupé par
la limite d'utilisation avant d'écrire son rapport ; ses calculs sont repris ici et ses fichiers de travail sont
dans `contre_revue/`.

| Ce qu'il a vérifié | Résultat |
|---|---|
| Les chiffres de la nuit (3 538 nuits, 4 stops) | retrouvés au dollar près |
| Les heures du fichier de nuit | **défaut trouvé** : depuis 2019, une heure d'avance pendant les 3 à 4 semaines par an où les États-Unis et l'Europe n'ont pas la même heure d'été (139 séances). Corrigé dans `donnees.cfd()` |
| Le fichier de nuit (CFD) contre le vrai future | l'écart entre les deux dérive de quelques dollars par nuit, mais le retirer nuit par nuit ne change rien (t 2,89 → 2,91) |
| La nuit lue sur le vrai future, de la clôture à l'ouverture | t 3,47 (exploration 2,95, contrôle 1,82), +25,5 $ par nuit : le résultat ne vient pas du CFD |
| Une entrée plus tardive | jusqu'à 2 heures de retard, le t reste entre 3,0 et 3,5 : l'heure exacte d'entrée ne compte pas |

Effet de la correction : la nuit sans stop passe de t 3,50 à 3,62, la nuit avec stop 0,50 % de 3,04 à 2,73. Les
verdicts ne changent pas (9 variantes sur 16 passent toujours), mais les chiffres du compte bougent beaucoup pour
125 nuits corrigées sur 3 538 : c'est la preuve qu'il faut les lire comme des ordres de grandeur. Les anciens
résultats sont dans `resultats/avant_correction/`.

**Non relu par le relecteur** : le simulateur de compte avec la nuit, la machine auto-évolutive, les parties A à I
et les outils. Le simulateur du bot seul, lui, redonne exactement les chiffres publiés de la vague 10.

## Copier les institutions et les banques (partie G)

Source : le rapport hebdomadaire de la CFTC sur le E-mini Nasdaq-100 (1 063 rapports, 2006 → octobre 2026). C'est la
seule donnée publique qui dit qui est acheteur et qui est vendeur sur les futures : gestionnaires d'actifs, fonds à
levier, banques. L'étude du 29 octobre avait joué ces signaux en séance : aucun ne passait. Ici on tient la position
comme eux, la nuit seule puis du soir à la clôture du lendemain (3 538 jours, 2012 → 2026).

| Signal | Nuit seule : t | Soir → clôture : t | Contre « acheter tous les jours » : t | Verdict |
|---|---|---|---|---|
| G1 suivre les gestionnaires d'actifs | +0,20 | +0,26 | −2,35 et −2,10 | éliminé |
| G2 suivre les fonds à levier | −1,60 | +0,60 | −4,00 et −1,96 | éliminé |
| G3 contre les fonds à levier trop chargés | +0,47 | −0,58 | −3,01 et −3,16 | éliminé |
| G4 suivre les banques et teneurs de marché | −0,39 | −0,15 | −2,83 et −2,42 | éliminé |
| G5 gestionnaires et fonds à levier d'accord | −0,71 | +0,87 | −3,52 et −2,32 | éliminé |
| Référence : acheter tous les jours | +3,62 | +3,26 | — | — |

Aucun signal ne bat des signaux décalés au hasard. Vendre parce que les géants vendent coûte cher : pendant ce temps,
le marché monte.

Ce qui n'est pas testable ici : les portefeuilles trimestriels des fonds (des actions, publiées 45 jours après), les
portefeuilles crypto et les gros comptes de Polymarket (pas de futures, pas de données dans le dépôt).

## Les heures de la nuit (partie H1)

Idée testée : ne garder que les heures où la hausse de nuit se fait. 3 538 nuits, 1 MNQ, 3 $ de frais.

| Fenêtre | Sans stop : t (exploration / contrôle) | Par nuit | Pire nuit | Avec stop 0,50 % : t | Verdict |
|---|---|---|---|---|---|
| Asie : 18 h (New York) → 8 h (Paris) | 3,02 (2,84 / 1,10) | +13,0 $ | −3 026 $ | 2,37 | retenue avec le stop |
| Ouverture de l'Europe : 8 h → 9 h (Paris) | 2,43 (2,44 / 0,55) | +4,1 $ | −740 $ | 1,90 | non : ne tient pas avec 6 $ de frais |
| Matin : 9 h (Paris) → 9 h 30 (New York) | 0,33 (−0,15 / 0,95) | +1,6 $ | −1 932 $ | 0,09 | non |
| 8 h (Paris) → 9 h 30 (New York) | 1,65 (1,15 / 1,35) | +8,7 $ | −1 981 $ | 1,81 | non |

- L'heure d'ouverture de l'Europe est bien la meilleure heure de la nuit (+7,1 $ avant frais, t 4,2), comme dans
  l'étude de Boyarchenko, Larsen et Whelan (2023). Mais 7 $ moins les frais, il ne reste presque rien.
- Aucune fenêtre ne fait mieux que la nuit entière. Dans le compte, la fenêtre « Asie » en secours donne 51 à 61 % de
  Masters au 3e retrait : pas mieux que la nuit entière.

## La nuit de secours dans le compte (partie H2)

Master Bulenox 50K Option 2, un compte neuf toutes les 20 séances de 2017 à octobre 2026. Un trade de secours qui
tombe dans un trou du fichier compte comme un trade à 0 $ (règle écrite avant le calcul).

| Module de nuit | Secours après | Atteignent le 3e retrait | Perdus par le plancher | Perdus par l'inactivité | Touché par Master | Dates de perte | Verdict |
|---|---|---|---|---|---|---|---|
| Nuit entière, stop 0,50 % | 2 jours | 70 % | 2 % | 0 % | +2 675 $ | 1 | adoptée (fragile) |
| Nuit entière, stop 0,50 % | 3 jours | 57 % | 14 % | 0 % | +2 286 $ | 3 | adoptée |
| Nuit entière, stop 0,50 % | 4 jours | 48 % | 17 % | 0 % | +2 044 $ | 5 | adoptée |
| Nuit entière, stop 0,75 % | 2 jours | 63 % | 18 % | 0 % | +2 466 $ | 7 | adoptée |
| Nuit entière, stop 0,75 % | 3 jours | 55 % | 11 % | 0 % | +2 333 $ | 4 | adoptée |
| Nuit entière, stop 0,75 % | 4 jours | 41 % | 34 % | 0 % | +1 889 $ | 12 | non adoptée |
| Asie, stop 0,50 % | 2 jours | 57 % | 8 % | 0 % | +2 260 $ | 2 | adoptée (fragile) |
| Asie, stop 0,50 % | 3 jours | 61 % | 7 % | 0 % | +2 395 $ | 3 | adoptée |
| Asie, stop 0,50 % | 4 jours | 51 % | 19 % | 0 % | +2 083 $ | 4 | adoptée |
| Asie, stop 0,50 %, chaque nuit | — | 41 % | 31 % | 21 % | +1 813 $ | 16 | non adoptée |

- Règle d'adoption : aucun Master perdu par inactivité, au plus 20 % perdus avant le 3e retrait, gain moyen positif.
  8 réglages de secours sur 9 la passent.
- Secours après 2 jours : 525 nuits depuis 2017 (une séance sur cinq), +8 342 $ au total. Après 4 jours : 179 nuits,
  −4 060 $. Un secours tôt prend plus de nuits, et la nuit gagne en moyenne.
- Les mêmes comptes lancés 5, 10 ou 15 séances plus tard donnent les mêmes ordres de grandeur (70 à 72 % et 0 à 2 %
  pour le premier réglage).
- **La nuit chaque soir reste à éviter** : avec la nuit entière et un stop, 55 à 59 % des Masters sont perdus par le
  plancher (`resultats/compte.txt`, `compte2.txt`).

## L'arbitrage

**Sur les futures.**
- L'écart ES / NQ en paires a déjà été testé dans le projet (`paires/`, 2006 - 2026) : il perd. L'avance de l'ES sur
  le NQ à la minute : rien non plus (`scalping/`, famille F7).
- Les vrais arbitrages (NQ contre QQQ, future contre indice, échéance contre échéance) se jouent en microsecondes
  avec deux jambes et beaucoup de capital. La plupart des firmes de futures interdisent le trading haute fréquence
  et l'arbitrage de latence (notes du projet, `research_notes/`). Je n'ai pas pu relire la règle exacte de Bulenox :
  leur site n'est pas accessible d'ici.

**Sur Polymarket.**
- Le site est bloqué en France : l'Autorité nationale des jeux a ordonné son blocage le 16 juillet 2026 et le traite
  comme une offre de jeu illégale ([ANJ](https://anj.fr/promotion-illegal-gambling-services-blocking-polymarket-website),
  [The Local](https://www.thelocal.fr/20260718/france-blocks-access-to-online-prediction-market-polymarket)). Je ne
  t'aide pas à contourner ce blocage.
- Les écarts de prix y existent et sont déjà exploités : une étude les a mesurés sur un an de données
  ([arXiv 2508.03474](https://arxiv.org/abs/2508.03474)). Depuis 2026, le site prend aussi des frais sur la plupart
  de ses marchés ([documentation Polymarket](https://docs.polymarket.com/trading/fees)).
- Et surtout : un gain sur Polymarket ne fait pas avancer ton compte Bulenox.

## Les six modèles du 11 novembre

1 MNQ au prix d'aujourd'hui, 3 $ de frais par aller-retour. Exploration jusqu'à fin 2022, contrôle depuis 2023.

| # | Modèle | Ce qui a été joué | Résultat | Verdict |
|---|---|---|---|---|
| A | Bot qui s'adapte au régime | 4 états (chute, volatil, tendance, calme) connus la veille ; couper la stratégie dans ses mauvais états ; retour à la moyenne quand le marché est calme | La zone gagne dans les 4 états : rien à couper. Le retour à la moyenne **perd même en marché calme** (t −2,34) | tué |
| B | Vendre la volatilité chère (« vol-crush ») | Version futures : vendre le haut et acheter le bas d'une bande tirée du VXN | 791 trades, −20 $ par trade, t −1,26 | tué |
| C | Machine auto-évolutive (SETS) | 96 stratégies × 40 générations × 18 évolutions sur le NQ, puis sur le bitcoin | NQ : 0 champion gagnant sur 6 ; 28 % des élites en gain au contrôle contre 22 % pour celles trouvées sur un faux marché | tuée |
| D | Suivre les baleines et les institutions | Positions déclarées à la CFTC, en séance (29 octobre) puis nuit comprise (partie G) | Aucun signal ne passe | tué |
| E | Rotation entre marchés avec stop suiveur | 7 marchés, on suit le meneur toutes les 15 minutes | +9,1 $ par séance avant frais, 10,3 $ de frais : net −1,2 $, t −0,31 | tuée |
| F | Bot EMA 50 / 200 + RSI + ATR en H1 | Or et Nasdaq, 2012 - 2026 | Or : −10 436 $ (t −0,76) ; Nasdaq : −33 163 $ (t −1,38) | tué |

**Modèle B, ce qu'il faut comprendre.** La prime existe : le VXN dépasse la volatilité réalisée du mois suivant de
2,8 points, 77 % du temps. Mais on ne peut la toucher qu'en vendant des options, ce que Bulenox ne permet pas. Avec des
futures seuls, « vendre les deux côtés » revient à parier contre les cassures, et sur le NQ les cassures gagnent :
c'est ce que fait la zone. Quant au récit Polymarket (vendre OUI à 52 et NON à 53 pour encaisser 1,05 $), il suppose
que quelqu'un accepte de payer 1,05 $ ce qui vaut au plus 1,00 $.

**Modèle C, ce qu'il faut comprendre.** La machine fonctionne comme annoncé : elle élève, teste sur 30 % de données
gardées de côté, et tue. Elle a essayé 56 928 stratégies sur le NQ et 56 117 sur le bitcoin. Ses survivantes ont
plus de 50 % de trades gagnants et un bon test, et elles perdent ensuite : en moyenne −4 991 $ pour un champion sur
2023 - 2026, avec un pire jour à −4 330 $ et 44 % de comptes Bulenox perdus en 60 séances. Les stratégies trouvées sur
un faux marché, où il n'y a rien à trouver, font pareil. Exiger « plus de la moitié de trades gagnants » sélectionne
des grilles qui gagnent souvent un peu et perdent rarement beaucoup.

## La nuit seule (partie N, données corrigées)

Achat de 1 MNQ à 18 h, vente à 9 h 30, 3 538 nuits de 2012 à octobre 2026.

| Variante | t (exploration / contrôle) | Par nuit | Pire nuit | Nuits stoppées |
|---|---|---|---|---|
| Sans stop | 3,62 (3,07 / 1,92) | +24,7 $ | −3 511 $ | — |
| Stop 0,50 % | 2,73 (1,95 / 2,04) | +14,2 $ | −334 $ | 1 147 |
| Stop 0,75 % | 2,97 (2,33 / 1,88) | +16,9 $ | −574 $ | 686 |
| Stop 1,00 % | 2,95 (2,25 / 1,98) | +17,8 $ | −584 $ | 424 |

- 9 variantes sur 16 passent leurs 5 conditions. Les filtres (VIX inversé, séance en baisse, peur chère) n'apportent
  rien : ils gardent moins de nuits, pas de meilleures nuits.
- **Limite honnête** : c'est surtout la hausse du marché, prise la nuit. L'achat de jour sur les mêmes dates fait
  t 1,18, et l'écart nuit − jour n'est pas significatif (t 1,10).

**Premières règles du compte** (écrites le 11 novembre ; une nuit absente du fichier y était comptée comme impossible) :

| Candidat | Atteignent le 3e retrait | Perdus par le plancher | Perdus par l'inactivité | Touché par Master | Verdict |
|---|---|---|---|---|---|
| Le bot seul | 0 % | 0 % | 99 % | −148 $ | référence |
| Le bot seul, si la règle d'inactivité n'existait pas | 65 % | 0 % | — | +2 532 $ | information |
| Bot + nuit chaque soir, stop 0,75 % | 32 % | 55 % | 7 % | +1 334 $ | non adoptée |
| Bot + nuit chaque soir, stop 0,50 % | 28 % | 59 % | 8 % | +1 334 $ | non adoptée |
| Bot + nuit de secours après 3 jours, stop 0,75 % | 10 % | 11 % | 47 % | +992 $ | non adoptée |
| Bot + nuit de secours après 3 jours, stop 0,50 % | 14 % | 8 % | 50 % | +1 055 $ | non adoptée |

Les pertes par inactivité de ces deux secours venaient des trous du fichier de nuit (surtout en 2023), alors qu'en
vrai le marché est ouvert ces nuits-là. La partie H2 corrige cette convention, par une règle écrite avant son calcul.

## Tenir l'inactivité avec la zone elle-même (partie I)

Le moteur recodé redonne les 3 465 trades de référence de la zone (même jour, même minute, même sens).

| Bande | Zone brute : t (exploration / contrôle) | Séries de 5 jours restantes | Masters perdus par l'inactivité | Verdict |
|---|---|---|---|---|
| k = 1 | 3,63 (3,28 / 1,55) | 56 | 99 % | non adoptée |
| k = 0,75 | 2,48 (2,66 / 0,26) | 31 | 99 % | non adoptée |
| k = 0,5 | 1,50 (2,12 / −0,79) | 8 | 69 % | non adoptée |

Une bande plus étroite trade plus souvent mais perd son avantage (au contrôle : t 0,26 puis −0,79), et elle ne
suffit toujours pas : même à k = 0,5, la zone reste silencieuse certains jours.

## Les outils livrés (`systeme/`)

| Fichier | Ce qu'il fait | Vérifié |
|---|---|---|
| `regime.py` | État du marché de la prochaine séance : CHUTE, VOLATIL, TENDANCE ou CALME | utilisé par la partie A ; affiché pour information, il ne change aucun ordre |
| `garde.py` | Contrôle avant chaque ordre : plancher, limite du jour (nuit comprise), taille maximale, frein, jours de la Fed, fenêtre 16 h 55 - 18 h, compteur d'inactivité, consigne de la nuit de secours, limite de baisse de 15 % pour un compte personnel | `python3 garde.py` lance ses tests (dont ton cas : +1 800 $ puis −1 100 $ = marge 1 400 $) |
| `rapport_matin.py` | Revue des trades de la veille depuis le journal du bot : résultat, pire et meilleur moment de chaque trade, écarts aux règles, marge, alertes et consigne de secours pour le soir ; envoi Telegram possible | redonne les −272 $ du trade audité du 21 octobre 2026 en 4 MNQ |

Ils ne sont pas branchés sur ton bot C# ni sur GitHub Actions : ce sont des modules à lancer ou à intégrer.

## Pour relancer

```bash
git worktree add ../kb origin/claude/keen-babbage-r686cl
git worktree add ../at origin/claude/affectionate-turing-tnz0mn
git worktree add ../op origin/claude/optimistic-ptolemy-xs24ra
cd chantier && pip install numpy pandas numba
python3 nuit.py && python3 compte.py && python3 compte.py 2 && python3 inactivite.py
python3 variantes.py g h1 h2 h3
python3 divers.py && python3 machine.py nq && python3 machine.py btc
```

## Limites

- Le contrôle 2023 - 2026 avait déjà servi à d'autres études du projet : ce n'est pas un coffre vierge.
- La nuit est lue sur un CFD (prix acheteur, barres de 5 minutes) : un vrai stop de nuit peut glisser de plus d'un
  tick. Le fichier a des trous en 2023.
- Les pourcentages du compte reposent sur 122 comptes qui se chevauchent et sur une poignée de dates de perte : ce
  sont des ordres de grandeur.
- Le frein est simulé comme une demi-taille de MNQ ; en vrai, c'est 1 MES, qui ne bouge pas exactement comme un
  demi-MNQ.
- Le filtre delta du bot ne peut pas être rejoué avant avril 2026 : le compte simule le bot sans lui.
- Le contrat du compte « funded » après le 3e retrait n'est pas connu : ses chiffres reposent sur des hypothèses.
- Machine sur le bitcoin : positions fermées à minuit UTC (et non après 24 h), frais de 4 points de base.
