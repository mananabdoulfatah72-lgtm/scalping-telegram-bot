# REA dans ton système de trading futures

REA (Reverse Engineer Anything) donne à Claude Code la capacité de lire un logiciel sans son code source : DLL .NET,
applications Electron, sites, applications Android, programmes Windows (avec Ghidra). Chaque conclusion vient avec sa
preuve (le type, la fonction, la chaîne, l'appel).

**Vérifié le 16 novembre 2026 :**
- REA existe bien : paquet npm `rea-agents` 6.9.0 (licence MIT, auteur morluto, publié depuis le 12 juillet 2026),
  dépôt github.com/morluto/rea, site rea.tools.
- **Testé ici** sur tes propres bots C# : REA lit leurs DLL en 2 à 3 secondes, sans les exécuter.
  - Il en sort les 45 appels que le Bot 3 en 1 fait à Quantower, avec leur signature exacte.
  - L'outil `compat.mjs` (plus bas) s'appuie sur cette lecture.

## Ce que REA fait pour toi, et ce qu'il ne fait pas

**Il ne trouve pas d'avantage de marché.** Un avantage se trouve dans les données des marchés, puis se prouve avec
l'usine (`usine/`, les 5 portes). REA lit des logiciels, pas des marchés.

**Il ne touche pas les serveurs.** La règle du plancher de Bulenox, les remplissages de Rithmic et la CME tournent sur
leurs serveurs, jamais livrés sur ton PC. REA ne les voit pas.

**Ce qu'il fait d'utile, sur ce que tu as le droit d'examiner :**

| Usage | À quoi ça sert pour ton compte | Comment |
|---|---|---|
| 1. Tes bots et la version de Quantower installée | Éviter qu'une mise à jour de Quantower casse un bot un lundi : plantage, ou solde lu vide sans plantage | `node rea/compat.mjs "C:\Quantower"`, testé ([ENQUETES.md](ENQUETES.md) n° 1) |
| 2. Le vrai plancher Bulenox dans Quantower | Que le bot lise lui-même sa marge (frein, consigne), sans que tu envoies ton solde | Journal du bot d'abord, REA ensuite (n° 2) |
| 3. Le delta de Quantower contre celui de la recherche | Que le filtre delta en direct soit bien celui qui a été testé | Comparaison sur une séance, REA en appui (n° 3) |
| 4. Audit avant d'installer ou de payer | Bot « passe-challenge », indicateur, application de signaux : voir ce qu'il envoie et où, en particulier tes identifiants | REA sur l'APK, le .exe ou l'application Electron (n° 4) |
| 5. Comprendre un outil que tu as le droit d'utiliser | En tirer une spécification, puis la passer aux 5 portes de l'usine avant tout argent | REA, puis [SPEC_MODELE.md](SPEC_MODELE.md), puis `usine/` (n° 5) |
| 6. Ce qui a changé dans une mise à jour | Quantower, une plateforme, un outil acheté | `rea compare-managed-members` (n° 6) |

Les pistes de marché (ce que ton projet a déjà fermé, ce qui reste ouvert) : [PISTES.md](PISTES.md).

## La ligne rouge

L'article cite « j'ai rétro-conçu TradingView, j'utilise leurs indicateurs premium gratuitement ». **Ça, non.**
- Se servir gratuitement d'indicateurs payants (TradingView « invite-only », extensions payantes) ou contourner une licence
  ou un abonnement viole la licence du logiciel et le droit d'auteur.
- Le projet REA refuse lui-même ces usages ([DISCLAIMER](https://github.com/morluto/rea/blob/main/DISCLAIMER.md)) :
  contourner une licence ou une protection, copier du code ou des contenus protégés, toucher aux services en ligne.
- Pas plus permis :
  - publier ou partager le code décompilé de quelqu'un d'autre ;
  - toucher aux serveurs ou aux comptes d'autrui ;
  - automatiser l'accès au tableau de bord de Bulenox en contournant ses conditions.

**Ce qui est permis, en droit européen** (directive 2009/24/CE ; ce n'est pas un avis juridique, la licence de chaque
logiciel compte aussi) :
- article 5.3 : tu peux observer, étudier et tester le fonctionnement d'un logiciel que tu as le droit d'utiliser, pendant
  que tu l'utilises, pour comprendre ses idées et ses principes ;
- article 6 : la décompilation est permise seulement si elle est indispensable pour faire fonctionner ton propre programme
  avec lui (l'interopérabilité : tes bots avec Quantower), sans diffuser ce que tu obtiens.

L'usage n° 1 ne lit que des noms et des signatures publics : ce que fait déjà le compilateur quand il construit tes bots
contre Quantower.

## Installer REA sur ton PC, sans risque

1. **Node.js.** REA demande Node 22.23.4 ou plus, 24.22.1 ou plus, ou 26.12.1 ou plus. L'article donne des versions
   périmées. Vérifie avec `node -v`.
2. **Dossier de confiance.** Ouvre le terminal dans un dossier à toi, pas dans le dossier d'une application à analyser.
   C'est la consigne de REA.
3. **Installation.** Lance `npx rea-agents@6.9.0 setup` (la version vérifiée ici).
   - Choisis ton agent (Claude Code).
   - **Lis le plan des modifications avant d'accepter** : REA ajoute un serveur MCP et une compétence à ta configuration,
     et sauvegarde l'ancienne.
   - Refuse Hopper : il ne sert pas pour Quantower, qui est en .NET.
4. **Vérification.** Redémarre Claude Code, puis lance `npx -y rea-agents@6.9.0 doctor --client claude_code --json`.
5. **Mises à jour.** Fais-les quand tu le décides (`rea update`), pas en automatique : une nouvelle version peut changer
   ce que fait l'outil.
6. **Fichiers douteux.** Ne lance rien d'inconnu hors d'une machine de test. La lecture statique n'exécute rien, mais les
   captures d'exécution de REA lancent bel et bien le programme.

## Le contrôle de compatibilité (usage n° 1), testé

Sur ton PC, Quantower fermé ou ouvert, une fois par semaine et après chaque mise à jour de Quantower :

```powershell
node rea\compat.mjs "C:\Quantower"
```

- Le script trouve la dernière bibliothèque `TradingPlatform\<version>\bin\TradingPlatform.BusinessLayer.dll` et chaque bot
  installé dans `Settings\Scripts\Strategies\`.
- Il les fait lire par REA, puis il vérifie deux choses :
  - chaque appel direct d'un bot existe dans Quantower, avec la même signature ;
  - chaque nom lu « par réflexion » existe (liste dans `reflexion.json` : `Balance`, `AdditionalInfo`, `GrossPnL`…).
- Le rapport s'écrit dans `compat_<date>.md`.

**L'essai fait ici.** Une fausse bibliothèque Quantower a été construite à partir de l'imitation du projet
(`Stubs.cs`), puis le Bot 3 en 1 compilé contre elle, comme le fait ton installateur.
- Version d'origine : les 45 appels directs sont tous trouvés.
- Version modifiée (`Balance` renommé, `PlaceOrder` avec un paramètre de plus) : le script signale le `PlaceOrder`, qui
  ferait planter le bot, et le `Balance`, que le bot lirait vide.
- Contre le vrai Quantower, `AdditionalInfo`, `NameKey`, `Accounts` et `Id` doivent être trouvés. L'imitation ne les
  définit pas, d'où leur absence dans l'essai.

**Ce qui n'a pas pu être vérifié ici :** la lecture du vrai Quantower (il n'est installé que sur ton PC) et le lancement
de Node sous Windows. Le script gère les chemins Windows et appelle `npx` par le shell Windows.
