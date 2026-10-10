# Bot 3 en 1 pour Quantower (zone de bruit + filtre delta + RSI(2))

Le bot qui trade pour de vrai, sur un compte Rithmic (par exemple DayTraders) avec Quantower. Il regroupe :
- **la zone de bruit** (V1, `zone/robot.py` sur main) : contrôle toutes les 30 minutes de 10 h à 15 h 30, sortie au
  plus tard à 16 h (heure de New York) ;
- **le filtre delta** (H1, `orderflow/`) : une entrée de zone n'est prise que si le delta (achats agressifs − ventes
  agressives) des 30 minutes du NQ va dans son sens. Le delta est lu en direct dans les transactions Rithmic, plus
  besoin de Databento ;
- **le RSI(2)** de Connors (`tournoi8/`) : décision à 15 h 50 (heure de New York), position tenue la nuit et le
  week-end si la règle le dit.

Taille : 1 MNQ par source. La position nette sur MNQ est la somme des deux (zone + RSI(2)).

## Les pièces

| Dossier | Rôle |
|---|---|
| `Bot3en1.Core/` | Le moteur : calendrier, zone, filtre, RSI(2). Ne dépend d'aucune plateforme. |
| `Bot3en1.Quantower/` | L'adaptateur Quantower : lit les transactions du NQ, construit les minutes, appelle le moteur, aligne la position sur MNQ, envoie les messages Telegram. |
| `Bot3en1.Replay/` | Rejeu de vérification sur des barres historiques. |
| `Bot3en1.TestQuantower/` | Joue l'adaptateur, transaction par transaction, contre une imitation de Quantower. |
| `Bot3en1.TestPlafond/` | Contrôles du plafond du jour (système Static) sur le moteur seul, avec des prix fabriqués. |
| `installer.bat`, `installer.ps1` | Installation sur le PC (double-clic) : dans Quantower et/ou Optimus Flow (une version de Quantower, gratuite avec la démo Optimus Futures). Si la plateforme n'est pas trouvée, glisser son dossier sur `installer.bat` ou coller son chemin quand le script le demande. |

## Vérifications faites (3 octobre 2026)

1. **Le moteur prend exactement les décisions du robot Python.**
   - Avril - 25 septembre 2026, avec le vrai delta : 77 trades de zone gardés, 20 écartés, +3 830,0 $. RSI(2) :
     5 trades, mêmes jours, mêmes prix, +536,0 $. Total **+4 366,0 $**, comme le rejeu Python.
   - 2023 - 25 septembre 2026, sans filtre : **+21 767,0 $**, comme `protection/` ; RSI(2) +11 098,5 $ sur 40 trades,
     comme le coffre de `tournoi8/`.
   - Même résultat avec les contrats tirés du calendrier (le mode du direct).
2. **L'adaptateur reproduit le rejeu.** Joué transaction par transaction sur avril - septembre 2026 :
   - les 174 signaux de zone et les 10 décisions du RSI(2) sont identiques ;
   - 164 ordres envoyés, position finale à plat, aucune erreur.
   - Un défaut a été trouvé et corrigé pendant ce test : l'attente de 15 secondes entre deux ordres utilisait
     l'horloge du PC au lieu de celle du serveur.
3. **Ce qui n'a pas pu être vérifié ici :** la compilation contre la vraie bibliothèque de Quantower (elle n'est pas
   publiée en ligne, elle s'installe avec Quantower), et le comportement réel des ordres chez Rithmic. D'où le test
   obligatoire sur un compte de simulation (voir le guide).

Relancer les vérifications (avec le kit .NET 8) :

