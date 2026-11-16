"""Rapprochement et glissement des ordres du bot, comme le rapport de glissement de pysystemtrade
(sysproduction/reporting/data/trades.py : glissement = sens x (prix de reference - prix d'execution), negatif = contre toi).

Usage (sur le PC, apres la seance) :
    python usine/rapprochement.py C:\\Bot3en1\\journal.txt executions.csv [--fuseau Europe/Paris] [--minutes nq_1min.csv.gz]
- journal.txt : le journal du Bot 3 en 1 (lignes « ordre envoye : achat 1 MNQ (position 0 -> 1) », heure UTC).
- executions.csv : l'export des executions (trades) de Quantower. Les colonnes sont reconnues par leur nom (heure, sens,
  quantite, prix, symbole) ; si l'une manque, le script affiche l'en-tete lu et s'arrete : envoie-le a Claude.
- --fuseau : fuseau des heures de l'export (celui de l'affichage de Quantower ; Europe/Paris par defaut).
- --minutes : minutes du NQ (zone/robot/nq_1min.csv.gz du depot par defaut, heures de New York).
Reference d'un ordre : cloture de la minute du NQ qui precede l'envoi (la decision du bot se prend a la cloture d'une
minute). Ecrit rapprochement_<date>.md dans le dossier courant.
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import pandas as pd

ICI = Path(__file__).resolve().parent
ORDRE = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC ordre envoye : (achat|vente) (\d+) (\S+) \(position (-?\d+) -> (-?\d+)\)")
COLONNES = {"heure": r"time|heure|date", "sens": r"side|sens|direction|action", "quantite": r"qty|quantity|quantit|size|taille",
            "prix": r"price|prix", "symbole": r"symbol|symbole|instrument"}
TICK, DOLLAR_POINT = {"MNQ": 0.25, "MES": 0.25}, {"MNQ": 2.0, "MES": 5.0}
HYPOTHESE_TICKS = -1.0           # l'usine compte 1 tick de glissement par ordre (moteur.COUT)
FENETRE_S = 120                  # une execution est rattachee a l'ordre envoye au plus 120 s avant


def lire_journal(f):
    lignes = [ORDRE.match(x) for x in Path(f).read_text(encoding="utf-8", errors="replace").splitlines()]
    o = pd.DataFrame([m.groups() for m in lignes if m], columns=["t", "sens", "qte", "symbole", "avant", "apres"])
    o["t"] = pd.to_datetime(o.t).dt.tz_localize("UTC")
    o["sens"] = o.sens.map({"achat": 1, "vente": -1}); o[["qte", "avant", "apres"]] = o[["qte", "avant", "apres"]].astype(int)
    o["racine"] = o.symbole.str.upper().str.extract(r"^(MNQ|MES)", expand=False)
    return o


def lire_executions(f, fuseau):
    e = pd.read_csv(f, sep=None, engine="python")
    trouve = {}
    for cle, motif in COLONNES.items():
        cands = [c for c in e.columns if re.search(motif, str(c), re.I)]
        if cle == "heure":
            cands = sorted(cands, key=lambda c: 0 if re.search(r"time|heure", str(c), re.I) else 1)
        if cle == "prix":
            cands = [c for c in cands if not re.search(r"limit|stop|trigger|declench", str(c), re.I)] or cands
        if not cands:
            sys.exit(f"Colonne « {cle} » introuvable dans {f}. En-tete lu : {list(e.columns)}. Envoie-le a Claude.")
        trouve[cle] = cands[0]
    x = pd.DataFrame({k: e[v] for k, v in trouve.items()})
    x["t"] = pd.to_datetime(x.heure, dayfirst=False).dt.tz_localize(fuseau, ambiguous="NaT").dt.tz_convert("UTC")
    x["sens"] = x.sens.astype(str).str.lower().map(lambda s: 1 if re.search(r"buy|achat|long", s) else (-1 if re.search(r"sell|vente|short", s) else 0))
    x["qte"] = pd.to_numeric(x.quantite, errors="coerce").abs()
    x["prix"] = pd.to_numeric(x.prix.astype(str).str.replace(",", ".").str.replace(" ", ""), errors="coerce")
    x["racine"] = x.symbole.astype(str).str.upper().str.extract(r"^(MNQ|MES)", expand=False)
    return x.dropna(subset=["t", "qte", "prix"]).sort_values("t").reset_index(drop=True), trouve


def tableau(df):
    """Table Markdown sans dependance (tabulate n'est pas toujours installe)."""
    fmt = lambda v: "" if v is None or (isinstance(v, float) and v != v) else (f"{v:.2f}" if isinstance(v, float) else str(v))  # noqa: E731
    return "\n".join(["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
                     + ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)])


