"""Mémoire à long terme de Jarvis (SQLite, recherche plein texte FTS5) : préférences, proches, projets, faits.
Les souvenirs utiles à une demande sont ajoutés au message envoyé au cerveau. Garde aussi le journal des
échanges et des valeurs datées (abonnés Instagram de la veille...)."""
from __future__ import annotations

import re
import sqlite3
import threading
import time
from pathlib import Path

CATEGORIES = ["profil", "preference", "personne", "projet", "fait", "autre"]
MOTS_VIDES = set("les des une un le la de du et ou que qui quoi est sont pour avec dans sur pas plus mon ma mes ton ta "
                 "tes son sa ses nos vos leur leurs ce cet cette ces je tu il elle on nous vous ils elles me te se moi "
                 "toi lui y en au aux par fait faire quand comment".split())


class Memoire:
    def __init__(self, fichier: Path):
        self.fichier = Path(fichier)
        self._verrou = threading.Lock()
        self.cx = sqlite3.connect(str(self.fichier), check_same_thread=False)
        self.cx.row_factory = sqlite3.Row
        self.fts = True
        with self._verrou, self.cx:
            self.cx.execute("CREATE TABLE IF NOT EXISTS souvenirs (id INTEGER PRIMARY KEY, texte TEXT NOT NULL, "
                            "categorie TEXT NOT NULL DEFAULT 'fait', cree REAL, maj REAL)")
            self.cx.execute("CREATE TABLE IF NOT EXISTS echanges (id INTEGER PRIMARY KEY, t REAL, source TEXT, "
                            "demande TEXT, reponse TEXT)")
            self.cx.execute("CREATE TABLE IF NOT EXISTS valeurs (cle TEXT, jour TEXT, valeur REAL, "
                            "PRIMARY KEY (cle, jour))")
            try:
                self.cx.execute("CREATE VIRTUAL TABLE IF NOT EXISTS souvenirs_fts USING fts5(texte, categorie, "
                                "content='souvenirs', content_rowid='id', tokenize='unicode61 remove_diacritics 2')")
                self.cx.executescript("""
                    CREATE TRIGGER IF NOT EXISTS s_ai AFTER INSERT ON souvenirs BEGIN
                      INSERT INTO souvenirs_fts(rowid, texte, categorie) VALUES (new.id, new.texte, new.categorie); END;
                    CREATE TRIGGER IF NOT EXISTS s_ad AFTER DELETE ON souvenirs BEGIN
                      INSERT INTO souvenirs_fts(souvenirs_fts, rowid, texte, categorie)
                      VALUES ('delete', old.id, old.texte, old.categorie); END;
                    CREATE TRIGGER IF NOT EXISTS s_au AFTER UPDATE ON souvenirs BEGIN
                      INSERT INTO souvenirs_fts(souvenirs_fts, rowid, texte, categorie)
                      VALUES ('delete', old.id, old.texte, old.categorie);
                      INSERT INTO souvenirs_fts(rowid, texte, categorie) VALUES (new.id, new.texte, new.categorie); END;
                """)
            except sqlite3.OperationalError:                  # SQLite sans FTS5 : recherche simple par LIKE
                self.fts = False

    # ------------------------------------------------------------------ souvenirs
    def retenir(self, texte: str, categorie: str = "fait") -> int:
        texte = texte.strip()
        if not texte:
            raise ValueError("souvenir vide")
        categorie = categorie if categorie in CATEGORIES else "autre"
        with self._verrou, self.cx:
            deja = self.cx.execute("SELECT id FROM souvenirs WHERE lower(texte) = lower(?)", (texte,)).fetchone()
            if deja:
                self.cx.execute("UPDATE souvenirs SET maj = ?, categorie = ? WHERE id = ?", (time.time(), categorie, deja["id"]))
                return int(deja["id"])
            cur = self.cx.execute("INSERT INTO souvenirs (texte, categorie, cree, maj) VALUES (?, ?, ?, ?)",
                                  (texte, categorie, time.time(), time.time()))
            return int(cur.lastrowid)

    def oublier(self, ident: int) -> bool:
        with self._verrou, self.cx:
            return self.cx.execute("DELETE FROM souvenirs WHERE id = ?", (int(ident),)).rowcount > 0

    def liste(self, categorie: str | None = None, limite: int = 50) -> list[dict]:
        with self._verrou:
            if categorie:
                rows = self.cx.execute("SELECT * FROM souvenirs WHERE categorie = ? ORDER BY maj DESC LIMIT ?",
                                       (categorie, limite)).fetchall()
            else:
                rows = self.cx.execute("SELECT * FROM souvenirs ORDER BY maj DESC LIMIT ?", (limite,)).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def mots(texte: str) -> list[str]:
        return [m for m in re.findall(r"[\wÀ-ÿ]{3,}", texte.lower()) if m not in MOTS_VIDES][:12]

    def chercher(self, requete: str, limite: int = 6) -> list[dict]:
        mots = self.mots(requete)
        if not mots:
            return []
        with self._verrou:
            if self.fts:
                q = " OR ".join(f'"{m}"*' for m in mots)
                rows = self.cx.execute("SELECT s.* FROM souvenirs_fts f JOIN souvenirs s ON s.id = f.rowid "
                                       "WHERE souvenirs_fts MATCH ? ORDER BY bm25(souvenirs_fts) LIMIT ?",
                                       (q, limite)).fetchall()
            else:
                cond = " OR ".join("lower(texte) LIKE ?" for _ in mots)
                rows = self.cx.execute(f"SELECT * FROM souvenirs WHERE {cond} ORDER BY maj DESC LIMIT ?",
                                       [f"%{m}%" for m in mots] + [limite]).fetchall()
        return [dict(r) for r in rows]

    def contexte(self, demande: str) -> str:
        """Souvenirs à joindre à une demande : le profil et les préférences, plus ceux qui correspondent."""
        vus, lignes = set(), []
        for s in self.liste("profil", 10) + self.liste("preference", 15) + self.chercher(demande):
            if s["id"] not in vus:
                vus.add(s["id"])
                lignes.append(f"- [{s['id']}] ({s['categorie']}) {s['texte']}")
        return "\n".join(lignes[:30])

    # ------------------------------------------------------------------ journal et valeurs datées
    def journal(self, source: str, demande: str, reponse: str) -> None:
        with self._verrou, self.cx:
            self.cx.execute("INSERT INTO echanges (t, source, demande, reponse) VALUES (?, ?, ?, ?)",
                            (time.time(), source, demande, reponse))

    def derniers_echanges(self, n: int = 20) -> list[dict]:
        with self._verrou:
            rows = self.cx.execute("SELECT * FROM echanges ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        return [dict(r) for r in reversed(rows)]

    def noter_valeur(self, cle: str, jour: str, valeur: float) -> None:
        with self._verrou, self.cx:
            self.cx.execute("INSERT OR REPLACE INTO valeurs (cle, jour, valeur) VALUES (?, ?, ?)", (cle, jour, valeur))

    def valeur(self, cle: str, jour: str) -> float | None:
        with self._verrou:
            r = self.cx.execute("SELECT valeur FROM valeurs WHERE cle = ? AND jour = ?", (cle, jour)).fetchone()
        return None if r is None else float(r["valeur"])
