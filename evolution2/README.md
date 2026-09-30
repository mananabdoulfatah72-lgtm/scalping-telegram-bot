# Nouvelles pistes : GEX, murs d'options, VIX, DIX, profil de volume

Après 57 stratégies intraday classiques sans survivant (tournois n°1 et n°2) et 180 conditions
d'order flow sans effet (`ordres/CONDITIONS.md`), l'utilisateur demande d'autres pistes : GEX et 0DTE,
call wall et put wall, heatmap, profil de volume, Level 1, quant… puis de les faire passer dans la machine
évolutive.

Deux étapes, avec les mêmes contrôles que d'habitude :
- **Tournoi n°3** : chaque piste, en règle fixe ;
- **Machine évolutive n°2** : les mêmes briques, données à la sélection naturelle.

## Règles (fixées le 30 septembre 2026, avant tout calcul)

### Ce qui peut être testé, et avec quelles données

| Piste | Données | Testable ? |
|---|---|---|
| **GEX** (exposition gamma des teneurs de marché) | SqueezeMetrics, S&P 500, quotidien depuis mai 2011, gratuit | oui |
| **DIX** (achats dans les dark pools) | SqueezeMetrics, même fichier | oui |
| **Structure du VIX** (VIX / VIX 3 mois) | CBOE, gratuit | oui |
| **Profil de volume** (POC, zone de valeur) | nos barres minute NQ / ES 2011-2026 | oui |
| **Call wall, put wall, zéro gamma** | intérêt ouvert par strike des options sur ES et NQ (Databento, CME) | seulement si le coût est faible (plafond : 25 $) ; sinon non testé, et le README le dira |
| **GEX 0DTE** | options qui expirent le jour même : quotidiennes sur le S&P depuis mai 2022 seulement | non : rien avant 2022, donc pas de période d'exploration |
| **Heatmap (Bookmap, « Protos »)**, carnet profond | carnet complet (MBP-10 / MBO), environ 100 $ par jour de données | non : hors budget |
| **Level 1** (meilleur acheteur / vendeur) | déjà testé dans `ordres/` | déjà fait : vraie information, mais sous les frais |
| **« Protos et son IA », EquityLab** | aucune donnée historique connue ; les pages publiques d'EquityLab sont relevées par le workflow | selon ce qu'on y trouve ; un niveau du jour sans historique ne se teste pas |

Les chiffres du jour d (GEX, DIX, VIX, profil de volume de la séance) ne servent qu'à partir de
l'ouverture du jour d + 1.

### Tournoi n°3 : règles fixes

Mêmes conditions que les tournois n°1 et n°2 :
- NQ et ES, de 9 h 30 à 16 h, tout fermé à 16 h ;
- pas de trade les jours incomplets ni le jour d'un changement d'échéance ;
- frais de 1,5 point de NQ et de 0,9 point d'ES par aller-retour ;
- signal à l'heure pile, exécution à l'ouverture de la minute suivante.

« Seuil sur 252 jours » veut dire : comparé aux 252 séances précédentes.

| # | Stratégie | Règle |
|---|---|---|
| G1 | Gamma négatif : suivre | si le GEX de la veille est < 0 : à 10 h, dans le sens de 9 h 30-10 h, jusqu'à 16 h |
| G2 | Gamma élevé : retour | si le GEX de la veille est dans le tiers le plus haut (252 j) : à 10 h 30, à l'inverse de 9 h 30-10 h 30, jusqu'à 16 h |
| G3 | Zone de bruit en gamma bas | la zone de bruit (référence), seulement si le GEX de la veille est sous sa médiane (252 j) |
| D1 | DIX élevé | si le DIX de la veille est dans les 10 % les plus hauts (252 j) : achat de 9 h 30 à 16 h |
| V1 | VIX en déport (stress) | si VIX / VIX 3 mois ≥ 1 à la clôture de la veille : à 10 h, dans le sens de 9 h 30-10 h, jusqu'à 16 h |
| V2 | VIX très calme | si VIX / VIX 3 mois ≤ 0,85 : à 10 h 30, à l'inverse de 9 h 30-10 h 30, jusqu'à 16 h |
| P1 | Règle des 80 % (Dalton) | ouverture hors de la zone de valeur de la veille ; dès que deux demi-heures de suite (clôtures de 10 h, 10 h 30…) finissent dedans : vers l'autre bord ; objectif = l'autre bord, stop = plus haut (ou plus bas) du jour à ce moment-là ; sortie à 16 h |
| P2 | Acceptation hors de la zone de valeur | ouverture dans la zone de valeur ; première demi-heure qui finit au-dessus du haut (ou sous le bas) : dans ce sens ; stop au POC de la veille ; sortie à 16 h |
| P3 | Rejet des bords | ouverture dans la zone de valeur ; premier contact avec le haut : vente au niveau ; objectif le POC ; stop à un quart de la largeur de la zone au-delà du bord ; symétrique en bas ; sortie à 16 h |
| W1 | Rejet du call wall | premier contact avec le call wall de la veille : vente au niveau, stop à 0,25 % au-dessus, sortie à 16 h |
| W2 | Rebond sur le put wall | premier contact avec le put wall de la veille : achat au niveau, stop à 0,25 % au-dessous, sortie à 16 h |
| W3 | Sous le zéro gamma : suivre | si l'ouverture est sous le niveau de zéro gamma de la veille : à 10 h, dans le sens de 9 h 30-10 h, jusqu'à 16 h |

