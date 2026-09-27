# Fonds multi-stratégies

Un fonds quantitatif ne cherche pas une stratégie miracle : il combine plusieurs sources de gain
**indépendantes**, chacune modeste, et contrôle le risque de l'ensemble. Ce dossier est le moteur
de ce fonds : chaque source est testée avec les mêmes règles, et seules celles qui passent entrent
dans le portefeuille.

## Les formules

**1. Diversification.** Avec N sources de même Sharpe S et une corrélation moyenne ρ entre elles :

    Sharpe du portefeuille = S × √( N / (1 + (N − 1) × ρ) )

6 sources à Sharpe 0,4 corrélées à 0,1 donnent 0,8 ; sans corrélation, 0,98.

**2. Même risque pour chaque source (ciblage de volatilité ex ante).** Chaque jour, une source est
multipliée par `10 % / σ`, où σ est la volatilité annualisée de ses 252 derniers jours (au moins 126,
connue la veille). Une fenêtre d'un an plutôt que 60 jours, parce que certaines sources ne tradent que
quelques jours par an (veille de la Fed) : sur 60 jours leur risque serait mal mesuré.
Le portefeuille est la moyenne des sources validées, puis ramené à **12 % de risque par an** de la
même façon.

**3. t de Student.** `t = moyenne / (écart-type / √n)`. Sert à juger si un gain moyen se distingue du hasard.

**4. Sharpe dégonflé (Bailey et López de Prado, 2014).** Plus on teste de stratégies, plus la
meilleure a un beau Sharpe par hasard. Avec N essais au total dans le projet (`essais.csv`) et
T jours de données, le Sharpe qu'on atteindrait par pur hasard est :

    SR0 = √(1/T) × ( (1 − γ) Φ⁻¹(1 − 1/N) + γ Φ⁻¹(1 − 1/(N e)) ),  γ = 0,5772

et la probabilité que le vrai Sharpe soit positif malgré les N essais :

    DSR = Φ( (SR − SR0) √(T − 1) / √(1 − γ₃ SR + (γ₄ − 1)/4 × SR²) )

(SR journalier, γ₃ asymétrie, γ₄ kurtosis des rendements). Donnée à titre d'information.

## Les règles d'entrée (fixées le 27 septembre 2026, avant les tests de la phase 2)

Une source entre dans le fonds si elle passe **les 5 règles**, calculées sur toute son histoire
disponible, frais compris :

1. **Rentable** : Sharpe net ≥ 0,20.
2. **Régulière** : Sharpe positif dans au moins 2 des 3 tiers de son histoire.
3. **Survit à sa publication** : Sharpe positif après la date de publication de l'étude
   (règle appliquée seulement s'il y a au moins 2 ans de données après).
4. **Pas un hasard** : pour une stratégie qui choisit *quand* ou *quoi* acheter, son Sharpe doit
   dépasser celui d'au moins 90 % de versions placebo (mêmes positions ou mêmes jours, mais placés
   au hasard). Ne s'applique pas à une prime de risque pure (acheter tout, tout le temps).
5. **Nouvelle** : corrélation ≤ 0,6 avec chaque source déjà validée (sinon elle fait doublon).

Ces règles s'appliquent aussi aux sources déjà testées avant la création du fonds. Le test placebo de
la tendance faisait mieux que 83,5 % des placebos sur 2007-2026 (voir `tendance/README.md`) : ce
résultat était connu quand la règle 4 a été fixée à 90 %, et la règle s'applique à la tendance comme
aux autres.

Chaque test est inscrit dans `essais.csv`, y compris les échecs : c'est le N du Sharpe dégonflé.

Non retenu : un frein qui coupe le risque après une baisse. Il n'est pas testé ici et, dans les
études, il coûte souvent plus qu'il ne protège (il vend après la baisse et rate le rebond).

## Résultats de la phase 2 (27 septembre 2026)

41 essais au total dans le projet. Chaque source est ramenée à 10 % de risque, frais compris,
sur toute son histoire disponible. `python3 moteur.py` refait tout (2 minutes) ; détails dans
`resultats.txt` et `resultats.json`.

| Source | Depuis | Sharpe | 3 tiers | Après publication | Placebo battu | Verdict |
|---|---|---|---|---|---|---|
| Acheter tout (parité des risques) | 1999 | 0,30 | +0,10 / +0,43 / +0,45 | +0,41 | sans objet | **validée** |
| Suivi de tendance | 1999 | 0,30 | −0,09 / +0,65 / +0,53 | +0,55 | 74 % | rejetée (règle 4) |
| Zone de bruit Nasdaq | 2011 | 0,40 | −0,98 / +0,97 / +1,14 | +0,76 (2,4 ans) | 100 % | **validée** |
| Momentum croisé | 2000 | −0,05 | −0,09 / −0,10 / +0,03 | −0,02 | 49 % | rejetée |
| Valeur (retour sur 5 ans) | 2005 | −0,18 | −0,15 / +0,17 / −0,56 | −0,34 | 52 % | rejetée |
| Actions pilotées par la volatilité | 1999 | 0,50 | +0,17 / +0,80 / +0,54 | +0,51 | 87 % | rejetée (règle 4) |
| Tournant du mois | 1998 | 0,14 | +0,25 / −0,01 / +0,20 | +0,10 | 48 % | rejetée |
| Veille de la Fed | 2011 | 0,32 | −0,01 / +0,41 / +0,52 | +0,50 | 86 % | rejetée (règle 4) |

