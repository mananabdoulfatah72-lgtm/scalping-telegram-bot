# Audit des pertes du bot 3 en 1 (séances du 13 au 30 octobre 2026)

Demandé par l'utilisateur les 31 octobre et 1er novembre 2026. Pour chaque perte, quatre réponses :
1. les conditions exactes qui ont déclenché le trade ;
2. si la perte était évitable avec ce que le bot savait au moment de décider ;
3. la règle responsable ou le filtre manquant ;
4. une correction précise pour que le même scénario ne se répète pas.

**Règle d'adoption.** Une correction n'entre dans le bot que si, sur 15 ans de NQ (2011 - 2026), elle évite plus de
pertes qu'elle ne retire de gains, sans baisser la plupart des périodes. Le protocole est fixé avant les calculs
(annexe A). Une correction qui ne passe pas aurait évité la perte de la semaine passée, mais elle ferait perdre plus
dans les semaines suivantes.

Les erreurs de logique, de réglage et d'opération sont corrigées tout de suite : elles ne dépendent pas du marché.

## En bref

| Jour | Résultat du jour sur le compte | Pertes de la journée | Évitable ? |
|---|---|---|---|
| 14 oct. | +988 $ | réouverture de la vente par le bot après ta fermeture à la main (environ −180 $) | **oui** : défaut de logique, **corrigé** |
| 20 oct. | −1 077 $ | achat 10 h 30, limite du jour | non |
| 21 oct. | −1 019 $ | achat 13 h (−272 $), puis achat 14 h 30, limite du jour (environ −740 $) | non |
| 22 oct. | +1 809 $ | — | — |
| 23 oct. | −119 $ | achat 11 h | non |
| 26 oct. | −994 $ | achat 11 h, limite du jour | non |
| 27 oct. | +933 $ | — (relance du bot qui a fermé sa position : défaut de logique, favorable ce jour-là, **corrigé**) | — |
| 29 oct. | −706 $ | vente à la cassure, stop de 70 points (réglages modifiés) | **oui** : réglages, **corrigé** |

- **Solde du compte.** Du 14 au 29 octobre, le bot a fait −185 $ (50 000 $ → environ 49 815 $). Les trades du
  30 octobre (10 et 13 MNQ) ne viennent pas du bot : ils ne sont pas dans son journal.
- **Pertes évitables : environ 886 $.** Il y a le 29 octobre (−706 $, réglages du 26 - 27 octobre) et la réouverture
  du 14 octobre (environ −180 $). Les deux causes sont corrigées.
- **Pertes non évitables : 3 209 $** (20, 21, 23 et 26 octobre). Ce sont des pertes normales de la zone :
  - le prix est reparti contre le trade dès l'entrée, et aucun de ces trades n'a été en gain de plus d'un quart de
    largeur de bande ;
  - sept corrections précises ont été écrites pour elles, puis testées sur 15 ans (C1 à C7). Toutes retirent plus de
    gains qu'elles n'évitent de pertes ;
  - le relecteur indépendant les situe entre le 75e et le 85e centile des pertes de la zone. Trois jours comme ça en
    six séances arrivent environ une fois sur onze.
- **Ce qui fait qu'une perte normale coûte 1 000 $, c'est la taille.** Avec 4 MNQ, 125 points de NQ font la limite de
  perte du jour. Voir « Le compte » plus bas.

## Les pertes, une par une

### 14 octobre, réouverture de la vente par le bot à 12 h 35 (environ −180 $, journée à +988 $)

1. **Conditions exactes.**
   - Vente de zone à 11 h 30 à 30 392,75 (delta 30 min −313).
   - À 12 h 35, tu as racheté les 4 MNQ à la main (+1 178 $).
   - Le bot a vu sa position revenir à 0 et l'a revendue aussitôt. Son journal note « ordre envoye : vente 4 MNQ
     (position 0 -> -4) » à 12 h 35.
   - Tu as arrêté le bot à 12 h 39.
2. **Évitable ?** Oui. Le bot savait que la position avait disparu sans ordre de sa part.
3. **Règle responsable.** L'alignement de la position. Le bot remettait toujours sur le compte la position de son
   moteur, sans règle pour une fermeture faite à la main.
4. **Correction (faite, testée).** Le bot ne rouvre plus une position fermée hors de lui.
   - Le trade est compté comme terminé, et la zone attend que le prix revienne dans la bande.
   - Pour ne pas confondre avec une coupure Rithmic (qui vide aussi la liste des positions), la fermeture n'est
     retenue que si la position reste à 0 pendant 30 s alors que des prix NQ arrivent.
   - Si la position revient telle quelle (coupure), le bot reprend son trade.
   - Rejeu du 14 octobre : l'ancien bot revend à 12 h 36, le nouveau ne revend pas.

### 20 octobre, achat à 10 h 30 : −1 077 $ (limite de perte du jour)

1. **Conditions exactes.**
   - Contrôle de 10 h 30 : prix 29 879,00, achat au-dessus de 29 820,62, VWAP 29 614,78, delta 30 min +3 972.
   - Le prix est 0,59 largeur de bande au-delà du niveau. Il est aussi **2,7 largeurs de bande au-dessus du VWAP**,
     après **+240 points en 30 minutes**.
   - Niveau de sortie à 29 820,62, à 58 points. 4 MNQ.
   - Le trade n'a jamais gagné plus de 18 points. À 11 h, il est encore au-dessus de la sortie (29 864,25).
   - Le NQ chute de 93 points dans la minute de 11 h 12 : la limite du jour ferme tout (estimation du bot −1 002 $).
2. **Évitable ?** Non avec ce que le bot savait.
3. **Filtre manquant possible.** « Pas d'achat juste après un pic, trop loin du VWAP. »
   - Une sortie vérifiée à chaque minute (C5) n'aurait rien changé : la chute tient dans une seule minute.
