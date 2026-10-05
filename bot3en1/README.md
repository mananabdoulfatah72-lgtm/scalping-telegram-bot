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
```

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
  - c'est la piste 4 de `protection/`, à n'activer que sur le compte financé, si l'utilisateur la choisit (500 $) ;
  - le bot la vérifie à chaque fin de minute (le backtest la vérifiait à l'intérieur de la minute).

## Limites connues

- Les ordres sont au marché. Le backtest compte 1,5 point par aller-retour pour la zone et 1 $ + 1 tick par ordre
  pour le RSI(2) ; un remplissage réel peut coûter un peu plus.
- Si le robot GitHub n'a pas tourné (données en retard), la zone utilise des paramètres d'un jour plus ancien : le
  bot le signale.
- Le PC (ou un serveur loué) doit rester allumé et connecté du lundi au vendredi, de 15 h 30 à 22 h 15 (heure de
  Paris).
- Ne pas trader MNQ à la main sur le même compte : le bot réalignerait la position.
