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
- Le mode appel (micro vert) : on se parle à voix haute, comme au téléphone.
  - Le cerveau écoute avec la reconnaissance vocale du navigateur.
  - Il lit sa réponse phrase par phrase pendant qu'elle s'écrit, puis il se remet à écouter tout seul.
  - Toucher le rond lui coupe la parole. Après 4 silences, il se met en pause.
  - Pendant que tu parles, des impulsions entrent vers le centre. Pendant qu'il parle, elles partent du centre et le cerveau respire.
  - Si le navigateur bloque le micro dans la page, il passe à la dictée du clavier. Il envoie tout seul après 1,7 s sans changement, et répond quand même à voix haute.
- Le bouton « Voix » lit aussi les réponses écrites.
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
- Mode appel, avec le micro, la voix et Claude simulés :
  - une question parlée, puis 4 phrases lues dans l'ordre, puis le retour à l'écoute, puis la pause après 4 silences ;
  - la coupure de parole, suivie d'une deuxième question ;
  - le micro refusé, puis la dictée envoyée toute seule et lue à voix haute.
- La partie Claude, la mémoire en base et le vrai micro ne peuvent être essayés que dans claude.ai.
