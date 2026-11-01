# Audit rétrospectif du bot 3 en 1 (séances du 12 au 30 octobre 2026)

L'utilisateur l'a demandé le 31 octobre 2026. Le but n'est pas d'augmenter les gains ni de changer de stratégie. Il est
de trouver les erreurs de logique, de réglage et d'exécution qui ont causé les pertes, de corriger seulement les règles
fautives, et de vérifier que chaque correction ne dégrade pas ce qui marche.

## Protocole (fixé avant de recevoir les fichiers du bot)

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

## Premier constat, sans les fichiers du bot : les réglages changés les 26 et 27 octobre

Les réglages par défaut du bot ont été changés les 26 et 27 octobre 2026 à la demande de l'utilisateur. Le rejeu du
moteur C# (`Bot3en1.Replay`, 1 MNQ, minutes du NQ 2011 - 29 octobre 2026) les compare à la zone validée, en les
ajoutant un par un. Gain brut total sur 15 ans :

| Réglage ajouté à la zone validée | Trades | Gain sur 15 ans | Effet |
|---|---|---|---|
| aucun (zone validée, sans filtre delta) | 3 580 | +20 956 $ | référence |
| entrée à la cassure entre deux contrôles (`CASSURE`) | 5 925 | +5 715 $ | **−73 %** |
| cassure + confirmation par le volume, sans entrée tardive, fenêtre de 5 min | 4 682 | +5 216 $ | **−75 %** |
| une entrée par séance, sortie au retour sous le niveau cassé (`COURIR`) | 2 301 | +14 645 $ | **−30 %** |
| pas de sortie aux contrôles (`SANS_SORTIE`) | 2 301 | +21 568 $ | +3 % |
| stop à 70 points (`STOP=70`) | 3 588 | +20 512 $ | −2 % |
| pas de sortie aux contrôles + stop à 70 points | 2 420 | +21 979 $ | +5 % |
| **réglages actuels (tous ensemble)** | 2 402 | **+2 688 $** | **−87 %** |

Les mêmes rejeux, par période, en $ au prix d'aujourd'hui (`audit/rejeux.py`) :

| Réglages | 2011 - 2018 | 2019 - 2022 | 2023 - 2026 | 12 - 30 oct. 2026 |
|---|---|---|---|---|
| zone validée | −7 788 $ (t −0,63) | +21 016 $ (t +1,90) | +19 448 $ (t +2,04) | +606 $ (14 trades) |
| réglages actuels | −29 610 $ (t −1,91) | +894 $ (t +0,08) | +6 657 $ (t +0,76) | +2 003 $ (10 trades) |
| cassure seule | −39 744 $ (t −2,85) | +11 615 $ (t +0,87) | +8 068 $ (t +0,69) | +1 929 $ |
| une entrée, sortie au niveau cassé | +2 244 $ (t +0,20) | +17 988 $ (t +1,62) | +9 900 $ (t +1,18) | +864 $ |
| pas de sortie + stop 70 | +4 673 $ (t +0,31) | +20 660 $ (t +1,64) | +20 306 $ (t +2,02) | +731 $ |

- **Règles responsables.** L'entrée à la cassure entre deux contrôles et, dans une moindre mesure, l'entrée unique avec
  sortie au niveau cassé détruisent la plus grande partie de l'avantage sur 15 ans.
- **Règles qui fonctionnent.** Garder le trade jusqu'à 16 h et le stop à 70 points ne dégradent rien. Ils améliorent
  même légèrement 2011 - 2018 et réduisent la plus forte baisse de 2023 - 2026.
- **Les 15 derniers jours ne sont pas expliqués par ces réglages.** En rejeu, les réglages actuels gagnent +2 003 $ du
  12 au 30 octobre pour 1 MNQ. Si le compte réel a perdu sur cette période, la cause est ailleurs : réglages qui ont
  changé en cours de route, taille, exécution, redémarrages, autres stratégies sur le compte. Il faut le journal et
  l'historique de Quantower pour la trouver.

## Corrections candidates, fixées le 31 octobre 2026 avant de les calculer

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

