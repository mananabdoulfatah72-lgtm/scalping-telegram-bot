# Couche de risque du compte Master Bulenox (partie 5 de l'article)

Règles appliquées chaque jour par `consigne.py` et envoyées dans le brief du matin. Elles viennent des portes de l'usine
(`TABLEAU.md`) et des calculs du 16 novembre 2026 (stops et limites de 200, 300 et 400 $ ; frein ; secours).

## Les règles

| Règle | Valeur | Pourquoi |
|---|---|---|
| Taille | **1 MNQ** ; la zone passe sur **1 MES** tant que la marge est sous 1 750 $ (réglage « Frein » = 750) | À 2 ou 4 MNQ, les Masters sont perdus beaucoup plus souvent (porte 5, `detail_g2`). |
| Un seul bot à la fois | Bot 3 en 1 chaque jour. Après 2 séances de suite sans trade, la séance suivante : **Supertrend NQ seul** (G2 manuel) | La zone seule perd 97 % des Masters par la règle d'inactivité. Deux bots ensemble sur le compte se ferment mutuellement leurs positions. |
| Perte maximale par trade | Pas de stop séparé | Les stops de 200 et 300 $ ne protègent presque pas le compte et coûtent 15 à 30 % du gain (calcul du 16 novembre). |
| Perte maximale du jour | **1 000 $** pour le Bot 3 en 1, **400 $** pour le Supertrend (Bulenox : 1 100 $) | Plus bas, la limite coupe les journées qui paient les autres. |
| Positions ouvertes | 1 au plus (MNQ ou MES) ; jamais de trade à la main sur le même compte | Le bot réaligne la position du compte sur la sienne. |
| À plat | Avant 16 h 59 (New York) : les bots le font seuls | Règle Bulenox. |

## L'arrêt d'urgence

**Comment :**
- Bot 3 en 1 : créer le fichier `C:\Bot3en1\STOP`.
- Supertrend NQ : créer le fichier `C:\SupertrendNQ\STOP`.

Dans les deux cas, la position est fermée et le bot ne reprend plus.

**Quand :**
- **Voyant rouge.** Le gain réel depuis le début du suivi passe sous la ligne des 5 % de ce qu'attend l'historique de la
  configuration jouée (G2 manuel, 2015 → aujourd'hui). Le brief le signale. On cherche la cause avant de reprendre :
  données, glissement, marché qui change.
- **Le bot signale un problème qu'il ne règle pas seul** : aucune transaction NQ reçue, solde illisible, mauvais
  contrat après un changement d'échéance.

**Ce que l'arrêt d'urgence ne fait pas.** Il ne sauve pas un compte proche du plancher. Un compte arrêté finit perdu par
la règle d'inactivité au bout de 5 séances sans trade. Avec 700 $ de marge, la porte 5 estime qu'environ 4 comptes sur 10
sont perdus dans le mois avec G2. Aucune règle de cette page ne rend ce risque petit : c'est la marge qui manque.

## Les alertes du brief

- **4 séances de suite sans trade** : un trade est obligatoire à la séance suivante, sinon le compte est perdu.
- **Marge plus petite que la limite du jour** : une seule mauvaise séance peut coûter le compte. Le brief le rappelle.
- **La zone ne passe plus les portes** (nouvelle vérification de chaque dimanche) : réduire à 1 MES en attendant la
  revue.

## La revérification de chaque semaine

Chaque dimanche, l'usine refait toutes les portes de la zone et du Supertrend avec les minutes les plus récentes. Une
stratégie en service qui échoue retourne au labo.

## Le parcours d'une nouvelle stratégie (de l'usine au réel)

| Étape | Condition pour passer à la suivante |
|---|---|
| **Papier** | 2 semaines au moins, chaque trade noté (robot virtuel GitHub ou compte de simulation Quantower) |
| **Accord** | Les résultats papier restent dans la fourchette de la marche en avant |
| **Petit réel** | 1 MES sur le compte, plusieurs semaines propres |
| **Taille normale** | 1 MNQ, seulement après ces semaines |

Aucune nouvelle stratégie n'a encore passé les 5 portes de l'usine (calcul du 16 novembre 2026). La zone, déjà en
service, est la seule qui passe.
