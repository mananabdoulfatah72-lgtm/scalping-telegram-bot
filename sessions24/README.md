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
