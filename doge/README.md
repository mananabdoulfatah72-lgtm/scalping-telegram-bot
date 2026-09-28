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
