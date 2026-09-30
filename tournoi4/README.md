# Tournoi intraday n°4 : les pistes pas encore vues

Après 75 stratégies intraday sans survivant (tournois n°1 à n°3), une recherche de la littérature a fait
ressortir des pistes que nous n'avions pas testées. Voici celles qui se testent avec nos données.

## Règles (fixées le 30 septembre 2026, avant tout calcul)

Mêmes conditions que les tournois précédents :
- NQ et ES, séance de 9 h 30 à 16 h, tout fermé à 16 h ;
- pas de trade les jours incomplets ni le jour d'un changement d'échéance ;
- frais de 1,5 point de NQ et de 0,9 point d'ES par aller-retour ;
- signal à l'heure pile, exécution à l'ouverture de la minute suivante.

« 252 j » veut dire : comparé aux 252 séances précédentes.

| # | Stratégie | Règle | Source |
|---|---|---|---|
| 1 | Même demi-heure, jours précédents (début et fin) | pour la 1re demi-heure (9 h 30-10 h) et la dernière (15 h 30-16 h) : dans le sens de la moyenne de cette même demi-heure sur les 20 séances précédentes | Heston, Korajczyk, Sadka (2010) |
| 2 | Même demi-heure, jours précédents (toute la journée) | même règle pour chacune des 13 demi-heures | idem |
| 3 | Rééquilibrage de fin de mois | les 4 dernières séances du mois : à l'inverse du mouvement du mois en cours (clôture de la dernière séance du mois précédent → clôture de la veille), si ce mouvement est dans le tiers le plus grand en valeur absolue (252 j) ; de 9 h 30 à 16 h | Harvey, Mazzoleni, Melone (2025) |
| 4 | Fin de séance après un grand mouvement | à 15 h 30, dans le sens de 9 h 30-15 h 30, si ce mouvement est dans les 20 % les plus grands en valeur absolue (252 j) ; jusqu'à 16 h | Barbon et Beckmeyer ; Baltussen et al. (2021) |
| 5 | Cassure du range de la nuit | première sortie du plus haut ou du plus bas de la nuit (18 h - 9 h, même contrat) ; stop au milieu du range de la nuit ; sortie à 16 h | pratique courante des traders de futures |
| 6 | Rejet du range de la nuit | premier contact du plus haut de la nuit : vente au niveau ; du plus bas : achat ; objectif le milieu du range, stop à un quart du range au-delà ; sortie à 16 h | idem |
| 7 | Rebond après une forte baisse | si la séance de la veille (ouverture → clôture) est dans les 10 % les plus bas (252 j) : achat de 9 h 30 à 16 h | retour à la moyenne à court terme |
| 8 | Modèle appris à 10 h | régression logistique réentraînée chaque 1er janvier sur les années passées seulement (1re année jouée : 2013). Elle prévoit le sens de 10 h → 16 h avec 8 variables connues à 10 h : écart d'ouverture, mouvement 9 h 30-10 h, volume de la 1re demi-heure contre sa moyenne sur 20 j, séance de la veille, amplitude de la veille contre sa moyenne sur 20 j, VIX / VIX 3 mois, GEX, DIX de la veille. Achat si la probabilité est > 0,55, vente si < 0,45 | « quant » : apprentissage sur le passé |

**Les données de la nuit** : barres d'une heure de Databento (`nuit/donnees`). Le range de la nuit va
de la barre de 18 h à celle de 8 h (qui finit à 9 h). La demi-heure 9 h - 9 h 30 n'y est pas, car elle est
dans la barre de 9 h, qui déborde sur la séance.

**Essais** : 8 stratégies × 2 marchés = **16**.

### Le tri (comme les tournois précédents)

1. t ≥ 2 sur 2011-2022, sur les rendements quotidiens nets en % du prix, jours sans trade compris.
2. **Bruit** : battre le plus haut t de 20 versions où les minutes de chaque séance sont mélangées. La
   nuit, la veille, GEX, DIX et VIX restent les mêmes.
3. **Jours au hasard**, pour les stratégies 3 et 7 : jouer toute la séance ne dépend pas de l'ordre des
   minutes, donc le bruit ne peut rien trancher. Il faut faire mieux que 95 % de 200 tirages de jours au
   hasard, en même nombre, avec le même sens.
