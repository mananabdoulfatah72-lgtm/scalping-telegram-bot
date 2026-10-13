# Jarvis

Un assistant vocal pour ton PC Windows. Il pense avec Claude et s'affiche sous la forme d'un **cerveau de neurones
en 3D** : chaque compétence a sa zone, et quand Jarvis travaille, la zone concernée s'allume et des impulsions
traversent le réseau jusqu'au noyau.

Tu dis « **Hey Jarvis** », tu parles, il agit et te répond à voix haute. Tu peux aussi lui écrire depuis l'écran,
ou depuis ton téléphone n'importe où (Telegram).

---

## Ce que Jarvis sait faire

| Sur la photo | Ce que fait Jarvis | Ce qu'il faut |
|---|---|---|
| **Tout à la voix** | Mot de réveil « Hey Jarvis » (openWakeWord) et transcription (Whisper) sur le PC, voix neuronale française (Piper). Il commence à parler pendant qu'il finit de réfléchir, puis écoute encore 6 s pour que tu enchaînes sans redire « Hey Jarvis ». | Un micro (installé tout seul) |
| **Vision de l'écran** | « C'est quoi cette erreur ? », « traduis ce qui est à l'écran », « lis-moi ça ». | Rien |
| **Domotique Philips Hue** | Allumer, éteindre, intensité, couleur, scènes, par pièce ou partout. | Le pont Hue (appairage à la voix) |
| **Streaming OBS** | Direct, enregistrement, scènes, replay, micro. | OBS 28 ou plus |
| **Contrôle du PC** | Ouvrir ou fermer des applis, son et lecture média, raccourcis clavier, taper du texte, fenêtres, presse-papiers, fichiers, verrouillage, veille et arrêt, commandes PowerShell. Statistiques en direct : processeur, mémoire, carte graphique, disque, batterie. | Rien |
| **Agenda Google** (avec iCal) | Lit tous tes agendas, y compris ceux auxquels tu es abonné par iCal ; crée des événements. | Un accès Google (10 min, voir plus bas) |
| **Mail Gmail** | Résume les non lus, cherche, lit, écrit des brouillons, envoie. | Le même accès Google |
| **Discord** | Qui t'a mentionné, récap des salons, envoi de messages. | Un bot Discord à toi |
| **Instagram** | Abonnés et vues comparés à la veille, plusieurs comptes, derniers posts. | API officielle de Meta |
| **Réservations web** | Restaurant (TheFork), médecin (Doctolib), coiffeur (Planity) ou n'importe quel site : Jarvis remplit, clique et valide. | Rien (Edge est déjà sur Windows) |
| **Assistant navigateur** | Résumer ou traduire une page, chercher sur le web, gérer les onglets, remplir des formulaires. | Rien |
| **Appels Twilio** | Appeler quelqu'un pour lui lire un message, ou **mener la conversation à ta place** (prévenir d'un retard, prendre rendez-vous) puis te faire le résumé. | Un compte Twilio |
| **Mémoire long terme** | « Retiens que je joue au foot le jeudi », « qu'est-ce que tu sais sur moi ? », « oublie ça ». | Rien |
| **Personnalités** | Majordome pince-sans-rire, neutre, concis, coach, pote : « change de personnalité ». | Rien |
| **Présence** | Sait si ton téléphone est sur le wifi de la maison ; à ton arrivée ou à ton départ, il lance des actions (scène Hue, message…). Notifications sur le téléphone. | IP fixe du téléphone ; appli ntfy |
| **Utilitaires** | Météo, minuteurs annoncés à voix haute, heure et date. | Rien |
| **Serveur MCP** | Claude Desktop, Claude Code ou tout client MCP peuvent utiliser les outils de Jarvis. | Une commande |
| *En plus* | **Telegram** : Jarvis sur ton iPhone partout. Messages, notes vocales, photos. | Un bot Telegram (2 min) |

Ce qui n'est pas configuré s'affiche « À CONFIG. » dans le panneau de droite, et tout le reste marche quand même.

---

## Le cerveau à l'écran

