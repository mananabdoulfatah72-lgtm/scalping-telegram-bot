# Les enquêtes REA pour ton compte, prêtes à copier

À lancer sur ton PC, dans Claude Code avec REA installé ([README.md](README.md)). Chaque enquête dit pourquoi elle sert,
sur quoi elle porte (et pourquoi c'est permis), quoi copier, ce que tu obtiens et ce que tu en fais. Les chemins sont ceux
de l'installateur des bots ; remplace `C:\Quantower` par ton dossier si Quantower ou Optimus Flow est ailleurs.

## 1. Tes bots fonctionnent-ils avec la version de Quantower installée ?

- **Pourquoi.** Quantower se met à jour seul. Si un nom change, deux choses peuvent arriver :
  - le bot plante au chargement ;
  - pire, il tourne mais lit un solde vide, et fausse son frein et sa limite du jour. C'est déjà arrivé (« solde
    illisible »).
- **Sur quoi.** La bibliothèque de Quantower et tes propres bots, noms et signatures seulement : l'interopérabilité.
- **Quand.** Chaque dimanche, et après chaque mise à jour de Quantower, avant l'ouverture.

```powershell
node rea\compat.mjs "C:\Quantower"
```

- **Ce que tu obtiens.** `compat_<date>.md`, avec deux listes : ce qui ferait planter le bot, et ce qu'il lirait vide.
- **Ce que tu en fais.**
  - Tout est trouvé : rien à faire.
  - Sinon : bot arrêté (fichier `STOP`), installateur relancé, contrôle refait.
  - Si un problème reste : envoie le rapport à Claude pour adapter le code.

## 2. Où Quantower expose le seuil de liquidation de Bulenox

- **Pourquoi.** Aujourd'hui, la marge du compte vient de toi (message Telegram « solde ») ou de l'estimation du bot. Si
  Quantower reçoit de Rithmic le seuil de liquidation du compte, le bot peut lire lui-même sa vraie marge. Le frein et la
  consigne deviennent alors exacts.
- **Étape 1, sans REA.** Au démarrage, le Bot 3 en 1 écrit dans `C:\Bot3en1\journal.txt` toutes les informations du compte
  que Quantower lui donne (`AdditionalInfo` : nom et valeur). Cherche-y un seuil de liquidation, un solde minimum, une
  perte maximale ou une perte du jour. Si tu le trouves, envoie le nom et la valeur à Claude : c'est fini.
- **Étape 2, avec REA, seulement si rien n'apparaît.** Interopérabilité avec la plateforme que tu as le droit d'utiliser.

```text
Avec REA (inspect_managed_members, lecture statique seulement), lis C:\Quantower\TradingPlatform\<derniere version>\bin\TradingPlatform.BusinessLayer.dll
et la DLL de la connexion Rithmic du meme dossier. Liste uniquement les types et membres publics, et les chaines de caracteres,
qui portent sur le risque du compte : solde, seuil de liquidation, perte du jour, drawdown. Pour chacun : le type, le membre,
et comment une strategie peut le lire par l'API publique. Ne recopie aucun code de Quantower. Dis ce qui reste incertain.
```

- **Ce que tu en fais.** Demande à Claude d'ajouter cette lecture au Bot 3 en 1 : le brief n'aura plus besoin de ton
  message « solde ».

## 3. Le delta de Quantower est-il celui de la recherche ?

- **Pourquoi.** Le filtre delta du bot a été testé avec des transactions Databento, puis Rithmic. En direct, il lit le côté
  agresseur que Quantower donne à chaque transaction. Si les deux définitions diffèrent, le filtre en direct n'est plus
  celui qui a été testé.
- **Étape 1, sans REA.** Compare une séance mesurée des deux côtés : l'export des transactions du bot
  (`ExportTransactions`) contre les deltas que le bot a écrits dans son journal. Demande à Claude de faire la comparaison,
  minute par minute.
- **Étape 2, seulement s'il y a un écart.**

