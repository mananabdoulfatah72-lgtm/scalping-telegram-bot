# Système de tendance multi-marchés

Système de suivi de tendance « à la CTA » sur 19 marchés futures (actions, taux, devises,
métaux, énergie, crypto), testé sur les vrais prix depuis 2007, puis rejoué sur les règles
d'un challenge Phidias Premium 50K.

## Fichiers

| Fichier | Rôle |
|---|---|
| `telecharger_donnees.py` | Télécharge les prix (lancé par le workflow `donnees-tendance.yml`) |
| `donnees/prix.csv.gz` | Historique quotidien (ETF, futures en continu, BTC/ETH, taux) |
| `systeme.py` | Signaux, tailles, coûts, backtest, optimisation des contrats entiers |
| `challenge_phidias.py` | Challenge Phidias Premium 50K démarré chaque semaine depuis 2008 |
| `rapport.py` | Reproduit tous les résultats ci-dessous (`python3 rapport.py`) |
| `robot.py` | Robot en argent virtuel : compte de 50 000 $, ordres chaque vendredi, résumé Telegram |
| `robot/` | État du compte virtuel (`etat.json`) et journal quotidien (`journal.csv`) |

## Réglages (fixés à l'avance, non optimisés)

- Signal : croisements de moyennes mobiles 16/64, 32/128, 64/256 jours (méthode EWMAC).
- Taille : risque égal par marché, les 6 familles pèsent autant.
- Rééquilibrage : chaque vendredi, avec une marge de 10 % pour éviter les petits ordres.
- Rendements « futures » : ETF moins le taux court ; BTC/ETH moins 7 %/an de coût de portage.

## Résultats (septembre 2026)

**Système idéal, positions divisibles à l'infini (2007–2026) :** Sharpe 0,56, +10,9 %/an pour
un risque de 19,5 %/an, pire baisse −36 %, 65 % d'années positives.
Robuste aux réglages (Sharpe 0,46 à 0,65), aux coûts ×3 (0,47) et au retrait d'une famille
(0,44 à 0,62). Mais 2023–2026 est négatif (Sharpe −0,16).

**Est-ce vraiment la tendance ?** Un portefeuille qui achète tout, tout le temps (même risque par
marché) fait aussi un Sharpe de 0,56, mais les deux ne sont presque pas corrélés (0,03) : la
tendance gagne en 2008 (+19 %) et 2022 (+18 %) quand l'achat perd. Test du hasard : des positions
décalées au hasard dans le temps, avec le même biais acheteur, font en moyenne 0,35, et 16,5 %
d'entre elles font aussi bien que le vrai système. Le « timing » ajoute environ +0,2, sans preuve
solide. Le mélange 50/50 tendance + achat fait 0,78, positif dans chaque période (0,37 sur
2023–2026), pire baisse −19 % à 12 % de risque.

**Compte 50K :** un seul contrat micro S&P, Nasdaq, or, argent ou Bitcoin peut perdre plus que
la marge de 2 500 $ en une journée de krach. Sans ces marchés, il reste 14 marchés dont le
Sharpe tombe à 0,16.

**Challenge Phidias Premium 50K (vrais prix, départ chaque semaine depuis 2008) :**
8 à 23 % d'évaluations réussies en 2 ans, 7 à 17 % perdues ; une fois financé,
50 à 210 $/an versés en moyenne.
Borne haute avec des contrats infiniment petits : environ 31 % de réussite.

**Conclusion :** le système est réel et robuste, mais un compte de 50 000 $ avec une marge
de 2 500 $ est trop petit pour lui : les contrats micro de la CME sont trop gros.

## Robot en argent virtuel

Le workflow `robot-tendance.yml` lance `robot.py` chaque soir de semaine à 22 h 30 UTC :
valorisation du compte virtuel, nouvelles positions le vendredi (contrats micro entiers
optimisés pour la taille du compte), suivi d'un challenge Phidias 50K virtuel, et résumé
envoyé sur Telegram (secrets `TELEGRAM_TOKEN` et `CHAT_ID`). Aucun ordre réel n'est passé.

Les contrats de taux micro (2YY, 10Y, 30Y) sont cotés en taux : les messages donnent le sens
de l'ordre sur ces contrats, qui est l'inverse du sens sur les obligations.
