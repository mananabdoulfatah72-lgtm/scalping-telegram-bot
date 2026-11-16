# Usine à stratégies pour le compte Bulenox

La méthode de l'article « La bonne façon d'utiliser Fable 5.2 », appliquée au compte Master Bulenox 50K (futures CME,
NQ et MNQ). Demande de l'utilisateur du 16 novembre 2026 : un système qui aide à sauver le compte.

- **Résultats :** [TABLEAU.md](TABLEAU.md). Page interactive (privée, à partager depuis son menu) : https://claude.ai/artifact/VU8EHCGWSy5NxGyTQDmh3A ; sa source est `tableau/page.html`, ses données `tableau/*.json`.
- **Règles, fixées avant le premier calcul :** [REGLES.md](REGLES.md).
- **Couche de risque :** [RISQUE.md](RISQUE.md).
- **Ce que font les logiciels des institutions, et les tests du 16 novembre au soir :** [INSTITUTIONS.md](INSTITUTIONS.md)
  (bande large, secours sur MES sous le frein, mesure du glissement réel).

## Ce que dit le premier calcul (16 novembre 2026)

Sept idées testées, chacune avec son avantage et la contrepartie qui perd en face.

| Idée | Verdict |
|---|---|
| Zone de bruit (le Bot 3 en 1) | **Passe les 5 portes.** Porte 2 de justesse : 9 permutations sur 1 000 font aussi bien. Sa marche en avant 2015 → 2026 n'est battue par aucune des 200 permutations. |
| Supertrend NQ | Rejeté à la porte 2 (p = 4 %). Sa marche en avant ne bat pas le hasard (p = 23,5 %). |
| Momentum de la première demi-heure | Rejeté à la porte 2 (p = 2,8 %) |
| ORB, cassure de la veille, fade du gap, fin de séance | Rejetés à la porte 1 : trop faibles, ou un pic isolé |

**Pourquoi le Supertrend échoue.**
- La permutation garde le mouvement de chaque journée (ouverture → clôture) et ne mélange que l'ordre des minutes.
- Un bot de tendance qui ne fait que suivre le mouvement du jour gagne autant sur les minutes mélangées. C'est le cas du
  Supertrend.
- La zone, elle, exploite l'ordre des minutes : elle bat les permutations.
- Sur le compte, le Supertrend reste utile comme secours contre la règle d'inactivité, pas comme source de gain prouvée.

**Ce que ça donne sur le compte (porte 5), zone avec le Supertrend en secours, 1 MNQ :**
- Master neuf, sur un an : environ 55 % de premiers retraits et 32 % de comptes perdus.
- Depuis une marge de 700 $, sur un mois : environ 4 comptes sur 10 perdus, et +300 $ de gain moyen.

## La méthode de l'article, et ce qui change ici

| L'article | Ici |
|---|---|
| QuantPilot fait les backtests | **Pas QuantPilot** : il trade de la crypto (Hyperliquid, Binance, Bybit), pas les futures CME du compte, et il n'est pas connecté. Le moteur déterministe du projet (`moteur.py`, numba) fait tous les calculs, contrôlé contre les moteurs déjà vérifiés (`valider.py`). |
| Le modèle ne calcule jamais | Claude écrit les règles, choisit les idées, lit les résultats ; il ne calcule aucun chiffre lui-même. |
| Mesure à chaque barre | Rendement net de chaque minute, frais compris. |
| Porte 1 : excellence sur 4 ans | 2011 - 2014, plateau exigé, réglage choisi au milieu du plateau. |
| Porte 2 : 1 000 permutations, p < 1 % | Oui. Minutes mélangées à l'intérieur de chaque séance (écarts et formes séparément). |
| Porte 3 : marche en avant, ré-optimisation tous les 30 jours | Oui, de 2015 à la dernière séance. |
| Porte 4 : permutation de la marche en avant | 200 permutations ; p < 1 % (plus de 2 ans hors échantillon). |
| — | **Porte 5 ajoutée : le compte Bulenox** (plancher, règle d'inactivité, limites du jour), depuis un Master neuf et depuis ta marge. |
| Registre des idées | `registre.csv` : chaque idée, résultat et rejet, avec sa raison. |
| Tableau de bord | `TABLEAU.md`, et une page publiée depuis la session Claude. |
| Chaque nuit, brief du matin | `.github/workflows/usine.yml` : brief à 7 h 15 (Paris) du mardi au samedi, toutes les portes refaites le dimanche. |
| Couche de risque, arrêt d'urgence | `consigne.py` et `RISQUE.md`. |

**Ce que les tests ne corrigent pas.** Le projet a déjà regardé 2011 - 2026 pour choisir la zone. Les p-values contrôlent
le choix du réglage, pas celui de l'idée. La seule donnée vraiment neuve, c'est l'avenir.

## Utiliser l'usine

```bash
pip install numpy pandas numba requests
git fetch --depth=1 origin claude/keen-babbage-r686cl
git show FETCH_HEAD:intraday/donnees/nasdaq100_1min.csv.gz > /tmp/nasdaq100_1min.csv.gz
export KB_MINUTES=/tmp/nasdaq100_1min.csv.gz
python3 usine/valider.py                    # le moteur contre les moteurs deja verifies
python3 usine/portes.py                     # les 5 portes pour les 7 idees (environ 4 minutes sur 4 coeurs)
python3 usine/tableau.py                    # TABLEAU.md et tableau/donnees.json
python3 usine/brief.py                      # le brief du matin et la consigne du compte
```

**Ajouter une idée.**
1. L'écrire dans `REGLES.md` (avantage, contrepartie, règle exacte, grille), puis commiter **avant** de calculer.
2. Ajouter son noyau dans `moteur.py`.
3. La nuit suivante, `portes.py --nouvelles` la fait passer par les portes. Le tableau et le brief la montrent le matin.

**Ton compte dans le brief.** Après la clôture (22 h, heure de Paris), envoie au bot Telegram, par exemple :
- `solde 49900` : le solde de fin de journée ;
- `solde 49900 haut 51700` : le premier jour, ou si le plus haut de fin de journée change ;
- `solde 49900 sans` : si tu n'as fait aucun trade ce jour-là.

Le brief du matin donne alors :
- le bot de la séance (Bot 3 en 1, ou Supertrend en secours) ;
- le frein, les limites ;
- le voyant (réel contre historique) ;
- une décision pour toi.

L'état du compte reste dans le cache de GitHub. Il n'est jamais commité ni imprimé dans les journaux : le dépôt est
public.

**Activer la nuit.** GitHub ne lance les tâches planifiées que depuis la branche principale (`main`). Il faut donc fusionner
cette branche pour que le brief parte chaque matin.

## Ce que ce système peut et ne peut pas faire

Il peut :
- tester chaque idée de la même façon et tuer celles qui doivent leur résultat à la chance ;
- dire ce que chaque idée ferait sur le compte Bulenox ;
- donner chaque matin la consigne du compte, et alerter quand le réel s'écarte de l'historique.

Il ne peut pas :
- garantir un gain, ni transformer une idée faible en avantage ;
- rendre neuves des données déjà testées ;
- rendre sûr un compte à 700 $ du plancher : c'est la marge qui manque, pas une règle.