## Correction candidate C4, fixée le 31 octobre 2026 avant de la calculer : le gain rendu (« profit trop gourmand »)

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

## Résultats des quatre corrections candidates (calculés après les avoir fixées)

Rejeu du moteur C# : 15 ans sans le filtre (2011 - 29 octobre 2026, 3 580 trades), puis avril - octobre 2026 avec le
filtre et le vrai delta (Databento, 88 trades). Gains en $ pour 1 MNQ au prix d'aujourd'hui (`audit/rejeux.py`).

| | Zone d'origine | C1 entrée tardive | C2 pas de retour après perte | C3 delta ≥ 300 | C4 gain rendu |
|---|---|---|---|---|---|
| 15 ans : gain, t | +32 676 $, t 1,71 | +22 865 $, t 1,31 | +34 955 $, t 2,11 | non mesurable | +27 320 $, t 1,58 |
| 2011 - 2018 | −7 788 $ | −9 489 $ | **+5 240 $** | | −13 352 $ |
| 2019 - 2022 | +21 016 $ | +16 560 $ | +15 596 $ | | +19 045 $ |
| 2023 - 2026 | +19 448 $ | +15 794 $ | +14 119 $ | | **+21 627 $** |
| Plus forte baisse sur 15 ans | −27 750 $ | −25 623 $ | **−11 914 $** | | −25 218 $ |
| Gagnants supprimés / perdants supprimés | | +73 751 $ / −63 940 $ | +93 932 $ / −96 211 $ | +793 $ / −749 $ | |
| Avril - octobre 2026, avec le filtre | +3 571 $, t 1,26 | +1 948 $ | +2 399 $ | +3 526 $ | **+5 402 $**, t 1,90 |
| Verdict | | **rejetée** | **rejetée** | **rejetée** | **rejetée** |

- **C1 (entrée trop tardive) : rejetée.** Elle baisse les trois périodes. Les entrées loin du niveau gagnent en
  moyenne : sur 15 ans, les 483 trades qu'elle supprime rapportaient +9 800 $. Le 26 octobre était une perte normale.
  Sensibilité : 0,75 et 1,5 largeur font aussi moins bien.
- **C2 (piégé dans le bruit) : rejetée.** C'est la plus tentante : sur 15 ans, elle monte le gain (+7 %) et le t
  (2,11), et elle divise la plus forte baisse par plus de deux. Mais tout vient de 2011 - 2018. Elle perd sur
  2019 - 2022 et 2023 - 2026 (−10 750 $ en tout), et sur avril - octobre 2026 avec le filtre (−1 172 $). Elle échoue
  au critère 2, fixé d'avance. Elle n'est pas adoptée. Elle reste à suivre, sans argent.
- **C3 (delta faible) : rejetée.** Elle supprime 13 trades sur 7 mois, autant gagnants que perdants (+793 $ /
  −749 $). C'est trop peu pour juger, et elle échoue au critère 3.
- **C4 (gain rendu, « profit trop gourmand ») : rejetée.** Elle aurait bien marché sur avril - octobre 2026
  (+1 831 $, t 1,90). Mais sur 15 ans, elle fait perdre 16 % et baisse 2011 - 2018 et 2019 - 2022. C'est le piège
  d'une règle qui colle aux derniers mois. La zone gagne sur les journées de tendance qui reculent puis repartent ;
  couper à mi-chemin coupe ces journées. Sensibilité : 0,5 et 2 largeurs font aussi moins bien sur 15 ans
  (+20 199 $ et +30 112 $).
- **Conclusion.** Aucune règle de stratégie de la zone d'origine n'est en faute. Ses pertes d'octobre entrent dans ce
  qu'elle perd d'habitude. Les erreurs à corriger sont ailleurs : réglages, logique de l'adaptateur et opérations.

## Les trades réels du 13 au 30 octobre, un par un

Heures de New York. Montants du compte (4 MNQ), lus dans l'export Rithmic et le journal du bot.

