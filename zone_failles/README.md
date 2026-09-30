# Zone de bruit NQ : failles et corrections

L'utilisateur laisse tomber les autres pistes et veut rendre la zone de bruit sur MNQ plus solide. Il
faut d'abord trouver ses failles, puis tester des corrections sans se raconter d'histoires : chaque
réglage essayé sur les données passées augmente le risque de trouver un faux progrès.

## 1. Autopsie (30 septembre 2026, 2011-2022 seulement)

`autopsie.py` rejoue la zone trade par trade. Le résultat est identique au backtest de référence,
vérifié jour par jour. Le rapport complet est dans `autopsie.txt`.

Sur NQ, 2011-2022 :

| Constat | Chiffres |
|---|---|
| **Les frais expliquent l'échec de 2011-2016** | Avant frais, t +3,89 sur 2011-2022 (+1,28 sur 2011-2016). 1,5 point de frais valait 6,5 pb du prix en 2011, 3,3 pb en 2016, 1 à 1,5 pb depuis 2020. |
| **Les allers-retours coûtent tout** | Jours à un seul trade : +11,1 pts par trade (t +7,6). Jours à 2 trades ou plus : −4,5 pts par trade (t −8,5). Trades coupés au bout de 30 min : −14,6 pts, 11 % de gagnants. |
| **Le régime compte** | GEX de la veille sous sa médiane : t +1,86 ; au-dessus : −0,92. Volatilité forte : t +1,42 ; calme : −0,20. VIX en déport : t +1,47. |
| **Les achats portent le résultat** | Achats : t +1,05 après frais ; ventes : −0,04 (toutes deux positives avant frais). |
| **Données polluées** | Jours dont la moyenne sur 14 jours contient une séance incomplète (férié CME, fermeture anticipée) : t −0,39 ; jours propres : t +1,08. La « veille » peut aussi être une séance incomplète. Le robot a la même faille. |
| **La taille de l'article dégrade** | Taille inverse de la volatilité (cible de volatilité) : t −0,44, contre +0,62 en taille fixe. La zone gagne justement quand ça bouge. |

Les mêmes constats valent sur ES, en plus faibles.

## 2. Variantes (fixées le 30 septembre 2026, avant tout calcul de variante)

| Variante | Correction | Faille visée |
|---|---|---|
| V0 | la zone telle quelle (référence) | — |
| V1 | **données propres** : moyenne sur les 14 dernières séances complètes ; veille = dernière séance complète du même contrat | données polluées |
| V2 | V1 + **un seul trade par jour** (pas de nouvelle entrée après un stop) | allers-retours |
| V3 | V1 + **seulement si le GEX de la veille est sous sa médiane sur 252 jours** | régime |
| V4 | V1 + **achats seulement** | sens |
| V5 | V1 + **stop suiveur sur le VWAP seul** (au lieu du plus serré entre la limite et le VWAP) | trades coupés trop tôt |

Aucun autre réglage (heure, nombre de jours, largeur de la zone) n'est essayé : l'autopsie montre des
écarts entre les heures d'entrée, mais les choisir serait tailler la stratégie sur le passé.

### Critères

1. **V1** est une correction de calcul : elle est adoptée quoi qu'il arrive, et son effet est donné.
2. **V2 à V5** sont comparées à V1. Une variante est retenue si elle remplit tout ce qui suit :
   - elle fait mieux que V1 sur NQ en 2011-2016 **et** en 2017-2022 (t des rendements quotidiens nets) ;
   - elle ne fait pas moins bien que V1 sur ES en 2011-2022, contrôle d'une correction qui doit être
     générale ;
   - **sur 2023-2026, ouvert une fois pour toutes les variantes**, elle fait mieux que V1, avec un t
     de la différence quotidienne avec V1 d'au moins 1,65.
3. Les variantes retenues sont réunies en une version finale. Celle-ci est jugée sur 2023-2026 : t ≥ 2
   et au moins 3 années positives sur 4.
4. Si la version finale passe, elle remplace la zone actuelle dans le robot (`zone/robot.py` sur
   main) et dans le script TradingView. Sinon, seule la correction V1 y est portée.

**À savoir** : 2023-2026 a déjà servi à juger la zone elle-même (t 2,01). Les variantes ne l'ont jamais
vu, mais on sait déjà que la base y est bonne. D'où le critère sur la différence avec V1, et pas sur
le résultat seul.

On donne aussi les résultats **aux frais d'aujourd'hui** : 1,5 point sur un NQ à environ 30 900
(dernier cours des données), soit environ 0,5 pb. C'est pour information, pour lire le passé avec le coût actuel. Les critères
restent aux frais en points de chaque époque.

## 3. Résultats (30 septembre 2026)

`variantes.py` refait tout (`variantes.txt`). Chiffres : t des rendements quotidiens nets sur NQ.

| Variante | 2011-2016 | 2017-2022 | 2011-2022 | 2023-2026 | Aux frais d'aujourd'hui, 2011-2022 | Verdict |
|---|---|---|---|---|---|---|
| V0 zone d'origine | −2,62 | +2,77 | +0,62 | +2,01 | +3,38 | référence |
| **V1 données propres** | **−2,26** | **+2,78** | **+0,81** | **+2,00** | **+3,61** | **adoptée** |
| V2 un trade par jour | −0,72 | +2,42 | +1,48 | +1,48 | +3,61 | rejetée |
| V3 filtre GEX | −0,49 | +2,65 | +1,99 | +1,38 | +3,39 | rejetée |
| V4 achats seulement | −0,76 | +1,97 | +1,09 | +2,07 | +3,30 | rejetée |
| V5 stop sur le VWAP | −1,89 | +2,98 | +1,17 | +1,76 | +3,40 | rejetée |

Pourquoi les rejets :
- **V2, V3 et V4** sauvent 2011-2016 mais font moins bien sur 2017-2022.
- **V5** fait mieux sur les deux moitiés mais moins bien sur 2023-2026. Le t de sa différence avec V1
  y vaut −0,38.
- **V3 (GEX) est le piège typique** : t 1,99 sur 2011-2022, la meilleure sur le passé. Mais sur
  2023-2026, elle fait 1,38 contre 2,00 pour V1. Sans le tri, on l'aurait adoptée à tort.

Sur ES, V1 ne change rien (t −1,72) et toutes les variantes restent négatives sur 2023-2026.

**Ce qu'on retient** :
- **Correction adoptée** (V1, données propres), portée dans le robot et le script TradingView sur main.
  Le robot corrigé donne exactement le backtest corrigé : 2 287 jours de trade, écart nul.
- **Aucune « amélioration » ne tient** hors de l'échantillon. La zone telle que publiée, corrigée de
  la faille de données, reste la meilleure version connue.
- **Le vrai frein était les frais, pas la règle.** Aux frais d'aujourd'hui (0,5 pb avec le NQ à
  30 900), la version corrigée aurait fait t +3,61 sur 2011-2022, contre +0,81 aux frais de chaque
  époque. Le NQ vaut aujourd'hui 10 fois plus qu'en 2011, pour les mêmes 1,5 point de frais.
  L'avantage de la zone est plus régulier qu'il n'y paraissait, et les frais pèsent peu au prix
  actuel.
- **Les pertes viennent des allers-retours**, inhérents à une règle de suivi de tendance : trades
  coupés en 30 min, jours à plusieurs entrées. Les couper (V2) fait perdre les bonnes journées.
  C'est le prix du système.
