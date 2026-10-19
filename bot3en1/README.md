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
| `telecharger.ps1` | Installation en une ligne à coller dans PowerShell : télécharge seulement ce dossier, puis lance `installer.ps1`. Recoller la ligne met le bot à jour : `irm https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/refs/heads/claude/keen-babbage-r686cl/bot3en1/telecharger.ps1 \| iex` |
| `installer.bat`, `installer.ps1` | Installation sur le PC (double-clic) : dans Quantower et/ou Optimus Flow (une version de Quantower, gratuite avec la démo Optimus Futures). Si la plateforme n'est pas trouvée, glisser son dossier sur `installer.bat` ou coller son chemin quand le script le demande. Sans winget (Windows Server 2022 des serveurs loués), le kit .NET s'installe avec le script officiel de Microsoft. |

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
- **Message à chaque contrôle (19 octobre 2026)** : toutes les 30 minutes, le journal et Telegram donnent l'heure de Paris
  et de New York, le prix, les limites d'achat et de vente, le VWAP, le delta des 30 minutes et la décision (achat,
  vente, cassure écartée, en position avec son niveau de sortie, trade écarté en attente de relance, pas de signal).
  Aucune décision ne change : mêmes ordres que sans message (banc et adaptateur avec le vrai delta).
- **Relance du filtre (19 octobre 2026, `relance/README.md`)** : réglage « Filtre delta : relance », coché par défaut.
- **Alerte « marché invisible » (18 octobre 2026) :**
  - dès la première transaction du NQ reçue après le lancement, le bot écrit « flux NQ recu (prix) : le bot voit le
    marche ». Lancé vers 9 h 15 (New York), cette ligne doit apparaître en quelques secondes ;
  - si aucune transaction n'est arrivée 3 minutes après le lancement (à partir de 8 h, le NQ s'échange avant
    l'ouverture) ou après l'ouverture, le bot écrit en rouge « ALERTE : aucune transaction NQ recue depuis le
    lancement », puis toutes les 15 minutes ;
  - quand le flux revient après l'alerte de silence de 3 minutes, il écrit « flux NQ revenu » ;
  - pourquoi : le 16 octobre 2026, le bot a tourné toute la séance sans recevoir un seul prix du NQ, et sans rien dire
    (l'alerte de silence ne marchait qu'après une première transaction). Il a manqué une vente de 449 points. Signes
    dans le journal : aucune ligne de zone à 10 h, et une décision du RSI(2) de 15 h 50 faite sur la clôture de la
    veille. Le solde du compte était illisible le même jour ;
  - **19 octobre 2026, cause probable** : un symbole ou un compte restauré depuis les réglages de Quantower peut être une
    copie qui ne reçoit rien (d'où aussi un solde lu à 0). Au lancement, le bot reprend désormais les objets de la
    connexion active (`Core.GetSymbol(symbole.CreateInfo())`, comme le modèle de stratégie Quantower ; compte de même Id
    dans `Core.Accounts`), par réflexion. À chaque alerte de flux, il les reprend encore et refait l'abonnement. L'heure
    d'une transaction est lue en UTC quel que soit son genre, et une heure illisible est signalée au lieu d'être ignorée ;
  - le message « solde du compte illisible » est désormais en rouge, lui aussi ;
  - **solde illisible** : le bot écrit aussi une ligne « diagnostic du solde » (valeur brute de `Account.Balance` et
    champs du compte qui ressemblent à un solde, noms et valeurs seulement), relit le solde chaque minute et écrit
    « solde du compte lu » dès qu'il y arrive. Tant qu'il reste illisible, le réglage « solde actuel du compte » sert
    de point de départ : il est repris une seule fois par valeur (gardé dans l'état), puis le bot le suit avec ses
    propres trades à 18 h. Contrôle : `SOLDE_MANUEL=51000` (plancher 48 500 $, objectif atteint dès 2 050 $ de gain,
    valeur non reprise au lancement suivant) ;
  - **Telegram** : jeton et numéro nettoyés (tous les espaces, même au milieu, et « bot » devant le jeton) ; un envoi refusé est écrit dans le
    journal avec la raison donnée par Telegram et un conseil (jeton faux, numéro faux ou bouton Démarrer pas appuyé,
    bot bloqué, internet), une seule fois tant que l'erreur ne change pas, jamais avec le jeton ;
  - contrôle : `SANS_NQ=1` dans `Bot3en1.TestQuantower` (première alerte à 9 h 33, puis toutes les 15 minutes, aucun
    ordre) ; `LANCEMENT=09:10` (alerte à 9 h 14, avant l'ouverture). Les 5 modes du banc donnent les mêmes ordres et le
    même journal du moteur qu'avant, avec une seule ligne « flux NQ recu » et aucune alerte en 6 mois.
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
1. **RSI(2) de nuit seulement, sur 1 MES** — **décoché par défaut depuis le 13 octobre 2026** (réglage « RSI(2) de nuit
   sur MES », voir plus bas : Bulenox interdit de garder une position la nuit). Coché, la règle est décidée à 15 h 50
   comme avant, mais rien n'est acheté à 15 h 50 :
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

**Réglages pour Bulenox 50K (option 2, perte calculée en fin de journée), version 30 jours (vague 13, version D) :**

| Réglage | Challenge (30 jours) | Compte Master (après la réussite) |
|---|---|---|
| Mode a plat chaque jour | coché | coché |
| RSI(2) de nuit sur MES | **décoché** | **décoché** |
| MNQ, MES, NQ | échéance du moment (ex. MNQZ6, MESZ6, NQZ6) | idem |
| MNQ par source | **4** | **1** |
| Plafond de gain du jour | 0 | **500** |
| Limite de perte du jour | **1 000** (100 $ de marge avant les 1 100 $ de Bulenox) | 1 000 |
| Frein | **0** | **750** |
| Solde de départ / perte max / blocage | 50 000 / 2 500 / 100 | 50 000 / 2 500 / 100 |
| Plus haut de fin de journée déjà atteint | 0 (compte neuf) | 0 (compte neuf) |
| Challenge : objectif | **53 000** | **0** |
| Challenge : dernier jour (AAAA-MM-JJ) | **date de fin donnée par Bulenox** | vide |
| Challenge : MNQ en fin de challenge | **6** | **0** |
| Challenge : nombre de dernières séances | 5 | (sans effet) |

**Challenge de 30 jours (vagues 12 et 13, 12 octobre 2026)** : Bulenox limite maintenant le challenge à 30 jours. Le bot
tel quel n'y valide qu'environ 5 % des challenges.
- **Vague 12 :** 4 MNQ par source et pas de frein pendant le challenge, environ 40 % de validés en simulation.
- **Vague 13, version D (retenue) :** environ 53 à 55 % de validés en simulation (45 % en 2025). Elle ajoute deux
  réglages :
  1. **Arrêt à l'objectif.**
     - Pendant la journée, dès que le compte atteint 53 050 $ (l'objectif de 53 000 $ plus 50 $ pour les frais de
       sortie), le bot ferme tout et ne prend plus rien jusqu'à 18 h.
     - Les jours suivants, si le solde de 18 h est à 53 000 $ ou plus, il ne trade plus du tout sur ce compte et le dit
       chaque soir.
     - Pas besoin de 6 000 $ quand 3 000 suffisent : c'est ce qui évite de reperdre un challenge déjà gagné.
  2. **Fin de course.** Si l'objectif n'est pas atteint, le bot passe à 6 MNQ par source (zone, et RSI(2) de nuit s'il
     est coché)
     pendant les 5 dernières séances avant la date de fin.
     - Il change de taille seulement quand il est à plat, normalement à 18 h.
     - Le décompte saute les week-ends et les jours fériés de la Bourse.
     - La date à mettre est le dernier jour où Bulenox laisse trader le compte (30 jours après l'achat, à vérifier sur
       le tableau de bord de Bulenox).
- Voir `vague12/README.md` et `vague13/README.md` avant d'acheter.

**Règles confirmées par Bulenox par e-mail (13 octobre 2026), et ce que fait le bot :**
- **Journée de trading de 17 h à 16 h (heure de Chicago)**, soit de 18 h à 17 h à New York. Le bot compte sa journée,
  sa limite de perte et son plafond à partir de 18 h (New York) : c'est la même journée.
- **Tout fermer avant 15 h 59 (Chicago), soit 16 h 59 (New York), 22 h 59 à Paris.** La zone ferme à 16 h (New York),
  22 h à Paris. Deux sécurités en plus depuis le 13 octobre :
  - **filet de 16 h 30 :** entre 16 h 30 et 18 h (New York), si une position MNQ ou MES est encore ouverte (ordre refusé,
    coupure, position ouverte à la main), le bot ferme tout ;
  - **arrêt du bot :** en mode à plat, arrêter la stratégie dans Quantower ferme d'abord toutes les positions. Le bot
    peut être relancé le jour même.
- **« Holding positions overnight is strictly prohibited ».** Le RSI(2) de nuit garde 1 MES de 18 h à 9 h 30 : il est
  donc **décoché par défaut**. Simulation du challenge de 30 jours (vague 13, version D, filtre fort), il n'apportait
  presque rien :

  | Période | Avec RSI(2) de nuit | Sans |
  |---|---|---|
  | 2012-2026 | 54,6 % | 54,4 % |
  | 2023-2026 | 55,4 % | 56,0 % |
  | 2025 | 44,7 % | 41,5 % |

- **Bots permis**, mais seulement un outil fait par le titulaire du compte, pour lui seul. Les outils « publicly
  distributed » sont interdits : passer le dépôt GitHub en privé une fois le bot installé.
- **100 $ par mois** si on se connecte à Rithmic par une API tierce ou un logiciel composite. Demander à Bulenox si
  Quantower avec Rithmic est concerné.
- **Taille (« EOD Dynamic Scaling Plan ») :** la limite de contrats monte avec le gain en fin de journée. Au premier
  palier (gain de 0 à 1 500 $), 2 contrats standard, soit 20 micros (1 standard = 10 micros chez Bulenox). Le bot tient
  au plus 6 MNQ à la fois pendant le challenge (vérifié sur le test de 30 jours), sous la limite dès le premier jour.
- **Limite de perte du jour : 1 000 $ dans le bot (13 octobre 2026), pour 1 100 $ chez Bulenox.** Le bot ferme tout
  après 3 secondes de confirmation : dans un marché rapide, la fermeture peut finir un peu plus loin que le réglage.
  À 1 050 $, la marge n'était que de 6 points du NQ en 4 MNQ, 4 en 6 MNQ ; à 1 000 $, elle double. Simulation du
  challenge de 30 jours (version D, sans RSI de nuit, filtre fort) : 54,4 % de validés avec la limite de Bulenox seule,
  54,6 % à 1 050 $, 54,5 % à 1 000 $, 54,2 % à 950 $, 53,6 % à 900 $. Si la limite de Bulenox est touchée quand même,
  le compte est suspendu pour le reste de la journée, sans être perdu (d'après Bulenox et les guides).
- **Ce que le bot ne peut pas empêcher :** la perte maximale suivie en fin de journée (2 500 $). C'est elle qui fait
  perdre environ un tiers des challenges en simulation : ce n'est pas une infraction, c'est un challenge raté.

**Au passage au compte Master :**
- choisir le nouveau compte dans les réglages ;
- le bot repart alors d'un plus haut de 50 000 $ (il reconnaît le changement de compte) ;
- mettre MNQ par source à 1, le frein à 750, le plafond à 500, l'objectif à 0, la date de fin vide et MNQ en fin de
  challenge à 0 (colonne de droite du tableau) ;
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
- **Moteur :** `Bot3en1.TestAPlat`, 21 contrôles sur 21 (frein avant et après blocage du plancher, Fed, nuit, plafond) ;
  34 depuis le 12 octobre.

```
dotnet run -c Release --project Bot3en1.TestAPlat
A_PLAT=1 SANS_FILTRE=1 dotnet run -c Release --project Bot3en1.TestQuantower -- <dossier> <nq_1min.csv.gz> <agresseurs.csv.gz> 2026-04-01 2026-09-25
```

**Vérifié (12 octobre 2026), réglages du challenge de 30 jours :**
- **Rien d'autre ne change.** Nouveaux réglages à 0 : ordres, journal et messages identiques octet pour octet à avant,
  dans les 4 modes testés (mode à plat, avec frein, avec plafond, ancien mode).
- **Moteur :** `Bot3en1.TestAPlat`, 34 contrôles sur 34. Les nouveaux portent sur :
  - le plafond de l'objectif : 53 050 $ moins le solde de 18 h, ou le plus petit avec le plafond du jour ;
  - le décompte des séances : semaine de Thanksgiving, 3 juillet 2026, après la date de fin ;
  - la taille : 4 MNQ, puis 6 MNQ les 5 dernières séances.
- **Adaptateur, transaction par transaction** (mode à plat, sans le filtre) :
  - **taille de fin de course** (date de fin au 8 juillet 2026) : mêmes trades qu'avant, en 6 MNQ au lieu de 1,
    seulement du 1er au 8 juillet (3 juillet férié sauté), puis retour à 1 ;
  - **objectif** : après le déclenchement, plus aucun ordre jusqu'à la fin du test. Solde lu à 53 000 $ dès le départ :
    aucun ordre du tout ;
  - **6 challenges de 30 jours rejoués en 2026** avec tous les réglages de la colonne challenge : 5 objectifs atteints
    sans aucun ordre ensuite, et 1 non atteint, joué en 6 MNQ sur ses 5 dernières séances. Ce test vérifie la mécanique,
    pas la rentabilité : il est fait sans le filtre et ne simule pas la perte du compte.
- **Défaut ancien trouvé et corrigé pendant ce test.** Quand la dernière séance de l'historique était incomplète, la
  zone restait coupée **pour toute la durée du lancement du bot**, pas seulement un jour. Exemples de séances
  incomplètes : demi-séance du 3 juillet, lendemain de Thanksgiving, 24 décembre, trou dans les données. Même chose après
  un rattrapage de transactions raté. Exemple : démarré le lundi 6 juillet 2026, le bot ne prenait aucun trade de zone
  pendant 30 jours. Maintenant, la zone est réautorisée à chaque nouvelle séance : démarré le 6 juillet, il prend les
  mêmes trades que s'il tournait depuis avril.

```
A_PLAT=1 SANS_FILTRE=1 TAILLE=4 OBJECTIF=53000 DATE_FIN=2026-05-12 TAILLE_FIN=6 SEANCES_FIN=5 FREIN=0 LIMITE=1050 \
  dotnet run -c Release --project Bot3en1.TestQuantower -- <dossier> <nasdaq100_1min.csv.gz> <agresseurs.csv.gz> 2026-04-13 2026-05-12
```

**Vérifié (13 octobre 2026), RSI(2) de nuit décoché, filet de 16 h 30 et arrêt du bot :**
- RSI(2) de nuit coché : ordres, journal et messages identiques octet pour octet à avant, dans les 5 modes testés (à plat,
  frein, plafond, challenge de 30 jours, ancien mode).
- Décoché (par défaut) : aucune nuit achetée, mêmes trades de zone, 0 erreur.
- Position MNQ ouverte à la main à 16 h 35 : fermée au tic suivant. Position MES ouverte puis arrêt du bot : tout fermé.

**Revue indépendante du code (10 octobre 2026), puis corrections :**
- **Défaut grave corrigé : le fichier STOP la nuit.** Le bot revendait puis rachetait le MES toutes les 16 secondes
  (15 ordres en 4 minutes dans le scénario de la revue). Maintenant : un seul ordre de vente, plus rien ensuite.
- **Plafond et limite de perte.** Ils ne se déclenchent plus sur une lecture fausse du compte (perte comptée deux fois
  pendant qu'une position se ferme). Il faut que la valeur lue dans Quantower et l'estimation du bot soient d'accord,
  3 secondes de suite, sans ordre envoyé dans les 10 dernières secondes.
- **RSI(2) de nuit.** Le bot n'achète que si la décision de 15 h 50 de la séance d'avant est bien connue. Sinon, il
  envoie une alerte au lieu d'acheter sur une décision périmée. La décision est enregistrée pour les redémarrages.
- **Un fichier d'état par compte** (`etat_<compte>.json`) : le challenge et le Master ne s'écrasent plus.
- **Nouveau réglage « plus haut de fin de journée déjà atteint »**, pour un compte qui a déjà tradé.
- **Détails :**
  - le gain du jour n'est plus compté deux fois après un redémarrage en séance ;
  - le solde estimé se recale sur le vrai solde ;
  - une alerte part si le flux du MES manque à l'heure de l'achat de nuit.
- **Revérifié après les corrections :**
  - ancien mode identique, octet pour octet ;
  - mêmes 19 nuits que la recherche ;
  - à plat chaque jour, 0 erreur ;
  - 21 contrôles du moteur sur 21 ;
  - scénarios de la revue repassés (STOP, redémarrage à 2 h, fausse lecture de perte).

**Limites :**
- Si le bot est éteint pendant toute une séance avec un MES de nuit ouvert, il le revend au redémarrage s'il est entre
  9 h 30 et 18 h, sinon seulement le lendemain à 9 h 30.
- Si le PC dort à 18 h, la nouvelle journée ne commence qu'au tic suivant après 18 h. Une nuit sans tic après 18 h fait
  manquer l'achat de nuit.
- La lecture du solde (`Account.Balance`) et des gains latents (`Position.GrossPnL`) passe par réflexion, pour ne pas
  bloquer la compilation si Quantower les nomme autrement. À chaque lancement, vérifier dans le journal que le message
  « mode a plat : solde ... » donne le vrai solde, et non « solde estimé ».
- Le flux du MES doit arriver : sans transaction MES récente, le bot n'achète pas le RSI(2) de nuit.
- RSI(2) de nuit coché seulement : PC (ou serveur) allumé de 18 h à 9 h 30 (New York), soit de minuit à 15 h 30 heure
  de Paris, en plus de la séance.

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
