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

## Les 5 premières minutes (20 novembre 2026, pour information) : `cinq_minutes.txt`

Question de l'utilisateur : un bot qui ne trade que les 5 minutes qui suivent minuit (heure de Paris), sur l'or, le
Nasdaq ou un autre marché. Mesure de la bougie de 18 h 00 → 18 h 05 (New York), achat :

| Marché | 2012 - 2022 : brut moyen, % positifs | 2023 - 2026 : brut moyen, % positifs | Frais |
|---|---|---|---|
| Nasdaq 100 | −0,13 pb, 46 % | +0,33 pb, 52 % | 0,8 à 2,9 pb |
| S&P 500 | −0,26 pb, 43 % | −0,06 pb, 49 % | 1,6 à 3,8 pb |
| Or | +1,40 pb, 63 % | +3,34 pb, 73 % | 2 pb |
| Dollar australien | +1,08 pb, 63 % | +1,65 pb, 69 % | 1,5 pb |
| Euro | +0,40 pb, 58 % | +0,93 pb, 68 % | 1,5 pb |
| Livre | +0,60 pb, 60 % | +1,25 pb, 68 % | 1,5 pb |
| Yen (dollar contre yen) | +0,13 pb, 50 % | +0,51 pb, 58 % | 1,5 pb |

- **Nasdaq et S&P 500 : rien**, avant comme après frais. Le sens de la dernière heure de New York n'y change rien.
- **Sur l'or et les devises, le prix acheteur monte presque toujours dans ces 5 minutes, sur tous les marchés en même
  temps**, y compris le dollar contre le yen, alors qu'un vrai mouvement du dollar ferait baisser l'un quand les autres
  montent. C'est la signature de l'écart entre acheteurs et vendeurs qui se resserre : le prix acheteur remonte vers le
  milieu de la fourchette, sans que personne ait pu acheter à ce prix. Avec ces données (prix acheteur seulement), un bot
  des 5 premières minutes ne peut pas être jugé.
- **Pour le juger** : il faut les vrais prix d'achat et de vente à 18 h 00 (Rithmic dans Quantower, en papier), sur le MGC,
  le MNQ et une micro-devise.

## Vérification sur de vrais prix de futures (fixée le 20 novembre 2026, avant le calcul)

- **Données** : Yahoo Finance, contrats continus de la CME (prix des transactions), heure de New York, fichiers
  `donnees_libres/yahoo/` de la branche `claude/affectionate-turing-tnz0mn` :
  - barres de 5 minutes du 12 août au 21 octobre 2026 ;
  - barres d'une heure du 30 mai 2024 au 21 octobre 2026.
  Le contrat continu n'est pas ajusté aux changements d'échéance : un trade du soir n'est touché que si Yahoo change
  d'échéance pendant ce trade.
- **Marchés** : or (MGC, et GC pour contrôle), Nasdaq (MNQ), S&P 500 (MES), euro (6E), yen (6J : yen contre dollar),
  dollar australien (6A), livre (6B).
- **Test 1, les 5 premières minutes** (description) : achat à l'ouverture de la barre de 18 h 00, vente à l'ouverture de
  celle de 18 h 05, du lundi au jeudi soir. Moyenne, part des soirs en hausse, t. Sur les soirs communs (12 août →
  2 octobre 2026), la même mesure sur les cotations HistData. Si HistData monte et pas les futures, l'effet des 5 premières
  minutes est un artefact de cotation.
- **Test 2, l'or du soir sur de vrais prix (décisif pour l'or)** : achat de l'or (MGC) à l'ouverture de la barre de 18 h,
  vente à l'ouverture de celle de 23 h (la plus proche de 23 h 30 en barres d'une heure), du lundi au jeudi soir, 30 mai
  2024 → 21 octobre 2026, frais d'un MGC (4 $ l'aller-retour pour 10 onces). **Confirmé** si : t ≥ 1,64, et moins de 5 %
  des mêmes fenêtres de 5 heures, commencées à toutes les autres heures pleines (à plus de 2 heures de 18 h), font aussi
  bien. Sinon, la piste de l'or est fermée.
- Pour information : Nasdaq et S&P 500, 18 h → 19 h sur les barres d'une heure.

### Résultat de la vérification sur de vrais futures (20 novembre 2026) : `vrais_futures.txt`

