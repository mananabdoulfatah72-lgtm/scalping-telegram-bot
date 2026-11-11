# Chantier du 11 novembre 2026 : résultats

Règles fixées avant chaque calcul : [`REGLES.md`](REGLES.md) (l'historique git montre que chaque règle a été
enregistrée avant son calcul). Détail de chaque partie : dossier `resultats/`.

## En bref

- **Les six modèles du message sont tués.** Aucun ne gagne d'argent sur des données qu'il n'a pas vues, après frais.
- **La nuit (achat 18 h, vente 9 h 30, avec stop) gagne sur le papier, mais pas sur ton compte.** À 1 MNQ chaque nuit,
  elle fait perdre 43 % des comptes Master par le plancher.
- **Le vrai danger de ton Master n'est pas le marché, c'est la règle d'inactivité.** Ton bot seul ne perd aucun
  compte par le plancher en simulation, mais 99 % par les 5 jours sans trade. Aucun secours testé ici ne passe sa
  règle fixée d'avance.
- **Ce qui reste valable : la zone de bruit (ton Bot 3 en 1).** C'est toujours la seule stratégie du projet qui tient
  sur 15 ans.
- **Trois outils sont livrés** : l'état du marché chaque matin, le contrôle du risque avant chaque ordre, le rapport
  du matin sur les trades de la veille.

Aucun système ne rapporte 847 $ par nuit ni ne transforme 100 $ en 2 981 $ en 45 minutes. Ces récits ne donnent ni
données, ni frais, ni période de contrôle : ils ne peuvent pas être reproduits.

## Les six modèles

1 MNQ au prix d'aujourd'hui, 3 $ de frais par aller-retour. Exploration jusqu'à fin 2022, contrôle depuis 2023.

| # | Modèle | Ce qui a été joué | Résultat | Verdict |
|---|---|---|---|---|
| A | Bot qui s'adapte au régime | 4 états (chute, volatil, tendance, calme) connus la veille ; couper la stratégie dans ses mauvais états ; retour à la moyenne quand le marché est calme | La zone gagne dans les 4 états : rien à couper. Le retour à la moyenne **perd même en marché calme** (t −2,34) | tué |
| B | Vendre la volatilité chère (« vol-crush ») | Version futures : vendre le haut et acheter le bas d'une bande tirée du VXN | 791 trades, −20 $ par trade, t −1,26 | tué |
| C | Machine auto-évolutive (SETS) | 96 stratégies × 40 générations × 18 évolutions sur le NQ, puis sur le bitcoin | NQ : 0 champion gagnant sur 6 ; 28 % des élites en gain au contrôle contre 22 % pour celles trouvées sur un faux marché | tuée |
| D | Suivre les baleines et les initiés | Déjà jugé dans `radar/` et `flux/` | Barres non franchies | tué (ancien) |
| E | Rotation entre marchés avec stop suiveur | 7 marchés, on suit le meneur toutes les 15 minutes | +9,1 $ par séance avant frais, 10,3 $ de frais : net −1,2 $, t −0,31 | tuée |
| F | Bot EMA 50 / 200 + RSI + ATR en H1 | Or et Nasdaq, 2012 - 2026 | Or : −9 065 $ (t −0,66) ; Nasdaq : −31 155 $ (t −1,31) | tué |

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

## La nuit (partie N)

Achat de 1 MNQ à 18 h, vente à 9 h 30, 3 538 nuits de 2012 à octobre 2026. Contrôle des prix : les rendements de nuit
du fichier suivent ceux du vrai future (corrélation 0,99).

| Variante | t (exploration / contrôle) | Par nuit | Pire nuit | Nuits stoppées |
|---|---|---|---|---|
| Sans stop | 3,50 (3,05 / 1,71) | +23,9 $ | −3 883 $ | — |
| Stop 0,50 % | 3,04 (2,19 / 2,24) | +16,0 $ | −334 $ | 1 155 |
| Stop 0,75 % | 3,24 (2,75 / 1,70) | +18,8 $ | −574 $ | 697 |
| Stop 1,00 % | 3,04 (2,57 / 1,63) | +18,6 $ | −584 $ | 437 |