```
dotnet run -c Release --project Bot3en1.Replay -- <nasdaq100_1min.csv.gz> <agresseurs.csv.gz> 2026-04-01 2026-09-25
SANS_FILTRE=1 dotnet run -c Release --project Bot3en1.Replay -- <nasdaq100_1min.csv.gz> - 2023-01-03 2026-09-25
dotnet run -c Release --project Bot3en1.TestQuantower -- <dossier avec nq_1min.csv.gz> <nq_1min.csv.gz> <agresseurs.csv.gz> 2026-04-01 2026-09-25
PLAFOND=500 dotnet run -c Release --project Bot3en1.TestQuantower -- <memes arguments>
dotnet run -c Release --project Bot3en1.TestPlafond
```

**Plafond du jour corrigé pour le système Static (8 octobre 2026)** :
- **Le défaut.** Le plafond comptait le gain d'un RSI(2) gardé depuis plusieurs jours à partir de son prix
  d'achat, et non depuis la veille. Il ne regardait pas non plus la nuit.
- **Maintenant, il fait ce que `static50k/` a simulé :**
  - le gain du jour est compté depuis le début de la journée de trading de la firme (18 h la veille). Un RSI(2) gardé
    la nuit compte à partir du dernier prix avant la pause de 17 h ;
  - le plafond est vérifié en séance à chaque fin de minute, et hors séance (après la fin de la séance, et avant
    9 h 30) à chaque transaction du NQ ;
  - une fois le plafond atteint, plus rien jusqu'à 18 h ;
  - en cas de redémarrage dans la journée, le bot reprend le gain déjà réalisé, la référence du RSI(2) et le plafond
    atteint (`etat.json`).
- **Revue de code indépendante, puis corrections :**
  - le gain du jour et la référence étaient perdus au redémarrage ;
  - pendant 2 secondes à 16 h, le plafond de nuit pouvait partir avant la fermeture de la zone ;
  - la nuit, le plafond n'était vérifié qu'une fois par demi-seconde ;
  - une transaction de 18 h pouvait arriver avant le changement de journée.
- **Vérifié :**
  - `Bot3en1.TestPlafond` : 15 contrôles sur 15 ;
  - avec le plafond à 0, les deux rejeux (+21 767,0 $ et +4 366,0 $) et le test de l'adaptateur (164 ordres, +4 370,0 $,
    position finale à plat, aucune erreur) sont identiques à avant la correction ;
  - avec `PLAFOND=500` et une transaction chaque soir à 19 h, l'adaptateur passe par 18 h et par le plafond hors séance
    sans erreur : 14 plafonds atteints d'avril à septembre 2026, 160 ordres, position finale à plat.
- **Limite des tests.** Le rejeu et le test de l'adaptateur n'ont que les minutes de 9 h 30 à 16 h. Leur référence
  pour le RSI(2) est donc la clôture de 16 h, alors qu'en direct c'est le dernier prix avant 17 h.

Le fichier des agresseurs se fabrique depuis `orderflow/donnees` (volumes par seconde regroupés par minute).

## Comment il fonctionne en direct

- **Au démarrage :**
  - il télécharge les barres d'une minute que le robot GitHub publie chaque soir
    (`zone/robot/nq_1min.csv.gz` sur main) ;
  - il les rejoue pour retrouver les paramètres de la zone (veille, bruit sur 14 jours) et l'état du RSI(2) ;
  - il relit sa position du RSI(2) dans `C:\Bot3en1\etat.json`.
- **Pendant la séance :**
  - chaque transaction du NQ alimente la minute en cours (prix, volume, côté agresseur) ;
  - à chaque fin de minute, le moteur décide ;
  - l'adaptateur aligne la position sur MNQ par un ordre au marché.
- **Démarrage après 9 h 30 :**
  - les minutes passées sont rattrapées grâce à l'historique de Quantower ;
  - la zone ne prend pas un trade déjà commencé, seulement les signaux suivants.
- **Changement d'échéance (mars, juin, septembre, décembre) :**
  - le RSI(2) se ferme la veille, comme dans le backtest ;
  - le bot prévient si les symboles choisis ne sont plus ceux du jour. Il faut alors choisir les nouveaux (NQ et
    MNQ) dans les réglages, quatre fois par an.
