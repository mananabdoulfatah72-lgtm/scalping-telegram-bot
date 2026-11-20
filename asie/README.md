# Minuit à Paris : la réouverture du soir (machine 7, règles fixées le 20 novembre 2026, avant tout calcul)

## La demande

> Tous les jours à minuit, heure de Paris, il se passe une dinguerie à l'ouverture de la session asiatique, beaucoup
> plus clean que l'ouverture US. La majorité de mes gains actuels viennent de la session asiatique. Étudie tous les
> phénomènes et études possibles, trouve ce qui est compatible avec l'ouverture asiatique et le meilleur marché.

## Ce que « minuit à Paris » est vraiment

- **18 h à New York : la réouverture quotidienne des futures du CME** (Globex), après la pause de 17 h à 18 h. C'est
  minuit à Paris presque toute l'année (6 heures d'écart), et 23 h pendant environ trois semaines par an, quand les
  États-Unis et l'Europe ne changent pas d'heure le même jour.
- **Ce n'est pas l'ouverture de Tokyo** (9 h à Tokyo = 1 h à Paris en hiver, 2 h en été), ni celle de Hong Kong et de
  Shanghai (9 h 30 = 2 h 30 à Paris en hiver). De novembre à mars, c'est aussi l'ouverture de Sydney.
- **Chez Bulenox, on peut y trader** : la session qui rouvre à 18 h fait partie de la journée de trading suivante. Il
  faut seulement être à plat avant 16 h 59 (New York).

## Ce que disent les études

- **La hausse des indices américains se fait la nuit.** Les futures du S&P 500 ont gagné l'essentiel de leur hausse
  hors de la séance de New York (Cliff, Cooper, Gulen 2008 ; Lou, Polk, Skouras 2019).
- **Mais pas à la réouverture.** Boyarchenko, Larsen et Whelan (« The Overnight Drift », Review of Financial Studies,
  2023) la trouvent concentrée entre 2 h et 3 h (New York), à l'ouverture européenne, et plus forte après des ventes en
  fin de séance américaine. Bondarenko et Muravyev (« Market Return Around the Clock », JFQA) : sur 2004 - 2018, les
  quatre heures de 23 h 30 à 3 h 30 (New York) font toute la hausse ; le volume et la volatilité montent d'un coup à
  18 h et à l'ouverture de Hong Kong et de la Chine, puis retombent.
- **Et elle a disparu.** Les auteurs de la Fed de New York (« The Disappearing Overnight Drift », juillet 2026) ne la
  trouvent plus sur 2021 - 2025 ; les fonds créés pour la capter (NightShares) ont fermé.
- **Volume** : pendant les heures d'Asie, 50 à 100 fois moins de contrats que pendant la séance américaine.

## Déjà testé dans le projet (pas refait)

- `nuit/` (branche `claude/keen-babbage-r686cl`) : achat à 18 h, vente à 9 h 30 sur NQ et ES, rejeté (NQ : t 1,74).
- `sessions24/`, machine 5 : fixing de Tokyo, cassure des 30 ou 60 premières minutes de Tokyo, fourchette d'Asie cassée
  à Londres, Tokyo → Londres et New York → Tokyo. Rien après frais : les effets existent, mais sont 2 à 3 fois plus
  petits que les frais.
- `sessions24/`, machine 6 : jours « gotobi » du yen (échoue au coffre), écart du week-end (non tradable sur la CME :
  tout se fait avant la réouverture de 18 h).

**Jamais testé : la réouverture de 18 h elle-même.** C'est l'objet de cette machine.

## Données

- **HistData, barres de 5 minutes en UTC, 2012 → 2 octobre 2026**, fichiers `sessions24/annees/` de la branche
  `claude/keen-babbage-r686cl` : Nasdaq 100 et S&P 500 (cotations CFD, corrélation 0,999 - 1,000 avec les futures
  après recalage, `sessions24/README.md`), or, yen, dollar australien, euro, livre. Pétrole exclu (s'arrête en 2023).
- **Couverture mesurée avant ces règles** : indices et or sans barre entre 17 h et 18 h, avec une barre à 18 h 00 pour
  92 à 97 % des soirs de semaine ; les devises cotent sans interruption.
- **Contrôle sur de vrais futures** : barres d'une heure de Databento, NQ et ES (`nuit/donnees/`, jusqu'au 28 septembre
  2026), pour les fenêtres qui tombent sur des heures pleines.
