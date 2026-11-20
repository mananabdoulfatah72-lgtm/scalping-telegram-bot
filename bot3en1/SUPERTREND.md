# Supertrend NQ : la stratégie (2 novembre 2026)

Stratégie Quantower à part, indépendante du bot 3 en 1. Elle s'installe avec la même ligne PowerShell et apparaît dans
le Strategies manager sous le nom **Supertrend NQ (10-3, 5 min)**.

## Ce qu'elle fait

- Bougies de 5 minutes du NQ, de 15 h 30 à 22 h (heure de Paris), l'indicateur continuant d'une séance à l'autre.
- **ATR** = amplitude moyenne des 10 dernières bougies (méthode de Wilder) ; la **ligne du Supertrend** est à 3 ATR du prix
  (environ 124 points en octobre 2026) : sous le prix en tendance haussière, au-dessus en tendance baissière.
- À la clôture de chaque bougie, la position suit le sens du Supertrend : **achat** si la ligne est sous le prix, **vente**
  si elle est au-dessus. Quand une bougie clôture de l'autre côté de la ligne, la position se **retourne** (un seul ordre).
- Première position à 15 h 35, plus de nouvelle position après 21 h 30, **tout est fermé à 21 h 55** (heure de Paris).
- Ordres au marché sur MNQ (prix lus sur le NQ).

## Vérifications

- Le moteur C# (`Supertrend.Core`) refait **exactement** les 9 628 trades du test sur 15 ans (`audit/machine6/supertrend.py`,
  règle H12 de `scalping/partie_h.py`) : mêmes jours, mêmes sens, mêmes minutes, mêmes prix (`Supertrend.Replay`).
- La stratégie Quantower (`Supertrend.TestQuantower`, imitation de l'API) passe les mêmes ordres que le moteur sur 64
  séances (août - octobre 2026, 0 différence), à 1 et 2 MNQ, et réagit comme prévu : limite du jour, objectif, fichier
  STOP, position fermée à la main (pas rouverte avant le prochain retournement), relance en pleine séance (position reprise).

## Le frein : ordres sur MES (16 novembre 2026)

Choisi par l'utilisateur pour sa situation (marge d'environ 700 $), après le test R de `usine/INSTITUTIONS.md` : depuis
700 $ de marge, 16 % de comptes perdus dans le mois au lieu de 25 % quand le secours passe aussi sur MES.

**Les réglages.**
- « Frein : ordres sur MES au lieu de MNQ » : à cocher les jours de secours où le brief du matin dit que le frein est actif
  (marge sous 1 750 $).
- « MES (ordres quand le frein est coché) » : le contrat du moment, par exemple MESZ6.
- Le reste ne change pas : le Supertrend lit toujours le NQ, les ordres partent sur MES, la limite du jour reste en
  dollars (400 $).

**Comment le résultat est compté sur MES.**
- 5 $ par point du S&P et 4,50 $ de frais par aller-retour (1 $ par ordre et 1 tick).
- Prix d'entrée et de sortie : le dernier prix du MES quand le Supertrend change de position.
- Après une relance avec une position ouverte : le prix d'entrée du compte (propriété `OpenPrice` de Quantower, lue par
  réflexion). S'il est illisible, le premier prix du MES reçu sert, et la perte latente d'avant la relance n'est pas
  comptée dans la limite du jour.

