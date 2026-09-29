# Dérive de nuit dans un compte de challenge « intraday »

## Idée (fixée le 29 septembre 2026, avant de télécharger les données)

Sur 2011-2026, le Nasdaq a fait **+394 % entre la clôture (16 h) et l'ouverture (9 h 30)**, contre +127 %
en séance (`challenge/resultats_version7_futures.txt`). C'est une anomalie connue : Cliff, Cooper et Gulen
(2008) ; Lou, Polk et Skouras (2019). Boyarchenko, Larsen et Whelan (2023, « The Overnight Drift », Fed de
New York) la trouvent concentrée **autour de l'ouverture européenne**, et plus forte **après une baisse
en fin de séance américaine**.

Point clé pour un challenge : Topstep et Apex interdisent de garder une position **après leur clôture**
(16 h 10 et 16 h 59, heure de New York). Mais la session de nuit, qui rouvre à 18 h, **fait partie de la
journée de trading suivante**. Acheter à 18 h et revendre à 9 h 30 respecte donc la règle
« intraday » (règles à vérifier chez chaque firme).

## Règles du test (données Databento ohlcv-1h ES et NQ, contrat le plus échangé, 2010-2026)

- **N1** : chaque jour de bourse, achat à l'ouverture de la barre de 18 h (réouverture), vente à
  l'ouverture de la barre de 9 h 30. Comme les barres sont horaires, la vente se fait à l'ouverture de la
  barre de 9 h, avec la barre de 9 h utilisée en entier comme approximation. Pas de position le
  dimanche soir vers le lundi s'il manque des barres ; pas de trade le soir d'un changement d'échéance.
- Frais : 1 $ par ordre et 1 tick de glissement par ordre (MES 1,25 $ par tick, MNQ 0,50 $ par tick).
- Mesures : gain net moyen par trade (1 micro), t, sous-périodes 2010-2014, 2015-2019 et 2020-2026,
  pire nuit, part des nuits gagnantes.
- **Information** (pas un essai) : rendement moyen de chaque heure de la nuit, et nuits après une séance
  en baisse contre nuits après une séance en hausse.
- Critère pour passer au challenge : t ≥ 2 sur toute la période **et** gain net positif dans les trois
  sous-périodes, sur ES comme sur NQ.
- Si le critère est rempli : bot coussin (même code que `challenge/`) sur les règles des firmes, avec le
  pire moment de la nuit tiré des barres horaires.
- Un essai (N1 sur ES et NQ) inscrit dans `fonds/essais.csv`. Aucune autre fenêtre horaire ne sera essayée
  comme stratégie après les résultats.

## Résultats (`analyse.py`, `resultats.txt`) : rejetée

| Marché | Nuits | Net par nuit (1 micro) | t | 2010-2014 | 2015-2019 | 2020-2026 |
|---|---|---|---|---|---|---|
| ES (MES) | 4 123 | +0,50 $ | 0,31 | −1,78 $ | −0,19 $ | +2,53 $ |
| NQ (MNQ) | 4 123 | +4,84 $ | 1,74 | −0,10 $ | +2,04 $ | +10,19 $ |

Le critère n'est pas rempli : pas de challenge simulé.
- Pour information, la hausse de nuit du Nasdaq se fait surtout **en dehors des heures qu'une prop firm
  intraday autorise** : juste après 16 h (+1,1 point de base pour la barre de 16 h) et autour de
  l'ouverture européenne (+1,2 pour 2 h). Le reste de la nuit rapporte à peine plus que les frais.
- Après une séance en baisse, la nuit est un peu meilleure (+0,06 % contre +0,03 % sur NQ), comme le
  trouvent Boyarchenko et al. Ce n'est pas testé comme stratégie, puisque ce n'était pas fixé à l'avance.
