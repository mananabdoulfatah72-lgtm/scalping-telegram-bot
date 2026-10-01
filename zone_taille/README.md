# Zone de bruit NQ : la règle de taille, 1 MNQ minimum

**Faille trouvée** (revue du 1er octobre 2026, `zone/README.md` sur main) : la taille vaut
0,15 × marge / risque d'un MNQ, arrondie en dessous. Quand la marge passe sous environ 1 400 $, elle
donne 0 MNQ. Le compte ne trade plus, ne peut donc plus remonter, et reste bloqué pour toujours.
C'est pour cela que tant de tentatives « n'ont pas fini » dans l'étude du challenge.

**Changement demandé par l'utilisateur** : 1 MNQ minimum. Nombre de MNQ = max(1, arrondi inférieur
de 0,15 × marge / risque), au plus 50. Le changement est adopté à sa demande. Ce dossier mesure son
effet ; il ne décide pas.

## Ce qu'on mesure (fixé le 1er octobre 2026, avant tout calcul)

- Série : la zone corrigée V1 seule (sans le rebond), 1 MNQ, frais réels, calculée par le robot
  lui-même (`zone/robot.py` sur main, `serie_du_bot`) sur les données de la recherche.
- Comptes : la fonction `une_journee` du robot, avec ses règles Phidias 50K (challenge, puis compte
  financé avec retraits). Un compte perdu est remplacé par un nouveau challenge le lendemain.
- Départs : un par semaine. Chaque départ est suivi 12 mois (252 séances).
- On compare l'ancienne règle (0 MNQ possible) et la nouvelle (1 MNQ minimum) sur les mêmes départs.
- On rapporte, séparément pour les départs 2011-2021 et pour les départs 2023-2025 :
  - part des départs qui valident le challenge en 12 mois ;
  - nombre moyen de challenges commencés (chacun se paie) ;
  - part des comptes perdus ;
  - séances passées à 0 MNQ ;
  - argent reçu en 12 mois (80 % des retraits) : moyenne, médiane, part des départs à 0 $.
- Plus le rejeu unique du robot depuis le 30 décembre 2022, comme dans `zone/README.md`.

**À savoir** : 1 MNQ minimum veut dire qu'un compte proche de sa limite continue à trader. Il peut
remonter, ou sauter et recommencer un challenge payant. L'ancienne règle le laissait gelé, ce qui ne
rapporte rien non plus.

## Résultats (1er octobre 2026)

`taille.py` → `taille.txt` (lancer avec `ROBOT_ZONE=/chemin/zone/robot.py`).

| | Départs 2011-2021, ancienne | Départs 2011-2021, nouvelle | Départs 2023-2025, ancienne | Départs 2023-2025, nouvelle |
|---|---|---|---|---|
| challenge validé en 12 mois | 21 % | 32 % | 42 % | 67 % |
| challenges commencés | 1,23 | 1,85 | 1,00 | 1,88 |
| comptes perdus | 0,23 | 0,85 | 0 | 0,88 |
| séances gelées à 0 MNQ, sur 252 | 113 | 0 | 123 | 0 |
| reçu en 12 mois : moyenne, médiane | 29 $, 0 $ | 48 $, 0 $ | 83 $, 0 $ | 83 $, 0 $ |
| départs qui ne reçoivent rien | 97 % | 95 % | 93 % | 93 % |

- **L'ancienne règle gelait le compte près de la moitié du temps** : 113 et 123 séances sur 252.
  Elle ne perdait presque jamais de compte, parce qu'un compte gelé ne trade plus.
- **Avec 1 MNQ minimum, le challenge passe bien plus souvent** : 32 % au lieu de 21 %, et 67 % au
  lieu de 42 % pour les départs récents.
- **Le prix à payer** : environ 0,9 compte perdu de plus par an, donc autant de challenges à repayer.
- **L'argent reçu reste presque nul en 12 mois** (médiane 0 $). Après le challenge, le compte financé
  doit passer de 50 000 $ à plus de 52 600 $ avant tout retrait, avec 1 ou 2 MNQ, et la meilleure
  journée doit rester sous 30 % du gain de la période. Avec environ 2 900 $ par an et par MNQ sur
  2023-2026, cela prend souvent plus d'un an. C'est la limite suivante.

Rejeu unique du robot depuis le 30 décembre 2022 :
- **Ancienne règle :** challenge réussi le 8 juin 2023, puis compte financé gelé 245 séances.
- **Nouvelle règle :** même challenge réussi. Le compte financé saute le 23 janvier 2026, et le
  challenge suivant est à +3 494 $ au 25 septembre 2026.
- Aucun retrait dans les deux cas.

Porté dans `zone/robot.py` sur main (`MIN_MNQ = 1`) et dans le tableau de bord. Le compte virtuel en
cours ne change pas : il tradait déjà 1 MNQ.
