# Ne plus rater les fortes cassures écartées par le filtre (règles fixées le 19 octobre 2026, avant tout calcul)

Demande de l'utilisateur, 19 octobre 2026 : garder le filtre delta, mais ne plus rater des mouvements comme le
16 octobre (vente de 10 h écartée, delta +72, +447,75 points) et le 19 octobre (achat de 11 h 30 écarté, delta −60, le
prix a ensuite monté).

## Ce que dit le code (`bot3en1/Bot3en1.Core/Moteur.cs`, `Zone`)

1. À la cassure, si le delta des 30 minutes va contre le trade, le trade est écarté.
2. **Le trade écarté reste « virtuel »** (`ZoneVirtuelle`) jusqu'à sa sortie (prix revenu dans la zone ou de l'autre
   côté du VWAP à un contrôle). Tant qu'il vit, **aucun nouveau signal n'est accepté**. Quand le prix part fort dans
   le sens de la cassure, le virtuel ne sort jamais : le bot reste dehors toute la journée, même si le delta devient
   favorable une demi-heure plus tard.

Le point 2 n'a jamais été testé : le filtre a été trouvé comme « garder ou écarter le trade », et le blocage qui
suit vient de la manière dont il a été branché sur la zone.

## Variantes testées

- **H1** : le bot actuel (référence).
- **R, « relance »** : tant que le trade écarté est encore vivant, à chaque contrôle suivant, si le delta des
  30 minutes qui finissent à ce contrôle va maintenant dans son sens, le bot entre (au prix du contrôle). Sorties
  inchangées.
- **S, « cassure forte »** : à la cassure, si le prix dépasse la limite d'au moins **1 fois** la marge de la zone
  (|prix − limite| ≥ 1 × σ × référence, c'est-à-dire un prix à 2 σ de la référence), le trade est pris quel que soit
  le delta. Seuil de 1 fixé ici. Pour information, le 16 octobre dépasse de 1,6 fois et le 19 octobre de 0,75 fois :
  ce seuil ne repêche pas le 19.
- **R + S** : les deux.
- Descriptif seulement : S et R + S avec un seuil de 0,5.

## Données

- **P1, choix** : 1er avril - 1er octobre 2026, vrai delta Databento (`agresseurs_2026.csv.gz`, fabriqué depuis
  `orderflow/donnees`), barres du robot. Aucune de ces variantes n'a été réglée sur cette période.
- **P2, contrôle** : 2 - 16 octobre 2026, vrai delta Rithmic (export de l'utilisateur). Elle contient le 16 octobre,
  qui a motivé l'étude : elle ne sert qu'à vérifier, pas à choisir.
- **15 ans, prix seuls** (pour S) : trades de la zone sans filtre, 2011-2026, coupés selon la force de la cassure.
- Moteur : le code C# du bot (`Bot3en1.Replay`), avec les variantes derrière des réglages éteints par défaut.

## Décision (fixée maintenant)

Une variante remplace H1 dans le bot seulement si, à la fois :
1. sur P1, elle gagne **plus** que H1 en points ;
2. sur P1, sa pire baisse (pertes enchaînées, en points) n'est pas pire que celle de H1 de plus de **20 %** ;
3. sur P2, elle ne fait **pas moins bien** que H1 ;
4. pour les variantes avec S : sur 15 ans, les cassures fortes (≥ 1 fois la marge) gagnent **plus** en moyenne que les
   autres, avec t ≥ 1.

Si plusieurs passent : celle qui gagne le plus sur P1. Si aucune ne passe : le bot ne change pas, et les résultats
sont publiés quand même.