```text
Avec REA, en lecture statique, trouve dans TradingPlatform.BusinessLayer.dll comment Quantower renseigne le cote agresseur d'une
transaction (AggressorFlag) pour une connexion Rithmic : d'ou vient la valeur, et quand elle vaut NotSet. Montre les types et
membres en cause, sans recopier de code. Dis ce qui reste incertain.
```

## 4. Audit d'un bot, d'un indicateur ou d'une application de signaux, avant d'installer ou de payer

- **Pourquoi.** Les traders de prop firms sont une cible. Bots qui « passent le challenge », copieurs de trades,
  applications de « signaux gratuits » : certains envoient tes identifiants Rithmic ou tes données ailleurs.
- **Sur quoi.** Un fichier que tu possèdes, examiné pour ta sécurité. À faire sur une machine de test, jamais sur le PC
  du compte.

```text
Avec REA, en lecture statique seulement (n'execute rien), examine <chemin du .apk, .exe, ou du dossier de l'application>.
Liste : les permissions demandees ; chaque domaine ou adresse avec lequel il communique ; ou vont les identifiants
(Rithmic, Bulenox, broker) saisis dans l'application ; s'il telecharge du code apres l'installation ; les traceurs et SDK
d'analyse ; ce qu'il ecrit sur le disque. Pour chaque point : la classe ou le fichier, et la preuve. Marque ce qui est
confirme et ce qui est deduit.
```

**Signaux d'alarme :**
- des identifiants envoyés à un autre domaine que celui du broker ;
- du code téléchargé après l'installation ;
- un code volontairement illisible ;
- des droits d'administrateur demandés ;
- des positions copiées depuis un serveur inconnu.

## 5. Comprendre un outil que tu as le droit d'utiliser, et le passer aux portes

- **Pourquoi.** Un indicateur ou un bot qui a l'air de marcher doit passer les mêmes 5 portes que tout le reste avant un
  dollar réel.
- **Étape 1, sans REA.** C'est le plus sûr et c'est permis : observe l'outil pendant que tu l'utilises (article 5.3).
  Note ses signaux pendant quelques semaines (alertes, journal, captures) à côté des prix. Demande à Claude d'en déduire
  la règle.
- **Étape 2, avec REA**, seulement pour un logiciel que tu as le droit d'examiner, selon sa licence : par exemple ton
  propre code, ou celui d'un ami qui te donne son accord écrit. **Jamais** pour un indicateur protégé de TradingView.

```text
Avec REA, etudie comment <outil> decide d'entrer et de sortir. Ecris SPEC.md avec le modele rea/SPEC_MODELE.md : comportement,
donnees d'entree, reglages, cas limites, et ce qui reste inconnu. Aucun code recopie. Puis ajoute l'idee a usine/REGLES.md
(avantage, contrepartie, regle exacte, grille), commite-la AVANT tout calcul, ecris son noyau dans usine/moteur.py et lance
python3 usine/portes.py <idee>.
```

- **Ce que tu en fais.** Rien sans les 5 portes. Ensuite : papier deux semaines, puis 1 MES, puis 1 MNQ (`usine/RISQUE.md`).

## 6. Ce qui a vraiment changé dans une mise à jour

- **Pourquoi.** Savoir ce qu'une mise à jour change dans ce que tes bots utilisent. Quantower garde les anciennes
  versions dans `TradingPlatform\<version>\`.

```powershell
rea compare-managed-members "C:\Quantower\TradingPlatform\<ancienne>\bin\TradingPlatform.BusinessLayer.dll" "C:\Quantower\TradingPlatform\<nouvelle>\bin\TradingPlatform.BusinessLayer.dll" --json > changements.json
```

Si la commande `rea` n'est pas installée, remplace `rea` par `npx -y rea-agents@6.9.0`. Puis, dans Claude Code :

```text
Lis changements.json et dis-moi quels changements touchent les membres utilises par mes bots
(C:\Quantower\Settings\Scripts\Strategies\*\*.dll, et rea\reflexion.json). En clair, avec ce que je dois faire avant lundi.
```
