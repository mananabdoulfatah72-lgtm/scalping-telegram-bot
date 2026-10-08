# Vague 3 : de nouvelles sources de plusieurs jours pour le système Static (règles fixées le 8 octobre 2026, avant le calcul)

## Pourquoi

Demande de l'utilisateur (8 octobre 2026) : faire A (adapter le bot au Static, `static50k/`) puis B, une vague 3
qui cherche d'autres sources que le RSI(2), pour le remplacer ou s'ajouter à la zone filtrée.

`static50k/` a gardé le RSI(2) : le système retenu est le bot tel quel, avec un plafond du jour de 500 $ sur le
compte Pro. La vague 3 cherche donc une **4e source** qui améliore ce système. Le Static permet la nuit et le
week-end : on cherche des stratégies de plusieurs jours sur le NQ, comme le RSI(2).

## Ce qui a déjà été testé et n'est pas repris

`fonds/essais.csv`, plus de 500 stratégies, dont :
- intraday : tournois 1 à 7, machines 3 à 5, order flow ;
- plusieurs jours : RSI(2), Double 7, IBS, rebond de 5 jours, veille de férié (tournoi 8) ; VIX tendu, RSI du VIX,
  mardi de rebond, nuit après une baisse, plus haut de 252 séances, achat piloté par la volatilité (tournoi 10) ;
  tournant du mois, veille de la Fed, tendance, carry, momentum, valeur (`fonds/`, `tendance/`) ; nuit sans
  condition (`nuit/`) ;
- calendrier intraday : jour de l'échéance des options et dernière heure de fin de mois (vague 2, `sessions24/`).

## Les règles du calcul

### Données et exécution

Exactement celles de `tournoi8/` (fonctions reprises de `tournoi8.py`) :
- minutes Databento du NQ (et de l'ES), séance de 9 h 30 à 16 h, 2011 - septembre 2026 ;
- une décision par séance, 10 minutes avant la fin (15 h 50) :
  - indicateurs sur la clôture de 15 h 49 ;
  - exécution à l'ouverture de la minute de décision ;
  - la position court d'une décision à la suivante, nuit et week-end compris ;
- position fermée à la dernière décision d'un contrat ;
- frais : 1 $ + 1 tick par ordre ;
- dates connues d'avance seulement :
  - calendrier de la Bourse ;
  - 3e vendredi de chaque mois ;
  - annonces programmées du FOMC (`fonds/fomc.py`), publiées un an à l'avance ;
- ZN (bons du Trésor à 10 ans, `fonds/donnees/futures_1d.csv.gz`, contrat le plus échangé) : seulement la clôture
  de la **veille** de chaque décision.

### Les 7 sources (sur le NQ ; les mêmes sur l'ES à titre descriptif)

| # | Source | Règle | Référence |
|---|---|---|---|
| W1 | **Semaine de l'échéance des options** | achat à la décision de la dernière séance avant la semaine du 3e vendredi, vente à la décision du 3e vendredi (la veille s'il est férié) | Stivers, Sun (2013) |
| W2 | **Semaines paires du cycle de la Fed** | en position quand la séance suivante est dans une semaine paire du cycle (semaine 0 = de la veille de l'annonce à 3 séances après ; semaine k = séances 5k − 1 à 5k + 3 après l'annonce ; semaines 0, 2, 4 et 6) | Cieslak, Morse, Vissing-Jorgensen (2019) |
| W3 | **Rééquilibrage de fin de mois, achat** | à la décision de la 5e séance avant la fin du mois : écart de rendement depuis le début du mois entre l'ES (clôture de 15 h 49) et le ZN (clôture de la veille). S'il est dans les 20 % les plus bas des 60 mois d'avant (au moins 36 mois connus), achat jusqu'à la décision de la dernière séance du mois | Harvey, Mazzoleni, Melone (2025) |
| W4 | **Rééquilibrage de fin de mois, vente** | même mesure ; dans les 20 % les plus hauts : vente jusqu'à la dernière séance du mois | idem (l'effet principal de l'article) |
| W5 | **RSI(2) vendeur** | vente si clôture < moyenne des 200 et RSI(2) > 90 ; rachat quand clôture < moyenne des 5 | Connors, Alvarez (2008), côté vendeur |
| W6 | **Écart NQ / ES, retour à la moyenne** | si le rendement du NQ moins celui de l'ES depuis la décision d'avant est dans les 10 % les plus bas des 252 séances d'avant : achat NQ et vente ES (même montant en dollars), 5 séances après le dernier signal. Frais des deux jambes | inversion à court terme entre indices (Lehmann 1990, version paire) |
| W7 | **Novembre - avril** | en position de la dernière décision d'octobre à la dernière décision d'avril | Bouman, Jacobsen (2002) |