- 9 variantes sur 16 passent leurs 5 conditions. Les filtres (VIX inversé, séance en baisse, peur chère) n'apportent
  rien : ils gardent moins de nuits, pas de meilleures nuits.
- **Limite honnête** : c'est surtout la hausse du marché, prise la nuit. L'achat de jour sur les mêmes dates fait
  t 1,15, et l'écart nuit − jour n'est pas significatif (t 1,07).

**Dans le compte Master** (simulateur de la vague 10, qui redonne ici exactement les chiffres publiés : 123 départs,
101 séries de 5 jours sans trade, 99,2 % de Masters perdus par l'inactivité) :

| Candidat | Atteignent le 3e retrait | Perdus par le plancher | Perdus par l'inactivité | Touché par Master | Verdict |
|---|---|---|---|---|---|
| Le bot seul | 0 % | 0 % | 99 % | −148 $ | référence |
| Le bot seul, si la règle d'inactivité n'existait pas | 65 % | 0 % | — | +2 532 $ | information |
| Bot + nuit chaque soir, stop 0,75 % | 46 % | 43 % | 7 % | +1 786 $ | non adoptée |
| Bot + nuit chaque soir, stop 0,50 % | 48 % | 40 % | 7 % | +1 931 $ | non adoptée |
| Bot + nuit de secours après 3 jours sans trade, stop 0,75 % | 16 % | 14 % | 38 % | +1 142 $ | non adoptée |
| Bot + nuit de secours après 3 jours sans trade, stop 0,50 % | 19 % | 8 % | 50 % | +1 111 $ | non adoptée |

- La nuit bouge deux fois plus que le bot (370 $ contre 188 $ d'écart type par séance) : à 1 MNQ, elle use le
  plancher de 2 500 $.
- Les pertes par inactivité de la nuit de secours viennent surtout de trous du fichier de nuit (107 séances sans
  nuit jouable, en 2023 pour la plupart).
- **Pour information, écrit après coup** (`resultats/compte2_info.txt`) : si une nuit de secours peut toujours être
  prise, la version à stop 0,50 % donne 69 % de Masters au 3e retrait, 8 % perdus par le plancher, 0 % par
  l'inactivité, 2 643 $ touchés par Master. C'est le niveau du secours W1 de la vague 10 (70 %, 10 %, 2 949 $), sans
  modèle d'apprentissage. Ce n'est pas une règle fixée d'avance : à confirmer en virtuel avant tout usage.

## Tenir l'inactivité avec la zone elle-même (partie I)

Le moteur recodé redonne les 3 465 trades de référence de la zone (même jour, même minute, même sens).

| Bande | Zone brute : t (exploration / contrôle) | Séries de 5 jours restantes | Masters perdus par l'inactivité | Verdict |
|---|---|---|---|---|
| k = 1 | 3,63 (3,28 / 1,55) | 56 | 99 % | non adoptée |
| k = 0,75 | 2,48 (2,66 / 0,26) | 31 | 99 % | non adoptée |
| k = 0,5 | 1,50 (2,12 / −0,79) | 8 | 69 % | non adoptée |

Une bande plus étroite trade plus souvent mais perd son avantage (au contrôle : t 0,26 puis −0,79), et elle ne
suffit toujours pas : même à k = 0,5, la zone reste silencieuse certains jours.

## Ce que ça change pour ton compte Bulenox

1. **Garde ton bot tel qu'il est.** Aucun des six modèles ne le remplace ni ne le complète.
2. **Règle d'inactivité : demande une réponse écrite à Bulenox avant tout.** Deux secours tiennent en simulation :
   le modèle W1 (vague 10) et la nuit de secours à stop 0,50 % (ici, pour information). Les deux sont déclenchés
   par le compteur d'inactivité, ce que le contrat peut voir comme une activité artificielle.
3. **Avec ta marge actuelle (environ 1 400 $), la taille décide de tout.** Le bot seul, rejoué depuis chaque séance
   de 2017 à 2026 à partir de ta situation (solde 50 700 $, plancher 49 300 $), sur 120 séances, sans compter la
   règle d'inactivité (`resultats/situation.txt`, descriptif) :

   | Taille | Compte perdu par le plancher | Solde ≥ 53 600 $ (1er retrait possible) | Séances jusque-là (médiane) |
   |---|---|---|---|
   | 1 MNQ avec le frein (demi-taille sous 1 750 $ de marge) | 0 % | 24 % | 84 |
   | 1 MNQ sans frein | 19 % | 33 % | 74 |
   | 2 MNQ avec le frein | 25 % | 39 % | 56 |
   | 2 MNQ sans frein | 50 % | 46 % | 39 |
   | 4 MNQ avec le frein | 52 % | 46 % | 30 |
   | 4 MNQ sans frein | 61 % | 39 % | 14 |

   À 4 MNQ, tu perds le compte plus d'une fois sur deux. À 1 MNQ avec le frein, tu ne le perds pas, mais c'est lent.

## Les outils livrés (`systeme/`)

| Fichier | Ce qu'il fait | Vérifié |
|---|---|---|
| `regime.py` | État du marché de la prochaine séance : CHUTE, VOLATIL, TENDANCE ou CALME | utilisé par la partie A ; affiché pour information, il ne change aucun ordre |
| `garde.py` | Contrôle avant chaque ordre : plancher, limite du jour (nuit comprise), taille maximale, frein, jours de la Fed, fenêtre 16 h 55 - 18 h, compteur d'inactivité, limite de baisse de 15 % pour un compte personnel | `python3 garde.py` lance ses tests (dont ton cas : +1 800 $ puis −1 100 $ = marge 1 400 $) |
| `rapport_matin.py` | Revue des trades de la veille depuis le journal du bot : résultat, pire et meilleur moment de chaque trade, écarts aux règles, marge, alertes pour le lendemain ; envoi Telegram possible | redonne les −272 $ du trade audité du 21 octobre 2026 en 4 MNQ |

Ils ne sont pas branchés sur ton bot C# ni sur GitHub Actions : ce sont des modules à lancer ou à intégrer.

## Pour relancer

```bash
git worktree add ../kb origin/claude/keen-babbage-r686cl
git worktree add ../at origin/claude/affectionate-turing-tnz0mn
git worktree add ../op origin/claude/optimistic-ptolemy-xs24ra
cd chantier && pip install numpy pandas numba
python3 nuit.py && python3 compte.py && python3 compte.py 2 && python3 inactivite.py
python3 divers.py && python3 machine.py nq && python3 machine.py btc
```

## Contre-revue (#ultrareview)

Un relecteur indépendant recalcule avec son propre code les chiffres de la nuit, du compte et de la machine. Elle était
encore en cours à l'écriture de ce rapport : ses défauts et corrections seront ajoutés ici.

## Limites

- Le contrôle 2023 - 2026 avait déjà servi à d'autres études du projet : ce n'est pas un coffre vierge.
- La nuit est lue sur un CFD (prix acheteur, barres de 5 minutes) : un vrai stop de nuit peut glisser de plus d'un
  tick. Le fichier a des trous en 2023.
- Le filtre delta du bot ne peut pas être rejoué avant avril 2026 : le compte simule le bot sans lui.
- Le contrat du compte « funded » après le 3e retrait n'est pas connu : ses chiffres reposent sur des hypothèses.
- Machine sur le bitcoin : positions fermées à minuit UTC (et non après 24 h), frais de 4 points de base.