- **Arrêt d'urgence :** créer un fichier nommé `STOP` dans `C:\Bot3en1` : le bot ferme tout et ne trade plus.
- **Messages :** chaque ordre et chaque alerte vont dans `C:\Bot3en1\journal.txt`, et sur Telegram si le jeton et le
  numéro de conversation sont remplis (ils restent sur le PC, jamais dans le dépôt).
- **Plafond du jour** (réglage, 0 par défaut) :
  - c'est le système retenu par `static50k/` :
    - **0 pendant l'évaluation Static et sur la démo** ;
    - **500 sur le compte Pro** (après la réussite) ;
  - en séance, le bot vérifie le plafond à chaque fin de minute. Le backtest le vérifiait à l'intérieur de la minute.
  - hors séance, il le vérifie à chaque transaction du NQ, **si le PC est allumé**. PC éteint la nuit : le RSI(2) reste
    ouvert, et le plafond n'est vérifié qu'au retour.

## Mode à plat pour Bulenox (et FundedNext) — ajouté le 10 octobre 2026

Bulenox oblige à être à plat avant 16 h 59 (New York) : le RSI(2) gardé plusieurs jours y est interdit. Le réglage
**« Mode a plat chaque jour »** fait ce que les vagues 8 à 11 ont simulé. Désactivé (par défaut), le bot ne change pas.

**Les 4 changements :**
1. **RSI(2) de nuit seulement, sur 1 MES.** La règle est décidée à 15 h 50 comme avant, mais rien n'est acheté à 15 h 50 :
   - le bot achète 1 MES à la réouverture de 18 h (dimanche 18 h avant un lundi) ;
   - il revend à 9 h 30.
   - Démarré plus tard dans la nuit, il achète jusqu'à 9 h 25, pas au-delà.
2. **Frein.** Quand le compte finit une journée à 750 $ ou plus sous son plus haut de fin de journée, la zone trade sur MES
   au lieu de MNQ toute la séance suivante. Plus précisément : coussin = solde − plancher, avec plancher = plus haut de fin
   de journée − 2 500 $, arrêté à 50 100 $ ; frein si coussin < 1 750 $. Le solde est lu dans Quantower ; s'il est
   illisible, le bot utilise sa propre estimation et le signale.
3. **Pas de zone les jours d'annonce de la Fed.** Les dates sont dans `Calendrier.JoursFed` jusqu'à fin 2027 ; on peut en
   ajouter dans les réglages.
4. **Plafond de gain du jour : 500 $, seulement sur le compte Master** (0 pendant le challenge). Il est vérifié deux fois
   par seconde sur la valeur réelle du compte (solde + gains latents), sinon sur l'estimation du bot. Une fois atteint, tout
   est fermé et plus rien n'est pris jusqu'à 18 h.

**Réglages pour Bulenox 50K (option 2, perte calculée en fin de journée) :**

| Réglage | Challenge | Compte Master (après la réussite) |
|---|---|---|
| Mode a plat chaque jour | coché | coché |
| MNQ, MES, NQ | échéance du moment (ex. MNQZ6, MESZ6, NQZ6) | idem |
| MNQ par source | 1 | 1 |
| Plafond de gain du jour | **0** | **500** |
| Limite de perte du jour | 1 050 (juste avant les 1 100 $ de Bulenox) | 1 050 |
| Frein | 750 | 750 |
| Solde de départ / perte max / blocage | 50 000 / 2 500 / 100 | 50 000 / 2 500 / 100 |

**Au passage au compte Master :**
- choisir le nouveau compte dans les réglages ;
- le bot repart alors d'un plus haut de 50 000 $ (il reconnaît le changement de compte) ;
- mettre le plafond à 500 ;
- demander chaque retrait dès que Bulenox l'autorise (au moins 1 000 $, 52 600 $ gardés).