| Jour | Ce qui s'est passé | Classe | Évitable ? | Règle ou cause | Correction |
|---|---|---|---|---|---|
| 14 oct. | Vente de zone à 11 h 30 (30 393,50). À 12 h 35, rachat de 4 MNQ à la main (+1 178 $). Le bot a revendu 4 MNQ aussitôt (« position 0 -> -4 »). Arrêt du bot à 12 h 39 (−180 $). La zone seule gardait jusqu'à 16 h : +207 points. | **O + L** | oui | l'adaptateur réaligne toute position sur celle du moteur, même fermée à la main | **le bot ne rouvre plus une position fermée hors de lui** (testé) |
| 20 oct. | Achat à 10 h 30 (29 879, delta +3 968, dépassement 0,60). Retournement immédiat, jamais plus de +18 points. Limite du jour à 11 h 12 : −1 072 $ (−1 002 $ estimés par le bot). | **N** (+ E faible) | non | perte normale ; 70 $ de glissement à la sortie au marché | aucune |
| 21 oct. | Achat à 13 h (delta +239), sorti à 14 h (−254 $). Nouvel achat à 14 h 30 (delta +115), limite du jour (−756 $). | **N** | non | perte normale (C2 et C3 visaient ce jour : rejetées) | aucune |
| 22 oct. | Vente à 10 h 30. Bot arrêté à la main à 14 h 02 (+1 814 $). Gardée jusqu'à 16 h : +1 468 $. | **O** (favorable) | — | intervention à la main | aucune |
| 23 oct. | Achat à 11 h, sorti à 11 h 30 (−114 $). | **N** | non | perte normale | aucune |
| 26 oct. | Achat à 11 h, dépassement 1,66. La zone d'origine prend le même trade. Limite du jour : −989 $. | **N** | non | perte normale (C1 visait ce jour : rejetée) | aucune |
| 27 oct. | Réglages modifiés : achat à la cassure à 10 h 55. Bot relancé à 11 h 50 sans arrêt : il a fermé sa propre position (+937 $). | **C + L** | oui | relance en cours de séance : le bot oubliait son trade et fermait la position | **le bot reprend son trade s'il est encore sur le compte** (testé) ; réglages d'origine |
| 29 oct. | Réglages modifiés : vente à la cassure de 10 h 10, stop de 70 points touché à 10 h 17 (−706 $). La zone d'origine ne trade pas ce jour-là. | **C** | oui | entrée à la cassure + stop 70 | **réglages d'origine par défaut** |
| 30 oct. | Trades de 10 et 13 MNQ, absents du journal du bot. | hors champ | — | pas le bot | aucune |

**Autre constat : la perte max suivie.** Le plancher affiché par le bot est passé de 48 500 $ à 49 500 $ le 21 octobre.
Le réglage « perte max suivie en fin de journée » semble avoir été mis à 1 500 $ au lieu de 2 500 $ (Bulenox 50K). Ce
réglage ne sert qu'au frein et aux messages, mais il faut le remettre à la vraie valeur du compte Bulenox.

## Anciennes règles et nouvelles règles