Portefeuilles à 12 % de risque, depuis juillet 1999 :

| Portefeuille | Sharpe | Gain/an | Pire baisse | Années positives |
|---|---|---|---|---|
| Fonds des sources validées (achat + zone de bruit) | 0,56 | +6,8 % | −42 % | 61 % |
| Mélange actuel du robot (tendance + achat) | 0,65 | +8,1 % | −20 % | 68 % |

### Ce qu'on en retient

- **Trois idées échouent nettement** sur nos marchés : momentum croisé, valeur, tournant du mois.
  Même les versions tirées au hasard font aussi bien.
- **Trois idées échouent de peu, au seul test du hasard** : tendance (74 %), actions pilotées par
  la volatilité (87 %), veille de la Fed (86 %). Toutes trois restent positives après leur publication.
- **Les règles strictes donnent un fonds moins bon que le mélange actuel.** Le test a révélé un défaut
  des règles : le placebo n'est pas aussi sévère pour toutes les sources. Pour la zone de bruit, il
  tire le *sens* au hasard (facile à battre si la stratégie gagne avant frais) ; pour la tendance, il
  décale les positions dans le temps en gardant leur penchant acheteur (bien plus dur). Les règles ne
  sont pas modifiées après coup pour repêcher une source : une version 2 sera fixée avant les
  prochains tests, sur de nouvelles données.
- **Aucune source n'est prouvée par nos seules données.** Le Sharpe dégonflé (probabilité d'un vrai
  Sharpe positif compte tenu des 41 essais) reste sous 70 % pour toutes. Avec 17 marchés et 20 ans,
  la puissance statistique est trop faible : il faut plus de marchés.
- **Le robot ne change pas** : il continue le mélange tendance + achat en argent virtuel.

### Limites connues

- Rendements « futures » reconstruits à partir d'ETF avant l'existence de certains contrats.
- Veille de la Fed : 14 annonces sur 125 exclues (jour de changement d'échéance du contrat ES, les
  prix de la veille et du jour viennent de deux contrats différents). À refaire avec les deux
  contrats (phase 3).
- Zone de bruit : placebo par sens tiré au hasard sur la journée entière (approximation).

### Phase 3 prévue

Barres journalières de 40 à 50 futures CME (céréales, bétail, softs, énergie, métaux, taux, devises,
indices) chez Databento depuis 2010, avec le contrat suivant de chaque marché. Deux ou trois fois plus
de marchés pour retester tendance, momentum et valeur, et une nouvelle source : le carry (écart entre
les deux premiers contrats, Koijen, Moskowitz, Pedersen, Vrugt 2018).

## Règles version 2 (fixées le 27 septembre 2026, avant de télécharger les données de la phase 3)

La phase 2 a montré que le test du hasard n'avait pas la même sévérité pour toutes les sources. La
version 2 remplace seulement la règle 4 ; les règles 1, 2, 3 et 5 ne changent pas.

4. **Pas un hasard (v2)** : le placebo retire *seulement* ce que la source prétend savoir faire,
   et garde tout le reste (mêmes marchés, mêmes tailles de position, mêmes frais) :
   - une source qui choisit un **sens** (acheteur ou vendeur) : sens tiré au hasard pour chaque
     marché à chaque rééquilibrage ;
   - une source qui choisit des **dates** : même position, à des dates tirées au hasard ;
   - une source qui **dose** son exposition : mêmes doses, attribuées aux périodes au hasard.
   Seuil : faire mieux que **95 %** des placebos (au lieu de 90 %), parce que tirer le sens au hasard
   donne un placebo plus facile à battre que l'ancien décalage dans le temps.

Application : la version 2 juge toutes les sources à partir de la phase 3, y compris celles de la
phase 2. Pour la zone de bruit, les actions pilotées par la volatilité et le tournant du mois, le
placebo était déjà du bon type ; seul le seuil passe à 95 %. Les sources multi-marchés (achat,
tendance, momentum, valeur) sont rejugées sur les nouvelles données (40 futures CME depuis 2010),
qui remplacent les ETF ; la veille de la Fed est rejugée avec les 14 annonces récupérées.

Nouvelle source testée en phase 3, règles fixées ici : **carry croisé** (Koijen, Moskowitz, Pedersen,
Vrugt, 2018). Carry d'un marché = (ln F proche − ln F suivant) / écart entre leurs échéances en
années (positif quand le contrat proche vaut plus que le suivant). Chaque fin de mois, dans chaque
famille, poids = rang du carry − rang moyen, même construction que le momentum croisé.
