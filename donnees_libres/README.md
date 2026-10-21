# Données gratuites pour l'étude large (21 octobre 2026)

Demande de l'utilisateur : n'utiliser que des données gratuites, rien de payant.

| Source | Contenu | Période | Script |
|---|---|---|---|
| **Alpaca** (offre gratuite, flux SIP, clés déjà dans les secrets du dépôt) | Barres de 5 minutes, 9 h 30 - 16 h, de 29 ETF qui suivent chaque famille de futures CME : indices (SPY, QQQ, DIA, IWM), taux (TLT, IEF, IEI, SHY), métaux (GLD, SLV, CPER, PPLT, PALL), énergie (USO, BNO, UNG, UGA), devises (FXE, FXY, FXB, FXA, FXC, FXF, UUP), agricoles (CORN, SOYB, WEAT), VXX, BITO | 2016 - aujourd'hui | `alpaca_etf.py` |
| **Yahoo** | Vrais futures CME (41 contrats continus) : barres d'une heure sur 730 jours, de 5 minutes sur 60 jours, du jour depuis le début ; VIX, VIX9D, VIX3M, VVIX, MOVE, OVX, GVZ, indice du dollar au jour | variable | `yahoo_futures.py` |
| **HistData** | 5 minutes, 24 h sur 24 : argent, Brent, Nikkei, indice du dollar, USD/CAD, USD/CHF, NZD/USD | 2012 - 2026 | `histdata_extra.py` |

Déjà présentes sur la branche de recherche (`claude/keen-babbage-r686cl`), téléchargées avant ce jour, donc sans coût
nouveau : minutes de NQ et ES (2011 - 2026), YM, GC, CL, 6E (2016 - 2026), RTY (2017 - 2026) ; environ 40 futures CME au
jour (2010 - 2026) ; heures de ZN et de 6 devises ; 5 minutes 24 h sur 24 de 8 marchés (HistData, 2012 - 2026).

Lancement : pousser `lancer.txt` sur la branche `claude/fervent-wright-21hspi` déclenche
`.github/workflows/donnees-libres.yml` (GitHub Actions), qui enregistre les fichiers sur la branche.

**Limites connues :**
- Un ETF suit son future pendant la séance américaine seulement. Les ETF de matières premières (USO, UNG, CORN…) suivent
  moins bien que ceux des indices et des taux.
- Le contrat continu de Yahoo n'est pas ajusté aux changements d'échéance. Les barres horaires ne couvrent que 2 ans.
