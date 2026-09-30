# Tournoi n°5 : les autres marchés et leurs rendez-vous

Tout ce qui a été testé jusqu'ici tournait autour du Nasdaq et du S&P 500. Or les prop firms laissent
aussi trader les devises, le pétrole, l'or, les taux et le bitcoin de la CME. Ces marchés ont leurs propres
rendez-vous (fixing des devises, rapport sur le pétrole, adjudications du Trésor), étudiés dans des
articles récents. Ce tournoi les teste.

## Règles (fixées le 30 septembre 2026, avant tout calcul)

| # | Stratégie | Marché | Règle | Source |
|---|---|---|---|---|
| A1 | Dollar avant le fixing de Londres | panier 6E, 6B, 6J, 6A, 6C, 6S | vente du panier (achat du dollar) pendant l'heure qui précède le fixing de 16 h à Londres | Krohn, Mueller, Whelan (Journal of Finance, 2024) |
| A2 | Dollar après le fixing de Londres | idem | achat du panier (vente du dollar) pendant l'heure qui suit le fixing | idem |
| B1 à B5 | Momentum de fin de séance | RTY, YM, GC, CL, 6E (un essai par marché) | 30 min avant la fin de la séance du marché : dans le sens du mouvement depuis la clôture de la veille, jusqu'à la fin | Baltussen, Da, Lammers, Martens (JFE, 2021), qui le trouvent sur 60 futures |
| C1 | Rapport EIA sur le pétrole | CL | le mercredi : à 14 h, dans le sens de la demi-heure 10 h 30-11 h (celle du rapport), jusqu'à 14 h 30 | Wen, Indriawan, Lien, Xu (Energy Journal, 2023) |
| D1 | Momentum intrajournalier du bitcoin | bitcoin CME | à 15 h 30, dans le sens de 9 h 30-10 h, jusqu'à 16 h | Shen, Urquhart, Wang (Financial Review, 2022) |
| E1 | Taux avant une adjudication | ZN (10 ans) | le jour d'une adjudication d'obligations du Trésor (2 à 30 ans, à 13 h) : vente de 9 h à 13 h | Lou, Yan, Zhang (2013) ; Krohn et Vala |
| E2 | Taux après une adjudication | ZN | achat de 13 h à 15 h le même jour | idem |

**Essais** : 11.

**Précisions.**
- **Heures** : toutes en heure de New York. Le fixing de 16 h à Londres tombe à 11 h à New York, sauf
  les semaines où un seul des deux pays a changé d'heure (10 h ou 12 h) : l'heure exacte est
  recalculée chaque jour.
- **Séances** (celles déjà téléchargées pour `zone_multi`) :

  | Marché | Séance (heure de New York) |
  |---|---|
  | RTY, YM | 9 h 30-16 h |
  | GC | 8 h 20-13 h 30 |
  | CL | 9 h-14 h 30 |
  | 6E | 8 h 20-15 h |

  Pour B, la « clôture de la veille » est la fin de la séance précédente, dans le même contrat.
- **Données à télécharger** (plafond total : 25 $, vérifié avant) :
  - barres d'une heure des 6 devises et du ZN depuis 2010 ;
  - minutes du bitcoin CME depuis fin 2017 (si le budget le permet ; sinon D1 n'est pas testé) ;
  - dates des adjudications : site du Trésor américain (gratuit).
- **Frais par aller-retour** : 1 tick plus 1 $ par ordre sur les micro-contrats (RTY, YM, GC, CL, 6E,
  micro-bitcoin), comme dans `zone_multi`. Pour les devises du panier et le ZN, 1 tick plus 2,50 $ par
  ordre sur le contrat standard : un contrat standard par devise tient dans un compte de 50K.
- **Périodes** :
  - exploration 2011-2022 pour les devises et le ZN ;
  - 2016-2022 pour RTY, YM, GC, CL, 6E (données depuis 2016 ; RTY depuis juillet 2017) ;
  - 2018-2022 pour le bitcoin ;
  - **coffre 2023-2026** pour tous.

### Le tri

1. t ≥ 2 sur la période d'exploration, sur les rendements quotidiens nets en % du prix, jours sans
   trade compris.
2. Contrôle, selon le type de stratégie :
   - **B, C et D** (minutes) : battre le plus haut t de 20 versions où les minutes de chaque séance sont
     mélangées sans leur volume (leçon du tournoi n°4) ;
   - **A** (une heure précise) : faire mieux que la même heure de trade placée à chacune des autres
     heures de la séance européenne et américaine (de 3 h à 15 h, heure de New York) ;
   - **E** (certains jours) : faire mieux que 95 % de 200 tirages de jours sans adjudication, en même
     nombre.
3. **Coffre 2023-2026** pour les survivants :
   - t ≥ seuil de Bonferroni ;
   - au moins 3 années positives sur 4.

Les 11 essais sont inscrits dans `fonds/essais.csv`. Rien n'est ajouté ni changé après avoir vu les
résultats.
