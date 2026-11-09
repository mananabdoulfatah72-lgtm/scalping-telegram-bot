#!/usr/bin/env python3
"""Sonde les sources gratuites du terminal live (nouvelles, calendrier, VIX, cotations) depuis GitHub Actions : le conteneur
de developpement ne les atteint pas. N'enregistre rien : affiche seulement le statut, le format et un apercu court de chaque
source dans le journal de l'Action, pour ecrire et tester les lecteurs du relais."""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
SOURCES = [l.split(None, 1) for l in open(sys.argv[1]) if l.strip() and not l.startswith("#")]


def lire(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


def local(tag):
    return tag.rsplit("}", 1)[-1]


for genre, url in SOURCES:
    url = url.strip()
    try:
        st, ct, b = lire(url)
    except Exception as e:
        print(f"ECHEC {genre:5} {url}\n      {type(e).__name__}: {str(e)[:150]}"); continue
    print(f"OK {st} {genre:5} {len(b) // 1024} Ko {ct[:40]} {url}")
    try:
        if genre == "rss":
            root = ET.fromstring(b)
            items = [e for e in root.iter() if local(e.tag) in ("item", "entry")]
            print(f"      racine {local(root.tag)}, {len(items)} articles")
            for it in items[:3]:
                champs = {local(c.tag): (c.text or c.attrib.get("href", "") or "").strip()[:90] for c in it}
                print("      champs", sorted(champs)[:12])
                print("      ", champs.get("title", "")[:90], "|", champs.get("pubDate") or champs.get("published") or champs.get("updated") or champs.get("date"))
        elif genre == "json":
            d = json.loads(b)
            if isinstance(d, list):
                print(f"      liste de {len(d)} ; premier : {json.dumps(d[0])[:400]}")
            else:
                def forme(x, p=0):
                    if p > 7: return "…"
                    if isinstance(x, dict): return {k: forme(v, p + 1) for k, v in list(x.items())[:40]}
                    if isinstance(x, list): return [forme(x[0], p + 1), f"x{len(x)}"] if x else []
                    return x[:40] if isinstance(x, str) else x
                print("      ", json.dumps(forme(d))[:2500])
        else:
            print("      ", b[:300].decode("utf-8", "replace").replace("\n", " | "))
    except Exception as e:
        print(f"      lecture impossible : {type(e).__name__}: {str(e)[:120]}")