Paramètres des sources, sans aucun réglage.

### Le tri (comme `tournoi8/`)

1. **Exploration 2011-2022.** Le programme d'exploration ne lit pas les années suivantes. Une source survit si :
   - t ≥ 2 sur les rendements quotidiens nets (en % du prix, jours sans position compris) ;
   - **et** son t dépasse 95 % des t de 1 000 placements au hasard des mêmes trades (mêmes durées, même sens, sans
     chevauchement ni passage d'échéance).
2. **Coffre 2023 - septembre 2026, ouvert une seule fois** pour les survivants. Un survivant passe s'il a :
   - un t au moins égal au seuil de Bonferroni pour m survivants (1,65 si m = 1, 1,96 si m = 2, 2,13 si m = 3…) ;
   - un résultat positif au moins 3 années sur 4.
3. **Dans le système Static** (`static50k/`, mêmes règles, mêmes départs), pour chaque source qui passe le coffre :
   - **ajoutée** au système retenu (E0 P500 + la source sur 1 MNQ) ;
   - et **à la place** du RSI(2) (zone + la source, P500).

   Une source entre dans le système si elle fait gagner plus d'argent net par achat que E0 P500, sur les départs de
   2012-2021 **et** sur ceux de 2023 - septembre 2025. Le moteur de `static50k/` sera étendu à une 3e position
   quotidienne, avec ses propres contrôles, seulement si une source arrive à cette étape.
4. **Publié pour chaque source** (descriptif) :
   - Sharpe, perte maximale pour 1 micro, temps en position, trades ;
   - corrélation quotidienne avec le RSI(2) et avec la zone.
5. Les 7 essais sont inscrits dans `fonds/essais.csv`. Aucune source, aucun paramètre ni aucun marché ne sera ajouté
   ou changé après avoir vu les résultats.

## Résultat de l'exploration 2011-2022 (8 octobre 2026) : aucun survivant (`exploration3.txt`)

Contrôles (`test_vague3.py`, 5 sur 5) :
- fenêtres d'octobre et d'avril 2022 (Vendredi saint) ;
- semaines du cycle de la Fed autour de l'annonce du 21 septembre 2022 ;
- écart ES - ZN de juin 2019 recalculé à la main et comparé au moteur ;
- journal d'une vente ;
- pas de regard vers le futur.

**Correction après la revue de code** :
- **Le défaut.** L'écart ES - ZN de W3 et W4 divisait des prix de deux échéances différentes quand le mois contenait
  un changement de contrat (mars, juin, septembre, décembre). C'était un saut d'échéance, pas un rendement.
- **La correction.** Les rendements sont maintenant enchaînés jour par jour sur un même contrat.
- **Ce qui change.**
  - W3 passe de t 1,85 / 91,8 % à **t 1,59 / 87,9 %** ;
  - W4 change à peine ;
  - les dollars de W6 sont maintenant comptés sur le montant du début de chaque journée : +1 343 $ au lieu de
    +2 363 $, t inchangé ;
  - **aucune décision ne change.**

| Source (NQ) | t | Bat le hasard | Trades | $ pour 1 MNQ | Verdict |
|---|---|---|---|---|---|
| W1 semaine de l'échéance des options | −0,03 | 8,7 % | 159 | −3 274 | éliminée |
| W2 semaines paires du cycle de la Fed | **2,04** | 68,6 % | 323 | +9 096 | éliminée : le hasard fait aussi bien (c'est la hausse du marché) |
| W3 rééquilibrage de fin de mois, achat | 1,59 | 87,9 % | 20 | +4 170 | éliminée |
| W4 rééquilibrage de fin de mois, vente | −0,44 | 57,2 % | 24 | −440 | éliminée |
| W5 RSI(2) vendeur | 0,70 | **93,3 %** | 23 | +2 895 | éliminée |
| W6 écart NQ / ES | 0,72 | 76,5 % | 164 | +1 343 | éliminée |
| W7 novembre - avril | 1,62 | 24,7 % | 37 | +5 344 | éliminée (le hasard fait mieux) |

- **Aucune source ne survit. Le coffre 2023 - 2026 n'est pas ouvert**, et rien n'entre dans le système Static. Les
  corrélations avec la zone, prévues pour les survivants, ne sont donc pas calculées.
- Les sources qui « gagnent » (W2, W7) sont surtout en position quand le Nasdaq monte : des dates tirées au hasard,
  avec les mêmes durées, font aussi bien.
- W3 (acheter les derniers jours du mois quand les actions ont fait moins bien que les obligations) va dans le sens
  de l'article, mais avec 20 trades en 9 ans, rien ne permet de conclure.
