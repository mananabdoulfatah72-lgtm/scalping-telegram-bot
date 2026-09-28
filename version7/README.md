# Robot version 7 (argent virtuel)

Suit en direct la version 7 de l'étude des secteurs (branche `claude/keen-babbage-r686cl`,
`secteurs/README.md`) : chaque fin de mois, les 5 actions technologie au meilleur rendement de
6 mois à 1 mois, 10 % du compte chacune, 50 % non investis. Tableau de bord :
[`robot/TABLEAU_DE_BORD.md`](robot/TABLEAU_DE_BORD.md).

**Ce n'est pas une stratégie validée.** Elle a été rejetée par le critère 8 (placebo battu à 93 %
pour 95 % exigés). Elle a aussi été choisie sur 2021-2026, après avoir vu les résultats. Le suivi en
argent virtuel sert justement à la juger sur des mois qu'aucun test n'a vus.

- Chaque soir de semaine (22 h 45 UTC), le compte virtuel est valorisé.
- La veille du dernier jour de bourse du mois, les ordres à passer à la clôture sont envoyés (Telegram et
  tableau de bord). Les signaux n'utilisent que des prix déjà connus.
- Le dernier jour, le compte est rééquilibré à la clôture (frais de 5 points de base par ordre). Les
  liquidités ne rapportent rien, comme sur un compte de challenge.
- Contrôle : rejoué sur 2021-2026, le robot choisit les mêmes actions que le backtest pour les 60 mois
  et finit à +163,7 % (backtest sans intérêts : +163,6 %).

**Challenge 50K** (`secteurs/challenge_v7.py` sur la branche de recherche) :
- Les comptes de futures (Topstep, Apex, Phidias) ne permettent pas d'acheter ces actions. Topstep
  et Apex interdisent aussi de garder une position la nuit.
- Il faut un compte qui permet les actions (CFD) et de garder la nuit et le week-end (compte « swing »).
- Le tableau de bord suit un challenge virtuel de ce type : +10 % à atteindre, perte maximale de 10 %,
  et 5 % par jour.

Sécurités :
- Si les prix de la séance attendue ne sont pas encore publiés, ou s'il manque un prix pour une action
  de la liste, le robot s'arrête sans rien enregistrer. Le passage suivant rattrape les jours manqués,
  rééquilibrages compris.
- Un mouvement de plus de 50 % en un jour est traité comme une erreur de données.
- Si la bourse ferme par surprise le dernier jour prévu du mois, le rééquilibrage se fait à la clôture
  de la veille.
