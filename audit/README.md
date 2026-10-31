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
