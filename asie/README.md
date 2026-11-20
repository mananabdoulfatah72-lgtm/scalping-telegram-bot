# Minuit à Paris : la réouverture du soir (machine 7, règles fixées le 20 novembre 2026, avant tout calcul)

## La demande

> Tous les jours à minuit, heure de Paris, il se passe une dinguerie à l'ouverture de la session asiatique, beaucoup
> plus clean que l'ouverture US. La majorité de mes gains actuels viennent de la session asiatique. Étudie tous les
> phénomènes et études possibles, trouve ce qui est compatible avec l'ouverture asiatique et le meilleur marché.

## Ce que « minuit à Paris » est vraiment

- **18 h à New York : la réouverture quotidienne des futures du CME** (Globex), après la pause de 17 h à 18 h. C'est
  minuit à Paris presque toute l'année (6 heures d'écart), et 23 h pendant environ trois semaines par an, quand les
  États-Unis et l'Europe ne changent pas d'heure le même jour.
- **Ce n'est pas l'ouverture de Tokyo** (9 h à Tokyo = 1 h à Paris en hiver, 2 h en été), ni celle de Hong Kong et de
  Shanghai (9 h 30 = 2 h 30 à Paris en hiver). De novembre à mars, c'est aussi l'ouverture de Sydney.
- **Chez Bulenox, on peut y trader** : la session qui rouvre à 18 h fait partie de la journée de trading suivante. Il
  faut seulement être à plat avant 16 h 59 (New York).

## Ce que disent les études

- **La hausse des indices américains se fait la nuit.** Les futures du S&P 500 ont gagné l'essentiel de leur hausse
  hors de la séance de New York (Cliff, Cooper, Gulen 2008 ; Lou, Polk, Skouras 2019).
- **Mais pas à la réouverture.** Boyarchenko, Larsen et Whelan (« The Overnight Drift », Review of Financial Studies,
  2023) la trouvent concentrée entre 2 h et 3 h (New York), à l'ouverture européenne, et plus forte après des ventes en
  fin de séance américaine. Bondarenko et Muravyev (« Market Return Around the Clock », JFQA) : sur 2004 - 2018, les
  quatre heures de 23 h 30 à 3 h 30 (New York) font toute la hausse ; le volume et la volatilité montent d'un coup à
  18 h et à l'ouverture de Hong Kong et de la Chine, puis retombent.
- **Et elle a disparu.** Les auteurs de la Fed de New York (« The Disappearing Overnight Drift », juillet 2026) ne la
  trouvent plus sur 2021 - 2025 ; les fonds créés pour la capter (NightShares) ont fermé.
- **Volume** : pendant les heures d'Asie, 50 à 100 fois moins de contrats que pendant la séance américaine.

## Déjà testé dans le projet (pas refait)

- `nuit/` (branche `claude/keen-babbage-r686cl`) : achat à 18 h, vente à 9 h 30 sur NQ et ES, rejeté (NQ : t 1,74).
- `sessions24/`, machine 5 : fixing de Tokyo, cassure des 30 ou 60 premières minutes de Tokyo, fourchette d'Asie cassée
  à Londres, Tokyo → Londres et New York → Tokyo. Rien après frais : les effets existent, mais sont 2 à 3 fois plus
  petits que les frais.
- `sessions24/`, machine 6 : jours « gotobi » du yen (échoue au coffre), écart du week-end (non tradable sur la CME :
  tout se fait avant la réouverture de 18 h).

**Jamais testé : la réouverture de 18 h elle-même.** C'est l'objet de cette machine.

## Données

- **HistData, barres de 5 minutes en UTC, 2012 → 2 octobre 2026**, fichiers `sessions24/annees/` de la branche
  `claude/keen-babbage-r686cl` : Nasdaq 100 et S&P 500 (cotations CFD, corrélation 0,999 - 1,000 avec les futures
  après recalage, `sessions24/README.md`), or, yen, dollar australien, euro, livre. Pétrole exclu (s'arrête en 2023).
- **Couverture mesurée avant ces règles** : indices et or sans barre entre 17 h et 18 h, avec une barre à 18 h 00 pour
  92 à 97 % des soirs de semaine ; les devises cotent sans interruption.
- **Contrôle sur de vrais futures** : barres d'une heure de Databento, NQ et ES (`nuit/donnees/`, jusqu'au 28 septembre
  2026), pour les fenêtres qui tombent sur des heures pleines.