| Règle | Avant | Maintenant | Pertes concernées |
|---|---|---|---|
| Position fermée hors du bot | rouverte à l'alignement suivant (dans la minute) | **pas rouverte**. Le trade est compté terminé au prix de la fermeture, sans relance. La zone attend le retour du prix dans la bande | 14 oct. |
| Relance du bot en pleine séance, position encore ouverte | trade oublié, position fermée | **trade repris et géré par les règles** si le compte tient exactement la position du trade rejoué ; sinon, comme avant | 27 oct. |
| Liste des positions vide pendant une coupure Rithmic | ordres de réalignement envoyés à l'aveugle | **aucun ordre pendant 30 s ni tant que le flux NQ est coupé** ; une fermeture n'est retenue que si la position reste à zéro 30 s pendant que des transactions NQ arrivent | (prévention) |
| Réglages par défaut de la zone | ceux du 26 - 27 octobre (cassure, volume, pas d'entrée tardive, fenêtre 5, une entrée par séance, pas de sortie aux contrôles, stop 70, filtre décoché) | **zone d'origine** : entrée et sorties aux contrôles de 30 minutes, filtre delta coché, relance décochée, sans stop. Les libellés ont changé, donc Quantower n'applique plus les anciennes valeurs enregistrées | 27 et 29 oct. |
| Règles de stratégie de la zone (entrée, filtre, sorties, 16 h) | — | **inchangées** (C1 à C4 rejetées) | 20, 21, 23, 26 oct. (normales) |

## Risques de régression, et ce qui a été vérifié

- **Rien ne change sans ces événements.** Six configurations d'avril au 30 octobre 2026, ancienne et nouvelle version,
  dans l'adaptateur Quantower imité transaction par transaction : mode à plat avec et sans le filtre, ancien mode avec
  plafond, challenge de 30 jours, réglages de l'utilisateur du 26 - 27 octobre, filtre avec relance. Les ordres, les
  deux journaux et les logs sont identiques octet pour octet (30 fichiers sur 30). Le rejeu du moteur sur 15 ans et sur
  avril - octobre 2026 est identique aussi, C1 à C4 désactivées.
- **Réglages par défaut.** Le bot lancé sans aucun réglage de zone donne, d'avril à octobre, exactement les ordres et les
  journaux de la zone d'origine réglée à la main (83 trades gardés, 30 écartés).
- **Scénarios (séances réelles du 14 et du 22 octobre, 4 MNQ, mode à plat).**

  | Scénario | Ancienne version | Nouvelle version |
  |---|---|---|
  | Fermeture à la main à 12 h 35 le 14 oct. | revend 4 MNQ à 12 h 36 | ne rouvre pas ; message « fermee hors du bot » |
  | Relance du bot sans arrêt à 12 h le 22 oct. | ferme la vente, puis revend à 13 h (+180 $ au lieu de +364 $ dans le test) | garde la vente jusqu'à 16 h (+364 $, comme sans relance) |
  | Coupure Rithmic de 3 minutes à 12 h le 22 oct. | 3 ordres envoyés pendant la coupure (refusés) | aucun ordre ; position retrouvée ; même résultat que sans coupure |

- **Moteur :** `Bot3en1.TestAPlat`, 37 contrôles sur 37 (3 nouveaux sur la fermeture à la main).
- **Risques qui restent :**
  - une fermeture partielle (4 MNQ ramenés à 2) n'est pas reconnue : le bot remet la taille voulue, comme avant ;
  - si Rithmic rétablit les prix plus de 30 s avant les positions, le bot peut croire à une fermeture. Il ne rouvre
    alors plus le trade, et il fermera la position quand elle réapparaîtra. Le journal et Telegram le signalent
    aussitôt (« position MNQ fermee hors du bot ») : vérifier le compte si ce message arrive sans fermeture à la main ;
  - après une relance, le prix d'entrée du trade repris est celui du rejeu (clôture de la minute du contrôle), pas le
    prix rempli : la limite de perte du jour peut s'écarter de quelques dollars ;
  - une fermeture faite par le courtier (liquidation) est traitée comme une fermeture à la main : le bot ne rouvre pas.
    C'est voulu.

## Ce qu'il faut faire sur le PC

1. Fermer Quantower, puis mettre le bot à jour avec la ligne d'installation habituelle, collée dans PowerShell :
   `irm https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/refs/heads/claude/optimistic-ptolemy-xs24ra/bot3en1/telecharger.ps1 | iex`
2. Ouvrir les réglages du bot. Les réglages de zone sont revenus à la zone d'origine, parce que leurs libellés ont
   changé. Vérifier au lancement la ligne du journal : « entree aux controles de 30 minutes seulement, …, aucun stop,
   sorties d'origine (aux controles, limite de la zone ou VWAP, et 16 h), …, filtre delta COCHE …, relance du filtre
   decochee ».
3. Remettre « perte max suivie en fin de journée » à la valeur du compte Bulenox (2 500 $ pour un 50K), si ce n'est
   pas déjà le cas.
4. Ne plus fermer ni arrêter le bot au milieu d'un trade. Le 14 et le 22 octobre, la règle faisait mieux ou presque
   aussi bien que la main. Si c'est nécessaire, le bot ne rouvrira plus la position.

## Corrections candidates C5 et C6, fixées le 1er novembre 2026 avant de les calculer : les « stop loss » pris

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
