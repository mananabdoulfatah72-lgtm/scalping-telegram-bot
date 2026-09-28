# Bot de challenge 50K (coussin)

Objectif : valider un challenge futures 50K en moins d'un an. `bot_challenge.py` rejoue le bot sur
les vrais prix (NQ minute 2011-2026 pour la zone de bruit, mélange tendance + achat pour la nuit).

## Le bot

- **Stratégie** : zone de bruit sur MNQ (intraday, voir `intraday/`), et pour les firmes qui
  permettent de garder des positions la nuit, la moitié du risque dans le mélange tendance + achat.
- **Taille des positions (coussin)** : chaque jour, le risque d'une journée normale (1 écart-type
  prévu) vaut f × coussin, où coussin = solde − limite de perte. Loin de la limite, le bot prend plus ;
  près de la limite, il réduit jusqu'à ne plus trader. f testé à 0,15, 0,25 et 0,35.
- **Après un échec**, une nouvelle tentative est achetée le lendemain, jusqu'à 12 mois.

## Résultats (un départ chaque semaine de 2011 à 2025)

| Firme | f | Validé en 12 mois | Sans avantage (même bot) | Tentatives achetées (moyenne / max) | Séances jusqu'à la validation (médiane) |
|---|---|---|---|---|---|
| Apex 50K (30 jours par tentative) | 0,25 | **87 %** | 61 % | 5,8 / 18 | 72 |
| Apex 50K | 0,35 | **94 %** | 82 % | 5,0 / 17 | 53 |
| Phidias 50K (zone de bruit) | 0,25 | 36 % | 20 % | 1,2 / 9 | 52 |
| Phidias 50K (zone + mélange) | 0,35 | 34 % | 14 % | 1,1 / 4 | 42 |
| Topstep 50K | 0,25 | 30 % | 17 % | 1,3 / 8 | 48 |

Détail complet : `resultats.txt`.

## Ce qu'il faut comprendre