**Testé ici** (`Supertrend.TestQuantower`, imitation de l'API Quantower, minutes réelles du NQ et du S&P) :

| Essai | Résultat |
|---|---|
| Ordres sur MNQ, 65 séances (août - octobre 2026) | 209 changements de position, 0 différence avec le moteur vérifié : rien n'a changé |
| Ordres sur MES, 40 séances (août - 25 septembre 2026) | 130 changements de position, 0 différence ; 130 ordres sur MES, 0 sur MNQ ; le résultat annoncé chaque soir égale celui des remplissages du test, les 40 séances |
| MES, limite du jour à 150 $ | la limite se déclenche entre −150 $ et −178 $ (le test n'envoie que 4 prix par minute) |
| MES, relance à 12 h avec une position ouverte | position reprise sur MES, 0 différence |

**Pas testé ici :** le vrai Quantower (seulement son imitation), la propriété `OpenPrice`, et les vrais remplissages du MES.

## Deux options : le renfort et l'arrêt après une bougie folle (20 novembre 2026)

Deux cases dans les réglages, **décochées par défaut** (le bot reste alors exactement le même) :
- « **Renfort** » : quand une clôture de 5 minutes est à 1 ATR ou plus en gain depuis l'entrée, le bot ajoute 1 contrat
  (Taille contrats de plus), une seule fois par trade, jamais après 15 h 30, et le garde jusqu'à la sortie du Supertrend.
  C'est le « scalpeur qui s'empile » du bureau de 6 agents. Il ne joue pas quand le frein (MES) est coché.
- « **Arrêt après une bougie folle** » : si une bougie de 5 minutes est plus grande que 3 fois l'ATR de la bougie d'avant,
  le bot ferme la position et ne trade plus jusqu'au lendemain (l'agent « actualités »).

**Ce que ça aurait donné** (1 MNQ de base, limite du jour, frais compris ; `usine/renfort_st.py`, `usine/comparaison_mois.py`) :

| Version | 13 oct. - 19 nov. 2026 | Par an, 2015 - 2026 | Par an depuis 2023 | 22 séances depuis 52 000 $ (plancher 50 100 $), départs depuis 2023 : retrait / compte perdu |
|---|---|---|---|---|
| Supertrend seul, limite 400 $ | +4 849 $ | +4 435 $ | +1 567 $ | 35 % / 22 % |
| Supertrend seul, limite 300 $ | +4 175 $ | +4 516 $ | +2 895 $ | 32 % / 14 % |
| Renfort + bougie folle, limite 400 $ | +9 989 $ | +8 455 $ | +5 025 $ | 47 % / 36 % |
| Renfort + bougie folle, limite 300 $ | +9 214 $ | +6 593 $ | +4 527 $ | 46 % / 31 % |
| Pour comparer : 2 MNQ tout le temps, limite 400 $ | +9 697 $ | +8 870 $ | +3 135 $ | 46 % / 50 % |

Le renfort gagne plus que le Supertrend 8 années sur 12 (écart quotidien t +2,43 sur 2015 - 2026) : il n'ajoute un
contrat qu'aux trades qui marchent, ce qui gagne autant que doubler la taille avec moins de risque. Mais il reste du
levier : **avec 1 900 $ de coussin, le risque de perdre le compte en un mois passe de 14 - 22 % à 31 - 36 %**, contre
une chance de retrait qui passe de 32 - 35 % à 46 - 47 %. Ces règles n'ont pas été fixées d'avance dans l'usine : c'est une
mesure à la demande, pas une validation.

**À quoi s'attendre chaque mois** (mois civils de janvier 2015 à octobre 2026, 142 mois, 1 MNQ de base) :

| Version | Mois moyen | Mois médian | Mois positifs | Mois à +9 000 $ ou plus | Pire mois | 5 séances à −1 900 $ ou pire |
|---|---|---|---|---|---|---|
| Supertrend seul, limite 400 $ | +341 $ | +181 $ | 56 % | 0 sur 142 | −3 822 $ (juin 2022) | 1,4 % des semaines |
| Renfort + bougie folle, limite 400 $ | +661 $ | +291 $ | 55 % | 2 sur 142 | −6 718 $ (mars 2020) | 4,7 % des semaines |
| Renfort + bougie folle, limite 300 $ | +501 $ | +293 $ | 54 % | 1 sur 142 | −4 618 $ (mars 2020) | 0 % des semaines |

Les 27 séances du 13 octobre au 19 novembre 2026 (+10 392 $ avec renfort, limite 400 $) font mieux que 99 % de toutes les
périodes de même longueur depuis 2015. Juste avant, juillet à septembre 2026 : −2 945 $, −2 343 $, −1 042 $ avec renfort
(limite 400 $).

**Vérifications** : le moteur C# refait exactement les trades du calcul Python, jambe par jambe, sur les mêmes minutes
(13 octobre - 18 novembre, 4 versions : 61, 92, 55 et 83 jambes identiques) ; la stratégie Quantower (imitation de
l'API) donne 0 différence sur 27 séances avec chaque option, avec 2 contrats de base, et avec le frein MES ; la limite du
jour se déclenche avec le renfort (vers −326 à −360 $ pour 300 $ dans le test, qui n'envoie que 4 prix par minute).

## Les chiffres (1 MNQ, au prix d'aujourd'hui, 3 $ de frais par aller-retour)

| Période | Séances | Par séance | t |
|---|---|---|---|
| 2011 - 2026 | 3 940 | +27,0 $ | 2,79 |
| 2011 - 2022 | 2 989 | +29,8 $ | 2,67 |
| 2023 - 2026 | 951 | +18,2 $ | **0,94** |

- 2,4 trades par séance, 42 % de trades gagnants (les gagnants sont plus grands que les perdants), une séance sur deux
  gagnante. Années perdantes : 2013, 2016, 2017.
- Le **t** mesure si le gain moyen est plus grand que le hasard : au-dessus de 2 à 3, le gain a peu de chances d'être de la
  chance. Sur 15 ans il fait 2,79 ; depuis 2023 il ne fait que 0,94 : le gain continue, mais il est devenu trop petit par
  rapport aux variations pour être sûr qu'il n'est pas dû au hasard.
- Challenge Bulenox depuis 50 000 $ avec un plancher à 49 000 $ suivi en temps réel (8 séances,
  `audit/machine6/resultats/supertrend.txt`) : 1 MNQ 3 à 8 % réussis / 32 à 46 % échoués ; 2 MNQ 14 à 22 % / 63 à 74 % ;
  4 à 6 MNQ environ 20 % / 77 à 80 %. Avec peu de marge au-dessus du plancher, elle est plus risquée que la zone.

## Réglages à remplir

| Réglage | Valeur |
|---|---|
| Compte | le compte qui tradera le Supertrend (**jamais le même que le bot 3 en 1 en même temps**) |
| NQ (prix et barres) | NQZ6 (contrat du moment) |
| MNQ (ordres) | MNQZ6 (même échéance) |
| MNQ par trade | **1** |
| Limite de perte du jour | **400** (par défaut) ; tout est fermé et plus de trade jusqu'au lendemain |
| Objectif | solde à atteindre (53 000 sur un challenge 50K), 0 sur un compte financé |
| Supertrend : ATR / multiple | **10 et 3** (seuls réglages testés : ne pas changer) |
| Dossier | C:\SupertrendNQ |
| Telegram | jeton et numéro de conversation (facultatif) |

## À savoir

- **Un compte, une stratégie.** La stratégie aligne la position MNQ du compte sur la sienne : si le bot 3 en 1 tourne sur le
  même compte, ils se ferment mutuellement leurs positions. De même, un trade manuel en MNQ sur ce compte est fermé.
- **La lancer avant 15 h 30 (heure de Paris).** Lancée plus tard, elle rejoue la séance sans ordre ; si sa position est déjà
  sur le compte, elle la reprend, sinon elle attend le prochain retournement (pas d'entrée au milieu d'une tendance).
- Position fermée à la main ou fichier `C:\SupertrendNQ\STOP` : position fermée, pas de nouvelle position dans le même sens
  avant le prochain retournement. Arrêter la stratégie ferme aussi la position.
- Journal : `C:\SupertrendNQ\journal.txt` ; état (résultat du jour, limite, objectif) : `C:\SupertrendNQ\etat.json`.
- Messages Telegram : lancement, chaque achat, vente et sortie (points et $), limite du jour, objectif, fin de séance,
  alertes (flux NQ coupé, symbole d'une autre échéance).
