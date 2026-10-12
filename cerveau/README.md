# Second cerveau

Un cerveau de neurones en 3D : chaque neurone est une note de la recherche.
Page publiée : https://claude.ai/artifact/PGPr62imebYHe3k7GfpGvn (privée).

## Ce qu'il fait

- L'écran ne montre que le cerveau. Deux petits boutons ronds : le micro (couper ou rallumer l'écoute) et la conversation écrite, cachée par défaut.
- Le cerveau parle en tant que Claude, l'auteur de la recherche, à la première personne. Il reçoit à chaque question les souvenirs de l'utilisateur.
- Une seule touche au départ réveille le cerveau. Les navigateurs l'imposent pour le son et le micro. Ensuite, plus rien à toucher :
  - l'écoute est continue (reconnaissance vocale du navigateur, mode continu) ;
  - une phrase est finie après environ 0,85 s de silence ;
  - l'écoute se rouvre toute seule quand le navigateur la ferme.
- La réponse est lue phrase par phrase pendant qu'elle s'écrit.
- On peut lui couper la parole en parlant :
  - pendant qu'il parle, seules les phrases finies sont jugées ;
  - une phrase dont au moins la moitié des mots viennent de ce qu'il vient de dire est son propre écho, et elle est ignorée ;
  - une vraie phrase, d'au moins deux mots, le fait taire et devient la nouvelle question.
- Le cerveau réagit : tes mots entrent vers le centre, ses phrases partent du centre, et il respire quand il parle.
- Les neurones sont rangés par aires, sans légende à l'écran :
  - le lobe préfrontal porte les objectifs ;
  - le cortex moteur porte le bot ;
  - l'avant porte les prop firms et la robustesse ;
  - l'arrière porte la recherche ;
  - les lobes temporaux portent les données ;
  - l'hippocampe porte les souvenirs.
- Recherche BM25 locale, citations cliquables dans la conversation écrite. Outils `chercher_notes` et `retenir` (qui refuse mots de passe, clés et identifiants). Souvenirs et 12 derniers échanges gardés dans `data/users/<id>/`, qui est privé.
- Si le micro est bloqué dans la page, il passe à la dictée de l'appareil : Windows + H, la dictée du Mac, ou le micro du clavier du téléphone. Il envoie tout seul après 1,7 s sans changement. La case est verrouillée pendant qu'il parle, pour qu'il ne s'écrive pas lui-même.
- Sans Claude, il passe en mode local et répond avec les extraits des notes.

## Fichiers

- `construire.py` rassemble trois sources :
  - 20 notes de cœur écrites à la main ;
  - les README des dossiers (titre, intro, conclusion) ;
  - `fonds/essais.csv`.

  Il calcule les liens (TF-IDF, dossier, catégorie) et vérifie qu'aucun secret n'est présent. Il écrit `savoir.json`, puis `cerveau.html` à partir de `page.html`.
- `page.html` : la page (three.js r128, shaders de lueur, orbite, conversation).
- Pour mettre le cerveau à jour après de nouvelles recherches : `cd cerveau && python3 construire.py`, puis republier `cerveau.html`.

## Contrôles

Tous faits dans Chromium sans écran, à 1280 px et à 400 px.

- Aucune erreur JS, aucun défilement horizontal, et plus aucune bulle d'aire à l'écran.
- Conversation simulée (micro, voix et Claude simulés, écho du haut-parleur activé) :
  - réveil, puis salut, dont l'écho est ignoré ;
  - une question parlée donne une seule réponse, lue en 4 phrases, chaque écho ignoré, puis il retourne à l'écoute ;
  - une deuxième question est coupée par la voix après sa première phrase, puis la troisième question reçoit sa réponse ;
  - le micro se coupe puis reprend ;
  - la conversation écrite s'ouvre ;
  - le mode dictée sous Windows marche quand le micro est refusé.
- La vraie reconnaissance vocale, Claude et la mémoire en base ne peuvent être essayés que dans claude.ai.
