# Labo de robustesse du bot 3 en 1 (11 octobre 2026)

Demande de l'utilisateur : le même Monte Carlo (moteur du bot, relief 3D), mais beaucoup plus complet, avec son equity
curve, le hors échantillon (« Oxford », compris comme *Out-Of-Sample* et walk-forward), la matrice de suroptimisation,
la construction de portefeuille, la matrice des corrélations et la permutation des paramètres. Page :
`labo_bulenox.html` (artefact), assemblée par `construire_v3.py` à partir de `page_v3.html`, des données du Monte Carlo
(`../montecarlo/donnees_v2.json`, `../montecarlo/moteur_jour.js`) et de `robustesse.json`.

## Fichiers

| Fichier | Rôle |
|---|---|
| `variantes.py` | Zone de bruit et RSI(2) de nuit avec des paramètres libres (même code que le bot) |
| `test_robustesse.py` | Contrôle : réglages du bot = séries du bot (écart 2e-13 $, 3 562 trades, 484 nuits) |
| `robustesse.py` | Toutes les analyses ; écrit `robustesse.json` et `robustesse.txt` |
| `page_v3.html`, `construire_v3.py` | Page et assemblage |

## Méthode

Séances du 3 janvier 2012 au 25 septembre 2026, en $ par séance au prix d'aujourd'hui, sans les règles du compte.
Zone 1 MNQ (pas de zone les jours de la Fed), RSI(2) de nuit 1 MES.
- **Filtre delta simulé** comme dans les vagues 9 à 11. La courbe et ses statistiques prennent le **tirage médian**
  des 10 tirages, pas leur moyenne : la moyenne lisserait les pertes. L'enveloppe des 10 tirages est affichée.
- **Permutation des paramètres** : 180 zones (jours de moyenne 5 à 30, contrôle toutes les 15, 30 ou 60 min, largeur
  ×0,6 à ×1,5, sortie VWAP ou zone seule) × 80 RSI(2) (moyenne longue 100 à 250, seuil 5 à 30, sortie 3 à 10) =
  14 400 bots, sans filtre (le filtre ne dépend pas de ces paramètres).
- **Matrice de suroptimisation** : PBO par validation croisée combinatoire (Bailey, Borwein, López de Prado, Zhu 2014),
  16 blocs, 12 870 découpages, critère Sharpe. Matrice des dixièmes de rang (400 découpages), logit du rang du
  champion, rang des réglages du bot. Sharpe dégonflé (Bailey et López de Prado 2014) en fonction du nombre d'essais et
  de leur dispersion ; nombre effectif d'essais par les valeurs propres de la corrélation des variantes.
- **Hors échantillon** : choix sur 2012-2021, jugement sur 2023-2026. **Walk-forward** : choix du meilleur Sharpe sur
  1, 2, 3 ou 5 ans passés, joué 3, 6 ou 12 mois, de 2015 à 2026 (12 réglages), efficacité = gain hors échantillon ÷
  gain dans l'échantillon du bot choisi.
- **Tests de permutation** : sens des 3 226 trades de zone tiré à pile ou face (20 000 fois) ; nuits du RSI(2) tirées
  au hasard (20 000 fois) ; ordre des séances mélangé (5 000 fois) pour la baisse maximale.
- **Portefeuille** : zone filtrée (0 à 2 MNQ par pas de 1 MES), RSI(2) de nuit (0 à 4 MES), suivi de tendance
  multi-marchés (`tendance/systeme.py`, 12 %/an sur 50 000 $) ; meilleur Sharpe choisi sur 2012-2021, jugé 2023-2026.
- **Corrélations** : jour, mois, rangs, jours où le Nasdaq perd plus de 2 % ; corrélation sur 12 mois glissants.
- **Direct** : le robot virtuel de main (zone sans filtre + RSI(2) sur 1 MNQ) face à un cône de 20 000 tirages de 60
  séances du backtest.

## Résultats : `robustesse.txt`
- Bot (filtre simule) : 9,380 $/an, Sharpe 2.04, baisse max 5,199 $ ; sans filtre 6,499 $/an, Sharpe 1.33
- Permutation : 14 400 bots, 100% gagnants, Sharpe median 0.98, bot = 1.33 (rang 99%)
- PBO : bots 30%, zones 28%, RSI(2) 48%
- Sharpe degonfle (sans filtre) : N=1 100.0%, N grille 99.8%, N effectif 19 -> 100.0%, N=800 000 99.1%
- Hors echantillon : meilleur bot 2012-2021 Sharpe 1.52 -> 2023-2026 1.35 ; bot 1.29 -> 1.40 ; correlation des rangs 0.30
- Walk-forward (3 ans, 12 mois) : 5,829 $/an, Sharpe 1.06, efficacite 63% ; bot fixe 6,943 $/an ; bot moyen de la grille 5,425 $/an
- Permutation : zone p = 0.0000 (77,690 $ contre -9,965 $ au hasard) ; nuits p = 0.0003 (19,874 $ contre 3,918 $) ; baisse max reelle 5,199 $, melanges : mediane 4,664 $, 95 % 6,873 $
- Portefeuille : meilleur Sharpe 2012-2021 = zone 0.4, nuit 0.5, tendance 0.125 -> Sharpe 2023-2026 2.07 ; bot (1, 1, 0) 2.04 ; correlation zone/nuit 0.02, zone/tendance -0.08

## Lecture

- **Le bot n'est pas un pic isolé** : les 14 400 bots gagnent tous de l'argent sans filtre (Sharpe médian 0,98). Mais
  ses réglages sont au 99e centile de la grille, d'où l'intérêt des tests suivants.
- **Suroptimisation modérée** : le champion d'un découpage finit dans la moitié basse 30 % du temps (PBO), sans
  jamais devenir perdant. Les réglages du bot, fixés d'avance, sont en moyenne au 93e centile hors échantillon.
- **Hors échantillon** : le bot fait mieux sur 2023-2026 (Sharpe 1,40) que sur 2012-2021 (1,29). Ré-optimiser chaque
  année (walk-forward) ne bat pas le bot fixe.
- **Hasard** : aucun des 20 000 tirages à pile ou face ne fait aussi bien que la zone ; les nuits du RSI(2) battent
  des nuits au hasard (p = 0,0003).
- **Portefeuille** : zone et nuit sont indépendantes (0,02) ; la zone porte 89 % du risque. Optimiser les poids sur le
  passé n'apporte rien hors échantillon.
- **Limite principale** : ces tests jugent la zone et le RSI(2). Le filtre delta, qui fait passer le Sharpe de 1,33 à
  ~2,0, reste prouvé sur 20 trades écartés seulement.
