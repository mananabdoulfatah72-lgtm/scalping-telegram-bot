#!/usr/bin/env python3
"""Compare les variantes de relance/README.md a partir des sorties de Bot3en1.Replay (une par variante) : points par
periode (P1 avril - 1er octobre 2026, P2 2 - 16 octobre), pire baisse, trades ajoutes. Usage : comparer.py <dossier>"""
import re
import sys
from pathlib import Path

D = Path(sys.argv[1])
P1_FIN = "2026-10-01"
MOTIF = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie)(?: 16h00)? (\d+h\d+) a ([\d.]+)(.*)$")


def trades(nom):
    out, ouvert = [], None
    for l in (D / f"{nom}.txt").read_text().splitlines():
        x = MOTIF.match(l)
        if not x or "ecarte" in l:
            continue
        j, quoi, h, p, reste = x.group(1), x.group(2), x.group(3), float(x.group(4)), x.group(5)
        if quoi in ("achat", "vente"):
            ouvert = (j, h, 1 if quoi == "achat" else -1, p, "relance" in reste, "cassure forte" in reste)
        elif ouvert:
            j0, h0, sens, e, rel, frt = ouvert
            out.append({"jour": j0, "heure": h0, "sens": sens, "points": sens * (p - e) - 1.5, "relance": rel, "force": frt})
            ouvert = None
    return out


def baisse(pts):
    c = pic = pire = 0.0
    for x in pts:
        c += x; pic = max(pic, c); pire = max(pire, pic - c)
    return pire


res = {}
for nom in ["H1", "R", "S1", "RS1", "S05", "RS05", "SANS"]:
    t = trades(nom)
    p1 = [x for x in t if x["jour"] <= P1_FIN]; p2 = [x for x in t if x["jour"] > P1_FIN]
    res[nom] = (t, p1, p2)
    print(f"{nom:5s} P1 {len(p1):3d} trades {sum(x['points'] for x in p1):+8.1f} pt (pire baisse {baisse([x['points'] for x in p1]):6.1f})"
          f" | P2 {len(p2):2d} trades {sum(x['points'] for x in p2):+7.1f} pt | relances {sum(x['relance'] for x in t)},"
          f" cassures fortes {sum(x['force'] for x in t)}")
h1 = {(x["jour"], x["heure"]) for x in res["H1"][0]}
for nom in ["R", "S1", "RS1"]:
    extra = [x for x in res[nom][0] if (x["jour"], x["heure"]) not in h1]
    print(f"\ntrades ajoutes par {nom} : {len(extra)}, {sum(x['points'] for x in extra):+.1f} pt")
    for x in extra:
        print(f"  {x['jour']} {x['heure']} {'achat' if x['sens'] > 0 else 'vente'} {x['points']:+.2f} pt{' (relance)' if x['relance'] else ''}{' (cassure forte)' if x['force'] else ''}")
