# Arène, vague 4 : le même Supertrend, en mieux (règles fixées avant tout calcul, 9 novembre 2026)

Suite de la vague 3 (aucun cousin du Supertrend ne fait nettement mieux ; V6, Supertrend + VWAP, le plus proche). Ici on
garde **les signaux du Supertrend NQ** et on change ce qu'on en fait : trier les signaux, régler la taille.

Même cadre que l'arène (`bots.py`, minute par minute, compte financé Bulenox Master 50K Option 2, vie réelle, 3 $ de frais,
limite du bot 400 $ par MNQ, 1 point de glissement à une sortie forcée). Mesure sur **2017 - 2026** (le tri apprend sur
les années d'avant), comparée au Supertrend NQ sur la même période.

## Les 3 candidats

**W1 · Tri des signaux par apprentissage (méta-étiquetage, López de Prado 2018).** Chaque trade du Supertrend NQ reçoit
une étiquette : gagnant après frais ou non. Un XGBoost (200 arbres, profondeur 3, pas 0,05, sous-échantillon 0,8 des
lignes et des colonnes, au moins 20 trades par feuille) apprend à partir de ce qui est connu **avant** l'entrée :
- les 22 variables du labo à la dernière bougie de 15 minutes terminée avant l'entrée ;
- le sens du trade, la minute d'entrée, l'écart à la VWAP de la séance en ATR (signé dans le sens du trade), le
  rendement depuis l'ouverture et l'écart d'ouverture (signés), le VIX moins le VIX à 3 mois de la veille, le nombre de
  trades déjà pris dans la séance et leur résultat.

Marche en avant : chaque année Y de 2017 à 2026, le modèle apprend sur tous les trades de 2011 à Y − 1 et trie ceux de Y.
Un trade est pris si la probabilité prédite dépasse la part de trades gagnants de l'apprentissage ; sinon le bot reste à
plat jusqu'au signal suivant.

**W2 · Taille selon l'agitation.** Signaux du Supertrend inchangés ; 2 MNQ (limite 800 $) quand la volatilité des
20 dernières séances (connue la veille) est dans la moitié basse de l'année écoulée, 1 MNQ (limite 400 $) sinon.

**W3 · W1 + W2** : les trades gardés par W1, avec la taille de W2.

## « Mieux que le Supertrend NQ » sur 2017 - 2026 : toutes ces conditions

1. t des résultats par séance d'au moins 2, et survie à Benjamini-Hochberg (q = 5 %) sur les 3 ;
2. positif sur 2017 - 2022 **et** sur 2023 - 2026 ;
3. avec 6 $ de frais (par MNQ), t d'au moins 1,5 ;
4. au moins 7 années positives sur 10 ;
5. trade au moins 80 % des séances ;
6. compte financé : survie à 60 séances d'au moins 10 points au-dessus du Supertrend, au moins 20 % de masters grillés
   par an en moins, pire baisse pas plus de 25 % plus profonde ;
7. net par an au moins égal à celui du Supertrend (mieux, c'est aussi gagner au moins autant).

## V6 en observation

V6 (Supertrend + VWAP), non retenu à la vague 3, est ajouté à la station du terminal comme agent **en observation**
(papier, sans argent), avec sa fiche du 11 août au 2 novembre, pour le suivre sur les séances neuves.

## Réserve

Les règles du Supertrend ont été choisies en regardant cet historique ; le tri et la taille sont jugés hors échantillon
(2017 - 2026), mais leurs réglages (paramètres du modèle, seuil, moitié basse) sont fixés ici sans avoir été essayés.
