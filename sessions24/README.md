# Machine 5 : les anomalies des sessions Asie, Londres et New York (règles fixées le 8 octobre 2026, avant les données)

## Demande de l'utilisateur (8 octobre 2026)

Si le RSI(2) n'est pas bien adapté aux challenges 50K « intraday », le supprimer et le remplacer par une source
d'avantage fiable. Analyser les phénomènes qui se répètent chaque jour, de l'ouverture à la fermeture de chaque
session (Asie, Londres, New York). Trouver une source meilleure que le RSI(2), qui rapporte plus et qui ne soit pas
bloquée par la limite de perte suivie pendant la journée ni par les règles de régularité.

## Point de départ honnête

- Plus de 90 stratégies intraday sur la séance américaine (9 h 30 - 16 h) n'ont rien donné (tournois 1 à 7,
  machines 3 et 4, `evolution*/`, `ordres/`, `orderflow/`). Elles ne sont pas refaites ici.
- La nuit du Nasdaq et du S&P a déjà été regardée heure par heure (`nuit/`, barres d'une heure 2010-2026) : un
  essai rejeté (N1), et un tableau descriptif des heures de la nuit. **Les familles qui touchent ES et NQ la nuit
  sont donc un peu « usées »** : leurs résultats sur ES et NQ comptent moins que sur les autres marchés.
- La barre à battre : le RSI(2) entre deux clôtures (`intraday50k/`) : +14 802 $ pour 1 MNQ sur 2012 - 2026,
  t 2,29, +9,4 $ par séance avec la zone ; dans les challenges, Topstep +152 $ net en 12 mois.

## Données (téléchargées après ce texte)

Dukascopy, barres de 5 minutes, 24 h sur 24, 2012 - 2026 (prix acheteur), via GitHub Actions
(`donnees-sessions.yml`) :

| Code | Marché | Contrat CME qu'un compte 50K peut trader | Frais d'un aller-retour (fixés maintenant) |
|---|---|---|---|
| usatechidxusd | Nasdaq 100 | MNQ | 1,5 point |
| usa500idxusd | S&P 500 | MES | 0,9 point |
| usa30idxusd | Dow Jones | MYM / YM | 3 points |
| eurusd | Euro | 6E | 1,5 point de base (pb) du prix |
| gbpusd | Livre | 6B | 1,5 pb |
| usdjpy | Yen | 6J | 1,5 pb |
| audusd | Dollar australien | 6A | 1,5 pb |
| xauusd | Or | MGC / GC | 2 pb |
| lightcmdusd | Pétrole WTI | MCL / CL | 4 pb |

Heures des sessions, chacune dans son fuseau (les changements d'heure sont ainsi gérés) : Tokyo 9 h - 15 h
(Asia/Tokyo), Londres 8 h - 16 h 30 (Europe/London), New York 9 h 30 - 16 h (America/New_York). Entrées et sorties à
l'ouverture des barres de 5 minutes, jamais avec une donnée future.

## Les familles (paramètres fixés ici, aucun réglage après coup)

| # | Famille | Règle | Source |
|---|---|---|---|
| F1 | **Fixings de change** | Le dollar monte avant les grands fixings et baisse après. Pour EUR, GBP et AUD contre le dollar : vente de la devise 60 min avant le fixing jusqu'au fixing (avant), achat du fixing à 60 min après (après), ou les deux. Pour le yen, l'inverse (achat de USD/JPY avant). Fixings : Tokyo 9 h 55 (heure de Tokyo), BCE 14 h 15 (heure de Francfort), WM/Reuters 16 h (heure de Londres). 4 devises × 3 fixings × 3 variantes = 36 | Krohn, Mueller, Whelan (2024), « Foreign Exchange Fixings and Returns Around the Clock », Journal of Finance |
| F2 | **Ouverture européenne des indices** | Achat des indices américains autour de l'ouverture de Francfort (9 h, heure de Francfort) : de 8 h à 9 h, de 9 h à 10 h, de 8 h à 10 h ; chacune sans condition, ou seulement si la séance de New York de la veille a baissé. 3 indices × 3 fenêtres × 2 = 18 | Boyarchenko, Larsen, Whelan (2023), « The Overnight Drift », Review of Financial Studies |
| F3 | **Cassure du début de chaque session** | Fourchette des 30 premières minutes (ou 60) de la session ; achat ou vente à la première clôture de 5 min au-delà ; stop de l'autre côté ; sortie à la fin de la session ; un trade par session. Sessions : Tokyo et Londres pour les 9 marchés, New York seulement pour change, or et pétrole (les indices y ont déjà été testés). 9 × 2 + 6 = 24 cas × 2 durées = 48 | Crabel (1990) ; Zarattini, Barbon, Aziz (2024) |
| F4 | **Cassure de la fourchette d'Asie à Londres** | Fourchette de 0 h à 7 h (heure de Londres) ; cassure entre 7 h et 12 h ; stop de l'autre côté ; sortie à 12 h ou à 16 h 30. 9 marchés × 2 sorties = 18 | pratique des salles de change (« London breakout »), testée ici pour la première fois |
| F5 | **D'une session à la suivante** | Pendant la session S, dans le sens du mouvement de la session d'avant (continuation), ou dans le sens inverse (retournement). Paires : Tokyo → Londres, Londres → New York, New York → Tokyo suivant. 9 marchés × 3 paires × 2 = 54 | Gao, Han, Li, Zhou (2018) pour la continuation ; Berkman et al. (2012) pour le retournement |
| F6 | **L'or selon l'heure** | Achat de l'or hors des heures de New York (18 h - 8 h 20, heure de New York) ; vente de l'or pendant les heures du COMEX (8 h 20 - 13 h 30). 2 | effet « nuit » de l'or, à confirmer (aucune source précise : traité comme exploratoire) |

**176 stratégies** au total.

## Le tri

1. **Exploration 2012 - 2022**, gains nets par jour (frais du tableau) :
   - t ≥ 2 ;
   - battre 95 % des placebos :
     - F1, F2 et F6 : la même fenêtre placée à toutes les autres heures de la journée (pas de 5 minutes, à plus de 2 h
       de l'événement) ;
     - F3, F4 et F5 : 1 000 tirages du sens de chaque trade au hasard, mêmes heures ;
   - positive dans au moins 2 des 3 sous-périodes (2012-2015, 2016-2019, 2020-2022) ;
   - Benjamini-Hochberg à 10 % sur les p des placebos, toutes stratégies confondues.
2. **Coffre 2023 - septembre 2026, ouvert une seule fois** pour les survivantes : même sens, t ≥ seuil de Bonferroni
   (5 % unilatéral, m survivantes), positive au moins 3 années sur 4.
3. **Challenges** pour celles qui passent le coffre : avec la zone de bruit, règles Topstep 50K et DayTraders S2F
   (moteur de `intraday50k/`), contre le bot zone + RSI(2) entre deux clôtures. Une source « remplace le RSI(2) »
   seulement si elle fait mieux que lui en gain net sur 12 mois dans ces deux comptes, sur les achats de 2023 -
   2025.
4. Publié pour toutes les stratégies, survivantes ou non : t, gain net, placebo, sous-périodes. Toutes sont inscrites
   dans `fonds/essais.csv`. Les heures où le PC doit être allumé sont indiquées (chez Topstep, pas de VPS).

## Ce qui serait une fausse découverte

Avec 176 essais, environ 9 dépasseront t = 2 par hasard. C'est pour cela que le placebo, le seuil de Benjamini-
Hochberg et le coffre sont obligatoires. Si rien ne passe, la conclusion sera « rien de fiable », et le RSI(2) entre
deux clôtures reste la meilleure source connue.

## Changement de source de données (8 octobre 2026, avant tout calcul)

- **Dukascopy refuse maintenant les téléchargements depuis GitHub** (réponse 202, vérifiée par un essai court).
  Les données viennent donc de **HistData** (prix minute gratuits, même nature : cotations CFD et change), en heure de
  l'Est sans changement d'heure (UTC − 5 h toute l'année), converties en UTC puis en barres de 5 minutes
  (`telecharger_histdata.py`). Correspondance : Nasdaq = NSXUSD, S&P 500 = SPXUSD, pétrole = WTIUSD, les autres sous
  leur nom.
- **HistData n'a pas le Dow Jones** : ses 18 stratégies sont retirées (F2 : 6, F3 : 4, F4 : 2, F5 : 6). Il en reste
  **158**. Les seuils (placebos, Benjamini-Hochberg, Bonferroni au coffre) se calculent sur ce nombre.
- Règles fixées maintenant, avant d'ouvrir les fichiers :
  - si un marché ne couvre pas les heures dont une stratégie a besoin (par exemple les indices la nuit), la stratégie
    est déclarée **« non testable »** si elle a moins de 200 jours de trades sur 2012-2022, et elle n'est pas jugée ;
  - pour F2 seulement (ouverture de Francfort sur les indices), si HistData ne couvre pas la nuit, on utilise les
    barres d'une heure de Databento déjà dans le projet (`nuit/donnees/`, NQ et ES, 24 h sur 24) : les fenêtres de F2
    tombent sur des heures pleines.
- **Correction de l'heure (avant tout calcul)** : malgré sa documentation (« EST sans changement d'heure »), HistData
  suit l'heure de New York **avec** l'heure d'été. Vérifié de deux façons :
  - le pic de volatilité des chiffres de l'emploi américains (8 h 30 à New York) tombait à 13 h 30 UTC en été au lieu
    de 12 h 30 ;
  - le Nasdaq de HistData contre le NQ de Databento : corrélation 0,75 en été avec l'ancienne conversion.

  Après correction (`recaler.py`, puis `telecharger_histdata.py` corrigé), le pic tombe à 12 h 30 en été et 13 h 30
  en hiver sur tous les marchés, et la corrélation avec le NQ est de 1,000 en été et 0,999 en hiver.
- Le pétrole (WTIUSD) s'arrête au 1er décembre 2023 chez HistData : ses stratégies ne pourront pas être jugées au
  coffre sur 4 années ; une survivante du pétrole serait déclarée « coffre incomplet ».

## Résultats de l'exploration 2012 - 2022 (9 octobre 2026) : `exploration5.txt`

**Aucune survivante sur 158 stratégies (toutes testables). Le coffre 2023 - 2026 n'est pas ouvert : il reste vierge.**

- Aucune stratégie n'atteint t = 2 après frais. Les meilleures :

| Stratégie | Avant frais, par jour | Frais | Après frais |
|---|---|---|---|
| F4 fourchette d'Asie cassée à Londres, yen, sortie 16 h 30 | +2,24 pb (t 3,64) | 1,50 pb | t 1,21 |
| F4 fourchette d'Asie cassée à Londres, or, sortie 16 h 30 | +3,20 pb (t 2,82) | 2,00 pb | t 1,06 |
| F3 cassure des 30 premières minutes de Londres, or | +2,84 pb (t 3,14) | 2,00 pb | t 0,92 |
| F3 cassure des 60 premières minutes de Londres, livre | +1,77 pb (t 2,88) | 1,50 pb | t 0,43 |
| F5 Tokyo → Londres, continuation, yen | +1,86 pb (t 2,65) | 1,50 pb | t 0,52 |

- **Des phénomènes existent avant frais**, surtout autour de l'ouverture de Londres (cassure de la fourchette
  d'Asie, cassure du début de séance, sur le yen, l'or et la livre). Les placebos le confirment : le sens choisi par
  ces règles bat le hasard (p ≤ 0,01). Mais **ils sont deux à trois fois plus petits que les frais** d'un contrat de
  futures (commission + 1 tick) : il ne reste presque rien après frais.
- **Fixings de change** (F1, Krohn, Mueller, Whelan 2024) : le dollar monte bien avant le fixing de Tokyo (yen :
  +0,72 pb avant frais, t 2,92), mais c'est la moitié des frais. Avant le fixing de Londres, l'effet est quasi nul
  sur l'euro et la livre. Toutes les variantes perdent après frais (t de −0,7 à −4,9).
- **Ouverture de Francfort** (F2) : le Nasdaq monte de 8 h à 10 h (+1,17 pb par jour avant frais, t 2,18), moins que
  les frais d'un MNQ sur ces années (2,88 pb).
- **D'une session à l'autre** (F5) et **l'or selon l'heure** (F6) : rien.

**Conclusion selon la règle fixée** : aucune source ne remplace le RSI(2). Le RSI(2) entre deux clôtures
(`intraday50k/`) reste la meilleure source connue pour un compte intraday.

# Vague 2 (règles fixées le 9 octobre 2026, avant tout calcul)

Demande de l'utilisateur : une deuxième vague, avec deux fois plus de phénomènes et de variantes que la première.
Mêmes données (HistData, 8 marchés, barres de 5 minutes en UTC), mêmes frais, même tri. **13 familles, 368
stratégies.** Toutes les heures sont dans le fuseau du phénomène ; « jour ouvré » = lundi à vendredi (jours fériés non
modélisés, ce qui ajoute un peu de bruit sans regard vers le futur).

Leçon de la vague 1 retenue avant de choisir : les petits effets quotidiens (1 à 3 pb) sont mangés par les frais
(1,5 à 2 pb). Cette vague cherche donc surtout des **événements qui font bouger les prix plus fort** (chiffres
américains, Fed, pétrole, écart du week-end, fins de mois), où les frais pèsent moins.

| # | Famille | Règle | Source | Nombre |
|---|---|---|---|---|
| G1 | Fin de mois au fixing de Londres | Dernier jour ouvré du mois (ou les 2 derniers). Avant : 15 h → 16 h (Londres) ; après : 16 h → 17 h. Sans condition : le dollar monte avant, baisse après. Selon le S&P : si le S&P a monté depuis le début du mois (à 15 h, Londres), le dollar baisse avant le fixing (les étrangers vendent du dollar pour couvrir leurs actions américaines) et remonte après ; l'inverse s'il a baissé. Euro, livre, yen, dollar australien | Melvin, Prins (2015) ; Krohn, Mueller, Whelan (2024) | 4 × 2 fenêtres × 2 conditions × 2 jeux de jours = 32 |
| G2 | Début de mois | Premier jour ouvré. 8 h → 12 h ou 15 h → 16 h (Londres). Sans condition : le dollar baisse. Selon le S&P du mois précédent : sens inverse de G1 (retour des flux) | idem | 4 × 2 × 2 = 16 |
| G3 | Fin de trimestre | G1 sur les seuls derniers jours de mars, juin, septembre, décembre (dernier jour seulement) | idem | 4 × 2 × 2 = 16 |
| G4 | Jours « gotobi » du yen | Les 5, 10, 15, 20, 25 et dernier jour du mois (veille ouvrée si week-end). Avant le fixing de Tokyo (7 h, 8 h ou 9 h → 9 h 55, heure de Tokyo) : le dollar monte ; après (9 h 55 → 11 h ou 12 h) : il baisse. Sur les 4 devises | Bessho, Ito, Yamada (Gotobi anomaly) ; Ito, Yamada (2017) | 4 × 5 = 20 |
| G5 | Fixings de l'or (LBMA) | 10 h 30 et 15 h (Londres). Avant (30 ou 60 min) : vente de l'or ; après (30 ou 60 min) : achat ; ou les deux | Caminschi, Heaney (2014) ; Abrantes-Metz, Metz (2014) | 2 × 6 = 12 |
| G6 | Stocks de pétrole (EIA) | Mercredi 10 h 30 (New York) : sens de 10 h 30 → 10 h 35 ; trade de 10 h 35 à 11 h, 12 h ou 14 h 30 ; continuation ou retournement ; toujours, ou seulement si le mouvement dépasse sa médiane des 26 mercredis d'avant. Pétrole | réaction aux annonces de stocks (Bjursell, Gentle, Wang) | 3 × 2 × 2 = 12 |
| G7 | Choc des chiffres de 8 h 30 | Chaque jour ouvré : mouvement de 8 h 30 → 8 h 35 (New York). Si sa taille dépasse le 80e (ou 90e) centile des 60 jours ouvrés d'avant (même heure) : trade de 8 h 35 à 9 h 30 ou 11 h, continuation ou retournement. 8 marchés | dérive ou retour après annonce (Andersen et al. 2003) | 8 × 2 × 2 × 2 = 64 |
| G8 | Choc de 10 h | Même règle à 10 h → 10 h 05 (ISM, confiance…), 90e centile, sortie 11 h ou 12 h | idem | 8 × 2 × 2 = 32 |
| G9 | Annonces de la Fed | Jours d'annonce programmée du FOMC (`fonds/fomc.py`), 14 h (New York), **2013 - 2026 seulement** (avant 2013, l'heure variait). Réaction 14 h → 14 h 05 ou → 14 h 15 ; trade jusqu'à 15 h ou 15 h 55, continuation ou retournement. 8 marchés | Lucca, Moench (2015) ; littérature sur la réaction aux annonces | 8 × 2 × 2 × 2 = 64 |
| G10 | Échéance mensuelle des options | 3e vendredi. Mouvement de 9 h 30 → 11 h (ou → 12 h) ; trade jusqu'à 15 h 55, retournement ou continuation. Nasdaq et S&P | Ni, Pearson, Poteshman (2005) | 2 × 2 × 2 = 8 |
| G11 | Écart du week-end | À la première barre après la pause du week-end : écart avec la dernière cotation du vendredi avant 17 h (New York). Comblement ou continuation ; sortie lundi 3 h ou 9 h 30 (New York) ; tout écart, ou seulement s'il dépasse sa médiane des 26 semaines d'avant. 7 marchés (sans le pétrole) | « weekend gap » (pratique), test exploratoire | 7 × 2 × 2 × 2 = 56 |
| G12 | Vendredi après-midi | Mouvement de la semaine (vendredi 16 h de la semaine d'avant → vendredi 12 h ou 14 h). Trade jusqu'à 15 h 55 : retournement (on ferme ses positions avant le week-end) ou continuation. 7 marchés | test exploratoire | 7 × 2 × 2 = 28 |
| G13 | Dernière heure de fin de mois (indices) | Dernier jour ouvré (ou les 2 derniers) : 15 h → 15 h 55 ou 15 h 30 → 15 h 55 (New York), à l'inverse du mouvement de l'indice depuis le début du mois (rééquilibrage des fonds) | Harvey, Mazzoleni, Melone (2025) | 2 × 2 × 2 = 8 |

**Placebos** :
- familles de calendrier (G1, G2, G3, G4, G10, G13) : la même règle sur des jours ouvrés tirés au hasard hors des
  jours de l'événement, en même nombre, 500 tirages ;
- G5 (tous les jours) : la même fenêtre à toutes les autres heures, comme F1 ;
- familles de réaction (G6, G7, G8, G9, G11, G12) : 1 000 tirages du sens de chaque trade au hasard.

**Tri** : comme la vague 1 :
- t ≥ 2 après frais, placebo battu à 95 %, positive dans au moins 2 des 3 sous-périodes ;
- Benjamini-Hochberg à 10 % sur les 368 ;
- exploration 2012-2022 (G9 : 2013-2022, sous-périodes 2013-2015, 2016-2019, 2020-2022) ;
- coffre 2023 - 2026 une seule fois, Bonferroni, 3 années positives sur 4 (pétrole : coffre incomplet) ;
- puis les challenges contre le RSI(2) entre deux clôtures ;
- moins de 200 jours de trades = « non testable », sauf les familles rares par nature (G1 à G6, G9, G10, G13 : au
  moins 60 trades).