- **Chez Apex, c'est surtout le rachat de tentatives qui fait valider** : le coussin fait rarement
  sauter le compte (3 à 16 % des tentatives), la plupart arrivent au bout des 30 jours sans avoir
  atteint l'objectif, et on en rachète une. Sans aucun avantage, le même bot valide déjà 61 à 82 % du
  temps en 12 mois ; la zone de bruit ajoute 12 à 26 points. Le coût réel, c'est le prix d'environ
  6 tentatives (jusqu'à 18 dans les mauvaises périodes).
- **Chez Topstep et Phidias**, sans limite de temps, le bot tient longtemps sans sauter ni réussir
  quand la stratégie traverse une mauvaise période (2011-2017) : environ 1 chance sur 3 de valider
  en 12 mois.
- **Valider n'est pas gagner** : le compte financé garde une limite de perte du même type ; les
  retraits resteront petits tant que le coussin est petit.
- **Limites** : la zone de bruit gagne surtout depuis 2018 (frais relatifs plus faibles) ; f a été
  choisi parmi 3 valeurs sur les mêmes données ; le mélange est supposé divisible ; **les règles des
  firmes sur les robots de trading sont à vérifier** (certaines interdisent ou encadrent les bots).

## Avec 2 comptes au maximum

Même rejeu, mais on s'arrête après 2 comptes achetés (ou 12 mois) :

| Firme | Réglage | Validé en 12 mois avec 2 comptes max | Sans avantage |
|---|---|---|---|
| Phidias 50K (zone de bruit) | f = 0,15 | 33 % (1,0 compte utilisé en moyenne) | 16 % |
| Phidias 50K (zone + mélange) | f = 0,35 | 33 % | 14 % |
| Apex 50K | f = 0,35 | 33 % | 22 % |
| Topstep 50K | f = 0,25 | 27 % | 13 % |

Chez Phidias avec f = 0,15, un seul compte réussit 39 % du temps et ne saute que 4 % du temps ;
le reste du temps il reste en vie sans atteindre l'objectif (paiement unique : attendre ne coûte rien).

## Après la validation : ce que rapporte le compte financé (`finance.py`)

Hypothèses Phidias à vérifier : limite bloquée à 50 100 $ une fois le solde à 52 600 $ ; retrait
mensuel de ce qui dépasse 52 600 $ si la meilleure journée ≤ 30 % du gain ; 80 % du retrait pour toi.

| Bot | Reçu en 12 mois (moyenne) | Médiane | Rien touché | Compte perdu |
|---|---|---|---|---|
| Zone de bruit seule, f = 0,15 | 679 $ | 0 $ | 86 % | 8 % |
| Zone + mélange 50/50, f = 0,15 | 625 $ | 0 $ | 71 % | 4 % |
| Multi (zone + panier), f = 0,15 | 811 $ | 0 $ | 62 % | 0 % |

## Bot « multi » : zone de bruit + panier de sources de nuit

Panier : tendance + achat, veille de la Fed, actions pilotées par la volatilité, carry (chacune au
même risque). Trois de ces sources ont échoué de peu aux tests du fonds : résultat optimiste.

| Réglage | 1 compte, sans limite de temps | Durée médiane jusqu'à la validation | En 12 mois, 2 comptes max | Sans avantage |
|---|---|---|---|---|
| f = 0,10 | réussi 83 %, sauté 0 % | 27 mois | 16 % | 0 % |
| f = 0,15 | réussi 86 %, sauté 0 % | 20 mois | 26 % | 1 % |
| f = 0,25 | réussi 54 %, sauté 20 % | 8 mois | 36 % | 10 % |

Choix à faire : valider sans sauter prend environ 2 ans ; valider dans l'année donne environ
1 chance sur 3, avec un risque de sauter. Détails : `resultats_finance.txt`, `resultats_multi.txt`.

## Version 7 adaptée aux futures intraday (fixée le 28 septembre 2026, avant son test)

Demande : adapter la version 7 (étude `secteurs/`) à un challenge 50K futures, avec clôture le jour même,
en réduisant le risque quitte à gagner moins.

Ce qui ne peut pas passer : les actions (un compte futures n'en a pas) et la nuit (clôture obligatoire).
Il reste la **technologie via le Nasdaq-100 (MNQ)**, entre l'ouverture et la clôture. Mise en garde
fixée avant le test : les études (Lou, Polk et Skouras, 2019) trouvent que les gains du momentum se font
surtout **la nuit**. Une version de jour peut donc perdre l'avantage.

Règles (données NQ minute 2011-2026, 9 h 30 - 15 h 59, heure de New York) :
- **Signal, comme la version 7, une fois par mois** : à la dernière séance du mois, rendement du
  Nasdaq de t − 126 à t − 21 séances. Le rendement de la nuit n'est pas compté les jours de changement
  d'échéance. S'il est positif, le robot achète chaque séance du mois suivant (**A, avec filtre**). La
  **variante B** achète chaque séance (la version 7 est toujours investie).
- **Chaque séance** : achat à l'ouverture de 9 h 30. **Stop à 0,5 % sous l'ouverture** : il limite
  la perte du jour, et la sortie se fait au stop moins 1 tick. Sinon, vente à 15 h 59. Toujours à plat
  le soir. Pas de trade le jour du changement d'échéance ni les jours de séance incomplète.
- Frais : 1 $ par ordre et 1 tick de glissement (1,5 point de NQ par aller-retour, comme `intraday/`).
- **Taille (coussin, moins de risque)** : nombre de MNQ tel que la perte au stop ne dépasse pas f × coussin
  (coussin = solde − limite de perte). f vaut 0,15, 0,25 ou 0,35. Si le coussin ne permet pas 1 MNQ, le
  robot ne trade pas.
- Mêmes règles de firmes que plus haut (`bot_challenge.REGLES`, à vérifier). Mêmes mesures : réussite en
  une tentative et en 12 mois, comparée au même bot sans avantage.
- Avant le challenge, on vérifie aussi l'avantage : gain net moyen par trade, t, et les sous-périodes.
  Enfin, pour information, le partage du rendement du Nasdaq entre la nuit et la journée.
- Deux essais (A et B) inscrits dans `fonds/essais.csv`. Aucune autre variante (stop, heure, taille)
  ne sera essayée après les résultats.
