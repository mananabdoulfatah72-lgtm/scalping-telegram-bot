# Robot zone de bruit + challenge Phidias 50K (argent virtuel)

Suit en direct le meilleur bot de challenge trouvé dans l'étude (`challenge/` sur la branche de
recherche) : zone de bruit sur le Nasdaq (MNQ), intraday, taille réduite quand le compte s'approche de
sa limite (f = 0,15). Il passe un challenge Phidias 50K virtuel puis, s'il le réussit, un compte
financé virtuel avec retraits. Tableau de bord : [`robot/TABLEAU_DE_BORD.md`](robot/TABLEAU_DE_BORD.md).

- Données : barres minute NQ de Databento (secret `DATABENTO_API_KEY`), environ 1 centime par jour. Les
  260 séances précédant le départ viennent des données de l'étude.
- Contrôle : rejoué sur 2023-2026, le robot donne, pour 1 MNQ, exactement les mêmes gains jour par jour
  que le backtest. Le challenge est réussi le même jour (7 juin 2023).
- Databento publie les barres minute environ 8 heures après la séance : chaque séance est rejouée le
  lendemain matin (heure de Paris). Pour trader en vrai, il faudrait recevoir les signaux en direct,
  toutes les 30 minutes.
- Historique : une tentative réussit 39 % du temps et saute 4 % du temps. Une fois financé, le compte
  rapporte environ 680 $ par an en moyenne, et rien dans 86 % des cas. Ce n'est pas un revenu.
