# Chantier des 11 et 12 novembre 2026 : résultats

Règles fixées avant chaque calcul : [`REGLES.md`](REGLES.md) (l'historique git montre que chaque règle a été
enregistrée avant son calcul). Détail de chaque partie : dossier `resultats/`.

## En bref

- **Grossir la taille ne paie pas sur ce contrat.** 48 façons de jouer le compte ont été testées. À 2 MNQ, on touche
  un peu plus et on perd le compte quatre fois plus souvent ; à 4 MNQ, on touche moins.
- **Un seul levier améliore à la fois le gain et la sécurité : jouer la nuit quand la marge est bonne.** Achat à 18 h,
  stop à 0,50 %, vente à 9 h 30, chaque soir dès que la marge atteint 2 600 $. Depuis ta situation : 1 274 $ touchés
  en un an au lieu de 750 $, sans perdre plus de comptes. C'est une piste, pas une preuve : elle ne passe pas la
  barre fixée d'avance.
- **Correction : le secours de nuit annoncé d'abord était trop beau.** Simulé avec un vrai MES sous le frein, il perd
  23 à 27 % des comptes, et non 2 %. Le secours le plus sûr est plus petit : 1 MES de 8 h à 9 h (Paris).
- **Ordre de grandeur honnête : ce compte paie environ 100 à 140 $ par mois de vie, à 1 MNQ.** Le contrat plafonne
  les trois premiers retraits à 1 500 $, puis le Master se termine.
- **Copier les institutions et les banques ne donne rien**, l'arbitrage n'est pas une solution de rechange, et les
  six modèles du message du 11 novembre sont tués.
- **Ce qui tient : la zone de bruit (ton Bot 3 en 1) et la hausse lente du Nasdaq pendant la nuit.**
- **La contre-revue a trouvé un défaut dans mes données de nuit**, corrigé. Elle a été coupée par la limite
  d'utilisation : seule la partie « nuit » a été relue par un regard indépendant.

Aucun système ne rapporte 847 $ par nuit ni ne transforme 100 $ en 2 981 $ en 45 minutes. Ces récits ne donnent ni
données, ni frais, ni période de contrôle : ils ne peuvent pas être reproduits.

## Le plan pour ton challenge

### 1. Ce qu'il faut faire tourner, selon ta marge

