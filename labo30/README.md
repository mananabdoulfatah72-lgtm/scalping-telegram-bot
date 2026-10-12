# Labo 30 jours (12 octobre 2026)

Page : `labo_30_jours.html` (artefact). Demande de l'utilisateur : la même chose que le labo Monte Carlo, mais pour la
version du bot pensée pour le challenge Bulenox de 30 jours. Elle devait montrer :
- les trades que cette version prend ;
- les gains et pertes à attendre ;
- ce que deviennent les challenges validés.

## Ce qui est montré

**La version retenue** est celle de la vague 13 : 4 MNQ, arrêt à l'objectif, et 6 MNQ pendant les 5 dernières séances
si l'objectif n'est pas atteint. Pour comparer, la page montre aussi :
- le bot tel quel ;
- 2 et 3 MNQ ;
- 4 MNQ (vague 12) ;
- 4 MNQ avec l'arrêt à l'objectif seul.

Sections de la page :
- **Verdict** en huit cartes.
- **Machine** : 300 challenges rejoués séance par séance, avec le solde chaque soir, l'objectif et le plancher qui
  monte. Chaque fil est un vrai achat simulé. Les compteurs exacts portent sur tous les achats de la sélection, pas
  seulement sur les 300 animés.
- **Rythme** : à quelle séance les challenges sont validés ou perdus.
- **Relief 3D** : la répartition des soldes encore en course, séance après séance.
- **Après la validation** : le Master en 1 MNQ. Délais des retraits, Masters perdus, argent pour toi mois par mois
  (bandes de l'échantillon), net d'un achat sur 24 mois.
- **Quatre fenêtres réelles de 2023-2026** (la plus rapide, une typique, une perdue, une expirée), trade par trade :
  zone de bruit et RSI(2) de nuit, signaux écartés par le filtre, gain du jour, solde, plancher.
- **Gains et pertes d'une séance** en 4 MNQ contre 1 MNQ (2012-2026), et les deux courbes du bot sans règles de compte.
- **Robustesse** :
  - choix contre vérification pour toutes les versions des vagues 12 et 13 ;
  - plafond de la taille ;
  - matrice taille × frein ;
  - réussite année par année ;
  - force du filtre ;
  - leviers de la vague 13.
- **Comparaison** avec les comptes sans limite de temps.

## Comment c'est calculé (`donnees30.py`)

- **Moteur** : `vague13/moteur13` (`defi13` pour le challenge, `master13` pour le Master). Ses séances passent par
  `vague4/moteur4.seance4` sans changement ; sans levier, il redonne exactement `parcours4` (`test_vague13.py`).
- **Statistiques exactes** :
  - chaque séance du 3 janvier 2012 au 26 août 2026 comme jour d'achat, sauf 2022 ;
  - 21 tirages du filtre (10 comme en 2026, 10 deux fois plus faibles, un sans filtre) ;
  - par version, filtre et période (2012-2021, 2023 - août 2026, 2025).
- **Échantillons** : 300 achats tirés au hasard (graines fixes) par version, filtre et période, rejoués avec leur
  solde chaque soir et les retraits du Master.
- **Exemples** : rejoués séance par séance avec `seance4`. Le solde final est identique à celui du moteur. Les montants
  par trade sont recalculés à partir des prix d'entrée et de sortie ; quand la limite du jour ou l'arrêt à l'objectif
  coupe la journée, seul le total du jour est exact, et la page le signale.
- **Gains d'une séance** : chaque séance 2012-2026 jouée sans règles de compte (limite du jour de 1 100 $ seulement),
  10 tirages du filtre comme en 2026.

Construction : `python3 donnees30.py D && python3 construire30.py`.
