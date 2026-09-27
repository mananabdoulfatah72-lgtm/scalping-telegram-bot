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
multipliée par `10 % / σ`, où σ est la volatilité annualisée de ses 60 derniers jours (connue la veille).
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
