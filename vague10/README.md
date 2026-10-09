# Vague 10 : freins contre les séries de pertes, un seul achat (règles fixées le 9 octobre 2026, avant le calcul)

## Demande de l'utilisateur

- **Un seul achat** de 50K : pas de rachat. Il faut savoir ce que rapporte ce compte-là et s'il survit.
- **Limiter les pertes** : se protéger quand ça tourne mal, au lieu de laisser les pertes brûler le compte.
- Ne pas faire de 2025 une année KO.

## Diagnostic (`diagnostic2025.py` → `diagnostic2025.txt`)

Comptes 50K achetés de janvier 2025 à mars 2026, bot zone 1 MNQ + RSI(2) de nuit sur 1 MES, en gardant 4 000 $ :
- **le bot a gagné en 2025** (+9 841 $), mais les comptes meurent surtout pendant le challenge, à deux moments :
  - **juillet-août 2025** (après les gains d'avril, la zone perd par petites touches pendant des semaines) ;
  - **janvier 2026** (−1 815 $ dans le mois), qui concentre la moitié des challenges perdus ;
- **ce ne sont pas de grosses pertes d'un coup** : le pire jour de 2025 est −821 $ ;
- **la règle de régularité n'y est pour rien** : sans elle, les mêmes challenges sont perdus (0 % de différence).

Un stop par trade existe déjà (la zone sort sur son stop). Contre une glissade de petites pertes, ce qui peut aider est
un **frein** déclenché par le recul du compte sous son plus haut.

## Les freins (fixés maintenant)

Tous avec la règle retenue en vague 9 (pas de zone les jours de la Fed). Le coussin est l'écart entre le solde de la
veille et le plancher : 2 000 $ au plus haut, il baisse quand le compte recule.

| Frein | Ce qu'il fait |
|---|---|
| aucun | le bot tel quel |
| MES sous 1 750, 1 500, 1 250 ou 1 000 $ de coussin | dès que le compte recule de 250, 500, 750 ou 1 000 $ sous son plus haut, la zone passe sur MES (environ deux fois moins de risque) jusqu'à ce que le coussin remonte |
| pause de 10 ou 20 séances sous 1 500 ou 1 000 $ de coussin | le bot entier s'arrête 10 ou 20 séances ; le frein se réarme quand le coussin repasse au-dessus du seuil |
| stop du jour 300 ou 500 $ | tout est fermé et le bot s'arrête jusqu'au lendemain quand la journée perd 300 ou 500 $ |
| MES sous 1 500 $ + stop du jour 500 $ | les deux |

Ces 12 freins sont essayés sur 3 comptes :
- LucidFlex 50K ;
- Topstep 50K ;
- FundedNext Legacy 50K.

Chaque compte est essayé en gardant 2 000 $ ou 4 000 $ après chaque retrait, soit **72 candidates**.

## Mesures : un seul achat, sans rachat

Un achat toutes les 5 séances, 10 tirages du filtre simulé aussi bon qu'en 2026, suivi jusqu'à 36 mois. Pour chaque
achat :
- challenge réussi ou perdu, et temps pour valider ;
- compte financé perdu dans les 12 mois ;
- retraits par mois tant que le compte vit ;
- **argent net de l'achat sur ses 24 premiers mois** (retraits × part − prix) ;
- part des achats qui perdent de l'argent.

Groupes d'achats :

| Groupe | Achats | Rôle |
|---|---|---|
| Choix | 2012-2021 (pas suivis après 2022) | sélection |
| Vérification | 2023 - mars 2026 | validation |
| 2025 | 2025 - mars 2026 | test de l'année difficile |

## Jugement

1. **Sûre** : sur les achats 2012-2021, challenge perdu ≤ 20 % et compte financé perdu dans les 12 mois ≤ 20 %.
2. **Retenue** : parmi les sûres, le plus d'argent net par achat sur 24 mois (achats 2012-2021).
3. **Validée** si, sur les achats 2023 - mars 2026 :
   - challenge perdu ≤ 25 % ;
   - compte financé perdu dans les 12 mois ≤ 25 % ;
   - argent net par achat positif ;
   - **et, pour les achats de 2025, challenge perdu ≤ 25 %** (l'année difficile, jamais utilisée pour choisir).

   Sinon, on prend la suivante.
4. On donne aussi la meilleure de chaque frein, pour voir lequel protège vraiment.

**À savoir avant d'y croire :**
- 2023-2026 a déjà été regardé de nombreuses fois ;
- le diagnostic ci-dessus a été fait sur 2025 ;
- le filtre est simulé.

## Contrôles

- `vague8/test_vague8.py` : par défaut, le moteur redonne exactement le moteur d'avant la vague 8 (213 achats,
  retraits séance par séance).
- `test_vague10.py` : la pause arrête le bot le bon nombre de séances et se réarme au bon moment (marché synthétique).