**Test 1, les 5 premières minutes (39 soirs, 12 août → 21 octobre 2026)** : sur les mêmes soirs, les cotations HistData
montent beaucoup plus que les vrais futures.

| Marché | Vrais futures, soirs communs | HistData, mêmes soirs | % de soirs en hausse sur HistData |
|---|---|---|---|
| Or (MGC) | +1,85 pb | +6,34 pb | 79 % |
| Livre (6B) | +0,16 pb | +2,25 pb | 90 % |
| Dollar australien (6A) | −0,40 pb | +2,10 pb | 75 % |
| Euro (6E) | −0,08 pb | +1,35 pb | 76 % |

L'effet des 5 premières minutes sur l'or et les devises est donc surtout un artefact des cotations (prix acheteur qui
remonte quand l'écart se resserre). Sur les vrais futures du Nasdaq et du S&P 500, la bougie de minuit fait +1,48 et
+0,88 pb en moyenne (t 1,20 et 1,29) : rien de significatif sur 39 soirs, et rien sur 14 ans de HistData.

**Test 2, l'or du soir (MGC, 18 h → 23 h, 474 soirs, mai 2024 → octobre 2026)** : +2,67 pb nets par soir, **t 0,95**,
49 % de soirs gagnants, première moitié négative (−108 pb), 16,7 % des fenêtres de 5 heures commencées ailleurs font aussi
bien. **Non confirmé sur de vrais prix : la piste de l'or est fermée**, comme la règle le prévoyait.

**Conclusion de la machine 7** : la réouverture de minuit a bien un pic de volatilité, mais aucune règle n'en tire un
gain sur de vrais prix après frais, sur aucun des 7 marchés.

# Machine 8 : la zone de bruit pendant la session asiatique (règles fixées le 20 novembre 2026, avant tout calcul)

**Pourquoi.** La zone de bruit est la seule source de gain validée du projet (5 portes de l'usine). Elle n'a jamais été
jouée la nuit. L'utilisateur dit faire l'essentiel de ses gains pendant la session asiatique.

**Ce qui la distingue de ce qui a échoué** : les cassures du début de session (machine 5, F3) et de la réouverture
(machine 7, R3) utilisent une fourchette fixe. La zone utilise une bande qui s'adapte au mouvement habituel de chaque
heure, et sort quand le prix revient sous la bande ou sous son prix moyen.

**Règle (celle du bot, transposée à la nuit)**, du lundi au jeudi soir, heures de New York :
- ouverture de référence O = ouverture de la barre de 18 h 00 ; clôture américaine C = clôture de la dernière barre entre
  16 h 00 et 17 h 00 (à défaut, O seule) ;
- contrôles toutes les 30 minutes, de 18 h 30 à 2 h 30, au prix de clôture de la barre qui finit à l'heure du contrôle ;
- bruit au contrôle k = moyenne, sur les 14 nuits complètes d'avant, de |prix au contrôle k ÷ O − 1| ;
- haut = max(O, C) × (1 + largeur × bruit) ; bas = min(O, C) × (1 − largeur × bruit) ;
- en achat, sortie si le prix ≤ max(haut, prix moyen) ; en vente, sortie si le prix ≥ min(bas, prix moyen) ; à plat, achat
  au-dessus du haut, vente sous le bas. Le prix moyen est la moyenne des clôtures de 5 minutes depuis 18 h 00 (pas de
  volume dans ces données, donc pas de VWAP) ;
- tout est fermé à l'ouverture de la barre de 3 h 00 (ouverture européenne) ;
- nuit complète : barre de 18 h 00 et les 17 contrôles présents ; on ne trade que les nuits complètes.

**Stratégies** : Nasdaq (MNQ), S&P 500 (MES), or (MGC) × largeur {1,0 (celle du bot) ; 1,4 (milieu du plateau de
l'usine)} = **6**. Frais d'un aller-retour : ceux de la machine 7.

**Tri** : celui de la machine 7. Exploration 2012 - 2022 (t ≥ 2, placebo de 1 000 sens au hasard battu à 95 %, 2
sous-périodes sur 3, Benjamini-Hochberg 10 % sur 6), puis coffre 2023 → 2 octobre 2026 une seule fois (Bonferroni, 3 années
sur 4), puis les vrais futures avant tout compte.

## Résultat de la machine 8 (20 novembre 2026) : `zone_nuit_exploration.txt`

**Aucune survivante. La zone de bruit perd la nuit sur les 3 marchés, et même avant frais** :

| Marché, largeur | Avant frais, par nuit | Après frais | t |
|---|---|---|---|
| Nasdaq, 1,0 | −0,88 pb | −6,59 pb | −7,67 |
| Nasdaq, 1,4 | −1,62 pb | −6,62 pb | −6,87 |
| S&P 500, 1,0 | −1,26 pb | −7,29 pb | −6,04 |
| Or, 1,0 | −1,38 pb | −5,43 pb | −7,78 |

La nuit, un prix qui sort de sa bande habituelle revient plus souvent qu'il ne continue : l'inverse de la séance
américaine. Le mécanisme de la zone (couverture des teneurs de marché, rééquilibrage des ETF à levier) vit pendant les
heures de New York. Jouer l'inverse (revenir vers la bande) gagnerait 1 à 2 points de base avant frais, moins que les
frais de ses 2 trades par nuit : ce n'était pas une règle fixée d'avance, ce n'est donc qu'une indication.

# Machine 9 : le Nikkei pendant la séance de Tokyo (règles fixées le 20 novembre 2026, avant tout calcul)

**Pourquoi.** La recherche du 20 novembre (`reports/Anomalies de la session asiatique.md`) ferme presque toutes les pistes
de la nuit (dérive de Boyarchenko nulle depuis 2021, fixing de Tokyo plus petit que les frais, BOJ arrêtée, or seulement sur
cotations). Il reste le Nikkei pendant sa propre séance, jamais testé dans le projet : momentum de fin de séance (Baltussen,
Da, Lammers, Martens, JFE 2021 ; BOJ 2016 : les fonds à levier suivent la journée à la clôture), ouverture de Tokyo qui
sur-réagit à la séance américaine (Finance Research Open 2026), et la zone de bruit (seule source validée du projet) jouée
dans la séance « maison » du Nikkei. Contrat visé : Micro Nikkei en dollars (MNK, 0,50 $ par point, CME), **à condition que
Bulenox l'ouvre** (sa FAQ ne le cite pas).

**Données** : HistData JPXJPY (Nikkei 225, cotations, 5 minutes, UTC, 2012 → 16 octobre 2026, branche
`claude/affectionate-turing-tnz0mn`) ; S&P 500 HistData (`usa500idxusd`) pour le signal de N2. Horloge vérifiée avant le
calcul : la barre la plus agitée est celle de 0 h 00 UTC (9 h 00 à Tokyo) en hiver comme en été.

**Conventions** : jours de Bourse de Tokyo (lundi - vendredi, hors fériés japonais et 31 décembre - 3 janvier) ;
C = clôture de la Bourse de Tokyo (15 h 00 avant le 5 novembre 2024, 15 h 30 depuis) ; C + 15 min = fin de la séance de
jour des futures d'Osaka ; prix = ouverture de la barre de 5 minutes qui commence à l'heure dite ; ni stop ni seuil ;
frais décisifs 2,8 points de base par aller-retour (un MNK à 50 000 points) ; pour information, les mêmes calculs avec
14 points d'indice (le vrai coût d'un MNK à chaque date) et avec des frais doublés.

| Règle | Signal | Trade |
|---|---|---|
| N1 | R = variation de C + 15 min la veille à C − 15 min | dans le sens de R, de C − 15 min à C + 15 min |
| N1v | variation de C + 15 min la veille à 9 h 30 (Gao et al.) | même fenêtre que N1 |
| N2 | S = variation du S&P 500 de 16 h à 16 h (New York) sur la dernière séance américaine finie avant 9 h à Tokyo | contre S, de 9 h 00 à 9 h 30 (Tokyo) |
| N2v | même S | dans le sens de S, de C − 15 min à C + 15 min |
| Z | zone de bruit de la machine 8 à l'horloge de Tokyo : O = 9 h 00, C' = clôture de Tokyo de la veille, bruit moyen sur 14 séances, largeur 1,0, prix moyen = moyenne des clôtures depuis 9 h | contrôles toutes les 30 min de 9 h 30 à C − 30 min (pas d'entrée au dernier), tout fermé à C |

**Tri** (celui des machines 7 et 8) : exploration 2012 - 2022, t ≥ 2 après frais (gains sommés par jour), placebo de
1 000 tirages au hasard du sens de chaque trade battu à 95 %, positive dans 2 sous-périodes sur 3, Benjamini-Hochberg à
10 % sur les 5 ; puis coffre 2023 → 2 octobre 2026, ouvert une seule fois : seuil de Bonferroni, 3 années positives sur 4.
Une survivante devra ensuite passer de vrais prix du Nikkei (que le projet n'a pas) et la vérification chez Bulenox.
Code : `asie/machine9.py`.

## Résultat de la machine 9 (20 novembre 2026) : `exploration9.txt`, `exploration9.json`

**Aucune survivante. Le coffre 2023 - 2026 du Nikkei n'est pas ouvert : il reste vierge.**

| Règle | Avant frais, par jour (t) | Après 2,8 pb de frais (t) | Placebo | Sous-périodes | $ pour 1 MNK, 2012 - 2022 |
|---|---|---|---|---|---|
| N2 ouverture de Tokyo contre le S&P 500 | +3,63 pb (t 5,45) | +0,83 pb (t 1,25) | p < 0,001 | + / − / + | +2 037 $ |
| Z zone de bruit à Tokyo | +5,23 pb (t 3,00) | +0,87 pb (t 0,50) | p < 0,001 | − / + / + | +1 326 $ |
| N1 fin de séance d'Osaka, sens de la journée | +2,08 pb (t 3,75) | −0,72 pb (t −1,30) | p < 0,001 | − / − / − | −1 573 $ |
| N1v signal de Gao et al. | +1,20 pb (t 2,18) | −1,60 pb (t −2,89) | p = 0,015 | − / − / − | −3 733 $ |
| N2v fin de séance dans le sens du S&P 500 | +0,97 pb (t 1,76) | −1,83 pb (t −3,35) | p = 0,049 | − / − / − | −4 414 $ |

- **Les trois phénomènes des études existent sur le Nikkei avant frais** : le momentum de fin de séance (t 3,75), le
  retournement de l'ouverture de Tokyo après la séance américaine (t 5,45), et la zone de bruit, qui gagne pendant la séance
  de Tokyo (t 3,00) alors qu'elle perdait la nuit sur le NQ, le ES et l'or (machine 8). Le mécanisme des fonds à levier et
  des couvertures vit bien dans la séance « maison » de chaque marché.
- **Mais ils sont plus petits que les frais d'un MNK** : environ 2,8 pb par aller-retour, contre 2 à 5 pb de gain brut
  par jour. Avec les frais doublés, tout perd ; avec le vrai coût d'un MNK aux prix de 2012 - 2022 (14 points d'indice),
  tout perd nettement. La meilleure, N2, rapporterait environ 185 $ par an pour un MNK.
- Code corrigé avant ce calcul (erreur de programmation, pas de règle) : les règles N2 et N2v prenaient le placebo des
  heures décalées au lieu des 1 000 tirages du sens fixés ci-dessus ; le premier lancement a été arrêté avant tout résultat.

# Machine 10 : deux familles jamais testées, aux frais d'aujourd'hui (règles fixées le 20 novembre 2026, avant tout calcul)

**Pourquoi ces deux-là.** Elles sont nouvelles dans le projet, alors que les variantes proches ont déjà été vues avant frais :
- **B, l'élan de fin de séance à l'heure de règlement propre à chaque marché** (Baltussen, Da, Lammers, Martens, JFE 2021 :
  « partout », dans plus de 60 futures, la journée prédit sa dernière demi-heure). L'étude large l'a testé à 15 h 30 - 16 h
  pour tous les marchés, sur des ETF, et l'a vu avant frais sur l'or (t +2,3 puis +3,0) et les obligations longues. Mais
  l'or se règle à 13 h 30, le pétrole à 14 h 30, les devises de la CME à 15 h (New York) : à ces heures, jamais testé.
- **T, le retournement de l'ouverture de Tokyo après la séance américaine**, net sur le Nikkei avant frais (machine 9,
  t 5,45), mais trop cher en Micro Nikkei. Ici, le même signal sur des contrats bien moins chers à l'heure de Tokyo.

**Frais décisifs : ceux d'aujourd'hui**, comme dans `etude_large/pistes/` (or à Londres) : 2 ticks de glissement plus les
commissions, sur le plus petit contrat raisonnable, divisés par la valeur du contrat au dernier prix avant le 2 octobre
2026 (calculé par le code). MNQ 3 $ ; MES 4 $ ; MGC 4 $ ; SIL 12 $ ; CL 25 $ (le Brent HistData sert d'approximation du
WTI, qui s'arrête en 2023) ; 6E, 6B, 6J, 6S 17,50 $ ; 6A, 6C, 6N 15 $.

| Famille | Règle | Marchés |
|---|---|---|
| T | S = variation du S&P 500 de 16 h à 16 h (New York) sur la dernière séance américaine finie avant 9 h à Tokyo ; position contre S de 9 h 00 à 9 h 30 (heure de Tokyo, jours de Bourse de Tokyo) | MNQ, MES, MGC (3) |
| B | R = variation du règlement de la veille à 30 minutes avant le règlement ; position dans le sens de R pendant les 30 dernières minutes (jours de Bourse de New York). Règlements : or 13 h 30, argent 13 h 25, pétrole 14 h 30, devises 15 h 00 | or, argent, pétrole, euro, livre, yen, dollar australien, dollar canadien, franc suisse, dollar néo-zélandais (10) |

**Tri** : celui des machines 7 à 9. Exploration 2012 - 2022 : t ≥ 2 après frais, placebo de 1 000 tirages du sens battu à
95 %, 2 sous-périodes positives sur 3, Benjamini-Hochberg à 10 % sur les 13. Coffre 2023 → 2 octobre 2026, ouvert une
seule fois : seuil de Bonferroni, 3 années positives sur 4. (Le coffre de l'or a déjà été ouvert une fois, pour une autre
règle, celle de 18 h : cette deuxième lecture est signalée.) Code : `asie/machine10.py`.

# Machine 11 : les mêmes effets, seulement les jours de grand mouvement (règle fixée le 20 novembre 2026, avant ce calcul)

**Née de l'exploration des machines 9 et 10, et dite comme telle.** Elles ont trouvé des effets réels avant frais (Nikkei
à l'ouverture de Tokyo t 5,45 et en fin de séance t 3,75 ; MNQ et MES à l'ouverture de Tokyo t 3,2 et 3,8 ; argent t 4,8,
pétrole t 2,7, or t 2,5, euro t 2,6 à l'heure de règlement), tous plus petits que les frais par trade. Si ces effets
viennent de flux de couverture ou de rééquilibrage, ils sont proportionnels à la taille du mouvement : ne jouer que les
grands mouvements doit augmenter le gain par trade, à frais égaux.

**Règle** : les 8 règles ci-dessus, inchangées, mais seulement quand |signal| ≥ 1,5 fois la moyenne de |signal| sur les 60
jours de signal précédents (calculée sans le jour même). Frais d'aujourd'hui (machine 10) ; Micro Nikkei : 7 $ par
aller-retour (2 ticks de 2,50 $ et 2 $ de commission supposés), au dernier prix.

**Tri** : exploration 2012 - 2022 (les versions sans condition y ont déjà été vues : c'est la limite de cette machine),
Benjamini-Hochberg à 10 % sur les 8, puis **le coffre 2023 → 2 octobre 2026, jamais ouvert pour ces marchés à ces heures,
décide** : seuil de Bonferroni, 3 années positives sur 4. Code : `asie/machine11.py`.

## Résultat de la machine 11 (20 novembre 2026) : `exploration11.txt`, `coffre11.txt`

**Deux survivantes à l'exploration, aucune au coffre.**

| Règle | Exploration 2012 - 2022 : brut, net par trade (t net) | Coffre 2023 - 2026 : net par trade (t) | Années 2023 / 2024 / 2025 / 2026 (pb) | Verdict |
|---|---|---|---|---|
| Nikkei, ouverture de Tokyo contre un grand mouvement du S&P 500 | +5,42 pb, +3,38 pb (t 2,28) | +6,17 pb (t 1,45) | −20 / +541 / −54 / +532 | échoue (t 1,96 exigé, 3 années sur 4) |
| Argent, fin de séance dans le sens d'une grande journée | +6,36 pb, +4,39 pb (t 3,01) | +0,37 pb (t 0,06) | −232 / −119 / +476 / −55 | échoue : l'effet a disparu |

Proches du seuil à l'exploration, sans coffre ouvert : MNQ à l'ouverture de Tokyo les grands jours (t 1,99, +1,24 pb net
par trade) et l'or à son règlement les grands jours (t 1,92).

**À retenir** : le Nikkei à l'ouverture de Tokyo reste positif sur des années jamais vues (+6,2 pb nets par trade, environ
+690 $ par an pour un MNK), mais pas assez régulier pour être prouvé. C'est un candidat à suivre en papier, si Bulenox
ouvre le MNK, pas une stratégie.

# Machine 12 : l'élan à l'heure de règlement de 7 marchés jamais testés à ces heures (règles fixées le 20 novembre 2026, avant tout calcul)

**Pourquoi.** Les machines 10 et 11 ont vu l'élan de fin de séance à l'heure de règlement sur l'argent, le pétrole, l'or et
l'euro (avant frais), plus fort les grands jours. Sept autres marchés de la CME n'ont jamais été testés à leur heure de
règlement : cuivre (HG, 13 h 00), platine (PL, 13 h 05), essence (RB, 14 h 30), gaz naturel (NG, 14 h 30), obligations à
30, 10 et 5 ans (ZB, ZN, ZF, 15 h 00), heures de New York.

**Données** : ETF de ces marchés (CPER, PPLT, UGA, UNG, TLT, IEF, IEI ; Alpaca, 5 minutes, 9 h 30 - 16 h, 2016 - 2026,
branche `claude/affectionate-turing-tnz0mn`). Prix à une heure = clôture de la dernière barre finie à cette heure (dernier
prix connu de la séance, les ETF de matières premières étant peu échangés).

**Règle** : R = variation du règlement de la veille à 30 minutes avant le règlement ; position dans le sens de R pendant
les 30 dernières minutes. Deux versions : tous les jours, et seulement les grands jours (|R| ≥ 1,5 fois sa moyenne des
60 jours précédents, comme la machine 11). 7 × 2 = **14 règles**.

**Frais d'aujourd'hui** (2 ticks plus commissions, sur la valeur du future le 21 octobre 2026) : HG 30 $, PL 15 $, RB
13,40 $, NG 25 $, ZB 67,50 $, ZN 36,25 $, ZF 20,60 $.

**Tri** : exploration 2016 - 2022 (sous-périodes 2016 - 2018, 2019 - 2020, 2021 - 2022 ; t ≥ 2 après frais, placebo de
1 000 tirages du sens battu à 95 %, 2 sous-périodes sur 3, Benjamini-Hochberg à 10 % sur les 14), puis coffre 2023 →
2 octobre 2026 ouvert une seule fois pour les survivantes (Bonferroni, 3 années positives sur 4). Code : `asie/machine12.py`.

## Résultat de la machine 12 (20 novembre 2026) : `machine12.json`

**Aucune survivante (0 sur 14) ; le coffre n'est pas ouvert.** Avant frais, l'élan existe sur les obligations (ZB t 2,62 ;
ZN t 2,44, et t 2,94 les grands jours ; ZF t 2,07) et sur le gaz naturel (+5,9 pb, t 3,32), comme dans Baltussen et al. ;
mais il fait 0,2 à 2 pb par trade quand un aller-retour coûte 2 à 9 pb. Rien sur le cuivre, le platine et l'essence.

## Bilan des machines 9 à 12 (20 novembre 2026)

40 règles nouvelles, toutes fixées avant leur calcul. **Les flux de couverture et de rééquilibrage autour des ouvertures et
des règlements existent sur presque tous les marchés, mais ils sont plus petits que les frais d'un aller-retour**, sauf
peut-être un : le Nikkei contre un grand mouvement du S&P 500, à l'ouverture de Tokyo (+3,4 pb nets par trade sur
2012 - 2022, +6,2 pb sur 2023 - 2026 jamais vu, mais t 1,45 et 2 années positives sur 4 : non prouvé). À suivre en papier
si Bulenox ouvre le Micro Nikkei (MNK).