**Définitions.**
- **Profil de volume de la veille** (séance de 9 h 30 à 16 h) : le volume de chaque minute est réparti à
  parts égales sur les ticks entre son plus bas et son plus haut.
- **POC** : le prix au plus fort volume.
- **Zone de valeur** : 70 % du volume, construite depuis le POC en ajoutant à chaque pas le côté le plus
  chargé (méthode habituelle).
- **Call wall et put wall** : strike au plus fort intérêt ouvert en calls (en puts) sur les options ES
  (ou NQ) qui expirent dans les 45 jours, à la clôture de la veille.
- **Zéro gamma** : prix où le gamma total des teneurs de marché change de signe. On suppose les teneurs
  acheteurs des calls et vendeurs des puts, et on prend le VIX de la veille comme volatilité de toutes
  les options.
- W1 à W3 seulement si les données d'options sont obtenues.

**Essais** : 9 stratégies × 2 marchés = 18, plus 6 si les murs sont testés.

**Précision sur les murs** (30 septembre, après avoir vu les coûts, avant tout calcul). L'intérêt
ouvert quotidien des options ES coûte 42 $ depuis 2011, celui des NQ 41 $, au-dessus du plafond. On
le relève donc **une fois par semaine** : les chiffres du vendredi, publiés avant le lundi, servent
toute la semaine suivante. Deux autres précisions :
- les options utilisées sont les options trimestrielles standard (ES et NQ) ; les hebdomadaires et les
  0DTE ne sont pas dans ces données ;
- les murs sont pris sur l'échéance trimestrielle la plus proche, car la règle des « 45 jours » laisserait
  la moitié des semaines sans mur.

Le zéro gamma est calculé sur toutes les échéances trimestrielles. Coût visé : moins de 25 $ au
total, vérifié avant le téléchargement.

**Précision sur W1 et W2** : le premier contact se fait par en dessous pour le call wall (seulement les
jours qui ouvrent sous le mur), par au-dessus pour le put wall.

**Le tri** (comme les tournois n°1 et n°2) :
1. t ≥ 2 sur 2011-2022, sur les rendements quotidiens nets en % du prix, jours sans trade compris.
2. **Bruit** : battre le plus haut t de 20 versions où les minutes de chaque séance sont mélangées. Le
   profil de volume est recalculé sur les minutes mélangées ; GEX, DIX, VIX et murs restent les mêmes.
3. **Filtre au hasard** (G1-G3, D1, V1, V2, W3) : faire mieux que 95 % de 200 versions où le filtre
   choisit des jours au hasard, en même nombre. Sinon, le GEX, le DIX ou le VIX n'apportent rien.
4. **Coffre 2023-2026** pour les survivants :
   - t ≥ seuil de Bonferroni (1,65 pour 1, 1,96 pour 2, 2,13 pour 3…) ;
   - au moins 3 années positives sur 4.

### Machine évolutive n°2 : les nouvelles briques dans la sélection

Même programme que `evolution/` : 96 stratégies par génération, 60 générations, 5 graines réelles et 5
sur bruit ; entraînement 2011-2018, porte 2019-2022, coffre 2023-2026. Seul le génome change :

**3 nouvelles espèces** (en plus des 4 anciennes), sur le profil de volume de la veille :
- **retour dans la zone de valeur** : seulement les jours qui ouvrent hors de la zone ; entrée vers la
  zone quand une clôture de 5 minutes revient à l'intérieur d'au moins Z écarts-types ;
- **acceptation hors de la zone** : achat si la clôture dépasse le haut de la zone de Z écarts-types,
  vente sous le bas ;
- **retour au POC** : vente si la clôture est au-dessus du POC de plus de Z fois la largeur de la
  zone, achat en dessous.

Si les murs d'options sont obtenus, 2 espèces de plus : rejet des murs, cassure des murs.

**Le gène « filtre » passe de 3 à 9 valeurs** :
- aucun ;
- jours agités, jours calmes ;
- GEX sous ou au-dessus de sa médiane sur 252 jours ;
- VIX en déport (≥ 1) ou en contango (< 1) ;
- DIX au-dessus ou sous sa médiane sur 252 jours.

**Bruit** : les barres de 5 minutes sont mélangées dans chaque séance. Le profil de volume est recalculé
sur les barres mélangées. GEX, DIX, VIX et murs ne changent pas.

**Finalistes et coffre** : la meilleure stratégie de chaque espèce, soit 7 à 9 finalistes (fitness ≥ 0,5
et porte passée). Le champion passe s'il remplit tout ce qui suit :
- t ≥ 2,7 sur 2023-2026 (2,5 pour 4 finalistes dans l'évolution n°1, relevé pour le nombre de
  finalistes) ;
- gain positif sur 2023, 2024, 2025 et 2026 ;
- Sharpe de validation supérieur au meilleur des 5 évolutions sur bruit.

**Suivi en direct** : la page au style de SETS (`evolution/tableau/`), avec les nouvelles espèces et les
nouveaux filtres.

**À savoir** : les années 2023-2026 ont déjà servi de coffre à d'autres essais (évolution n°1, zone de
bruit). La machine n°2 ne les voit jamais pendant la recherche, mais ce coffre n'est plus vierge. Tous
les essais sont comptés dans `fonds/essais.csv`.

## Décision de l'utilisateur (30 septembre 2026)

La machine évolutive n°2 n'est lancée que si une stratégie survit au tournoi n°3, murs d'options
compris. Sinon, elle reste prête mais n'est pas lancée : le code et les tests sont dans ce dossier.
