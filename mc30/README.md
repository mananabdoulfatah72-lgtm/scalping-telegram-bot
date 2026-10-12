# Monte Carlo 30 jours (version D de la vague 13)

Page : **monte_carlo_30_jours.html** (publiée : https://claude.ai/artifact/WEd38z75JyWSqJBJ1y9Vjv).

Elle remplace l'animation de `labo30/`, qui se bloquait à 300 tirages. La page tirait 300 chemins pré-calculés et
redimensionnait ses toiles à chaque image.

## Les données : l'univers complet des achats

`donnees_mc30.py` rejoue **chaque séance du 3 janvier 2012 au 26 août 2026 comme jour d'achat** (3 761 jours), avec
**chacun des 21 tirages du filtre simulé** (10 « comme en 2026 », 10 « deux fois plus faible », 1 « sans filtre »). Cela
fait 78 981 challenges. Ils passent par le moteur exact de la vague 13 : `vague13/moteur13.defi13` puis `master13`, qui
appellent `vague4/moteur4.seance4` séance par séance.

- **Challenge** (Bulenox Legacy 50K option 2, 30 jours calendaires) :
  - 4 MNQ par source, pas de frein ;
  - tout fermé à 53 050 $ ;
  - 6 MNQ les 5 dernières séances.
- **Master** :
  - 1 MNQ, frein 750 $, plafond du jour 500 $ ;
  - suivi 24 mois après la validation, ou jusqu'à la fin des données ;
  - suivi jusqu'au 3e retrait : Bulenox passe alors le compte en réel, et la simulation s'arrête là.
- **Gardé pour chaque achat :**
  - l'issue et le solde à la fin de chaque séance du challenge ;
  - au Master : la séance de la perte éventuelle, la durée suivie, et chaque retrait (séance et montant).
- **Stockage :** `univers_mc30.json` contient l'en-tête (dates, séances dans les 30 jours, références, comparaison des
  versions). `univers_mc30.bin.gz` contient les tableaux binaires : 2,4 Mo, 0,46 Mo compressés.
- **Contrôle :** les taux de validation recalculés sur l'univers sont **exactement ceux de la vague 13**.

| Filtre | 2012-2021 | 2023-2026 | 2025 | 2012-2026 |
|---|---|---|---|---|
| Comme en 2026 | 53,3 % | 55,4 % | 44,7 % | 54,6 % |
| Deux fois plus faible | 50,5 % | 52,7 % | 42,4 % | 51,7 % |
| Sans filtre | 47,6 % | 48,6 % | 40,1 % | 48,6 % |

2022 n'était pas dans les groupes de la vague 13. Elle est ici dans « 2012 – 2026 » et en période seule, car la page ne
sert pas à choisir une version.

## La page

- **Machine.** Tirage au hasard (graine affichée, reproductible) parmi les achats de la période et du filtre choisis :
  - 100 à 5 000 challenges ;
  - traits animés séance par séance, en orange pendant les séances à 6 MNQ ;
  - compteurs, avec le bruit du tirage et l'incertitude réelle.
- **Animation.**
  - Les toiles ne sont redimensionnées que quand la largeur change.
  - Les traces finies sont dessinées une seule fois, sur leur propre calque. Les challenges en cours sont sur un calque
    effacé à chaque image.
  - L'horloge est interne et plafonnée à 50 ms par image : pas de saut au retour sur l'onglet.
  - Mode instantané par paquets de 800.
  - Mesuré dans Chromium : 60 images par seconde à 500 et à 5 000 challenges (moyenne 16,7 ms), y compris pendant
    un redimensionnement.
- **Convergence.** La part validée du tirage converge vers la valeur exacte. Deux bandes :
  - le bruit du tirage ;
  - l'incertitude réelle (Wilson sur le nombre de périodes de 30 jours vraiment différentes, environ 180 sur
    2012-2026).
- **Séances.** Séance de fin par issue, gain de chaque séance (4 et 6 MNQ), journées à −1 000 $ ou pire par challenge.
- **Rachats.**
  - 4 000 personnes rachètent dès la séance suivante après un échec, jusqu'à 1 à 10 achats. Leurs challenges
    s'enchaînent dans le temps.
  - Résultats : part validée achat après achat (comparée à des achats indépendants), coût, délai.
  - Argent net sur 6, 12 ou 24 mois de Master.
- **Master.** Calculé sur tous les validés de la sélection :
  - retraits cumulés mois par mois (médiane, 25-75 %, 10-90 %) ;
  - comptes perdus ;
  - délai du premier retrait ;
  - 3 retraits en 12 mois.
- **Un challenge en détail.** Séance par séance (date, taille, gain, solde, plancher), puis ses retraits au Master.
- **Comparaison des versions et limites.**

## Vérifié (12 octobre 2026)

Tests faits dans Chromium sans écran, à 1 280 px et à 400 px :
- **Décodage :** 5 chemins de la page identiques à ceux de Python.
- **Taux :** taux exacts identiques pour toutes les périodes et tous les filtres.
- **Master :** chiffres identiques à un calcul Python indépendant :
  - 56 % des comptes ont un retrait dans les 6 mois ;
  - 58 % font 3 retraits en 12 mois ;
  - 13 % sont perdus en 12 mois ;
  - retraits cumulés médians : 3 817 $ à 12 mois, 3 979 $ à 24 mois.
- **Comportement :**
  - pause et reprise ;
  - passage à l'instantané en pleine animation ;
  - changement de chaque réglage.
- **Affichage :** aucun défilement horizontal, aucune erreur.

Le suffixe `#controle` dans l'adresse expose les tableaux décodés (`window.__mc30`) pour ces tests.

```
python3 donnees_mc30.py      # environ 1 minute
python3 construire_mc30.py   # page_mc30.html + données -> monte_carlo_30_jours.html
```