def reference_nq(minutes, t_utc):
    """Cloture de la minute du NQ qui precede l'envoi (heures de New York dans le fichier)."""
    ny = t_utc.tz_convert("America/New_York").tz_localize(None).floor("min") - pd.Timedelta(minutes=1)
    return minutes.get(ny.strftime("%Y-%m-%d %H:%M"))


def principal():
    a = argparse.ArgumentParser(); a.add_argument("journal"); a.add_argument("executions")
    a.add_argument("--fuseau", default="Europe/Paris"); a.add_argument("--minutes", default=str(ICI.parent / "zone/robot/nq_1min.csv.gz"))
    a = a.parse_args()
    o = lire_journal(a.journal); x, trouve = lire_executions(a.executions, a.fuseau)
    m = pd.read_csv(a.minutes, usecols=["t", "c"]); minutes = dict(zip(m.t, m.c))
    pris = set(); lignes = []
    for _, r in o.iterrows():
        cand = x[(x.racine == r.racine) & (x.sens == r.sens) & (x.t >= r.t - pd.Timedelta(seconds=2))
                 & (x.t <= r.t + pd.Timedelta(seconds=FENETRE_S)) & ~x.index.isin(pris)]
        reste, morceaux = r.qte, []
        for i, e in cand.iterrows():
            if reste <= 0:
                break
            q = min(reste, e.qte); morceaux.append((i, q, e.prix, e.t)); reste -= q
        pris.update(i for i, _, _, _ in morceaux)
        prix = sum(q * p for _, q, p, _ in morceaux) / sum(q for _, q, _, _ in morceaux) if morceaux else None
        delai = (morceaux[0][3] - r.t).total_seconds() if morceaux else None
        ref = reference_nq(minutes, r.t) if r.racine == "MNQ" else None
        gl = r.sens * (ref - prix) if (ref is not None and prix is not None) else None   # comme price_slippage de pysystemtrade
        lignes.append(dict(heure_utc=r.t.strftime("%Y-%m-%d %H:%M:%S"), ordre=f"{'achat' if r.sens > 0 else 'vente'} {r.qte} {r.symbole}",
                           execute=r.qte - reste, prix=prix, delai_s=delai, reference_nq=ref, glissement_points=gl,
                           glissement_ticks=(gl / TICK[r.racine] if gl is not None else None),
                           glissement_dollars=(gl * DOLLAR_POINT[r.racine] * r.qte if gl is not None else None)))
    L = pd.DataFrame(lignes)
    orphelines = x[~x.index.isin(pris) & x.racine.notna()]
    mesures = L.dropna(subset=["glissement_ticks"])
    date = dt.date.today().isoformat()
    T = [f"# Rapprochement des ordres du bot ({date})", "",
         f"Colonnes reconnues dans l'export : {trouve}. Heures de l'export lues dans le fuseau {a.fuseau}.", "",
         f"- Ordres du journal : {len(L)} ; executes en entier : {int((L.execute == o.qte.values).sum()) if len(L) else 0} ; "
         f"sans execution trouvee : {int((L.execute == 0).sum()) if len(L) else 0}.",
         f"- Executions de l'export sans ordre du bot (trade a la main, autre bot, ou fuseau faux) : {len(orphelines)}."]
    if len(mesures):
        moy = mesures.glissement_ticks.mean()
        T += [f"- Glissement moyen des ordres MNQ contre la cloture de la minute de decision : **{moy:+.2f} tick** par ordre "
              f"({mesures.glissement_dollars.mean():+.2f} $), sur {len(mesures)} ordres ; delai moyen {mesures.delai_s.mean():.1f} s.",
              f"- Hypothese de l'usine : {HYPOTHESE_TICKS:+.0f} tick par ordre. "
              + ("**Le reel est pire que l'hypothese** : les resultats de l'usine sont trop optimistes d'environ "
                 f"{(HYPOTHESE_TICKS - moy) * 0.5 * 2:.2f} $ par aller-retour." if moy < HYPOTHESE_TICKS
                 else "Le reel est dans l'hypothese ou meilleur.")]
    T += ["", "Une valeur negative est contre toi (achat plus cher, vente moins chere que la reference).", "",
          tableau(L) if len(L) else "Aucun ordre dans le journal.", ""]
    if len(orphelines):
        T += ["Executions sans ordre du bot :", "", tableau(orphelines[["t", "symbole", "sens", "qte", "prix"]]), ""]
    f = Path(f"rapprochement_{date}.md"); f.write_text("\n".join(T), encoding="utf-8")
    print("\n".join(T[:8])); print(f"\nRapport ecrit : {f.resolve()}")


if __name__ == "__main__":
    principal()
