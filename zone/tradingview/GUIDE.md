# Tester le bot zone de bruit (MNQ) : du virtuel au challenge

## Étape 1 : le suivi virtuel (rien à faire, déjà en place)

Le robot rejoue chaque séance le lendemain matin, vers 7 h 35 heure de Paris, et suit un challenge
Phidias 50K virtuel. À regarder sur la [page d'accueil du dépôt](../../README.md) et le
[détail du robot](../robot/TABLEAU_DE_BORD.md). Chaque matin, le détail donne aussi :
- les **trades de la veille** ;
- les **niveaux et la taille conseillée pour la séance du jour** (section « Pour la séance du ... ») ;
- le même résumé sur Telegram, si les secrets du bot Telegram sont configurés.

Il faut plusieurs mois pour juger. En 2011-2026, même quand le bot a fini par valider, il lui a
souvent fallu 2 à 5 mois.

## Étape 2 : les signaux en direct sur TradingView (sans argent)

1. Ouvre un graphique du **contrat MNQ du trimestre** (par exemple MNQZ2026), en **1 minute**, avec des
   **données CME en temps réel**. Deux solutions : l'abonnement de données CME de TradingView, ou la
   connexion de TradingView au courtier de ta prop firm (Tradovate, par exemple) si elle le permet.
   Avec les données différées de 10 minutes, les signaux arrivent trop tard.
2. Ouvre l'éditeur Pine (en bas), colle le contenu de [`zone_de_bruit.pine`](zone_de_bruit.pine),
   « Enregistrer », puis « Ajouter au graphique ».
3. Regarde le tableau en haut à droite :
   - « Séances en mémoire » doit afficher **14 / 14**. Il faut environ 20 000 barres d'une minute
     d'historique, car le graphique contient aussi la nuit. Selon ton abonnement TradingView, ce n'est
     pas toujours possible. Dans ce cas, utilise les niveaux publiés chaque matin par le robot
     (étape 1). Il te suffit alors du prix d'ouverture de 9 h 30, et d'un VWAP calculé **depuis 9 h 30**
     (dans TradingView, l'indicateur VWAP avec un point de départ à 9 h 30 : son réglage « Séance »
     part de 18 h sur les futures). Ne regarde le prix qu'aux heures de contrôle, sans stop placé dans
     le marché.
   - « Taille du jour » : le calcul automatique demande 40 séances où le script pouvait trader, soit
     plus d'historique que ce que charge TradingView. Mets donc toi-même la taille dans le réglage
     « Nombre de contrats imposé » (voir l'étape 3 pour la calculer).
   - « Aujourd'hui » indique les jours de fête ou de demi-séance, où le script ne trade pas (comme le
     backtest).
4. Crée une alerte : bouton « Alerte », condition « Zone de bruit MNQ (challenge) », puis « Appels de
   fonction alert() uniquement » (sinon chaque signal arrive en double), avec notification sur
   l'application mobile. **Une alerte garde les
   réglages du moment où elle a été créée** : si tu changes la taille, supprime-la et recrée-la.
5. **Pendant 2 à 4 semaines**, compare chaque jour les signaux TradingView avec les « Trades du ... »
   publiés par le robot le lendemain matin. Ils doivent être les mêmes, à quelques points près (les
   données ne viennent pas du même fournisseur). S'ils diffèrent souvent, ne pas passer à l'étape 3.

Heures de contrôle : de 10 h à 15 h 30 à New York, soit **de 16 h à 21 h 30 à Paris**. Tout est fermé à
15 h 59 à New York (21 h 59 à Paris). Pendant les semaines où les deux pays n'ont pas encore changé d'heure
tous les deux (environ 3 semaines en mars et une semaine fin octobre), tout se décale d'une heure : de
15 h à 20 h 30, et fermeture à 20 h 59 à Paris. Le robot donne chaque matin les heures de Paris exactes.

## Ordres automatiques (facultatif)

Le script peut envoyer ses ordres tout seul, par un « webhook » vers un service qui passe les ordres chez le
courtier de ta prop firm. Il te faut un abonnement TradingView qui permet les webhooks, avec la
**double authentification activée** sur ton compte TradingView (sinon l'adresse du webhook ne peut pas être
enregistrée).
1. **Vérifie d'abord que ta prop firm autorise le trading automatique** : certaines l'interdisent ou
   exigent que tu sois présent, et un compte peut être fermé pour ça.
2. Ouvre un compte **TradersPost** (les messages du script sont à son format) et relie-le toi-même au
   courtier de ton compte de challenge, s'il est pris en charge (Tradovate, par exemple). Ne donne tes
   identifiants à personne d'autre. Dans la stratégie TradersPost, règle-la pour **utiliser la quantité
   envoyée par le signal** et pour **fermer puis inverser la position sur un signal opposé**. Un autre
   service (PickMyTrade, CrossTrade...) attend un autre format de message : le script devrait être adapté.
3. Dans les réglages du script : « Format des alertes » = JSON, et « Symbole envoyé dans les ordres » =
   le symbole attendu par le service (par exemple MNQZ2026).
4. Crée l'alerte : condition = le script, « Appels de fonction alert() uniquement », coche « URL du
   webhook » et colle l'adresse donnée par le service. Les messages ont ce format :
   `{"ticker": "MNQZ2026", "action": "buy", "sentiment": "long", "quantity": 2}` pour un achat, et
   `{"ticker": "MNQZ2026", "action": "exit", "sentiment": "flat"}` pour une sortie. Un retournement
   (rare) est un seul message dans l'autre sens, d'où le réglage « fermer puis inverser » ci-dessus.
5. **Teste plusieurs jours sur un compte de démonstration du service** avant le challenge, et vérifie
   que chaque ordre arrive.
6. Surveille quand même : si TradingView ou le service tombe en panne, un ordre peut manquer (surtout
   la fermeture de 15 h 59).
7. **Une alerte garde tous les réglages du moment où elle a été créée** (taille, coussin, format,
   symbole). À chaque changement, supprime-la et recrée-la. En particulier, au changement de contrat
   (mars, juin, septembre, décembre) : passe le graphique **et** le réglage « Symbole envoyé » au
   nouveau contrat, puis recrée l'alerte.

## Étape 3 : un challenge, si les étapes 1 et 2 se passent bien

- Firme : Phidias ou Topstep 50K. Vérifie leurs règles actuelles : limite de perte, règles de
  régularité, trading automatique permis ou non, horaires de fermeture.
- Taille : f = 0,25, soit environ **2 MNQ** sur un compte neuf. En cours de challenge, la taille baisse
  quand le compte s'approche de sa limite. Chaque matin : **MNQ = 0,25 × (solde − limite de perte) /
  risque d'un MNQ**, arrondi en dessous. Le risque est publié chaque matin par le robot (environ 215 $
  en ce moment). Exemple : coussin de 1 500 $ → 0,25 × 1 500 / 215 = 1,7 → 1 MNQ. La taille « compte
  neuf » publiée ne vaut que tant que le coussin est entier.
- Ne trade pas :
  - les jours de fête américaine où la bourse ferme à 13 h, ni les demi-séances. Le script et le robot
    les signalent (« pas de trade ») ;
  - le jour où tu passes au contrat du trimestre suivant. Le backtest change de contrat quand le
    suivant devient le plus échangé, en général **le mercredi de la semaine d'échéance** (2 jours de
    bourse avant le 3e vendredi de mars, juin, septembre et décembre ; entre 1 et 4 jours selon les
    années). Change ce jour-là et ne trade pas ce jour-là. Avant, les niveaux publiés par le robot
    sont ceux de l'ancien contrat : ils ne valent pas pour le nouveau.
- N'ajoute rien, ne coupe rien à la main : les chiffres ne valent que si les règles sont suivies à la
  lettre.
- Chances d'après l'historique, avec 2 comptes au plus : environ 30 % de valider en 12 mois sur
  2011-2026, 45 à 50 % sur 2020-2026. Quand ça valide, c'est souvent en 2 à 4 mois. Ce n'est pas une
  garantie : l'avantage du bot n'est pas prouvé.
