# Zone de bruit + RSI(2) sur un même compte : quelle taille ?

Le RSI(2) sur le NQ a passé le tournoi 8 (`tournoi8/`). Il est indépendant de la zone de bruit
(corrélation ≈ 0). Avec deux sources dont les pertes ne tombent pas les mêmes jours, le même risque
autorise peut-être une taille plus grande. Pour la zone seule, aucune des 128 gestions testées ne
faisait mieux que la gestion actuelle de façon fiable (`zone_retrait/`).

## Règles (fixées le 2 octobre 2026, avant tout calcul)

Même méthode que `zone_retrait/`, avec deux sources :
- **Simulateur** : `carriere()` de `zone_retrait/` (règles Phidias 50K Fundamental, gestion du robot,
  vérifié égal à `une_journee`) avec une deuxième source.
  - Chaque source reçoit f × coussin / √2 de risque, au moins 1 MNQ.
  - Le pire moment du jour est la somme des deux.
  - Le RSI(2) est compté comme dans `tournoi8/combinaison8.py`.
- **Grille : 128 gestions** :
  - f du challenge, f du compte financé avant blocage de la limite, f après blocage, chacun parmi
    0,15 / 0,25 / 0,35 / 0,50 ;
  - marge gardée après un retrait : 0 $ ou 1 000 $.
- **Choix** : la gestion au meilleur gain net par an (retraits reçus − challenges payés à 164 $) sur
  les départs 2011-2020, un tous les 5 jours, suivis 24 mois.
- **Contrôle** : départs 2023-2024 suivis 24 mois. La gestion choisie **remplace la gestion actuelle
  (0,15 partout, marge 0) seulement si elle fait mieux qu'elle sur ce contrôle.** Sinon, on garde
  0,15.
- **Pour information** : départs 2023-2025 suivis 12 mois ; part des départs qui ne reçoivent rien ;
  comptes perdus par an ; voisins de la gestion choisie (un réglage changé).

Le choix sur 2011-2020 utilise des années où le RSI(2) a été sélectionné. Seul le contrôle 2023-2024
juge.