4. **Correction testée : C7, pas d'entrée à plus de 2 largeurs de bande du VWAP.**
   - Elle évite cette perte.
   - Sur 15 ans, elle fait +77 028 $ au lieu de +79 847 $, moins bien sur 2019 - 2022 et 2023 - 2026, et elle retire
     plus de gagnants que de perdants : **rejetée**.
   - **Exécution (classe E) :** la sortie a glissé d'environ 8,75 points (environ −70 $). La limite attend 3 s de
     confirmation pour ne pas fermer sur une lecture fausse du solde, et la minute était très rapide. Pas de
     correction : sans cette attente, une lecture fausse fermerait des trades à tort.

### 21 octobre, achat à 13 h : −272 $

1. **Conditions exactes.**
   - Contrôle de 13 h : prix 30 079,50, achat au-dessus de 30 029,56, VWAP 29 918,41.
   - Delta 30 min **+239 (faible)**, dépassement 0,32. 4 MNQ.
   - Sortie par la règle au contrôle de 14 h à 30 047,00 (−32,5 points). Le trade a gagné au mieux +34 points.
2. **Évitable ?** Non : la règle a coupé la perte au premier contrôle défavorable.
3. **Filtre manquant possible.** Un delta trop faible pour confirmer.
4. **Correction testée : C3, delta d'au moins 300 contrats.** Sur avril - octobre 2026, elle retire autant de gains
   que de pertes (+795 $ contre −748 $) : **rejetée**.

### 21 octobre, achat à 14 h 30 : environ −740 $ (limite de perte du jour, journée à −1 019 $)

1. **Conditions exactes.**
   - Contrôle de 14 h 30 : prix 30 088,00, achat au-dessus de 30 058,36, VWAP 29 940,48.
   - Delta **+115 (faible)**. C'est **le deuxième achat de la journée, 30 minutes après la sortie perdante** de 14 h.
   - Le trade n'a jamais gagné plus d'1 point. Limite du jour à 14 h 51.
2. **Évitable ?** Non avec une règle qui tient sur 15 ans.
3. **Filtre manquant possible.** Le piège du bruit : une nouvelle entrée dans le même sens juste après une perte.
4. **Corrections testées :**
   - **C2, pas de nouvelle entrée dans le même sens après une sortie perdante.** Sur 15 ans, +68 332 $ au lieu de
     +79 847 $, moins bien sur 2019 - 2026 : **rejetée**.
   - **C3, delta d'au moins 300 contrats :** **rejetée** (voir plus haut).
   - **C5, sortie dès qu'une minute clôture sous le niveau de sortie.** Elle aurait coupé vers −35 points à 14 h 47,
     soit environ −300 $ au lieu de −740 $. Mais sur 15 ans, elle fait moins bien sur les trois périodes (le piège du
     bruit à la minute) : **rejetée**.

### 23 octobre, achat à 11 h : −119 $

1. **Conditions exactes.**
   - Contrôle de 11 h : prix 29 283,25, achat au-dessus de 29 263,90, VWAP 29 139,21.
   - Delta +750, dépassement 0,16.
   - Sortie par la règle au contrôle de 11 h 30 à 29 261,00 (−22 points).
2. **Évitable ?** Non.
3. **Règle responsable.** Aucune : la règle a fait ce qu'elle doit, et la perte est petite.
4. **Correction.** Aucune.

### 26 octobre, achat à 11 h : −994 $ (limite de perte du jour)

1. **Conditions exactes.**
   - Contrôle de 11 h : prix 29 554,75, achat au-dessus de 29 353,90, VWAP 29 312,44.
   - Delta +1 902. **Dépassement 1,63** : l'entrée a lieu 200 points au-delà du niveau, donc tard.
   - Le niveau de sortie est **à 201 points**, plus loin que la limite du jour (125 points avec 4 MNQ). Le trade ne
     pouvait pas sortir par sa règle avant d'être coupé.
   - Il n'a jamais gagné plus de 17 points. Limite du jour à 12 h 43.
2. **Évitable ?** Non avec une règle qui tient sur 15 ans.
3. **Filtres manquants possibles.** L'entrée tardive, et un niveau de sortie plus loin que la limite du jour.
4. **Corrections testées :**
   - **C1, pas d'entrée à plus d'une largeur de bande au-delà du niveau.** Sur 15 ans, +63 830 $ au lieu de
     +79 847 $, moins bien sur les trois périodes : **rejetée**. Les entrées tardives gagnent en moyenne : ce sont
     les journées de forte tendance.
   - **C6, taille réduite pour que la perte jusqu'au niveau de sortie ne dépasse pas 500 $.** Ce jour-là, elle
     aurait pris 1 MNQ au lieu de 4. Sur 15 ans, elle fait moins bien sur les trois périodes, et elle aurait aussi
     coupé de moitié le gagnant du 22 octobre : **rejetée**.

### 29 octobre, vente à 10 h 10 : −706 $ (stop de 70 points)

1. **Conditions exactes.**
   - Réglages du 27 octobre : entrée à la cassure entre deux contrôles, stop de 70 points, pas de sortie aux
     contrôles, filtre delta décoché.
   - Vente à la cassure de 10 h 10 à 29 517,00 (delta −133).
   - Stop touché à 10 h 17 à 29 605,50.
2. **Évitable ?** Oui. La zone d'origine ne prend aucun trade ce jour-là. Le relecteur l'a vérifié sur les minutes
   Rithmic de toute la séance, avec et sans le filtre.
3. **Règle responsable.** Les réglages modifiés : l'entrée à la cassure entre deux contrôles, avec un stop fixe.
4. **Correction (faite).** Les réglages par défaut sont revenus à la zone d'origine. Sur 15 ans, les réglages du
   26 - 27 octobre font +10 339 $ contre +79 847 $ pour la zone d'origine (annexe C).

### Ce qui n'est pas une perte, mais compte

- **22 octobre.** Le bot a été arrêté à la main à 14 h 02 (+1 809 $ sur le compte). Gardée jusqu'à 16 h, la vente
  faisait environ +1 468 $.
