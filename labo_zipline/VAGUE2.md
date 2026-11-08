# Labo zipline, vague 2 : des effets publiés, testés après leur publication (règles fixées avant tout calcul, 8 novembre 2026)

La vague 1 (`REGLES.md`) n'a rien trouvé : une règle de tendance classique ne bat l'achat-conservation sur aucun des 9
actifs. On cherche maintenant parmi des effets **documentés par la recherche**, et chacun est jugé sur la période qui
**suit sa publication** (vrai hors échantillon : les auteurs ne pouvaient pas l'avoir ajusté dessus ; beaucoup d'effets
s'affaiblissent après publication, McLean et Pontiff 2016).

## Données

- Fonds indiciels : prix **ajustés des dividendes** (Yahoo, `auto_adjust`), téléchargés par GitHub Actions
  (`telecharger_ajuste.py`, `.github/workflows/donnees-ajustees.yml`) dans `labo_zipline/donnees/ajuste.csv.gz`. Les
  prix du radar sont bruts (SPY à 324,87 $ le 2 janvier 2020) et oublieraient les dividendes, énormes sur les obligations.
  Si le téléchargement échoue, les prix bruts du radar sont utilisés et c'est dit.
- Cryptos, VIX, VIX à 3 mois, taux des bons du Trésor à 3 mois (^IRX) : radar (`radar/donnees/jour/yahoo`).
- Bot 3 en 1 : le rejeu minute par minute de l'arène (`ml/arene/bots.py`).

Tous les rendements sont en excès du taux sans risque (^IRX) : l'argent hors marché rapporte ce taux, l'achat-conservation
aussi est mesuré en excès. Les décisions sont prises à une clôture et jouent à partir de la séance suivante.

## Les 12 tests

| Test | Effet (source) | Règle | Hors échantillon |
|---|---|---|---|
| Z1, Z2 | Tournant du mois (Lakonishok et Smidt 1988 ; McConnell et Xu 2008) | investi du dernier jour de bourse du mois au 3e jour du mois suivant (entrée à la clôture de l'avant-dernier jour, sortie à la clôture du 3e), sinon hors marché ; QQQ (Z1), SPY (Z2) | 2009 - 2026 |
| Z3, Z4, Z5 | Exposition gérée par la volatilité (Moreira et Muir 2017) | à chaque fin de mois, poids = c ÷ variance réalisée du mois écoulé (rendements quotidiens), plafonné à 2 ; c = 1 ÷ moyenne passée de (1 ÷ variance), calculée sur le passé seul ; SPY (Z3), QQQ (Z4), BTC (Z5) | 2016 - 2026 (BTC : 2016 - 2026, jamais étudié par les auteurs) |
| Z6, Z7 | Structure du VIX (signal connu des praticiens depuis le début des années 2010) | investi le jour J seulement si le VIX était sous le VIX à 3 mois à la clôture de J − 1, sinon hors marché ; SPY (Z6), QQQ (Z7) | 2015 - 2026 |
| Z8 | Tendance de chaque marché (Moskowitz, Ooi et Pedersen 2012) | 22 fonds (SPY, QQQ, IWM, EFA, EEM, EWJ, EWG, EWZ, FXI, TLT, IEF, TIP, HYG, LQD, GLD, SLV, USO, UNG, UUP, FXE, FXY, VNQ) ; à chaque fin de mois, signe du rendement sur 252 séances × (10 % ÷ volatilité des 63 dernières séances annualisée), plafonné à ± 2, moyenne des fonds disponibles ; acheteur ou vendeur | 2012 - 2026 |
| Z9, Z10 | Élan des cryptos sur 4 semaines (Liu et Tsyvinski 2021) | chaque dimanche, investi pour 7 jours si le rendement des 28 derniers jours est positif, sinon hors marché ; BTC (Z9), ETH (Z10) | 2019 - 2026 |
| Z11 | Le rendement vient la nuit (Lou, Polk et Skouras 2019) | QQQ acheté à chaque clôture, vendu à l'ouverture suivante | 2014 - 2026 |
| Z12 | Structure du VIX appliquée au Bot 3 en 1 | le Bot 3 en 1 ne trade pas le jour J si le VIX était au-dessus ou égal au VIX à 3 mois à la clôture de J − 1 | 2014 - 2026 (rejeu de l'arène) |

Frais : fonds 2 points de base par unité échangée, cryptos 0,31 % par passage (0,26 % + 5 points de glissement).

## Verdict (fixé d'avance)

**Z1 - Z7, Z9 - Z11** (une stratégie sur un actif), sur la période hors échantillon :
1. alpha de la régression des rendements quotidiens de la stratégie sur ceux de l'achat-conservation, t d'au moins 2
   (erreurs de Newey-West, 5 retards) ;
2. ratio de Sharpe supérieur à celui de l'achat-conservation ;
3. alpha positif sur chacune des deux moitiés ;
4. avec des frais doublés, t de l'alpha d'au moins 1,5.

**Z8** (acheteur et vendeur) : t des rendements d'au moins 2, positif sur chaque moitié, t d'au moins 1,5 avec frais doublés.

**Z12** : les 6 règles de `ml/arene/VARIANTES.md` face au Bot 3 en 1 de base (t, deux moitiés, frais doublés, années
positives, survie et comptes grillés sur le compte financé, pire baisse).

Benjamini-Hochberg (q = 5 %) sur les 12 p du premier critère. Retenu = passe ses critères **et** la correction.

**Deux moteurs** : le calcul principal est fait avec pandas ; chaque test retenu sur un fonds est rejoué dans zipline et
doit donner le même verdict.

## Écartés d'avance

- L'élan entre les grandes valeurs du Nasdaq : la liste du radar est celle des géants **d'aujourd'hui**, choisis après
  coup (biais du survivant), le test serait faux.
- La dérive avant les réunions de la Fed : pas de calendrier fiable des réunions dans nos données.
