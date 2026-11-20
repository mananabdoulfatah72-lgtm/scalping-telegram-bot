# Tournoi des indicateurs populaires de TradingView (20 novembre 2026)

Règles fixées et commitées avant le calcul : `REGLES.md`, idées 9 à 15. Code : `indicateurs.py` (les 7 indicateurs) et
`tournoi_tv.py` (les 5 portes de l'usine). Bilan : `python3 usine/tournoi_tv_bilan.py`.

## Résultat : aucun indicateur ne passe les 5 portes

| Indicateur | Porte 1 (2011-2014, meilleur reglage) | Reglage par defaut, 2011-2014 | Porte 2 (permutations qui font aussi bien) | Porte 3 (2015 -> 2026) | Porte 4 | Verdict |
|---|---|---|---|---|---|---|
| Squeeze Momentum (LazyBear) | PF 1.008, t 1.27, plateau oui | PF 1.005 | 11.5% | - | - | rejetee a la porte 2 |
| UT Bot Alerts (QuantNomad) | PF 1.012, t 2.65, plateau oui | PF 0.993 | 0.1% | PF 1.005, +4,384 $/an | 21.0% | rejetee a la porte 4 |
| SSL Channel (ErwinBeckers) | PF 1.003, t 0.60, plateau oui | PF 0.999 | - | - | - | rejetee a la porte 1 |
| Range Filter Buy and Sell (DonovanWall, guikroth) | PF 1.012, t 2.66, plateau oui | PF 1.010 | 0.1% | PF 1.004, +3,889 $/an | 56.0% | rejetee a la porte 4 |
| WaveTrend (LazyBear) | PF 1.009, t 1.87, plateau non | PF 0.994 | - | - | - | rejetee a la porte 1 |
| Hull Suite (InSilico) | PF 1.006, t 1.35, plateau oui | PF 1.003 | 1.5% | - | - | rejetee a la porte 2 |
| Chandelier Exit (everget) | PF 1.009, t 1.91, plateau oui | PF 1.008 | 2.4% | - | - | rejetee a la porte 2 |
| Supertrend NQ, bougies de 5 minutes | PF 1.008, t 1.77, plateau oui | PF 1.005 | 4.0% | PF 1.006, +5,009 $/an | 23.5% | rejetee a la porte 2 |
| Zone de bruit (Bot 3 en 1 sans filtres) | PF 1.018, t 1.65, plateau oui | PF 1.014 | 0.9% | PF 1.024, +4,073 $/an | 0.0% | passe les 5 portes |

(Porte 2 et porte 4 : part des marchés aux minutes mélangées qui font aussi bien ; 1 % au plus exigé.)

## Ce que ça veut dire

- **SSL Channel et WaveTrend** ne gagnent déjà pas sur 2011 - 2014, ou seulement sur un réglage isolé.
- **Squeeze Momentum, Hull Suite et Chandelier Exit** gagnent un peu sur 2011 - 2014, mais autant que sur des marchés aux
  minutes mélangées : leur gain n'a rien de propre à l'indicateur.
- **UT Bot Alerts et Range Filter vont le plus loin** : ils battent le hasard sur 2011 - 2014 (porte 2) et gagnent sur
  2015 - 2026 (+4 384 $ et +3 889 $ par an à 1 MNQ). Mais 21 % et 56 % des marchés mélangés font aussi bien sur cette
  période : comme le Supertrend, ils gagnent en suivant le mouvement de la journée, que le mélange conserve, pas grâce à
  l'ordre des minutes.
- **La zone de bruit reste la seule** à battre tous les marchés mélangés sur 2015 - 2026.

## À savoir sur les calculs

- **Contrôles** : le SSL Channel redonne exactement la formule du portage de `technical` (freqtrade) sur les 317 928
  bougies ; l'élan du Squeeze redonne une régression linéaire calculée à part (écart 1e-14).
- **Squeeze Momentum** : le script d'origine de LazyBear utilise le multiple de Keltner pour les bandes de Bollinger. Le
  multiple s'annule alors dans la compression (Bollinger dans Keltner revient à écart-type < moyenne du vrai range) : les
  5 valeurs de ce réglage donnent le même résultat. pandas-ta « corrige » ce point ; la règle fixée suit le script
  d'origine.
- **Chandelier Exit et Hull Suite** : écrits comme les scripts d'origine (stops qui ne reculent pas, racine arrondie),
  qui diffèrent un peu de pandas-ta.
- **Écartés avant le calcul** : QQE MOD, HalfTrend et Smart Money Concepts (LuxAlgo), au code trop long pour être recopié
  sans risque d'erreur. Les pages TradingView n'étaient pas accessibles depuis la session.