- **27 octobre.** Relancé à 11 h 50 sans avoir été arrêté, le bot a fermé sa propre position (+933 $, favorable ce
  jour-là). C'est un défaut de logique, **corrigé** : le trade est maintenant repris s'il est encore sur le compte. Si
  Quantower n'a pas encore chargé les positions, le bot attend 60 s, sans ordre, avant de décider.
- **30 octobre.** Les trades de 10 et 13 MNQ ne viennent pas du bot. La zone d'origine n'aurait rien pris ce jour-là
  (deux ventes écartées par le filtre).

## Le compte : ce qui fait qu'une perte normale coûte 1 000 $

Soldes lus dans le journal du bot, à l'ouverture de chaque séance :

| Jour | Solde | Plus haut de fin de journée | Plancher affiché par le bot |
|---|---|---|---|
| 14 oct. | 50 000 $ | 50 000 $ | 47 500 $ |
| 20 oct. | 50 988 $ | 51 000 $ | 48 500 $ |
| 21 oct. | 49 911 $ | 51 000 $ | **49 500 $** |
| 22 oct. | **48 892 $** | 51 000 $ | 49 500 $ |
| 23 oct. | 50 701 $ | 51 000 $ | 49 500 $ |
| 26 oct. | 50 582 $ | 51 000 $ | 49 500 $ |
| 27 oct. | 49 588 $ | 51 000 $ | 49 500 $ |
| 29 oct. | 50 521 $ | 51 000 $ | 49 500 $ |

- **La taille.** Avec 4 MNQ, la limite de perte du jour (1 000 $) tombe à 125 points du NQ. Trois des six pertes
  l'ont touchée. Ce sont des pertes normales de la zone ; c'est la taille qui les rend lourdes.
- **Le 22 octobre, le challenge s'est joué à 392 $.**
  - Le compte a ouvert à 48 892 $, 392 $ au-dessus du seuil de Bulenox (51 000 − 2 500 = 48 500 $).
  - La limite du jour était toujours de 1 000 $ : une seule perte normale ce jour-là, et le challenge était perdu.
  - Le frein (zone sur MES) est désactivé pendant le challenge : c'est le choix des vagues 12 et 13, qui donne
    environ 55 % de challenges validés en simulation et accepte environ 45 % d'échecs.
- **Le plancher affiché est passé de 48 500 $ à 49 500 $ le 21 octobre.** Le réglage « perte max suivie » semble être
  à 1 500 $ au lieu de 2 500 $. Il ne change pas les trades, seulement les messages et le frein, mais il doit être à
  la vraie valeur du compte Bulenox.
- **Aujourd'hui.** Après le 29 octobre, le solde est d'environ 49 815 $, avant les trades à la main du 30. La marge
  avant le seuil est donc d'environ 1 315 $.
  - Il reste 9 séances jusqu'au 12 novembre, dont les 5 dernières à 6 MNQ : la limite de 1 000 $ y tombe à
    83 points.
  - Deux pertes normales suffisent à perdre le challenge.
  - Le seul levier qui réduit une perte normale sans abîmer la stratégie est la taille. 2 MNQ divisent par deux les
    pertes et les gains.
  - C'est un choix entre le risque d'échec et la chance d'atteindre 53 000 $.

## La revue de chaque fin de semaine

C'est la boucle demandée par l'utilisateur, sur le modèle de son ami : le bot trade, on exporte la semaine, on
vérifie chaque perte, et on ne réécrit que les règles qui tiennent sur 15 ans.

1. **Le vendredi après la séance**, après 16 h à New York, soit 22 h à Paris :
   - copier `C:\Bot3en1\journal.txt` ;
   - exporter les transactions du NQ de la semaine (stratégie « Export transactions NQ », fichier
     `transactions_NQ*.csv`).
2. **M'envoyer les deux fichiers.**
3. **Je lance la revue :**

   ```bash
   python3 audit/semaine.py journal.txt transactions_NQZ6.csv --sortie audit/semaines/<date>.md
   ```

   - Pour chaque perte, elle sort les 4 points : conditions exactes, évitable ou non, règle responsable ou filtre
     manquant, correction.
   - Elle signale l'entrée tardive (dépassement, distance au VWAP, pic des 30 minutes d'avant) et le piège du bruit
     (nouvelle entrée après une perte, sortie rapide).
   - Elle signale aussi le profit rendu (gain maximal en cours face au résultat), les stops et limites, les
     interventions à la main, les relances et les réglages différents de la zone d'origine.
   - Elle montre ce que chaque correction aurait fait aux gagnants de la semaine.
4. **Corrections.**
   - Les erreurs de logique, de réglage et d'opération sont corrigées tout de suite.
   - Une nouvelle règle de stratégie est d'abord écrite, avant tout calcul. Elle est ensuite jugée sur 15 ans avec
     les quatre critères de l'annexe A, et elle n'entre dans le bot que si elle passe.
   - Sinon, la règle ne change pas : c'est ce qui évite de réparer la semaine passée en abîmant les suivantes.
   - Le tableau `CORRECTIONS` de `semaine.py` garde les verdicts.
5. **Exemple.** La revue des séances du 13 au 30 octobre est dans `audit/semaines/2026-10-13_au_30.md`.

## Ce qui change dans le bot

