# SPEC : <nom de la stratégie> (écrite le <date>, avant tout calcul)

Modèle pour passer d'un outil compris (enquête n° 5 de [ENQUETES.md](ENQUETES.md)) à une idée que l'usine peut tester.
Aucun code d'un tiers n'y entre : on décrit un comportement.

## D'où elle vient

- **Outil ou source :** <indicateur, bot, article, observation>.
- **Ce qui donne le droit de l'étudier :** <ton propre code / accord écrit de l'auteur / observation pendant l'usage
  (article 5.3) / licence qui l'autorise>.
- **Comment elle a été comprise :** <signaux notés sur N séances à côté des prix / lecture REA (quels fichiers, quelles
  preuves)>.
- **Code recopié :** aucun.

## L'avantage, en une phrase, et qui perd en face

- **L'avantage :** <pourquoi ça gagnerait>.
- **Qui perd en face :** <qui paie ce gain>.

## La règle exacte

| | |
|---|---|
| Marché, contrat | NQ (prix), ordres sur MNQ |
| Heures | <début, dernière entrée, sortie forcée ; à plat avant 16 h 59 à New York (Bulenox)> |
| Entrée | <condition exacte, à la clôture ou à l'ouverture de quelle minute> |
| Sortie | <condition, stop, objectif> |
| Taille, limite du jour | 1 MNQ ; <limite> |
| Réglages et grille de la porte 1 | <réglage : valeurs ; réglage : valeurs> |

## Cas limites

- **Jours courts, jours fériés, changement d'échéance :** <comment>.
- **Minutes manquantes :** <comment>.

## Ce qui reste inconnu

- <ce que l'observation ou REA n'a pas établi>

## Passage à l'usine

1. Recopier l'idée dans `usine/REGLES.md` (avantage, contrepartie, règle exacte, grille), puis commiter **avant** de
   calculer.
2. Écrire son noyau dans `usine/moteur.py`, à côté des 7 autres.
3. Lancer `python3 usine/portes.py <idée>`. Le tableau de bord et le brief du matin donnent le verdict.
4. Si elle passe les 5 portes : papier deux semaines, puis 1 MES, puis 1 MNQ (`usine/RISQUE.md`).