**Vérifié (10 octobre 2026) :**
- **Ancien mode inchangé :**
  - rejeu 2023-2026 : +21 767,0 $ ;
  - test de l'adaptateur avec trades de zone (sans filtre), avec et sans plafond : ordres, journal et messages identiques
    octet pour octet à avant le changement.
- **RSI(2) de nuit :** d'avril à septembre 2026, le bot achète **les mêmes 19 nuits** que la recherche Python
  (`vague4/moteur4.py`, rsi = 4).
- **Adaptateur en mode à plat** (avril - septembre 2026, transaction par transaction) :
  - à plat chaque jour à 16 h, jamais de MNQ la nuit, 0 erreur ;
  - avec un solde lu à 49 000 $, toute la zone part sur MES ;
  - avec le plafond à 500 $, 7 journées arrêtées.
- **Moteur :** `Bot3en1.TestAPlat`, 21 contrôles sur 21 (frein avant et après blocage du plancher, Fed, nuit, plafond).

```
dotnet run -c Release --project Bot3en1.TestAPlat
A_PLAT=1 SANS_FILTRE=1 dotnet run -c Release --project Bot3en1.TestQuantower -- <dossier> <nq_1min.csv.gz> <agresseurs.csv.gz> 2026-04-01 2026-09-25
```

**Limites :**
- La lecture du solde (`Account.Balance`) et des gains latents (`Position.GrossPnL`) passe par réflexion, pour ne pas
  bloquer la compilation si Quantower les nomme autrement. Au premier lancement, vérifier dans le journal que le message
  « mode a plat : solde ... » donne le vrai solde, et non « solde estimé ».
- Le flux du MES doit arriver : sans transaction MES récente, le bot n'achète pas le RSI(2) de nuit.
- PC (ou serveur) allumé de 18 h à 9 h 30 (New York) pour le RSI(2) de nuit, soit de minuit à 15 h 30 heure de Paris, en
  plus de la séance.

## Limites connues

- Les ordres sont au marché. Le backtest compte 1,5 point par aller-retour pour la zone et 1 $ + 1 tick par ordre
  pour le RSI(2) ; un remplissage réel peut coûter un peu plus.
- Si le robot GitHub n'a pas tourné (données en retard), la zone utilise des paramètres d'un jour plus ancien : le
  bot le signale.
- Le PC (ou un serveur loué) doit rester allumé et connecté du lundi au vendredi, de 15 h 30 à 22 h 15 (heure de
  Paris).
- Ne pas trader MNQ à la main sur le même compte : le bot réalignerait la position.

## Essai sur le compte d'essai Optimus Flow / Ironbeam (critères fixés le 6 octobre 2026, avant le premier lancement)

But : vérifier que le bot **trade correctement** sur une vraie plateforme. Ce n'est pas un test de rentabilité :
sur une dizaine de séances, le gain dépend surtout du hasard (environ ±1 000 $ pour un gain attendu d'environ
+250 $).

Période : du 7 au 16 octobre 2026, soit environ 8 séances, jusqu'à la fin de la démo. Le bot tourne de 15 h 30 à
22 h 05, heure de Paris.

**Feu vert pour un vrai compte** si tout ceci est vrai :
1. au moins 6 séances jouées sans erreur ni arrêt imprévu ;
2. chaque signal de zone (heure, sens, gardé ou écarté) et chaque décision du RSI(2) sont les mêmes que ceux du
   robot virtuel (`zone/robot.py` sur main) pour la même séance. Toute différence doit être expliquée et corrigée ;
3. jamais plus de 1 MNQ par source, et aucune position de zone après 16 h (New York) ;
4. glissement moyen d'au plus 1 tick par ordre sur MNQ ;
5. le delta noté par le bot à chaque signal a le même signe que celui de l'export Ironbeam pour la même minute.

**Pas de feu vert** si une différence n'est pas expliquée, si la taille est fausse ou si une sortie est manquée :
correction, puis nouvel essai.

Le gain ou la perte de ces séances n'entre pas dans la décision.