| Règle | Avant | Maintenant | Pertes concernées |
|---|---|---|---|
| Position fermée hors du bot | rouverte dans la minute | **pas rouverte**. Le trade est compté terminé, et la zone attend le retour du prix dans la bande. La fermeture est retenue après 30 s à 0 pendant que des prix NQ arrivent. Si la position revient telle quelle (coupure), le trade est repris | 14 oct. |
| Relance du bot en pleine séance | trade oublié, position fermée | **trade repris** si le compte tient sa position. Si les positions ne sont pas encore chargées, le bot attend 60 s sans ordre | 27 oct. |
| Coupure Rithmic (liste des positions vide) | ordres de réalignement envoyés à l'aveugle | **aucun ordre** tant que la fermeture n'est pas confirmée ; si la position revient, le trade continue | (prévention) |
| Fichier STOP, filet de 16 h 30, arrêt du bot | — | une fermeture faite par le bot n'est jamais prise pour une fermeture à la main | (prévention) |
| Réglages par défaut | ceux du 26 - 27 octobre (cassure, volume, pas d'entrée tardive, fenêtre 5, une entrée par séance, pas de sortie aux contrôles, stop 70, filtre décoché) | **zone d'origine** : entrée et sorties aux contrôles de 30 minutes, filtre delta coché, relance décochée, sans stop | 29 oct. |
| Règles de stratégie de la zone | — | **inchangées** : C1 à C7 rejetées | 20, 21, 23, 26 oct. |

## Risques de régression, et ce qui a été vérifié

- **Rien ne change sans ces événements.**
  - Six configurations, d'avril au 30 octobre 2026, ont été jouées dans l'adaptateur Quantower imité transaction par
    transaction, avec l'ancienne et la nouvelle version : mode à plat avec et sans le filtre, ancien mode avec
    plafond, challenge de 30 jours, réglages du 26 - 27 octobre, filtre avec relance.
  - Ordres, journaux et logs sont identiques, hors ligne de version (30 fichiers sur 30).
  - Le rejeu du moteur sur 15 ans et sur avril - octobre 2026 est identique aussi, avec C1 à C7 désactivées.
  - Le relecteur indépendant a refait ces comparaisons de son côté et trouve la même chose.
- **Réglages par défaut.** Lancé sans aucun réglage de zone, le bot donne d'avril à octobre exactement les ordres et
  les journaux de la zone d'origine réglée à la main (4 MNQ, limite de 1 000 $ : 83 trades gardés, 30 écartés).
- **Scénarios sur les séances réelles du 14 et du 22 octobre** (4 MNQ, mode à plat) :

  | Scénario | Ancienne version | Nouvelle version |
  |---|---|---|
  | Fermeture à la main à 12 h 35 le 14 oct. | revend 4 MNQ à 12 h 36 | ne rouvre pas |
  | Fermeture à la main 5 s après l'entrée | revend | ne rouvre pas |
  | Relance du bot à 12 h le 22 oct. | ferme la vente, puis revend à 13 h (+180 $ au lieu de +364 $ dans le test) | garde la vente jusqu'à 16 h (+364 $) |
  | Relance avant que les positions soient chargées | ferme la vente | attend, puis garde la vente |
  | Coupure Rithmic de 3 minutes | 3 ordres envoyés pendant la coupure (refusés) | aucun ordre, même résultat que sans coupure |
  | Coupure où les prix reviennent avant les positions | — | fermeture retenue puis annulée quand la position revient : même résultat que sans coupure |
  | Fichier STOP de 12 h à 12 h 10 | ferme, puis rouvre au retrait | pareil (pas pris pour une fermeture à la main) |

- **Moteur :** `Bot3en1.TestAPlat`, 39 contrôles sur 39 (5 nouveaux sur la fermeture à la main et son annulation).
- **Risques qui restent :**
  - Une fermeture partielle (4 MNQ ramenés à 2) n'est pas reconnue : le bot remet la taille voulue, comme avant.
  - Ancien mode (hors mode à plat) avec un RSI(2) tenu : la fermeture à la main de la zone n'est pas reconnue, comme
    avant.
  - Jours de frein (zone sur MES) : la fermeture à la main et la reprise après une relance ne s'appliquent pas au MES.
    Le frein est désactivé pendant le challenge.
  - **Reprise après une relance.** Le bot rejoue la séance avec l'historique de Quantower. Si cet historique n'a pas
    le côté agresseur des transactions, le delta rejoué est nul : le trade est écarté au rejeu et n'est pas repris.
  - **Libellés des réglages.** Le retour aux réglages par défaut suppose que Quantower range les réglages par leur
    libellé. Il faut le vérifier sur la ligne de lancement du journal (voir plus bas).
  - **Prix d'une fermeture à la main.** Le gain est compté au dernier prix NQ, pas au prix rempli : écart de
    quelques dollars.

## Ce qu'il faut faire sur le PC

1. Fermer Quantower, puis mettre le bot à jour avec la ligne d'installation habituelle, collée dans PowerShell :
   `irm https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/refs/heads/claude/optimistic-ptolemy-xs24ra/bot3en1/telecharger.ps1 | iex`
2. Au lancement, vérifier la ligne du journal :
   - elle doit contenir « version du 31 octobre 2026 (audit …) » ;
   - et aussi « entree aux controles de 30 minutes seulement, …, aucun stop, sorties d'origine (aux controles, limite
     de la zone ou VWAP, et 16 h), …, filtre delta COCHE …, relance du filtre decochee ».
   - Sinon, régler la zone à la main comme ça.
3. Mettre « perte max suivie en fin de journée » à la vraie valeur du compte Bulenox (2 500 $ pour un 50K).
4. Ne plus fermer ni arrêter le bot au milieu d'un trade. Le 14 et le 22 octobre, la règle faisait mieux ou presque
   aussi bien que la main. Si c'est vraiment nécessaire, le bot ne rouvrira plus la position.
5. Chaque vendredi soir, envoyer le journal et l'export de la semaine (voir « La revue de chaque fin de semaine »).

## Couche de risque R1 et R2, fixée le 1er novembre 2026 avant de la calculer (modèle du bot de l'ami)

**La demande.** L'utilisateur ne veut plus reprendre les mêmes grosses pertes. Il prend pour modèle le bot d'un ami :
« la partie la plus importante est le risque ». Ce bot a un stop par trade d'au plus 1 % du compte, une perte par jour
limitée, et il s'arrête après une série de défaites.

Les filtres C1 à C7 essayaient d'éviter les mauvais trades : aucun ne tient sur 15 ans. Cette couche ne cherche pas à
deviner le mauvais trade. Elle limite ce qu'il peut coûter. Le bot aura encore tort parfois, mais une erreur ne doit
plus coûter 1 000 $.

