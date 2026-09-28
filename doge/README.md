# DOGE : un mouvement brutal à 2 h, 13 h et 23 h ?

Idée à tester : « tous les jours à 2 h, 13 h et 23 h (heure de Paris), le prix du DOGE part
subitement dans une direction ».

## Données

Bougies d'une minute DOGE/USDT de Binance (archive publique), depuis juillet 2019, regroupées en
bougies de 5 minutes. On teste le **prix**, c'est-à-dire ce qu'on achète et vend. La courbe de
capitalisation (CRYPTOCAP:DOGE sur TradingView) = prix × nombre de DOGE en circulation : si ce nombre
est mis à jour à heure fixe, la courbe peut sauter à ces heures sans que le prix bouge.

## Tests (fixés le 28 septembre 2026, avant de télécharger les données)

Heures testées : 2 h, 13 h et 23 h, heure de Paris (heure d'été comprise).

1. **Y a-t-il un mouvement plus fort ?** Mouvement absolu moyen des 15 minutes qui suivent l'heure,
   comparé à la même mesure pour toutes les autres heures de la journée.
2. **Peut-on en gagner de l'argent ?** Trois règles, position de l'heure pile (ou de l'heure + 5 min)
   jusqu'à l'heure suivante :
   - **sens fixe** : toujours acheteur (et toujours vendeur) à cette heure-là ;
   - **suivre l'heure d'avant** : sens du mouvement de la dernière heure ;
   - **suivre le départ** : sens des 5 premières minutes après l'heure, entrée à l'heure + 5 min.
   Frais : 0,10 % par aller-retour (futures perpétuels, ordres au marché) ; aussi montré à 0,20 %
   (achat-vente au comptant).
3. **Verdict** : une règle est exploitable si elle gagne après frais avec t ≥ 2 **et** fait mieux
   que 95 % des placebos (même règle appliquée à des heures tirées au hasard). 3 heures × 4 règles
   = 12 essais : avec autant d'essais, un t de 2 peut arriver par hasard ; on regarde aussi si le
   résultat tient sur chaque année.

Remarque : les prop firms futures (Apex, Topstep, Phidias) ne tradent que des contrats CME ; le DOGE
n'y est pas coté à notre connaissance (à vérifier). Un avantage sur le DOGE ne servirait donc pas pour
leurs challenges.

## Résultats (28 septembre 2026) — DOGE/USDT de juillet 2019 à septembre 2026 (2 638 jours)

**1. Mouvement dans les 15 minutes après l'heure** (moyenne en valeur absolue) :

| Heure (Paris) | Mouvement moyen | Autres heures | Jours avec plus de 1 % en 15 min |
|---|---|---|---|
| 2 h | 0,44 % | 0,38 % (× 1,15) | 9 % (autres : 7 %) |
| 13 h | 0,36 % | 0,38 % (× 0,96) | 6 % |
| 23 h | 0,36 % | 0,38 % (× 0,95) | 6 % |

13 h et 23 h ne bougent pas plus que les autres heures. 2 h bouge un peu plus : c'est minuit UTC
(fermeture de la bougie journalière des plateformes et paiement du financement des contrats
perpétuels). Les heures les plus agitées sont 16 h et 17 h (ouverture de Wall Street).

**2. Règles de trading** : les 12 règles perdent après 0,10 % de frais. Le sens du mouvement n'est
pas prévisible (suivre les 5 premières minutes ou l'heure d'avant perd même avant frais). Seule
« acheteur de 23 h à minuit » gagne un peu avant frais (+0,09 % par trade, mieux que 100 % des
placebos) mais −0,01 % après frais (t = −0,4), et le résultat change de signe d'une année à l'autre
(+88 % en 2021, −60 % en 2022). Détails : `resultats.txt`.

**Conclusion** : pas de mouvement brutal exploitable à 2 h, 13 h ou 23 h sur le prix du DOGE.
Ce qu'on voit sur la courbe de capitalisation de TradingView vient probablement de la mise à jour
à heure fixe du nombre de DOGE en circulation, pas d'un mouvement de prix qu'on pourrait trader.

**Capture TradingView du 28 septembre 2026 (CRYPTOCAP:DOGE, 30 min)** : sur la même période, le
prix du DOGE est passé de 0,079 $ à 0,104 $ ; avec environ 157 milliards de DOGE en circulation, cela
donne une capitalisation de 12,4 à 16,3 milliards de dollars, comme sur la capture. Les sauts sont
donc de vrais mouvements de prix. Mais les 8 plus gros mouvements de 30 minutes du 13 au 25 septembre
ont eu lieu à 4 h 30, 6 h, 6 h 30, 15 h 30, 16 h et 16 h 30, jamais à 2 h, 13 h ou 23 h
(`doge_heures.png`).