- Heures en New York (America/New_York), changements d'heure compris. Entrées et sorties à l'ouverture des barres.

## Les soirs étudiés

Du lundi au jeudi soir (chacun suivi d'une journée de trading). Le dimanche soir est exclu (écart du week-end, déjà testé
par la machine 6).

## Les familles (aucun réglage après coup)

| # | Famille | Règle | Nombre |
|---|---|---|---|
| R1 | **Dérive de la réouverture** | Position à l'ouverture de la barre de 18 h 00, sortie à 19 h 00, 21 h 00 ou 23 h 30. Indices et or : achat seulement (dérive de nuit positive dans les études). Devises : achat et vente (pas de sens connu ; achat = achat de la première devise : euro, livre, dollar australien, dollar contre le yen). | 3 × 3 + 4 × 2 × 3 = 33 |
| R2 | **Le soir contre la fin de séance américaine** | Signal : sens du mouvement de 15 h 00 → 16 h 00 (dernière heure de New York) ou de 9 h 30 → 16 h 00 (séance entière), entre les ouvertures de ces barres. À 18 h 00 : position contraire (retour, l'idée de Boyarchenko et al.) ou dans le même sens (continuation) ; sortie à 19 h 00, 21 h 00 ou 23 h 30. | 7 × 2 × 2 × 3 = 84 |
| R3 | **Cassure de la fourchette de réouverture** | Fourchette des barres de 18 h 00 → 18 h 15 ou 18 h 00 → 18 h 30 (au moins 2 barres). Première clôture de 5 minutes au-delà, avant 20 h 00 ; entrée à l'ouverture de la barre suivante ; stop de l'autre côté de la fourchette ; sortie à 21 h 00, 23 h 30 ou 3 h 00 (ouverture européenne). Un trade par soir. | 7 × 2 × 3 = 42 |
| R4 | **Cassure de l'ouverture de Hong Kong et de Shanghai** | Fourchette de 9 h 30 → 10 h 00, heure de Hong Kong (Asia/Hong_Kong). Première clôture au-delà avant 11 h 30 (Hong Kong) ; stop de l'autre côté ; sortie à 12 h 00 (Hong Kong, pause de midi) ou à 3 h 00 (New York). | 7 × 2 = 14 |

**173 stratégies.** Frais d'un aller-retour, ceux de la machine 5 : 1,5 point sur le Nasdaq (MNQ), 0,9 point sur le
S&P 500 (MES), 1,5 point de base sur les devises, 2 points de base sur l'or.

## Le tri (celui des machines 5 et 6)

1. **Exploration 2012 - 2022**, gains nets par soir :
   - t ≥ 2 ;
   - placebo battu à 95 % : R1, la même fenêtre décalée à toutes les autres heures de la journée (pas de 5 minutes, à
     plus de 2 heures de 18 h) ; R2, R3 et R4, 1 000 tirages au hasard du sens de chaque trade, mêmes heures ;
   - positive dans au moins 2 des 3 sous-périodes (2012 - 2015, 2016 - 2019, 2020 - 2022) ;
   - Benjamini-Hochberg à 10 % sur les p des placebos des 173 ;
   - moins de 200 soirs avec un trade : « non testable ».
2. **Coffre 2023 → 2 octobre 2026, ouvert une seule fois** pour les survivantes : même sens, t au moins égal au seuil
   de Bonferroni (5 % unilatéral, m survivantes), positive au moins 3 années sur 4 (2026, incomplète, compte).
3. **Réalisme**, pour celles qui passent le coffre : frais doublés (la nuit, l'écart entre acheteurs et vendeurs est plus
   large) ; pour les indices, mêmes fenêtres sur les vrais futures (Databento) quand elles tombent sur des heures
   pleines. Ensuite seulement : le compte Bulenox, puis le papier.

## Pour information seulement (aucune décision) : minuit est-il « plus propre » que 15 h 30 ?

Pour le Nasdaq, le S&P 500 et l'or, sur 2012 - 2022 et sur 2023 - 2026 :
- la volatilité moyenne de chaque barre de 5 minutes, de 17 h à 3 h (New York) ;
- l'amplitude de la première heure (plus haut − plus bas), en points, après 18 h 00 et après 9 h 30 ;
- l'efficacité du mouvement de la première heure : |clôture − ouverture| ÷ somme des |variations de 5 minutes|
  (1 = une ligne droite, proche de 0 = des allers-retours), après 18 h 00 et après 9 h 30.