- **18 zones** de couleur : voix, vision, domotique, streaming, PC, agenda, mail, Discord, Instagram, réservations,
  navigateur, appels, mémoire, personnalité, présence, utilitaires, MCP, Telegram.
- Quand Jarvis utilise un outil, sa zone s'illumine, des impulsions partent vers le noyau et le nom de l'action
  s'affiche. Le noyau pulse au rythme de sa voix.
- Autour du cerveau : état (en veille, écoute, réflexion, parle), jauges du PC en direct, minuteurs, journal des
  actions, dialogue.
- **Espace** : parler (comme « Hey Jarvis »). **F** : plein écran. **H** : cacher les panneaux (cerveau seul,
  idéal sur une télé). La souris tourne le cerveau, la molette zoome.

Pour voir le cerveau sans rien configurer : `lancer.bat --demo` (une démonstration joue toute seule).

---

## Installation (Windows 10 ou 11)

Il te faut un micro et des haut-parleurs (ou un casque), internet et environ 3 Go de place. Une carte NVIDIA
accélère la transcription, mais elle n'est pas obligatoire.

1. **Ouvre PowerShell** : clique sur Démarrer, tape `PowerShell`, appuie sur Entrée.
2. **Colle cette ligne** (clic droit dans la fenêtre pour coller), puis appuie sur Entrée :
   ```
   irm https://raw.githubusercontent.com/mananabdoulfatah72-lgtm/scalping-telegram-bot/refs/heads/claude/keen-babbage-r686cl/jarvis/telecharger.ps1 | iex
   ```
   Elle télécharge seulement Jarvis (moins de 1 Mo) dans ton dossier personnel (`C:\Users\TON_NOM\Jarvis`), puis
   installe Python si besoin, les modules, le mot de réveil, la transcription et la voix française. Elle crée
   aussi la configuration et un raccourci **Jarvis** sur le Bureau. Compte 10 à 20 minutes la première fois. Le
   journal complet est enregistré sur le Bureau (`installation_jarvis.txt`). Recoller la même ligne plus tard met
   Jarvis à jour.

   *Autre façon :* télécharge le dépôt en ZIP depuis GitHub (**Code > Download ZIP**, mais il pèse plusieurs
   centaines de Mo à cause des données de trading), ouvre le dossier `jarvis` et double-clique sur `installer.bat`.
3. **Choisis le cerveau** dans la configuration qui s'ouvre à la fin (`%APPDATA%\Jarvis\config.toml`), voir
   ci-dessous. Mets aussi ton prénom dans `proprietaire`.
4. **Double-clique sur Jarvis** sur le Bureau. Le cerveau s'ouvre dans le navigateur. Dis « Hey Jarvis ».

La configuration reste sur ton PC, **jamais dans le dépôt**. Après chaque modification, redémarre Jarvis : ferme
la fenêtre noire, puis relance le raccourci.

### Le cerveau : abonnement Claude ou clé d'API

**Avec ton abonnement Claude (Pro ou Max), sans payer en plus** :
1. Installe Claude Code. Dans PowerShell : `irm https://claude.ai/install.ps1 | iex` (ou, si tu as Node.js :
   `npm install -g @anthropic-ai/claude-code`).
2. Tape `claude` une fois dans un terminal et connecte-toi à ton compte.
3. Laisse `moteur = "auto"` et `cle_api = ""`. Jarvis trouve Claude Code tout seul.

Claude Code reste ouvert en permanence, prêt dès le démarrage de Jarvis : une réponse simple arrive en une à
deux secondes. L'usage compte dans les limites de ton abonnement. Pour aller encore plus vite (un peu moins
malin), mets `modele_claude_code = "haiku"` ou `"sonnet"` dans `[cerveau]`.