| Ta marge au-dessus du plancher | Le bot | Secours après 2 jours de trading sans trade | La nuit |
|---|---|---|---|
| Moins de 1 750 $ (ton cas aujourd'hui) | 1 MES (le frein) | 1 MES de 8 h à 9 h, heure de Paris, sans stop | non |
| De 1 750 à 2 600 $ | 1 MNQ | 1 MES de 8 h à 9 h, heure de Paris, sans stop | non |
| 2 600 $ et plus | 1 MNQ | inutile : la nuit compte comme un trade | 1 MNQ : achat à 18 h (New York), stop à 0,50 %, vente à 9 h 30 |

Sur un compte Master neuf, rejoué de 2017 à octobre 2026 (122 comptes, `resultats/partie_k2.txt`) :

| | Atteignent le 3e retrait | Perdus par le plancher | 1er retrait | 3e retrait |
|---|---|---|---|---|
| Ton bot + le secours d'une heure | 63 % | 17 % | 191 séances | 623 séances |
| La même chose + la nuit dès 2 600 $ de marge | 70 % | 13 % | 160 séances | 513 séances |
| Ton bot + le secours de nuit (mon premier conseil) | 53 % | 27 % | 148 séances | 426 séances |

Depuis ta situation (solde 50 700 $, marge 1 400 $), sur 250 séances, environ un an :

| | Compte perdu | Au moins un retrait | Touché en moyenne |
|---|---|---|---|
| Ton bot + le secours d'une heure | 11 % | 55 % | 750 $ |
| La même chose + la nuit dès 2 600 $ de marge | 11 % | 57 % | 1 274 $ |
| 2 MNQ tout le temps + la nuit | 43 % | 59 % | 1 565 $ |
| 4 MNQ tout le temps + la nuit | 66 % | 43 % | 1 123 $ |

À savoir :

- **La nuit dès 2 600 $ de marge est une piste.** Elle améliore tous les chiffres ci-dessus, mais sur des comptes
  neufs elle ne touche que 10 % de plus par mois de vie ; la règle fixée d'avance demandait 25 %.
- **Elle doit être codée dans le bot.** Le Bot 3 en 1 réaligne toute position MNQ prise à la main. Ce n'est pas fait.
- **Le secours d'une heure ne gagne rien** (−0,7 $ en moyenne, pire résultat −513 $) : il sert seulement à garder le
  compte actif. Il se joue sur MES, donc sans gêner le bot.
- **Il faut l'accord écrit de Bulenox**, qui ne compte pas une « activité artificielle ».
- **Ces pourcentages tiennent à peu d'épisodes** : presque toutes les pertes de la première ligne viennent de
  comptes déjà au bord du plancher après la mauvaise année 2025.

### 2. Pourquoi grossir ne paie pas

Le Master ne paie que trois retraits de 1 500 $ au plus, alors que le plancher reste à 2 500 $. Doubler la taille
double les pertes possibles, mais pas ce qu'on a le droit de retirer.

| Taille du bot (avec le secours d'une heure) | Atteignent le 3e retrait | Perdus par le plancher | Touché par Master |
|---|---|---|---|
| 1 MNQ | 63 % | 17 % | 2 451 $ |
| 2 MNQ dès 2 600 $ de marge | 62 % | 17 % | 2 489 $ |
| 2 MNQ dès 2 600 $, 3 dès 3 600 $ | 60 % | 18 % | 2 451 $ |
| 2 MNQ dès 2 000 $, 3 dès 3 000 $, 4 dès 4 000 $ | 60 % | 23 % | 2 333 $ |
| 2 MNQ tout le temps | 52 % | 34 % | 2 176 $ |
| 4 MNQ tout le temps | 31 % | 59 % | 1 288 $ |

Attendre 1 500 $ au lieu de retirer dès 1 000 $ ne change presque rien non plus.

### 3. Combien par mois, et quand tombe un retrait

Ce que gagne le bot seul sur le marché, à 1 MNQ, frais compris, sur 118 mois (`resultats/mois.txt`) : +318 $ par
mois en moyenne, 36 % de mois perdants, pire mois −1 235 $, et l'année 2025 entière perdante (−639 $).

Ce que tu touches vraiment est plus petit : **environ 100 à 140 $ par mois de vie du compte**. Les premiers 2 600 $
gagnés doivent rester sur le compte, tu ne touches que 90 % du reste, et un compte sur six ou sept est perdu en route.

Les retraits du compte Master, d'après ton contrat (annexe A du 23 octobre 2026) :

| Condition | Valeur |
|---|---|
| Solde à garder sur le compte | 52 600 $ |
| Montant de chacun des 3 premiers retraits | 1 000 à 1 500 $, dont 90 % pour toi : 900 à 1 350 $ |
| Solde qu'il faut donc avoir pour demander | 53 600 $ au moins |
| Jours tradés depuis le dernier retrait | 10 au moins |
| Ta meilleure journée | pas plus de 40 % du gain fait depuis le dernier retrait |
| Après le 3e retrait | le Master se termine et tu passes sur le compte « funded » |

Ton solde est à environ 50 700 $ : il manque **2 900 $** avant le premier retrait. Avec le plan du point 1, un peu
plus d'un compte sur deux y arrive en un an, en 132 séances en médiane (6 mois).

### 4. Pour gagner vraiment plus

Dans ce compte, le plafond est le contrat, pas la stratégie. Ce qui peut multiplier le gain est ailleurs, et tout
est à vérifier auprès de Bulenox avant de payer quoi que ce soit :

- **Plusieurs comptes avec le même bot.** C'est la façon habituelle de grossir chez une firme : chaque compte a son
  propre plafond de retraits. Les guides ne sont pas d'accord sur le nombre de Masters permis (3, 5 ou 11) ni sur le
  droit de copier ses trades d'un compte à l'autre
  ([TradingFinder](https://tradingfinder.com/props/bulenox/rules),
  [CrossTrade](https://crosstrade.io/prop-firms/bulenox),
  [The God Funded](https://thegodfunded.com/en/news/bulenox-launches-fast-track-and-momentum-and-removes-recurring-evaluation-subscriptions)).
  Chaque compte coûte une qualification, et ils seraient tous perdus en même temps dans une mauvaise période.
- **Le compte « funded » après le 3e retrait.** D'après les guides, les retraits n'y sont plus plafonnés
  ([Prop Trading Vibes](https://proptradingvibes.com/blog/bulenox-payout-rules)). Je n'ai pas ses règles : c'est
  seulement là que grossir la taille pourrait payer.
- **Un nouvel avantage mesuré.** Le projet a testé plus d'un million de règles sans en trouver d'autre que la zone
  et la nuit.

### 5. Pour tes trades à la main

- **Le sens.** La seule règle de direction validée sur 15 ans reste la zone de bruit : acheter au-dessus de la bande
  haute, vendre sous la bande basse, ne rien faire entre les deux. Un setup à contre-sens de la zone joue contre le
  seul avantage mesuré du projet.
- **L'heure.** Entre 8 h et 9 h (Paris), à l'ouverture de l'Europe, le NQ monte en moyenne de 7 $ par MNQ
  (3,5 points ; t 4,2 sur 2012 - 2026). C'est trop petit pour être tradé seul une fois les frais payés, mais c'est
  un vent dans le dos des achats et un vent de face pour les ventes à cette heure-là.
- **Le risque.** Avec 1 400 $ de marge, une limite du jour de 1 000 $ veut dire qu'une seule mauvaise journée peut
  coûter le compte. `systeme/garde.py` calcule la taille permise avant chaque ordre et refuse ceux qui pourraient
  toucher le plancher.

### 6. Le message à envoyer à Bulenox

> Hello, I trade a Master 50K account with an automated strategy that can stay flat for several days. Two questions.
> (1) To remain active, I would add a small second strategy: buying 1 MES at 2:00 ET and closing it at 3:00 ET on the
> morning that follows two trading days without a trade. It is a real position with its own risk. Do you consider it
> valid trading activity under the inactivity rule, or "artificial activity"? (2) How many Master accounts may I hold
> at the same time, and may I run the same automated strategy on all of them? Could you confirm in writing? Thank you.

### 7. Pour l'automatiser

Trois ajouts au bot, dans cet ordre : un compteur de jours de trading sans trade ; le secours (1 MES de 8 h à 9 h,
heure de Paris, quand le compteur vaut 2 ou plus) ; la nuit (1 MNQ à 18 h, heure de New York, stop à 0,50 %, sortie
à 9 h 30, seulement si la marge atteint 2 600 $), dont le résultat entame la limite du jour. Je ne les ai pas écrits
dans `bot3en1/` : c'est du code qui passerait de vrais ordres sur ton compte, à décider avec toi et après la réponse
de Bulenox.

## Les bots enregistrés, rejoués depuis le début du challenge (12 novembre 2026)

Du 13 octobre 2026 (première séance du challenge) au 11 novembre 2026 (dernière séance des dépôts) : 22 séances. Chaque
bot est rejoué par son propre code (moteurs C# de `bot3en1/` de la branche `claude/optimistic-ptolemy-xs24ra`, machine de
veille `flux/veille.py`, journaux des robots de `main`). Dollars réels pour 1 MNQ, frais compris ; « à 4 MNQ » avec la
limite du jour de 1 000 $. Détail : `resultats/rejeu_periode.txt` ; pour refaire : `rejeu_periode.sh`.

Sur la période, le NQ est passé de 30 618 à 28 484 points (−7 %), avec un plus bas à 26 738 le 5 novembre.

| Bot | Trades | 1 MNQ | 4 MNQ | Après le 2 novembre (vraiment futur) |
|---|---|---|---|---|
| W1 (Supertrend trié par un modèle) | 27 | +6 152 $ | +15 672 $ | +3 262 $ (modèle entraîné jusqu'au 2 novembre) |
| Supertrend NQ 10-3 | 49 | +4 884 $ | +15 744 $ | +2 933 $ |
| Cassure de la veille (veille) | 18 séances | +3 326 $ | — | +3 391 $ |
| XGBoost NQ | 21 | +3 191 $ | +10 030 $ | +232 $ (modèle entraîné jusqu'au 2 novembre) |
| ORB 5 minutes (veille) | 21 séances | +2 531 $ | — | +2 342 $ |
| Bot 3 en 1, réglages actuels (C2 + Q1), sans filtre delta | 17 | +1 724 $ | +7 930 $ | +807 $ (C2 et Q1 choisis le 1er novembre) |
| Pivots R1/S1 (veille) | 7 séances | +1 083 $ | — | 0 $ |
| Bot 3 en 1, zone d'origine sans filtre | 25 | +986 $ | +5 984 $ | +375 $ |
| Bot 3 en 1, ta règle du 26 octobre | 15 | +296 $ | +1 388 $ | −498 $ |
| Bot 3 en 1, ta règle du 27 octobre (stop 70 points) | 15 | +294 $ | +1 072 $ | −638 $ |
| RSI(2) du bot (tenu la nuit, décoché chez Bulenox) | 2 | −1 019 $ | — | — |
| Robot tendance (19 marchés, compte virtuel) | — | −1 498 $ | — | +587 $ |
| Robot version 7 (actions, compte virtuel) | — | −4 165 $ | — | +922 $ |

- **Contrôles** : la zone d'origine donne +986 $ par le moteur C#, +988 $ par la machine de veille et +991 $ dans le
  journal du robot de `main` ; le rejeu des réglages actuels redonne trade par trade le journal `c2q1.txt` de l'arène ;
  W1 redonne le total de son propre programme de rejeu (+6 152 $, 27 trades).
- **Ce que ça dit** : sur ces 22 séances, les bots qui suivent la tendance (Supertrend, W1, cassures) gagnent le plus,
  parce que le NQ a baissé de 7 % puis rebondi. Sur 15 ans, ces mêmes bots grillent environ un compte financé neuf
  sur deux dans l'année à 1 MNQ (`ml/arene/VAGUE6.md`) ; la zone non. 22 séances ne suffisent pas à classer des bots.
- **Ce qui n'est pas rejouable** : FluxNQ (il lui faut les transactions Rithmic, absentes après le 30 octobre) ; le
  filtre delta après le 30 octobre (même raison) ; le filtre VIX après le 30 octobre (VIX absent des dépôts ; avant,
  il n'aurait coupé aucune séance).

## Gagner plus : la taille, la nuit, le retrait (parties J, K et K2)

**La nuit sur le MES (partie J).** Elle sert sous le frein, et pour tout ordre passé à la main.

| 1 MES, frais 4,50 $ | t (exploration / contrôle) | Par nuit | Pire nuit | Verdict |
|---|---|---|---|---|
| Sans stop | 2,57 (2,21 / 1,34) | +10,5 $ | −2 574 $ | non : pire nuit, frais doublés |
| Stop 0,50 % | 1,22 (0,91 / 0,89) | +3,9 $ | −399 $ | non |

La hausse de nuit existe aussi sur le S&P, mais le MES coûte plus cher en frais et la nuit avec stop n'y passe pas.
C'est ce qui change le secours de nuit : sous le frein, chaque nuit stoppée coûte environ 200 $ sur un vrai MES,
contre 144 $ pour le « demi-MNQ » de la simulation d'avant, qui n'existe pas.

**Les 24 politiques avec le secours d'une heure (partie K2).** N1 = la nuit chaque soir dès 2 600 $ de marge.
Retrait dès 1 000 $ disponibles ; l'attente à 1 500 $ donne les mêmes ordres de grandeur (`resultats/partie_k2.txt`).

| Taille du bot | Nuit | 3e retrait | Perdus par le plancher | 1er retrait (séances) | 3e retrait (séances) | Touché par Master | Par mois de vie | Verdict |
|---|---|---|---|---|---|---|---|---|
| 1 MNQ | secours seul | 63 % | 17 % | 191 | 623 | 2 451 $ | 96 $ | référence |
| 1 MNQ | N1 | 70 % | 13 % | 160 | 513 | 2 569 $ | 106 $ | non : +10 % seulement |
| 2 MNQ dès 2 600 $ | secours seul | 62 % | 17 % | 219 | 685 | 2 489 $ | 94 $ | non |
| 2 MNQ dès 2 600 $ | N1 | 67 % | 16 % | 172 | 590 | 2 590 $ | 107 $ | non |
| 2 puis 3 MNQ | secours seul | 60 % | 18 % | 200 | 676 | 2 451 $ | 91 $ | non |
| 2 puis 3 MNQ | N1 | 67 % | 16 % | 188 | 794 | 2 579 $ | 86 $ | non |
| 2, 3 puis 4 MNQ | secours seul | 60 % | 23 % | 260 | 853 | 2 333 $ | 84 $ | non |
| 2, 3 puis 4 MNQ | N1 | 62 % | 20 % | 208 | 767 | 2 419 $ | 86 $ | non |
| 2 MNQ tout le temps | secours seul | 52 % | 34 % | 109 | 506 | 2 176 $ | 121 $ | non : trop de comptes perdus |
| 2 MNQ tout le temps | N1 | 51 % | 41 % | 96 | 370 | 2 134 $ | 168 $ | non : trop de comptes perdus |
| 4 MNQ tout le temps | secours seul | 31 % | 59 % | 70 | 411 | 1 288 $ | 121 $ | non : trop de comptes perdus |
| 4 MNQ tout le temps | N1 | 37 % | 59 % | 54 | 319 | 1 472 $ | 183 $ | non : trop de comptes perdus |

- Règle d'adoption : aucun compte perdu par inactivité, au plus 30 % perdus par le plancher, et au moins 25 % de
  plus par mois de vie que la référence, dans chaque moitié de la période. **Aucune politique ne la passe.**
- « Par mois de vie » monte avec la taille parce que les comptes y meurent vite : c'est pour cela que la règle
  regarde aussi les comptes perdus.
- Contrôle : le nouveau simulateur redonne exactement H2 quand on lui donne les mêmes hypothèses (69,7 %, 2,5 %,
  2 675 $), et exactement le bot seul quand le secours ne coûte rien (65 %, 0 %).

**Les mêmes politiques avec le secours de nuit (partie K).** Référence : 53 % au 3e retrait, 27 % perdus par le
plancher, 119 $ par mois de vie. La meilleure qui reste sous 30 % de comptes perdus (2 MNQ dès 2 600 $, nuit chaque
soir, retrait à 1 500 $) fait 59 %, 25 % et 145 $ : +22 %, sous la barre de 25 %. Aucune n'est adoptée (`resultats/partie_k.txt`).

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

**Attention : ces chiffres sont trop beaux.** Ils simulent le frein comme un « demi-MNQ », qui n'existe pas. Avec un
vrai MES, le premier réglage donne 53 % au 3e retrait et 27 % de comptes perdus par le plancher (partie J).

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
| `garde.py` | Contrôle avant chaque ordre : plancher, limite du jour (nuit comprise), taille maximale, frein, jours de la Fed, fenêtre 16 h 55 - 18 h, compteur d'inactivité, consigne du secours d'une heure et de la nuit, limite de baisse de 15 % pour un compte personnel | `python3 garde.py` lance ses tests (dont ton cas : +1 800 $ puis −1 100 $ = marge 1 400 $) |
| `rapport_matin.py` | Revue des trades de la veille depuis le journal du bot : résultat, pire et meilleur moment de chaque trade, écarts aux règles, marge, alertes, consigne du secours et de la nuit ; envoi Telegram possible | redonne les −272 $ du trade audité du 21 octobre 2026 en 4 MNQ |

Ils ne sont pas branchés sur ton bot C# ni sur GitHub Actions : ce sont des modules à lancer ou à intégrer.

## Pour relancer

```bash
git worktree add ../kb origin/claude/keen-babbage-r686cl
git worktree add ../at origin/claude/affectionate-turing-tnz0mn
git worktree add ../op origin/claude/optimistic-ptolemy-xs24ra
cd chantier && pip install numpy pandas numba
python3 nuit.py && python3 compte.py && python3 compte.py 2 && python3 inactivite.py
python3 variantes.py g h1 h2 h3 mois
python3 tailles.py j k k2
python3 divers.py && python3 machine.py nq && python3 machine.py btc
```

## Limites

- Le contrôle 2023 - 2026 avait déjà servi à d'autres études du projet : ce n'est pas un coffre vierge.
- La nuit est lue sur un CFD (prix acheteur, barres de 5 minutes) : un vrai stop de nuit peut glisser de plus d'un
  tick. Le fichier a des trous en 2023.
- Les pourcentages du compte reposent sur 122 comptes qui se chevauchent et sur une poignée de dates de perte : ce
  sont des ordres de grandeur.
- Le frein du bot est simulé comme une demi-taille de MNQ ; en vrai, c'est 1 MES, qui ne bouge pas exactement comme
  un demi-MNQ. Depuis les parties J et K, les trades de nuit et de secours sous le frein sont de vrais MES.
- Un compte perdu coûte aussi une nouvelle qualification (frais et temps), que le simulateur ne compte pas.
- Le filtre delta du bot ne peut pas être rejoué avant avril 2026 : le compte simule le bot sans lui.
- Le contrat du compte « funded » après le 3e retrait n'est pas connu : ses chiffres reposent sur des hypothèses.
- Machine sur le bitcoin : positions fermées à minuit UTC (et non après 24 h), frais de 4 points de base.
