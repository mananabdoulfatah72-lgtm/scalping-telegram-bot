# Second cerveau

Un cerveau de neurones en 3D : chaque neurone est une note de la recherche.
Page publiée : https://claude.ai/artifact/PGPr62imebYHe3k7GfpGvn (privée).

## Ce qu'il fait

- 189 neurones et 587 connexions, rangés par aires :
  - le lobe préfrontal porte tes objectifs ;
  - le cortex moteur porte le bot ;
  - l'avant gauche porte les prop firms, l'avant droit la robustesse ;
  - l'arrière porte la recherche et les tournois ;
  - les lobes temporaux portent l'order flow et les données ;
  - l'hippocampe porte les souvenirs.
- Tu poses une question. Une recherche BM25 trouve les notes proches, elles s'allument, et des impulsions partent du centre.
- Claude répond depuis ton compte claude.ai (capacité `sample`, sans abonnement en plus). Il cite les neurones utilisés ; un clic sur une citation ouvre la note.
- Deux outils servent à Claude :
  - `chercher_notes` pour fouiller le cerveau ;
  - `retenir` pour créer un souvenir. Il refuse les mots de passe, les clés et les identifiants.
- Les souvenirs et les 12 derniers échanges sont gardés dans `data/users/<id>/`, qui est privé.
- La voix : la dictée du clavier sert pour poser la question. Le bouton « Voix » lit la réponse (speechSynthesis).
- Sans Claude (page ouverte hors de claude.ai, ou permission refusée), il passe en mode local : il répond avec les extraits des notes.

## Fichiers

- `construire.py` rassemble trois sources :
  - 20 notes de cœur écrites à la main ;
  - les README des dossiers (titre, intro, conclusion) ;
  - `fonds/essais.csv`.

  Il calcule les liens (TF-IDF, dossier, catégorie) et vérifie qu'aucun secret n'est présent. Il écrit `savoir.json`, puis `cerveau.html` à partir de `page.html`.
- `page.html` : la page (three.js r128, shaders de lueur, orbite, conversation).
- Pour mettre le cerveau à jour après de nouvelles recherches : `cd cerveau && python3 construire.py`, puis republier `cerveau.html`.

## Contrôles

- Chromium sans écran, à 1280 px et à 400 px : aucune erreur JS, aucun défilement horizontal.
- Le rendu 3D s'affiche.
- La réponse locale marche, avec ses citations cliquables.
- Un souvenir crée un neurone blanc ; un mot de passe est refusé.
- La partie Claude et la mémoire en base ne peuvent être essayées que dans claude.ai.
