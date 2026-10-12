"""Mémoire à long terme : retenir, retrouver, lister, oublier (préférences, proches, projets, faits)."""
from __future__ import annotations

from ..memoire import CATEGORIES
from ..services import S
from . import ErreurOutil, module, outil, p


@module("memoire", "MEMOIRE")
def etat() -> tuple[str, str]:
    if S.memoire is None:
        return "erreur", "mémoire non ouverte"
    return "pret", f"{len(S.memoire.liste(limite=10000))} souvenirs"


@outil("memoire_retenir", "Retient durablement une information sur l'utilisateur (préférence, proche, projet, "
       "habitude, fait). Une phrase autonome et précise, ex. « Sa sœur s'appelle Inès, anniversaire le 3 mai ».",
       "MEMOIRE", {"texte": p("string", "L'information, en une phrase autonome"),
                   "categorie": p("string", "Catégorie", enum=CATEGORIES)}, requis=["texte"])
def memoire_retenir(texte: str, categorie: str = "fait") -> str:
    ident = S.memoire.retenir(texte, categorie)
    return f"Retenu (souvenir {ident})."


@outil("memoire_chercher", "Cherche dans la mémoire à long terme.", "MEMOIRE",
       {"requete": p("string", "Mots à chercher")}, requis=["requete"])
def memoire_chercher(requete: str) -> str:
    r = S.memoire.chercher(requete, 10)
    return "\n".join(f"[{s['id']}] ({s['categorie']}) {s['texte']}" for s in r) or "Rien trouvé dans ma mémoire."


@outil("memoire_liste", "Liste les souvenirs, éventuellement d'une catégorie.", "MEMOIRE",
       {"categorie": p("string", "Catégorie", enum=CATEGORIES)})
def memoire_liste(categorie: str = "") -> str:
    r = S.memoire.liste(categorie or None, 60)
    return "\n".join(f"[{s['id']}] ({s['categorie']}) {s['texte']}" for s in r) or "Ma mémoire est vide."


@outil("memoire_oublier", "Oublie un souvenir (par son numéro).", "MEMOIRE",
       {"id": p("integer", "Numéro du souvenir")}, requis=["id"])
def memoire_oublier(id: int) -> str:
    if not S.memoire.oublier(id):
        raise ErreurOutil(f"Pas de souvenir numéro {id}.")
    return f"Souvenir {id} oublié."
