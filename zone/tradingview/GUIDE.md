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
     (étape 1) : il te suffit du prix d'ouverture de 9 h 30.
   - « Taille du jour » : le calcul automatique demande 40 séances, soit environ 55 000 barres, plus
     que ce que charge TradingView. Reporte donc la taille publiée chaque matin par le robot dans le
     réglage « Nombre de contrats imposé ».
   - « Aujourd'hui » indique les jours de fête ou de demi-séance, où le script ne trade pas (comme le
     backtest).
4. Crée une alerte : bouton « Alerte », condition « Zone de bruit MNQ (challenge) », puis « N'importe
   quel appel de fonction alert() », avec notification sur l'application mobile. **Une alerte garde les
   réglages du moment où elle a été créée** : si tu changes la taille, supprime-la et recrée-la.
5. **Pendant 2 à 4 semaines**, compare chaque jour les signaux TradingView avec les « Trades du ... »
   publiés par le robot le lendemain matin. Ils doivent être les mêmes, à quelques points près (les
   données ne viennent pas du même fournisseur). S'ils diffèrent souvent, ne pas passer à l'étape 3.

Heures de contrôle : de 10 h à 15 h 30 à New York, soit **de 16 h à 21 h 30 à Paris**. Tout est fermé à
15 h 59 à New York (21 h 59 à Paris). Pendant les semaines où les deux pays n'ont pas encore changé d'heure
tous les deux (environ 3 semaines en mars et une semaine fin octobre), tout se décale d'une heure : de
15 h à 20 h 30, et fermeture à 20 h 59 à Paris. Le robot donne chaque matin les heures de Paris exactes.

## Étape 3 : un challenge, si les étapes 1 et 2 se passent bien

- Firme : Phidias ou Topstep 50K. Vérifie leurs règles actuelles : limite de perte, règles de
  régularité, trading automatique permis ou non, horaires de fermeture.
- Taille : f = 0,25, soit environ **2 MNQ** sur un compte neuf. Chaque matin, mets à jour le coussin
  (solde − limite de perte) dans les réglages du script, ou lis la taille publiée par le robot.
- Ne trade pas :
  - les jours de fête américaine où la bourse ferme à 13 h, ni les demi-séances. Le script et le robot
    les signalent (« pas de trade ») ;
  - le jour où tu passes au contrat du trimestre suivant, environ une semaine avant l'échéance du
    3e vendredi de mars, juin, septembre et décembre (le backtest ne trade pas ce jour-là).
- N'ajoute rien, ne coupe rien à la main : les chiffres ne valent que si les règles sont suivies à la
  lettre.
- Chances d'après l'historique, avec 2 comptes au plus : environ 30 % de valider en 12 mois sur
  2011-2026, 45 à 50 % sur 2020-2026. Quand ça valide, c'est souvent en 2 à 4 mois. Ce n'est pas une
  garantie : l'avantage du bot n'est pas prouvé.
