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

## Surface de volatilité implicite (23 octobre 2026) : `surface.py`, `surface_page.html`, `surface.html`

Deuxième page, demandée par l'utilisateur (« un meilleur visuel physique 3D ») : la vraie surface par prix d'exercice et
par échéance, et un labo 3D des stratégies de volatilité posées dessus (vendre un straddle, iron condor, calendar,
acheter un straddle ; gain ou perte selon le mouvement et les jours, avec un choc de volatilité réglable).

- Données gratuites : chaînes d'options du QQQ et du SPY chez Yahoo (`donnees_libres/options/`, workflow
  `donnees-options.yml`), cotations de clôture du 22 octobre 2026. Une photo, pas un historique.
- Méthode : milieu de fourchette ; forward de chaque échéance par la parité call-put ; volatilité recalculée (Black sur le
  forward, taux ^IRX) sur les options hors de la monnaie ; lissage SVI par échéance (erreur médiane 1,2 % de la variance).
  La clôture du 22 octobre manquait chez Yahoo : le cours est tiré de la parité de l'échéance du lendemain (QQQ 704,88 ;
  SPY 764,17).
- Ce soir-là : QQQ au cours à 30 jours 25,5 % contre SPY 15,1 % ; put à 90 % +8,8 points au-dessus du cours ; QQQ à 7 jours
  29,1 % contre 24,2 % à un an (le devant au-dessus du fond, profil de lendemain de forte baisse).
- Lancer : `python3 etude_large/volatilite/surface.py` (écrit `surface.json` et `surface.html`).
