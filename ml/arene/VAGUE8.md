# Arène, vague 8 : les journées sans Z12, et des filtres de journée pour Z12 (règles fixées avant tout calcul, 9 novembre 2026)

Les vagues 1 à 7 ont tourné autour des mêmes signaux de tendance. Deux directions nouvelles :

**A. Les journées où Z12 ne fait rien** (environ 6 séances sur 10, souvent sans tendance). Une stratégie de retour à la
moyenne y ajouterait des gains sur d'autres moments que Z12, sans empiler le risque. Chacune est jouée seule, puis **sur
le même compte que Z12, un contrat à la fois, Z12 prioritaire** (comme P2 de la vague 5).

| | Règle (1 MNQ, décisions à la clôture des bougies de 5 min, ordre à l'ouverture de la minute suivante, entrées de 10 h à 15 h, à plat à 15 h 55, au plus 2 trades par séance) |
|---|---|
| R1 | Bandes de la VWAP : clôture au-dessus de VWAP + 2 écarts types (pondérés par le volume, depuis l'ouverture) : vente ; en dessous de VWAP − 2 : achat ; objectif la VWAP du moment de l'entrée, stop à la même distance de l'autre côté |
| R2 | RSI 2 sur bougies de 5 min (Connors) : sous 5 achat, au-dessus de 95 vente ; sortie quand le RSI 2 repasse 50 ; stop à 1,5 ATR (bougies de 15 min) |
| R3 | Fausse cassure de l'ouverture : la plage des 30 premières minutes est cassée (clôture de 5 min au-delà) puis la clôture revient dedans dans les 3 bougies suivantes : position vers l'autre bout de la plage (objectif), stop au plus extrême depuis la cassure ; un trade par séance |

**B. Des filtres de journée pour Z12**, connus avant l'ouverture :

| | Filtre |
|---|---|
| F1 | pas de trade les jours d'annonce de la Fed (calendrier officiel, `fonds/fomc.py`) : la règle du vrai bot, que l'arène ne simulait pas |
| F2 | pas de trade si l'écart d'ouverture dépasse 1 % (dans un sens ou l'autre) |
| F3 | pause d'une séance après une séance perdante de Z12 |
| F4 | limite du jour du bot de 250 $ au lieu de 400 $ |

## Verdict (2014 - 2026, cadre de l'arène)

Pour les 7 tests : t des résultats par séance d'au moins 2 (pour R1 - R3 : la stratégie seule) et survie à
Benjamini-Hochberg (q = 5 %) sur les 7 ; positif sur 2014 - 2022 et 2023 - 2026 ; t d'au moins 1,5 avec 6 $ de frais ;
au moins 9 années positives sur 13. Puis :
- **R1 - R3, avec Z12 sur le même compte** : survie à 60 séances d'au moins 95 %, au plus 20 % de comptes neufs grillés
  dans l'année, au plus 0,15 master grillé par an, net par an au moins 30 % au-dessus de Z12 seul, au moins 50 % des
  séances tradées ;
- **F1 - F4** : strictement moins de comptes neufs grillés dans l'année que Z12, pas plus de masters grillés par an, et un
  net par an au moins égal.
