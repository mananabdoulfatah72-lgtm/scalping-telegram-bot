# Arène, vague 10 : ton bot tel qu'il est réglé, face au vrai contrat Master (règles fixées avant tout calcul, 9 novembre 2026)

La relecture de la vague 9 a montré que l'arène simulait un bot un peu différent du vrai (limite du jour de 400 $ au lieu
de 1 000 $, sans le frein) et un compte plus généreux que le contrat (Master éternel, 100 % des retraits). Cette vague
refait le calcul dans le cadre du contrat.

## Le bot (Z12F, 1 MNQ)

- **Zone** : journal de rejeu C2 + Q1 (`donnees/c2q1.txt`), sans les jours de VIX inversé (filtre VIX) ni les jours de la
  Fed. **Le filtre delta ne peut pas être rejoué** : avant avril 2026, le delta de chaque transaction est inconnu, et le
  rejeu garde tous les trades (ce que fait le filtre quand le delta est nul). On le dit, on ne le devine pas.
- **Limite du jour** : 1 000 $ (le réglage du README pour le Master).
- **Frein** : la zone passe sur MES quand la marge au-dessus du plancher tombe sous 1 750 $ (2 500 − 750).
  - Simulé comme **une demi-exposition**. 1 MES expose environ 38 000 $ sur un indice moins volatil, 1 MNQ environ
    57 000 $ : le rapport de risque est proche de 0,5.
  - C'est une approximation annoncée.
- **Plafond du jour** : 0 (tableau du README) ; variante à 500 $ (tout est fermé dès 500 $ de gain dans la journée).

## Le contrat (Annexe A du 23 octobre 2026, Option 2)

- **Plancher.** Il est à 2 500 $ sous le plus haut des fins de journée, contrôlé en temps réel (latent compris). Il
  s'arrête au solde de départ (50 000 $, le texte du contrat ; l'arène mettait 50 100 $).
- **Retraits.**
  - 10 jours tradés depuis le dernier retrait.
  - Au moins 1 000 $ ; au plus 1 500 $ pour les 3 premiers.
  - 2 600 $ gardés : solde d'au moins 52 600 $ après le retrait.
  - Meilleure journée au plus 40 % du gain depuis le dernier retrait.
  - **90 % pour toi** ; activation de 148 $.
- **Le Master s'arrête au 3e retrait** et passe en funded. Le contrat du funded n'est pas connu ; hypothèses :
  - plancher initial de 2 000 $ (le seul chiffre donné), qui s'arrête au solde de départ ;
  - mêmes règles de retrait sans le plafond de 1 500 $ ;
  - frein réglé sur 2 000 $ (MES dès que la marge passe sous 1 250 $).
- **Inactivité.** 5 jours de trading de suite sans trade = **compte perdu** (suspension, solde confisqué). On compte de
  façon prudente : tous les jours du fichier, demi-journées et jours fériés courts compris, comptent comme sans trade
  quand le rejeu n'y trade pas.

## Les candidats (2017 - 2026, un Master neuf toutes les 20 séances)

| | |
|---|---|
| T0 | le bot tel qu'il est réglé : limite 1 000 $, frein, plafond 0 |
| T1 | T0 avec un plafond du jour de 500 $ |
| T2 | T0, et **secours du même bot** : après 3 jours de trading de suite sans trade, ce jour-là la zone tourne sans le filtre VIX, sans la règle de la Fed et sans le filtre Q1 (journal C2 : la même zone que celle de ta qualification, avec moins de filtres) |
| T3 | T2 avec un plafond de 500 $ |

Pour information seulement (pas candidats) :
- T0 avec une limite de 400 $ ;
- T0 sans frein ;
- K1c : W1 après 3 jours sans trade, limite 1 000 $. W1 est un modèle d'apprentissage, ce qui pose la question de la
  section 20 du contrat.

## Mesures

Pour chaque départ :
- part des Masters qui atteignent le 3e retrait ;
- part perdue avant (par le plancher, par l'inactivité, séparément) ;
- part encore en cours à la fin des données ;
- médiane des séances jusqu'au 1er et au 3e retrait ;
- ce que tu touches sur le Master (90 % des retraits, moins l'activation) ;
- puis, pour le funded : part perdue dans l'année et ce que tu touches dans l'année.

On compte aussi les épisodes distincts (dates) des pertes : peu d'épisodes = écarts fragiles.

## Règle de choix (écrite avant le calcul)

1. **Conforme** = aucun compte perdu par inactivité sur 2017 - 2026.
2. Parmi les conformes, le plus petit taux de Masters perdus avant le 3e retrait. Si deux candidats sont à moins de
   5 points, ou si l'écart repose sur moins de 3 épisodes distincts, on garde le plus simple (ordre T0, T1, T2, T3).
3. Le plafond de 500 $ est gardé seulement s'il raccourcit d'au moins 15 % la médiane jusqu'au 3e retrait, sans
   augmenter de plus de 2 points les pertes avant le 3e retrait.
4. Si aucun T n'est conforme : le bot seul ne tient pas la règle d'inactivité. On le dit, et la suite dépend de la réponse
   écrite de Bulenox (seconde stratégie, W1).