**R1, stop par trade à 1 % du compte.** Une perte de trade ne doit pas dépasser 500 $ (1 % de 50 000 $).
- Le stop est à 500 / (2 $ × MNQ) points du prix d'entrée : 62,5 points avec 4 MNQ, 41,7 points avec 6 MNQ. Il est
  vérifié à chaque prix.
- Après le stop, le trade est traité comme écarté : pas de nouvelle entrée avant que le prix revienne dans la zone.
- Sur 15 ans, la distance est ramenée au prix du moment (62,5 points à 30 900, soit 0,202 % du prix).

**R2, arrêt après une défaite dans la journée.** Après un trade perdant (sortie, stop ou limite), le bot ne prend plus
de trade de zone ce jour-là.

**Conditions des tests.**
- Pertes visées : R1 vise le 20, le 21 (14 h 30) et le 26 octobre. R2 vise le 21 octobre (deuxième achat).
- Variantes : R1, R2, et R1 + R2.
- Rejeu : 2011 - 2026, sans le filtre (seul possible sur 15 ans).
- Réglages simulés : 4 MNQ, limite de perte du jour de 1 000 $ vérifiée sur les plus bas et plus hauts de chaque
  minute, frais de 3 $ par MNQ, gains au prix d'aujourd'hui.

**Une règle de risque est adoptée si les quatre conditions sont remplies :**
1. Elle réduit les pertes visées sur les séances d'octobre.
2. Elle garde au moins 90 % du gain sur 15 ans, et au moins 90 % sur deux des trois périodes. Une règle de risque
   paie en gain ce qu'elle retire en risque : au-delà de 10 %, le prix est trop cher.
3. Elle réduit la pire journée et la plus forte baisse du cumul sur 15 ans.
4. Sur des challenges Bulenox 50K simulés, elle ne baisse pas le taux de réussite de plus de 2 points, et elle baisse
   le taux d'échec.
   - Règles simulées : objectif +3 000 $, perte max suivie de 2 500 $ en fin de journée, avec plancher bloqué à
     50 100 $, et échec dès que le compte la touche pendant la séance.
   - Durée et taille : 22 séances, 4 MNQ, puis 6 MNQ les 5 dernières.
   - Départs : chaque séance de 2011 à 2026, puis de 2019 à 2026.

## Nouveau critère pour les corrections C1 à C7, fixé le 1er novembre 2026 avant de le calculer

