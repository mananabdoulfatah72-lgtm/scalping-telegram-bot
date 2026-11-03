# Supertrend : ajouter 1 MNQ quand le prix va dans le sens du Supertrend (règles fixées le 3 novembre 2026, avant calcul)

Demande de l'utilisateur : « à chaque fois que le prix va en direction du Supertrend, on ajoute 1 MNQ […] avec la limite
des 400 $, et on reste sur 1 MNQ quand il va contre ».

Lecture retenue (pyramide des « Turtles », R. Faith, *Way of the Turtle*, 2007) :
- entrée à 1 MNQ comme aujourd'hui ; N = ATR(10) des barres de 5 minutes au moment de l'entrée, fixe pour tout le trade ;
- à la clôture de chaque barre de 5 minutes, si le prix a avancé d'au moins **k × N** dans le sens du trade depuis le dernier
  ajout (ou l'entrée), **+1 MNQ** à l'ouverture suivante, jusqu'à **4 MNQ** au plus ; aucun ajout après 15 h 30 (New York) ;
- rien n'est retiré quand le prix recule : tout est fermé ensemble au retournement du Supertrend, à 15 h 55 ou à la limite ;
- **limite du jour 400 $** sur le résultat de la journée (fermé + latent), au pire prix de chaque minute, 1 point de
  glissement ; frais 3 $ par MNQ ; gains au prix d'aujourd'hui (28 500).
- Deux écarts testés, pas d'autre : **k = 0,5** (règle des Turtles) et **k = 1**. Témoin : 1 MNQ sans ajout, limite 400 $.
- Mesures : 15 ans (2011 - octobre 2026) et depuis 2023 (t, gain par séance, pire journée, journées coupées) ; les 15
  séances du 13 octobre au 2 novembre (export Rithmic) ; challenge depuis 50 000 $ / plancher 49 000 $ suivi en temps réel,
  8 séances (même règle que `audit/machine6`).
