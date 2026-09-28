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