**La demande.** L'utilisateur précise que son but n'est pas le gain maximal (« sans surentabilité ») : il ne veut plus
reprendre ces pertes, et il veut passer son challenge. Le critère du protocole refusait toute correction qui baisse le
gain sur 15 ans : il ne correspond donc pas à ce but. La couche R1 / R2 (règles du bot de l'ami) est abandonnée à sa
demande. Résultats publiés pour mémoire : R1 et R2 ne baissent pas les échecs sans baisser les réussites.

**Le nouveau juge : des challenges Bulenox 50K simulés** (`audit/risque.py`).
- Règles du challenge :
  - objectif +3 000 $ ;
  - perte max suivie de 2 500 $ en fin de journée, avec plancher bloqué à 50 100 $ ;
  - échec dès que le compte touche le plancher pendant la séance.
- Durée et taille : 22 séances, 4 MNQ, puis 6 MNQ les 5 dernières.
- Le trade : limite de perte du jour de 1 000 $ vérifiée sur chaque minute, frais de 3 $ par MNQ, gains au prix
  d'aujourd'hui.
- Départs : chaque séance de 2011 à 2026, puis de 2019 à 2026.

Les trades viennent du rejeu de chaque correction sur 15 ans, sans le filtre delta. C3 n'est donc pas jugeable : il
lui faut le vrai delta. C6 change la taille : elle est simulée avec la taille qu'elle donne à chaque trade.

**Une correction de perte est adoptée si :**
1. elle évite ou réduit la perte d'octobre qu'elle vise ;
2. sur les deux plages de départs, elle baisse le taux d'échec, sans baisser le taux de réussite de plus d'un point ;
3. la zone reste nettement gagnante sur 15 ans (t ≥ 3).

Les valeurs des corrections restent celles fixées avant : aucune n'est réglée de nouveau.

## Annexe A : protocole (fixé le 31 octobre 2026, avant de recevoir les fichiers du bot)

**Données demandées à l'utilisateur.**
- `C:\Bot3en1\journal.txt` : toutes les décisions du bot, horodatées.
- `C:\Bot3en1\etat*.json` : l'état enregistré du bot.
- L'historique des ordres et des trades de Quantower, exporté en CSV, du 12 octobre à aujourd'hui.
- Les réglages du bot, avec leurs dates de changement si possible.
- L'export des transactions du NQ (stratégie « Export transactions NQ », séance du jour) pour les mêmes jours.

**Pour chaque trade réel perdant, on établit :**
1. **Les conditions exactes du déclenchement.** Ce sont l'heure, le prix, le contrôle et les niveaux de la zone, le
   VWAP, le delta et les réglages en vigueur, lus dans le journal et recalculés sur les minutes du jour.
2. **La comparaison avec deux rejeux sur les mêmes minutes (`Bot3en1.Replay`).**
   - Le rejeu des réglages en vigueur ce jour-là vérifie que le bot a fait ce que disent ses règles.
   - Le rejeu de la zone validée montre ce qu'aurait fait la stratégie de référence.
3. **L'exécution.** On mesure l'écart entre le prix rempli et le prix de la règle, le délai et les remplissages
   partiels.
4. **Une classe :**
   - **N** : perte normale. La règle a fait ce qu'elle doit, et la perte entre dans ce que la stratégie perd
     d'habitude. On ne la corrige pas.
   - **E** : exécution. Le glissement dépasse 2 ticks, ou l'ordre est arrivé en retard ou en partie.
   - **L** : erreur de logique. Le bot a fait autre chose que ce que disent ses règles.
   - **C** : réglage. Les réglages diffèrent de la zone validée, et la zone validée n'aurait pas eu cette perte.
   - **O** : opération. Redémarrage, coupure, intervention à la main, autre stratégie sur le même compte, changement
     de contrat.
5. **Évitable ?** Oui seulement si la cause était connaissable au moment de la décision (classes E, L, C, O).

**Une correction n'est acceptée que si elle remplit les quatre conditions suivantes :**
1. Elle supprime le défaut identifié sur les séances concernées.
2. Sur le rejeu 2011 - 2026, elle ne fait baisser ni le gain ni le t sur l'ensemble, et pas sur plus d'une des trois
   périodes (2011 - 2018, 2019 - 2022, 2023 - 2026).
3. Les trades gagnants qu'elle supprime pèsent moins, en $, que les trades perdants qu'elle supprime.
4. Elle ne crée aucun comportement nouveau : nombre de trades par jour, taille, position gardée après 16 h 59. C'est
   vérifié par les tests du bot (`Bot3en1.TestAPlat`, `Bot3en1.TestPlafond`, `Bot3en1.TestQuantower`).


## Annexe B : corrections candidates, chacune fixée avant son calcul

### Corrections candidates, fixées le 31 octobre 2026 avant de les calculer

Ces trois corrections viennent des pertes du bot d'origine (zone + filtre delta) du 14 au 26 octobre. Elles sont
écrites avant d'être testées, une seule valeur chacune. Les autres valeurs ne sont publiées qu'à titre de
sensibilité ; on ne choisit pas la meilleure.

| Code | Erreur visée | Règle ajoutée (désactivée par défaut) | Séances |
|---|---|---|---|
| C1 | entrée trop tardive (26 octobre : 1,66 fois la largeur de la bande au-delà du niveau) | pas d'entrée si le prix est déjà au-delà du niveau de plus d'**une fois** la largeur de la bande (`DepassementMax = 1`). Le trade est traité comme un trade écarté : le bot attend que le prix revienne avant toute nouvelle entrée | 26 oct. |
| C2 | piégé dans le bruit (21 octobre : deux achats perdants de suite au même niveau) | après une sortie perdante, plus d'entrée dans le même sens pendant la séance (`PasDeRetourApresPerte`) | 21 oct. |
| C3 | delta trop faible pour confirmer (21 octobre : +239 et +115) | le filtre delta demande \|delta 30 min\| ≥ 300 contrats au lieu d'un simple bon signe (`DeltaMin = 300`) | 21 oct. |

**Comment chaque correction est jugée.**
- C1 et C2 sont jugées sur 2011 - 2026 (zone sans filtre, la seule testable sur 15 ans), puis sur avril - octobre
  2026 avec le filtre delta (Databento).
- C3 ne peut être jugée que sur avril - octobre 2026 et sur la quinzaine d'octobre (données Rithmic), parce qu'il faut
  les volumes acheteurs et vendeurs.
- Les critères sont ceux du protocole ci-dessus.

**Corrections de logique (sans effet sur la stratégie), à vérifier dans le code de l'adaptateur Quantower :**
- **14 octobre.** Le bot a rouvert une vente de 4 MNQ juste après une fermeture faite à la main.
- **27 octobre.** Le bot relancé en pleine séance a fermé une position ouverte et gagnante, parce qu'il ne savait plus
  qu'elle était à lui.

**Hors du champ des règles.**
- Les arrêts à la main du 14 et du 22 octobre.
- Les trades du 30 octobre, qui ne viennent pas du bot (10 et 13 MNQ, absents du journal).


### Correction candidate C4, fixée le 31 octobre 2026 avant de la calculer : le gain rendu (« profit trop gourmand »)

L'utilisateur demande aussi où le profit a été trop gourmand. Mesure faite sur les trades du bot d'origine (zone +
filtre delta) du 14 au 27 octobre, avec le plus haut et le plus bas des minutes entre l'entrée et la sortie :

| Trade | Résultat | Gain maximal en cours | Perte maximale en cours |
|---|---|---|---|
| 14 oct., vente 11 h 30 → 16 h | +207 pts | +315 pts | −9 pts |
| 20 oct., achat 10 h 30 → 11 h 30 | −137 pts | +18 pts | −190 pts |
| 21 oct., achat 13 h → 14 h | −34 pts | +33 pts | −36 pts |
| 21 oct., achat 14 h 30 → 15 h | −145 pts | +1 pt | −150 pts |
| 22 oct., vente 10 h 30 → 16 h | +184 pts | +297 pts | −50 pts |
| 23 oct., achat 11 h → 11 h 30 | −22 pts | +3 pts | −65 pts |
| 26 oct., achat 11 h → 16 h | −115 pts | +17 pts | −158 pts |
| 27 oct., achat 11 h → 14 h | +50 pts | +154 pts | −11 pts |
| 27 oct., achat 15 h → 16 h | −10 pts | +58 pts | −20 pts |

- **Aucune perte ne vient d'un gain rendu.** Les six trades perdants n'ont jamais été en gain de plus de 58 points,
  soit au plus un quart de la largeur de bande (98 à 230 points ces jours-là) : ils sont partis contre le bot dès
  l'entrée.
- **Les gagnants ont rendu une partie de leur pic** : 108 points le 14, 114 le 22, 104 le 27. C'est là que la
  question « trop gourmand » se pose.

**C4, une seule valeur.** À chaque contrôle (10 h 30 à 15 h 30), si le trade tenu a atteint, sur les clôtures des
minutes depuis l'entrée, un gain d'au moins **une largeur de bande** (référence × σ du contrôle d'entrée, l'unité du
« dépassement ») et que le prix du contrôle a rendu **la moitié** de ce gain maximal ou plus, le bot sort au prix du
contrôle. Le trade est ensuite traité comme un trade écarté : pas de nouvelle entrée (ni de relance) avant que le prix
revienne dans la zone. Sinon, rien ne change (`ProtegerGain = 1`, désactivé par défaut).

- **Sensibilité publiée, pas choisie :** 0,5 et 2 largeurs de bande.
- **Jugée comme C1 et C2 :** sur 2011 - 2026 sans le filtre, puis sur avril - octobre 2026 avec le filtre, avec les
  quatre critères du protocole.


### Corrections candidates C5 et C6, fixées le 1er novembre 2026 avant de les calculer : les « stop loss » pris

L'utilisateur demande de se concentrer sur les pertes qui ont touché un stop. Ce sont les limites de perte du jour du
20, du 21 et du 26 octobre (environ −1 000 $ chacune) et le stop de 70 points du 29 (réglages modifiés).

**Constat dans le journal du bot.** Les jours de limite, le trade de zone n'a pas été coupé par sa propre règle. Sa
sortie n'est vérifiée qu'aux contrôles de 30 minutes. Entre deux contrôles, seule la limite du jour le protège : avec
4 MNQ, elle coupe à environ 125 points.
- **20 octobre.** Achat à 10 h 30 à 29 879. Le niveau de sortie est à 29 820,62, 58 points plus bas. Le prix le casse,
  puis descend jusqu'à la limite à 11 h 12, entre deux contrôles.
- **21 octobre, 14 h 30.** Achat à 30 088. Le niveau de sortie est à 30 058,36, 30 points plus bas. Limite à 14 h 51.
- **26 octobre.** Achat à 11 h à 29 554,75. Le niveau de sortie est à 29 353,90, **201 points plus bas**. La limite du
  jour (125 points) est plus proche que la sortie de la règle : le trade ne pouvait pas sortir par sa règle avant
  d'être coupé.

**C5, stop au niveau de sortie.** Entre deux contrôles, si une minute clôture au-delà du niveau de sortie affiché au
dernier contrôle, le bot sort à cette clôture. Pour un achat, c'est une clôture sous le maximum de la limite haute et
du VWAP du contrôle ; pour une vente, au-dessus du minimum de la limite basse et du VWAP. Aux contrôles, rien ne change
(`StopNiveauSortie`, désactivé par défaut).

**C6, taille selon le risque.** Le bot réduit la taille pour que la perte jusqu'au niveau de sortie ne dépasse pas
500 $, soit 1 % du compte et la moitié de la limite du jour :
- MNQ = min(taille, partie entière de 500 / (2 $ × distance en points)) ;
- si le calcul donne 0, pas de trade.

Sur 15 ans, la distance est ramenée au prix d'aujourd'hui (× 30 900 / prix), avec une taille de 4 MNQ comme dans le
challenge.

**Jugées comme C1 à C4.**
- **Périodes :** 2011 - 2026 sans le filtre, puis avril - octobre 2026 avec le filtre.
- **Variantes :** C5, C6, et C5 + C6 ensemble, une seule valeur chacune.
- **Critères :** les quatre du protocole. Pour C6, le critère 3 compare les dollars retirés aux trades gagnants et
  aux trades perdants.

**C7, fixée le 1er novembre 2026 après le calcul de C5 et C6 mais avant le sien : pas d'entrée trop loin du VWAP.**
Le 20 octobre, l'achat de 10 h 30 a été pris 264 points au-dessus du VWAP, soit 2,7 largeurs de bande, juste après une
hausse de 240 points en 30 minutes. C7 refuse l'entrée si le prix est à plus de **2 largeurs de bande** du VWAP, du
côté du trade. Le trade est alors traité comme un trade écarté (`VwapMax = 2`, désactivé par défaut). Elle est jugée
comme les autres. Elle est écrite après avoir vu le 20 octobre : seul le calcul sur 15 ans, qu'elle n'a pas vu, compte.

## Annexe C : résultats sur 15 ans (frais corrigés le 1er novembre 2026)

Rejeu du moteur C# du bot (`Bot3en1.Replay`) sur les minutes du NQ du 24 janvier 2011 au 29 octobre 2026, sans le
filtre delta (il faut le vrai delta, qui n'existe que depuis avril 2026). Les gains sont en $ pour 1 MNQ au prix
d'aujourd'hui : les points sont ramenés à 30 900, avec des frais fixes de 3 $ par aller-retour. Calcul :
`audit/rejeux.py`.

**Correction des frais.** Les tableaux publiés le 31 octobre multipliaient aussi les frais par 30 900 / prix, soit
environ 13 fois en 2011. Le relecteur indépendant l'a relevé, et c'est corrigé.
- **Les verdicts ne changent pas.**
- La zone d'origine gagne aussi sur 2011 - 2018 (t 2,69), et non plus −7 788 $.
- « Pas de sortie aux contrôles » et le stop de 70 points font un peu moins bien que la zone d'origine. Ils ne sont
  pas « sans effet », comme écrit avant.
- C2 n'est plus « la plus tentante » : elle fait moins bien sur 15 ans.

**Les réglages du 26 - 27 octobre, ajoutés un par un à la zone d'origine :**

| Réglages | 2011 - 2018 | 2019 - 2022 | 2023 - 2026 | 15 ans | t |
|---|---|---|---|---|---|
| zone d'origine | +32 539 $ | +26 334 $ | +20 974 $ | **+79 847 $** | 4,22 |
| entrée à la cassure entre deux contrôles | +27 650 $ | +20 300 $ | +10 581 $ | +58 531 $ | 2,62 |
| cassure + volume, sans entrée tardive, fenêtre de 5 min | +16 537 $ | +9 637 $ | +15 476 $ | +41 650 $ | 2,15 |
| une entrée par séance, sortie au niveau cassé | +28 476 $ | +21 316 $ | +10 885 $ | +60 677 $ | 3,36 |
| pas de sortie aux contrôles | +29 573 $ | +24 381 $ | +20 737 $ | +74 691 $ | 2,98 |
| stop de 70 points | +31 980 $ | +26 758 $ | +20 045 $ | +78 783 $ | 4,19 |
| pas de sortie aux contrôles + stop de 70 points | +31 095 $ | +24 268 $ | +21 383 $ | +76 746 $ | 3,49 |
| **tous les réglages du 26 - 27 octobre** | −1 713 $ | +4 326 $ | +7 726 $ | **+10 339 $** | 0,49 |

**Les corrections candidates, 1 MNQ :**

| | Zone d'origine | C1 entrée tardive | C2 retour après perte | C4 gain rendu | C7 loin du VWAP |
|---|---|---|---|---|---|
| 15 ans | +79 847 $ (t 4,22) | +63 830 $ (t 3,68) | +68 332 $ (t 4,14) | +74 491 $ (t 4,34) | +77 028 $ (t 4,22) |
| 2011 - 2018 | +32 539 $ | +25 643 $ | +33 751 $ | +26 975 $ | +34 652 $ |
| 2019 - 2022 | +26 334 $ | +21 058 $ | +19 369 $ | +24 363 $ | +25 702 $ |
| 2023 - 2026 | +20 974 $ | +17 130 $ | +15 212 $ | +23 152 $ | +16 674 $ |
| Gagnants / perdants supprimés | | +76 066 $ / −60 050 $ | +98 629 $ / −87 114 $ | (sorties) | +26 376 $ / −23 557 $ |
| Avril - octobre 2026, avec le filtre | +3 589 $ (t 1,27) | +1 965 $ | +2 415 $ | +5 420 $ (t 1,91) | +4 134 $ (t 1,52) |
| Verdict | | **rejetée** (3 périodes en baisse) | **rejetée** (15 ans et 2 périodes en baisse) | **rejetée** (15 ans en baisse ; coupe le gagnant du 14 oct.) | **rejetée** (15 ans en baisse, retire plus de gagnants) |

**Sensibilité, publiée et pas choisie :**
- C1 : à 0,75 largeur, +52 465 $ ; à 1,5, +71 983 $.
- C4 : à 0,5 largeur, +67 370 $ ; à 2, +77 283 $.
- C7 :
  - à 1,5 largeur, +66 490 $ ;
  - à 3 largeurs, +80 833 $ (t 4,28), à peine mieux que la zone d'origine. Mais ce n'est pas la valeur fixée
    d'avance, et elle n'aurait pas évité le 20 octobre (2,7 largeurs).

**C3 (delta d'au moins 300)** ne se mesure que sur avril - octobre 2026 : +3 542 $ au lieu de +3 589 $. Les 13 trades
qu'elle supprime font +795 $ en gains et −748 $ en pertes : **rejetée**.

**C5 et C6, avec 4 MNQ (la taille du challenge) :**

| | Zone d'origine | C5 sortie à la minute | C6 taille selon le risque | C5 + C6 |
|---|---|---|---|---|
| 15 ans | +319 389 $ (t 4,22) | +247 298 $ (t 3,66) | +232 568 $ (t 3,67) | +164 121 $ (t 3,08) |
| 2011 - 2018 | +130 157 $ | +98 043 $ | +108 814 $ | +98 257 $ |
| 2019 - 2022 | +105 335 $ | +79 392 $ | +62 027 $ | +10 053 $ |
| 2023 - 2026 | +83 896 $ | +69 863 $ | +61 726 $ | +55 811 $ |
| Verdict | | **rejetée** (3 périodes en baisse) | **rejetée** (3 périodes en baisse) | **rejetée** |

**Ce que montrent ces tests.**
- La zone gagne sur les journées de tendance. Une entrée tardive, une deuxième entrée ou un trade qui recule avant de
  repartir y gagnent aussi.
- Chaque filtre qui coupe ces trades pour éviter une perte d'octobre coupe davantage de gains sur 15 ans.
- Les contrôles toutes les 30 minutes sont le filtre du bruit : une sortie vérifiée à chaque minute (C5) se fait
  piéger.

**Données.**
- Le fichier des agresseurs n'a pas de données du 2 au 12 octobre : 5 signaux y sont écartés avec un delta de 0 dans
  le test avec le filtre.
- À partir du 13 octobre, les données viennent de l'export Rithmic de l'utilisateur, et non plus de Databento.
- Le stop de 70 points est en points fixes : il ne joue qu'à partir de 2018 environ.

## Annexe D : la revue indépendante (#ultrareview)

Deux relecteurs indépendants ont repris le travail le 1er novembre 2026.

**Relecteur des conclusions.**
- **Chiffres.** Il a refait les calculs : tous les chiffres publiés se retrouvent. Les critères ont été fixés avant
  les calculs, d'après l'historique git, et aucun n'a été plié.
- **Ce qu'il a fait corriger :**
  - les frais multipliés par le prix (annexe C) ;
  - le 27 octobre, classé maintenant comme un défaut de logique favorable, et non comme un réglage ;
  - la classe E (exécution) pour le glissement du 20 octobre ;
  - C4, qui coupait aussi le gagnant du 14 octobre ;
  - le rapprochement des soldes du compte ;
  - la taille face à la perte max suivie, et le 22 octobre à 392 $ de l'échec.

**Relecteur du code.**
- Aucun défaut bloquant : rien ne peut doubler une position ni laisser une exposition sans limite.
- Il a trouvé 8 points à corriger. Tous sont corrigés et ont un scénario de test (`Bot3en1.TestQuantower`).
  - **Coupure où les prix reviennent avant les positions.** La fermeture était retenue à tort, puis la position était
    fermée à son retour. Maintenant, le trade est repris.
  - **Relance avant que Quantower charge les positions.** Le bot attend 60 s.
  - **Fermeture à la main.** Son gain n'était pas sauvegardé tout de suite.
  - **Fermeture dans les 15 s qui suivent l'entrée.** Elle était manquée.
  - **Fichier STOP.** Il était pris pour une fermeture à la main.
  - **Documentation :** l'introduction du README du bot contredisait les nouveaux réglages, et les limites de la
    fermeture à la main n'étaient pas écrites (ancien mode avec le RSI(2), jours de frein).
- **Défaut ancien, non introduit par l'audit.** En ancien mode, une relance compte deux fois les trades déjà faits
  dans `RealiseJour`. Le mode à plat, celui du challenge, n'est pas touché.