**Avec une clé d'API (le plus rapide)** :
1. Sur [console.anthropic.com](https://console.anthropic.com) : **Settings > API keys > Create Key**, puis ajoute
   du crédit dans **Billing**.
2. Colle la clé dans `cle_api = "..."` de la configuration.

Les **conversations téléphoniques** demandent la clé d'API, parce que chaque réplique doit arriver en quelques
secondes.

### Combien ça coûte

| | Prix |
|---|---|
| Moteur Claude Code | Compris dans l'abonnement |
| API, `claude-opus-5-5` (par défaut, le plus intelligent) | 4 $ par million de mots-jetons lus et 20 $ par million écrits. Les consignes et la liste des outils (environ 8 000 jetons) sont mises en cache. Compte environ **1 centime** par demande quand tu enchaînes, et **3 à 6 centimes** pour la première demande après quelques minutes de silence. Soit à peu près **20 à 45 $ par mois** pour 30 demandes par jour. |
| API, `claude-sonnet-5-5` | Moitié prix d'Opus |
| API, `claude-haiku-5-5` | Environ 40 fois moins cher qu'Opus (**1 à 2 $ par mois**). Très bien pour la domotique, le PC et la météo, moins fort pour les longues tâches comme les réservations. |
| Twilio | Un numéro (quelques euros par mois) et quelques centimes par minute d'appel |
| Hue, OBS, Google, Discord, Instagram, ntfy, Telegram, météo | Gratuit |

Le modèle se change dans `[cerveau] modele`.

---

## Utilisation

Quelques exemples (après « Hey Jarvis », ou tapés dans le champ en bas de l'écran) :

- « Allume le salon en bleu à 30 % » · « Mets la scène Détente » · « Éteins tout »
- « Ouvre Spotify » · « Monte le son » · « Pause » · « Piste suivante » · « Tape : j'arrive dans 10 minutes »
- « Comment va le PC ? » · « Qu'est-ce qui prend toute la mémoire ? » · « Verrouille l'ordi »
- « C'est quoi cette erreur ? » · « Traduis ce qu'il y a à l'écran »
- « Lance le live » · « Passe sur la scène Jeu » · « Sauvegarde le replay »
- « Qu'est-ce que j'ai demain ? » · « Ajoute dentiste jeudi à 14 h 30 »
- « Résume mes mails non lus » · « Réponds à Lucas que c'est OK pour samedi »
- « Qui m'a mentionné sur Discord ? » · « Fais-moi le récap du serveur »
- « Combien d'abonnés j'ai gagnés depuis hier ? »
- « Réserve une table pour deux chez Mamma Mia samedi à 20 h » · « Trouve un dentiste dispo cette semaine à Lyon »
- « Résume la page » · « Ferme l'onglet 2 »
- « Appelle le garage pour savoir si la voiture est prête »
- « Retiens que ma copine s'appelle Inès » · « Qu'est-ce que tu sais sur moi ? »
- « Minuteur 12 minutes pour les pâtes » · « Il fait quel temps demain ? »
- « Stop » coupe la parole. « Merci » ou « c'est tout » termine la conversation.

### Aucune confirmation

Jarvis a accès à tout et agit directement, comme quelqu'un de confiance : il envoie, appelle, valide, ferme ou
éteint sans te demander « tu confirmes ? ». Il ne touche jamais aux processus de Windows ni à lui-même.

Si un jour tu veux qu'il demande ton accord avant les actions qui ont des conséquences (envoyer, appeler, payer,
éteindre, commandes…), mets `confirmations = true` dans `[general]` de la configuration. Tu réponds alors « oui »
ou « non » à voix haute, à l'écran ou sur Telegram.

---

## Réglages module par module

Tout se règle dans `%APPDATA%\Jarvis\config.toml` (tape `%APPDATA%\Jarvis` dans la barre de l'Explorateur). Chaque
ligne y est commentée. Pour voir l'état de chaque module : `lancer.bat --verifier`.

### Voix
- **Il ne m'entend pas** : vérifie le micro par défaut de Windows, ou mets un morceau de son nom dans
  `micro = "Realtek"`. Baisse `seuil_reveil` à 0,4.
- **Il se réveille tout seul** : monte `seuil_reveil` à 0,6 ou 0,7.
- **Transcription lente** : `modele_whisper = "base"`. Avec une carte NVIDIA, Jarvis l'essaie tout seul.
- **Voix** : Piper (neuronale) par défaut, sinon la voix française de Windows. Tu peux régler `vitesse`.
- Jarvis coupe son micro pendant qu'il parle, pour ne pas s'entendre lui-même. Pour l'interrompre, utilise
  **Stop** à l'écran ou la touche Espace.

### Philips Hue
Appuie sur le bouton rond du pont, puis dans les 30 secondes dis « **appaire les lumières** ». Jarvis trouve le pont
et enregistre la clé tout seul.

### OBS
Dans OBS : **Outils > Paramètres du serveur WebSocket > Activer**. Copie le mot de passe dans `[obs] mot_de_passe`.

### Google Agenda et Gmail (une fois, environ 10 minutes)
1. Va sur [console.cloud.google.com](https://console.cloud.google.com) et crée un projet « Jarvis ».
2. **API et services > Bibliothèque** : active **Google Calendar API** et **Gmail API**.
3. **Écran de consentement OAuth** :
   - type **Externe**, nom « Jarvis », ton adresse mail ;
   - dans **Audience** (ou « Utilisateurs test »), ajoute ta propre adresse Gmail.
4. **Identifiants > Créer des identifiants > ID client OAuth** : choisis **Application de bureau**, puis
   **télécharge le JSON**. Renomme-le `google_identifiants.json` et mets-le dans `%APPDATA%\Jarvis`.
5. À la première demande (« qu'est-ce que j'ai demain ? »), le navigateur s'ouvre. Autorise Jarvis. Sur l'écran
   « Google n'a pas validé cette application », clique sur **Continuer** : c'est ta propre application.

Tant que l'application est « en test », Google redemande l'autorisation tous les 7 jours. Pour éviter ça, dans
**Audience**, clique sur **Publier l'application** (elle reste privée : toi seul as les identifiants).

**Agendas iCal** : dans Google Agenda, **Autres agendas > + > À partir de l'URL**. Jarvis les lit avec les autres.

### Discord (un bot à toi)
Discord interdit d'automatiser un compte utilisateur : Jarvis passe par un bot.
1. Va sur [discord.com/developers/applications](https://discord.com/developers/applications) et crée une
   **New Application** « Jarvis ».
2. Onglet **Bot** :
   - **Reset Token**, copie le jeton dans `[discord] jeton` ;
   - active **Message Content Intent**.
3. **OAuth2 > URL Generator** :
   - coche le scope `bot` ;
   - permissions : *View Channels*, *Read Message History*, *Send Messages* ;
   - ouvre l'adresse générée et invite le bot sur tes serveurs.
4. Ton identifiant Discord : **Paramètres > Avancés > Mode développeur**, puis clic droit sur ton nom >
   **Copier l'identifiant**. Mets-le dans `utilisateur_id`.

Jarvis voit les salons des serveurs où le bot est invité (pas tes messages privés).

### Instagram (API officielle de Meta)
Il faut un compte **professionnel** (créateur ou entreprise) relié à une **Page Facebook**.
1. Sur [developers.facebook.com](https://developers.facebook.com), crée une application de type
   **Entreprise**.
2. Ouvre l'**Explorateur de l'API Graph** :
   - choisis ton application ;
   - ajoute les autorisations `instagram_basic`, `instagram_manage_insights`, `pages_show_list` et
     `pages_read_engagement` ;
   - clique sur **Generate Access Token**.
3. Dans l'**outil de débogage des jetons**, clique sur **Prolonger le jeton d'accès** : tu obtiens un jeton de
   60 jours.
4. Dans l'Explorateur, interroge `me/accounts?fields=name,instagram_business_account`. L'`id` du champ
   `instagram_business_account` est l'identifiant à mettre.
5. Ajoute un bloc par compte dans la configuration :
   ```toml
   [[instagram.comptes]]
   nom = "principal"
   id = "1784..."
   jeton = "EAAG..."
   ```
Jarvis note les abonnés de chaque jour pour comparer avec la veille. Le jeton est à renouveler tous les 60 jours.

### Navigateur et réservations
Jarvis ouvre sa propre fenêtre Edge, avec un profil à lui (`%APPDATA%\Jarvis\navigateur`). Connecte-toi une fois
dans cette fenêtre aux sites que tu utilises (Doctolib, TheFork…) : les connexions restent. Il ouvre seulement des
pages web, jamais les fichiers du PC.

### Appels (Twilio)
1. Crée un compte sur [twilio.com](https://www.twilio.com) et achète un numéro. Un numéro français demande un
   justificatif d'adresse. En compte d'essai, tu ne peux appeler que des numéros vérifiés.
2. Dans la console Twilio, copie **Account SID** et **Auth Token** dans `[twilio] sid` et `jeton`, et ton numéro
   dans `numero` (ex. `"+33…"`).
3. **Voice > Settings > Geo permissions** : autorise la France (et les autres pays à appeler).
4. Ajoute tes contacts dans `[contacts]` (`maman = "06…"`).
5. **Pour les conversations** (Jarvis parle et écoute), Twilio doit joindre Jarvis depuis internet. Dans un
   terminal, choisis l'une des deux commandes et colle l'adresse `https://…` obtenue dans `[twilio] url_publique` :
   - `cloudflared tunnel --url http://localhost:8765` ;
   - ou `ngrok http 8765`.

   L'adresse d'un tunnel rapide change à chaque lancement ; ngrok offre une adresse fixe gratuite. Par ce tunnel,
   seuls les appels signés par Twilio sont acceptés : la page de Jarvis y est refusée.

N'appelle que des gens d'accord pour parler à un assistant. Jarvis se présente toujours comme ton assistant.

### Présence et notifications
- **Notifications** :
  1. installe l'application gratuite **ntfy** (iPhone ou Android) ;
  2. abonne-toi à un sujet secret et long (ex. `jarvis-manan-8f3k2`) ;
  3. mets ce sujet dans `[ntfy] sujet`.
- **Présence** :
  1. dans ta box, réserve une adresse IP fixe pour le téléphone (réservation DHCP), et mets-la dans
     `[presence] ip_telephone` ;
  2. sur iPhone : **Réglages > Wi-Fi > (i)** à côté de ton réseau, puis **Adresse Wi-Fi privée : Fixe** (ou
     désactivée).

  Un téléphone en veille répond mal : Jarvis attend environ 5 minutes sans réponse avant de te croire parti.
- **Actions à l'arrivée et au départ** (exemple) :
  ```toml
  [presence]
  ip_telephone = "192.168.1.42"
  arrivee = [{ outil = "hue_scene", arguments = { scene = "Détente" } }, { dire = "Bon retour, monsieur." }]
  depart = [{ outil = "hue_regler", arguments = { cible = "tout", allumer = false } }]
  ```

### Telegram (Jarvis partout sur ton téléphone)
1. Dans Telegram, écris à **@BotFather**, envoie `/newbot` et choisis un nom. Copie le jeton dans
   `[telegram] jeton`.
2. Redémarre Jarvis et envoie un message à ton bot : il te répond ton numéro de conversation. Mets-le dans
   `chat_id`, puis redémarre.

Ensuite, tu peux lui écrire, lui envoyer des notes vocales et des photos. Personne d'autre ne peut le commander.

### Serveur MCP (Claude Desktop, Claude Code)
- **Claude Desktop** : l'installateur le propose. Sinon, lance `lancer.bat --claude-desktop`, puis quitte
  complètement Claude Desktop et rouvre-le.
- **Claude Code** :
  ```
  claude mcp add jarvis -- "%LOCALAPPDATA%\Jarvis\venv\Scripts\python.exe" -m jarvis --mcp
  ```
Si Jarvis tourne, les demandes passent par lui et les neurones s'allument. Sinon, les outils marchent seuls.

### Sur la télé ou le téléphone du salon
Dans `[interface]`, mets `reseau = true` et une `cle` longue. Ouvre ensuite `http://IP-DU-PC:8765/?cle=TA_CLE` sur
la télé, puis appuie sur **H** pour n'afficher que le cerveau. Autorise Jarvis sur les **réseaux privés** quand le
pare-feu Windows le demande.

Si le cerveau est affiché sur l'écran principal, cache-le (**H**) avant de demander à Jarvis de regarder l'écran,
ou mets-le sur un second écran.

---

## Sécurité et vie privée

- **Le micro reste sur le PC.** Le mot de réveil et la transcription tournent en local. Seul le texte de tes
  demandes part vers Claude. Une capture d'écran n'est envoyée que quand tu demandes à Jarvis de regarder.
- **Les secrets** (clé d'API, jetons) sont seulement dans `%APPDATA%\Jarvis\config.toml`, jamais dans le dépôt.
- **Le serveur de Jarvis n'écoute que ton PC.** Chaque commande exige un jeton local, glissé dans la page. Un site
  web ouvert dans le navigateur ne peut donc pas commander Jarvis. La page n'est pas donnée aux demandes qui
  passent par un tunnel, ni aux sites qui détournent leur nom vers ton PC. Le mode télé exige sa clé.
- **Ce que Jarvis lit** (pages web, mails, messages Discord) est traité comme une information, jamais comme un
  ordre : une page web ou un mail ne peut pas lui faire faire quelque chose à ta place.
- Il ne touche jamais aux processus de Windows ni à lui-même.

---

## Dépannage

| Problème | Solution |
|---|---|
| Rien ne se lance | Double-clique sur `lancer.bat` dans `C:\Users\TON_NOM\Jarvis` : la fenêtre noire affiche l'erreur. |
| « Your credit balance is too low » | La clé d'API n'a plus de crédit (elle est payée à part de l'abonnement). Si Claude Code est installé, Jarvis passe tout seul sur ton abonnement. Pour ne plus jamais utiliser la clé : `moteur = "claude_code"` dans `[cerveau]`. |
| « Aucun cerveau disponible » | Mets une clé d'API, ou installe Claude Code et connecte-toi (voir plus haut). |
| Un module affiche « À CONFIG. » | Il manque un réglage dans la configuration ; `lancer.bat --verifier` dit lequel. |
| « Port déjà utilisé » | Jarvis tourne déjà, ou change `[interface] port`. |
| Google : « autorisation expirée » | Redemande : le navigateur s'ouvre pour renouveler (voir « Publier l'application »). |
| La carte graphique n'est pas utilisée | Supprime `%APPDATA%\Jarvis\whisper_cuda.txt` après avoir installé tes pilotes : Jarvis refait l'essai. |
| Tout réinstaller ou mettre à jour | Recolle la ligne dans PowerShell (ta configuration est gardée). |

Pour essayer sans micro : `lancer.bat --texte` (conversation au clavier dans le terminal).

---

## Pour les curieux

```
jarvis/
  telecharger.ps1                téléchargement en une ligne (PowerShell), puis installation
  installer.bat, installer.ps1   installation Windows
  lancer.bat                     lancement (--demo, --texte, --verifier, --mcp, --claude-desktop)
  config.exemple.toml            configuration commentée (copiée dans %APPDATA%\Jarvis)
  jarvis/
    cerveau.py, moteurs.py       la réflexion : API Claude (texte en continu, outils, cache) ou Claude Code
    outils/                      les 66 outils, chacun relié à sa zone du cerveau
    voix/                        micro, mot de réveil, transcription, synthèse, boucle mains libres
    serveur.py, ui/              le serveur local et le cerveau 3D (three.js)
    mcp_serveur.py, telegram.py  les autres portes d'entrée
    memoire.py                   souvenirs (SQLite, recherche plein texte)
  tests/                         python -m pytest tests
```

Les tests utilisent de faux services (API Claude, Hue, Discord, Telegram…) avec les vraies bibliothèques
(SDK Anthropic, client MCP, validateur de signature Twilio). Les parties propres à Windows (clavier, fenêtres, son,
voix SAPI), le vrai micro et les vrais comptes ne peuvent être essayés que sur ton PC.
