# Relief de la volatilité implicite (23 octobre 2026) : description, pas un test

Page interactive en 3D (`relief.html`, publiée en artefact) demandée par l'utilisateur : ce que disent les options du
S&P 500 et ce que les stratégies de volatilité implicite peuvent ou ne peuvent pas apporter à la zone.

- `page.html` : la page sans données ; `donnees.py` : calcule `donnees.json` et écrit `relief.html` (page + données).
- Lancer depuis la racine : `KB=<branche de recherche extraite> python3 etude_large/volatilite/donnees.py`.

## Données (gratuites)

Clôtures quotidiennes Yahoo (`donnees_libres/yahoo/jour/`) : VIX9D, VIX, VIX3M, VVIX, future ES ; dernière clôture de
chaque semaine (825 semaines, 7 janvier 2011 → 23 octobre 2026). Volatilité réalisée : écart type des rendements du ES
sur 21 séances, annualisé. Zone : V1 sans filtre, pas de zone les jours de la Fed, 1 MNQ au prix du 20 octobre 2026,
frais compris (`partie_d.chemins_zone()`), 3 614 séances 2012 - 2026, VIX et pente VIX / VIX3M **de la veille**.

## Ce que montrent les chiffres

| Mesure | Valeur |
|---|---|
| Semaines en contango (VIX < VIX3M) | 93,2 % |
| VIX moins la volatilité réalisée du mois suivant (prime de variance) | +3,4 points en moyenne, positive 82,6 % du temps |
| Dernière semaine (23 octobre 2026) | VIX9D 15,7 ; VIX 16,8 ; VIX3M 18,8 (contango) ; VVIX 95,7 |
| Gain moyen de la zone par séance (1 MNQ) | +20,1 $ |

Zone par sextile du VIX de la veille ($ par séance, du VIX le plus bas au plus haut) :

| Période | 9,1-12,9 | 12,9-14,4 | 14,4-16,2 | 16,2-18,4 | 18,4-22,3 | 22,3-82,7 |
|---|---|---|---|---|---|---|
| 2012 - 2022 | +7,2 | +0,7 | +12,2 | +36,9 | +41,7 | +25,2 |
| 2023 - 2026 | +32,5 | +29,1 | +13,6 | +29,7 | −5,2 | +67,1 |

Le lien entre le niveau du VIX et les gains de la zone change de forme d'une période à l'autre : pas de règle à en
tirer (même conclusion que la vague 9, condition « VIX haut »). Les options et les futures VIX ne sont pas permis chez
Bulenox ou Topstep (futures du CME seulement) : les stratégies classiques de volatilité (vente de straddles, calendar
spreads, roulement des futures VIX) ne sont pas accessibles au compte. Idée non testée : une largeur de zone tirée de
la volatilité implicite (VXN) plutôt que des 14 séances passées ; à pré-enregistrer avant tout calcul si elle est
retenue.