- Heures en New York (America/New_York), changements d'heure compris. Entrées et sorties à l'ouverture des barres.

## Les soirs étudiés

Du lundi au jeudi soir (chacun suivi d'une journée de trading). Le dimanche soir est exclu (écart du week-end, déjà testé
par la machine 6).

## Les familles (aucun réglage après coup)

| # | Famille | Règle | Nombre |
|---|---|---|---|
| R1 | **Dérive de la réouverture** | Position à l'ouverture de la barre de 18 h 00, sortie à 19 h 00, 21 h 00 ou 23 h 30. Indices et or : achat seulement (dérive de nuit positive dans les études). Devises : achat et vente (pas de sens connu ; achat = achat de la première devise : euro, livre, dollar australien, dollar contre le yen). | 3 × 3 + 4 × 2 × 3 = 33 |
| R2 | **Le soir contre la fin de séance américaine** | Signal : sens du mouvement de 15 h 00 → 16 h 00 (dernière heure de New York) ou de 9 h 30 → 16 h 00 (séance entière), entre les ouvertures de ces barres. À 18 h 00 : position contraire (retour, l'idée de Boyarchenko et al.) ou dans le même sens (continuation) ; sortie à 19 h 00, 21 h 00 ou 23 h 30. | 7 × 2 × 2 × 3 = 84 |
| R3 | **Cassure de la fourchette de réouverture** | Fourchette des barres de 18 h 00 → 18 h 15 ou 18 h 00 → 18 h 30 (au moins 2 barres). Première clôture de 5 minutes au-delà, avant 20 h 00 ; entrée à l'ouverture de la barre suivante ; stop de l'autre côté de la fourchette ; sortie à 21 h 00, 23 h 30 ou 3 h 00 (ouverture européenne). Un trade par soir. | 7 × 2 × 3 = 42 |
| R4 | **Cassure de l'ouverture de Hong Kong et de Shanghai** | Fourchette de 9 h 30 → 10 h 00, heure de Hong Kong (Asia/Hong_Kong). Première clôture au-delà avant 11 h 30 (Hong Kong) ; stop de l'autre côté ; sortie à 12 h 00 (Hong Kong, pause de midi) ou à 3 h 00 (New York). | 7 × 2 = 14 |

**173 stratégies.** Frais d'un aller-retour, ceux de la machine 5 : 1,5 point sur le Nasdaq (MNQ), 0,9 point sur le
S&P 500 (MES), 1,5 point de base sur les devises, 2 points de base sur l'or.

## Le tri (celui des machines 5 et 6)

1. **Exploration 2012 - 2022**, gains nets par soir :
   - t ≥ 2 ;
   - placebo battu à 95 % : R1, la même fenêtre décalée à toutes les autres heures de la journée (pas de 5 minutes, à
     plus de 2 heures de 18 h) ; R2, R3 et R4, 1 000 tirages au hasard du sens de chaque trade, mêmes heures ;
   - positive dans au moins 2 des 3 sous-périodes (2012 - 2015, 2016 - 2019, 2020 - 2022) ;
   - Benjamini-Hochberg à 10 % sur les p des placebos des 173 ;
   - moins de 200 soirs avec un trade : « non testable ».
2. **Coffre 2023 → 2 octobre 2026, ouvert une seule fois** pour les survivantes : même sens, t au moins égal au seuil
   de Bonferroni (5 % unilatéral, m survivantes), positive au moins 3 années sur 4 (2026, incomplète, compte).
3. **Réalisme**, pour celles qui passent le coffre : frais doublés (la nuit, l'écart entre acheteurs et vendeurs est plus
   large) ; pour les indices, mêmes fenêtres sur les vrais futures (Databento) quand elles tombent sur des heures
   pleines. Ensuite seulement : le compte Bulenox, puis le papier.

## Pour information seulement (aucune décision) : minuit est-il « plus propre » que 15 h 30 ?

Pour le Nasdaq, le S&P 500 et l'or, sur 2012 - 2022 et sur 2023 - 2026 :
- la volatilité moyenne de chaque barre de 5 minutes, de 17 h à 3 h (New York) ;
- l'amplitude de la première heure (plus haut − plus bas), en points, après 18 h 00 et après 9 h 30 ;
- l'efficacité du mouvement de la première heure : |clôture − ouverture| ÷ somme des |variations de 5 minutes|
  (1 = une ligne droite, proche de 0 = des allers-retours), après 18 h 00 et après 9 h 30.

## Résultat de l'exploration 2012 - 2022 (20 novembre 2026) : `exploration7.txt`, `info7.txt`

**Aucune survivante sur 173. Le coffre 2023 - 2026 n'est pas ouvert pour elles.**

- **Nasdaq et S&P 500 : tout perd après frais.** Acheter le NQ à 18 h 00 et revendre à 19 h 00 rapporte +0,25 point de
  base avant frais, pour environ 2,6 de frais. Les cassures de la fourchette de réouverture perdent même avant frais
  (−1,1 à −1,8 point de base par soir sur le NQ) : elles se retournent plus souvent qu'elles ne continuent.
- **L'idée de Boyarchenko et al. se voit, mais en petit** : après une dernière heure de séance en baisse, le NQ remonte
  un peu de 18 h à 19 h (+0,77 point de base avant frais, placebo battu, p = 0,009), trois fois moins que les frais.
- **Une seule règle se détache : l'or acheté à 18 h 00 et revendu à 23 h 30.** +3,16 points de base par soir avant frais,
  bat toutes les autres heures (p < 0,001), positive dans les 3 sous-périodes ; t 1,75 après frais (2 exigé).

**Le pic de minuit, mesuré (`info7.txt`).** Amplitude moyenne d'une barre de 5 minutes, 2023 - 2026 :

| | Barre de 18 h 00 (minuit à Paris) | 18 h 05 | 18 h 30 | Barre de 9 h 30 (15 h 30 à Paris) |
|---|---|---|---|---|
| Nasdaq 100 | 9,5 pb (environ 25 points) | 6,6 | 5,6 | 29,1 pb (environ 78 points) |
| S&P 500 | 7,9 pb | 5,1 | 4,0 | 17,1 pb |
| Or | 11,7 pb | 7,6 | 6,1 | 18,0 pb |

- Le pic existe : la barre de minuit est la 2e plus agitée de la nuit sur le Nasdaq et le S&P 500, derrière l'ouverture
  européenne (3 h à New York, 9 h à Paris). Il retombe dès la barre suivante.
- Il est 3 fois plus petit que l'ouverture de New York.
- **Minuit n'est pas « plus propre »** : l'efficacité du mouvement de la première heure est la même à 18 h 00 et à
  9 h 30 (0,30 sur le Nasdaq, 0,29 sur le S&P 500 et sur l'or) ; l'amplitude de cette heure est 3 fois plus petite.
- **D'où vient le pic** : de 17 h 45 à 18 h (New York), la CME accepte les ordres sans les exécuter ; à 18 h, tout s'exécute
  d'un coup (avis SER 8921 de la CME, 2022), dans un marché 50 à 100 fois moins actif que la séance américaine.

## Après l'exploration : un test unique de l'or sur le coffre (fixé le 20 novembre 2026, avant d'ouvrir 2023 - 2026)

- **Pourquoi celui-là.** C'est la seule des 173 qui bat tous ses placebos (p < 0,001), qui gagne dans les 3
  sous-périodes et qui n'échoue que sur le t après frais (1,75 pour 2 exigé). Les frais de la machine (2 points de base)
  valent environ 4 $ l'aller-retour sur un micro-or (MGC) quand l'or est à 2 000 $ ; ils pèsent moitié moins à 4 000 $.
- **Règle, inchangée** : achat de l'or à l'ouverture de la barre de 18 h 00 (New York), du lundi au jeudi soir, vente à
  l'ouverture de la barre de 23 h 30 (minuit → 5 h 30 à Paris).
- **Période** : 2023-01-01 → 2026-10-02, jamais regardée pour cette règle.
- **Frais, deux lectures fixées maintenant** :
  - décisive : 2 points de base par aller-retour, ceux de l'exploration ;
  - pour information : le MGC avec la convention du projet (1 $ par ordre et 1 tick de 1 $ par ordre), soit 4 $ pour
    10 onces, en rendement 4 ÷ (10 × prix).
- **Passe si** : t ≥ 1,64 (un seul test, 5 % unilatéral) avec les frais décisifs, et gain positif au moins 3 années sur 4
  (2026 incomplète compte).
- **Attention à ce qu'on teste** : c'est la meilleure de 173 ; un résultat plus faible sur le coffre est attendu, même si
  l'effet est réel.
- **S'il passe** : vérifier que Bulenox ouvre le MGC, mesurer les vrais frais à cette heure en papier (`usine/rapprochement.py`),
  puis seulement 1 MGC sur le compte. **S'il échoue** : la piste est fermée.

### Résultat du test de l'or sur le coffre (20 novembre 2026) : `or_coffre.json`

**Il passe la règle fixée** : 730 soirs, +8,66 points de base par soir avant frais, +6,66 après, **t 3,49**, positif les 4
années (2023 +935, 2024 +843, 2025 +1 458, 2026 +1 625 points de base). Avec les frais d'un MGC : t 3,77, environ +18 500 $
pour 1 MGC sur la période.

### Avant d'y croire : robustesse, pour information (`or_robustesse.txt`)

- **Le gain se fait surtout dans les 5 premières minutes.** Entrée à 18 h 05 au lieu de 18 h 00 : +3,3 points de base nets
  par soir, t 1,76 ; entrée à 18 h 30 : t 1,25. Sur 2023 - 2026, l'heure de 18 h fait à elle seule 58 % de toute la hausse de
  l'or.
- **C'est exactement là que les données sont les moins fiables.** Ce sont des cotations du comptant (prix acheteur) : à la
  réouverture, l'écart entre acheteurs et vendeurs est très large, puis se resserre en quelques minutes. Le prix acheteur
  remonte alors sans que personne ait pu acheter à ce prix. La machine 6 a trouvé le même piège sur l'écart du week-end
  du dollar australien (`sessions24/README.md`).
- Frais doublés (4 points de base), entrée à 18 h 00 : t 2,44. Ça ne règle pas le problème : à 18 h, l'écart réel peut
  dépasser 10 points de base.
- Fenêtres de 5 h 30 placées ailleurs dans la journée : 5,4 % font aussi bien (celles qui contiennent aussi 18 h). Une
  fenêtre au hasard rapporte +1,9 point de base avant frais, contre +8,7 à 18 h.
- **En dollars, 1 MGC à 4 173 $** : +30 $ par soir en moyenne, écart-type 215 $, 57 % de soirs gagnants, pire soir −1 358 $,
  pire moment d'un soir −2 117 $, pire baisse −5 536 $.

**Verdict.** Statistiquement, l'or passe. Mais l'essentiel du gain tient dans les 5 premières minutes, là où ces cotations
ne sont pas un prix auquel on peut acheter. **Ce n'est pas validé comme tradable.** La seule façon de trancher : 3 à 4
semaines en papier sur le MGC, en notant chaque soir le vrai prix d'achat à 18 h 00 (minuit à Paris) et le prix de
23 h 30, puis `usine/rapprochement.py`. Avec 1 900 $ de marge sur le compte, 1 MGC est déjà trop gros sans limite : son
pire soir (−1 358 $) en mangerait les trois quarts.