4. **Coffre 2023-2026** pour les survivants :
   - t ≥ seuil de Bonferroni ;
   - au moins 3 années positives sur 4.

### Une hypothèse née d'un résultat précédent, jugée seulement sur le coffre

La paire NQ / ES en retour à la moyenne (tournoi n°2) perd nettement : t −6,15, pire que le bruit.
L'écart entre les deux marchés continue donc dans la journée. D'où l'idée inverse :

**Paire en continuation** : mêmes points de contrôle et même seuil que la paire du tournoi n°2, mais
achat du plus fort et vente du plus faible. Sortie si l'écart repasse 0, ou à 16 h.

Cette idée vient de 2011-2022 : ces années ne peuvent donc pas la juger. Elle est jugée **uniquement
sur le coffre 2023-2026**, dans le même lot que les éventuels survivants (Bonferroni sur l'ensemble), avec
au moins 3 années positives sur 4.

Les 17 essais sont inscrits dans `fonds/essais.csv`. Rien n'est ajouté ni changé après avoir vu les
résultats.

## Résultats (30 septembre 2026) : aucun survivant, 0 sur 17

Détail dans `exploration4.txt` et `coffre4.txt`.

**Correction pendant le calcul** : la stratégie 7 n'avait aucun trade. Son seuil sur 252 jours valait
« rien » dès qu'une séance sans veille (un changement d'échéance) tombait dans la fenêtre. Le seuil
porte maintenant sur les 252 dernières valeurs existantes, puis tout a été relancé.

| Stratégie | NQ : t 2011-2022 | ES : t 2011-2022 | Remarque |
|---|---|---|---|
| 7. Rebond après une forte baisse | +1,80 (2017-22 : +2,09) | +1,48 | le plus proche, mais sous 2 ; bat les jours au hasard |
| 8. Modèle appris à 10 h | +1,09 | −0,43 | voir l'encadré sur le bruit |
| 4. Fin de séance après un grand mouvement | +0,78 | +0,52 | |
| 3. Rééquilibrage de fin de mois | +0,63 | +0,15 | ne bat pas les jours au hasard |
| 5. Cassure du range de la nuit | −0,09 | −1,59 | |
| 6. Rejet du range de la nuit | −4,00 | −6,75 | |
| 1. Même demi-heure (début et fin) | −7,69 | −10,09 | |
| 2. Même demi-heure (toute la journée) | −24,21 | −38,08 | 13 allers-retours par jour |

**Paire en continuation (jugée seulement sur le coffre 2023-2026)** : t −1,52, négative chaque année
(−1,4 %, −0,5 %, −0,2 %, −0,8 %). Rejetée. En retour à la moyenne comme en continuation, la paire perd :
les frais dépassent le mouvement.

**Ce qu'on retient** :
- La périodicité des demi-heures (Heston, Korajczyk, Sadka) existe peut-être sur les actions une par
  une, mais pas sur le Nasdaq ou le S&P entiers après frais.
- Le rebond après une forte baisse est la seule piste qui s'approche : t 1,80 sur NQ et 1,48 sur ES,
  et il bat les jours tirés au hasard. Mais il n'atteint pas 2, et il ne gagne que depuis 2017.
- **Le bruit est trop sévère pour les stratégies qui lisent le volume.** Sur les minutes mélangées, le
  modèle appris fait t +9,7. Mélanger les minutes avec leur volume peut placer au début les grosses
  minutes, qui portent le mouvement du jour. Comme le résultat du jour est conservé, un gros volume
  en début de séance « annonce » alors que le mouvement est déjà fait. Sur vraies données, ce lien
  n'existe pas : le modèle y utilise surtout l'écart d'ouverture et le premier mouvement.
  - Ce défaut du contrôle ne change aucun verdict : le modèle fait t 1,09 sur vraies données, sous le
    seuil de 2, et le range de 5 minutes avec volume du tournoi n°2 fait t 1,54.
  - Pour une future stratégie au volume, il faudra mélanger les minutes sans leur volume.
