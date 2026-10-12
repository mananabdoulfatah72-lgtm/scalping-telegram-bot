"""Navigateur piloté par Jarvis (Playwright) : une vraie fenêtre Edge (ou Chrome) avec son propre profil, où les
connexions restent gardées. Jarvis lit, résume et traduit l'onglet actif, gère les onglets, clique, remplit des
formulaires et fait des réservations (restaurant, rendez-vous) ; le clic final (réserver, payer, confirmer)
passe toujours par une confirmation.

Playwright exige que tout se passe dans un même fil : chaque action est envoyée au fil du navigateur."""
from __future__ import annotations

import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote_plus, urlparse

from ..config import dossier
from ..services import S
from . import ErreurOutil, Resultat, module, outil, p

MOTS_SENSIBLES = re.compile(r"(réserv|reserv|confirm|pay|valider|validez|commander|commande|acheter|achat|book|"
                            r"submit|envoyer|s'inscrire|inscription|souscrire|checkout|régler|paiement|abonner|"
                            r"supprimer|delete|transf[eé]r|virement)", re.I)
REPERER = """() => {
  document.querySelectorAll('[data-jarvis]').forEach(e => e.removeAttribute('data-jarvis'));
  const els = [...document.querySelectorAll('a,button,input,select,textarea,summary,[role=button],[role=link],[role=tab],[role=menuitem],[role=option],[role=checkbox],[role=radio],[onclick],[contenteditable=true]')];
  let n = 0; const out = [];
  for (const e of els) {
    const r = e.getBoundingClientRect(), st = getComputedStyle(e);
    if (r.width < 2 || r.height < 2 || st.visibility === 'hidden' || st.display === 'none' || e.disabled) continue;
    if (r.bottom < -50 || r.top > innerHeight * 2.5) continue;
    if (e.type === 'hidden') continue;
    n++; e.setAttribute('data-jarvis', String(n));
    const lab = e.id ? document.querySelector(`label[for="${CSS.escape(e.id)}"]`) : null;
    const t = (e.innerText || e.value || e.getAttribute('aria-label') || (lab && lab.innerText) || e.getAttribute('placeholder') || e.title || e.name || e.alt || '').trim().replace(/\\s+/g, ' ').slice(0, 90);
    out.push({n, tag: e.tagName.toLowerCase(), type: e.type || e.getAttribute('role') || '', t, visible: r.top >= 0 && r.top < innerHeight});
    if (n >= 160) break;
  }
  return out;
}"""
LIRE = """() => {
  const choix = [...document.querySelectorAll('main, article, [role=main]')].sort((a, b) => b.innerText.length - a.innerText.length)[0];
  const base = choix && choix.innerText.length > 600 ? choix : document.body;
  return base ? base.innerText : '';
}"""


@module("navigateur", "NAVIGATEUR")
def etat() -> tuple[str, str]:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return "absent", "module playwright à installer (installer.bat)"
    return "pret", "navigateur prêt" + (" (ouvert)" if NAV.ctx is not None else "")


class Navigateur:
    def __init__(self):
        self._fil = ThreadPoolExecutor(max_workers=1, thread_name_prefix="navigateur")
        self.pw = self.ctx = self.navig = None
        self.page = None
        self.reservation_jusqua = 0.0

    @property
    def reservation(self) -> bool:
        return time.time() < self.reservation_jusqua

    def faire(self, fn, *args, delai: float = 90):
        """Exécute fn dans le fil du navigateur ; relance une fois si la fenêtre a été fermée."""
        def tache():
            for essai in range(2):
                try:
                    self._assurer()
                    return fn(*args)
                except ErreurOutil:
                    raise
                except Exception as e:
                    nom = type(e).__name__
                    if "Timeout" in nom:
                        raise ErreurOutil("La page met trop de temps à répondre.")
                    if essai == 0 and ("closed" in str(e).lower() or "Target" in str(e)):
                        self._reinitialiser()
                        continue
                    raise ErreurOutil(f"Le navigateur a eu un problème : {nom} : {str(e)[:200]}")
        return self._fil.submit(tache).result(timeout=delai)

    def _reinitialiser(self) -> None:
        for objet in (self.ctx, self.navig):
            try:
                if objet:
                    objet.close()
            except Exception:
                pass
        self.ctx = self.navig = self.page = None

    def _assurer(self) -> None:
        if self.ctx is not None:
            pages = [pg for pg in self.ctx.pages if not pg.is_closed()]
            if pages:
                if self.page is None or self.page.is_closed():
                    self.page = pages[-1]
                return
            self._reinitialiser()
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ErreurOutil("Le navigateur a besoin du module playwright (relance installer.bat).")
        if self.pw is None:
            self.pw = sync_playwright().start()
        cdp = S.cfg.get("navigateur.cdp", "")
        if cdp:
            self.navig = self.pw.chromium.connect_over_cdp(cdp)
            self.ctx = self.navig.contexts[0] if self.navig.contexts else self.navig.new_context()
        else:
            canal = S.cfg.get("navigateur.canal", "msedge" if sys.platform == "win32" else "")
            kw = dict(user_data_dir=str(dossier() / "navigateur"), headless=bool(S.cfg.get("navigateur.sans_tete", False)),
                      no_viewport=True, locale="fr-FR", args=["--start-maximized"])
            try:
                self.ctx = self.pw.chromium.launch_persistent_context(channel=canal or None, **kw)
            except Exception:
                self.ctx = self.pw.chromium.launch_persistent_context(**kw)      # Chromium de Playwright
        self.page = self.ctx.pages[-1] if self.ctx.pages else self.ctx.new_page()

    # ------------------------------------------------------------------ actions (fil du navigateur)
    def onglets(self) -> list:
        return [pg for pg in self.ctx.pages if not pg.is_closed()]

    def element(self, cible: str):
        pg = self.page
        if cible.strip().isdigit():
            loc = pg.locator(f'[data-jarvis="{cible.strip()}"]')
            if loc.count() == 0:
                raise ErreurOutil(f"L'élément {cible} n'existe plus : relis la page avec nav_elements.")
            return loc.first
        for loc in (pg.get_by_role("button", name=cible), pg.get_by_role("link", name=cible),
                    pg.get_by_label(cible), pg.get_by_placeholder(cible), pg.get_by_text(cible)):
            try:
                if loc.count() > 0:
                    return loc.first
            except Exception:
                continue
        raise ErreurOutil(f"Je ne trouve pas « {cible} » sur la page.")

    def libelle(self, cible: str) -> tuple[str, str]:
        """Texte de l'élément visé et site de l'onglet actif (lus dans le fil du navigateur)."""
        def lire():
            if self.ctx is None or self.page is None:
                return cible, ""
            site = urlparse(self.page.url).netloc
            try:
                el = self.element(cible)
                texte = el.inner_text(timeout=2000) or el.get_attribute("value") or el.get_attribute("aria-label") or cible
                return texte.strip(), site
            except Exception:
                return cible, site
        try:
            return self._fil.submit(lire).result(timeout=10)
        except Exception:
            return cible, ""

    def formulaire_actif(self) -> tuple[str, str]:
        """Boutons du formulaire où se trouve le curseur, et site : Entrée y vaut un clic sur l'envoi."""
        def lire():
            if self.ctx is None or self.page is None:
                return "", ""
            site = urlparse(self.page.url).netloc
            try:
                return self.page.evaluate(FORMULAIRE) or "", site
            except Exception:
                return "", site
        try:
            return self._fil.submit(lire).result(timeout=10)
        except Exception:
            return "", ""


FORMULAIRE = """() => {
  const f = document.activeElement && document.activeElement.closest ? document.activeElement.closest('form') : null;
  if (!f) return '';
  return [...f.querySelectorAll('button, input[type=submit], [role=button]')]
    .map(b => (b.innerText || b.value || b.getAttribute('aria-label') || '').trim()).join(' | ').slice(0, 300) || 'envoyer';
}"""
NAV = Navigateur()


def adresse_web(url: str) -> str:
    """Seulement des pages web : pas de fichiers du PC (file://) ni de pages internes du navigateur."""
    url = url.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", url):
        url = "https://" + url
    if urlparse(url).scheme.lower() not in ("http", "https"):
        raise ErreurOutil("Je n'ouvre que des pages web (http ou https) dans le navigateur.")
    return url


def zone(_args: dict) -> str:
    return "RESERVATIONS" if NAV.reservation else "NAVIGATEUR"


def resume_page(pg) -> str:
    return f"Onglet : {pg.title()[:120]} — {pg.url}"


def nettoyer(texte: str) -> str:
    texte = re.sub(r"[ \t ]+", " ", texte)
    return re.sub(r"\n\s*\n+", "\n\n", texte).strip()


@outil("nav_ouvrir", "Ouvre une adresse web dans le navigateur de Jarvis (onglet actif, ou nouvel onglet).", zone,
       {"url": p("string", "Adresse"), "nouvel_onglet": p("boolean", "Ouvrir dans un nouvel onglet")}, requis=["url"])
def nav_ouvrir(url: str, nouvel_onglet: bool = False) -> str:
    url = adresse_web(url)

    def f():
        if nouvel_onglet:
            NAV.page = NAV.ctx.new_page()
        NAV.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        NAV.page.bring_to_front()
        return resume_page(NAV.page)
    return NAV.faire(f)


@outil("nav_rechercher", "Fait une recherche sur le web et renvoie les résultats.", zone,
       {"requete": p("string", "Recherche")}, requis=["requete"])
def nav_rechercher(requete: str) -> str:
    def f():
        NAV.page.goto(f"https://duckduckgo.com/?q={quote_plus(requete)}&kl=fr-fr", wait_until="domcontentloaded",
                      timeout=30000)
        NAV.page.wait_for_timeout(1200)
        liens = NAV.page.evaluate("""() => [...document.querySelectorAll('article h2 a, a[data-testid=result-title-a]')]
            .slice(0, 8).map(a => a.innerText.trim() + ' — ' + a.href)""")
        return "Résultats :\n" + ("\n".join(liens) if liens else nettoyer(NAV.page.evaluate(LIRE))[:3000])
    return NAV.faire(f)


@outil("nav_lire", "Lit le texte de l'onglet actif (pour le résumer, le traduire ou répondre à une question).", zone,
       {"max_caracteres": p("integer", "Longueur maximale (défaut 15000)")})
def nav_lire(max_caracteres: int = 15000) -> str:
    def f():
        texte = nettoyer(NAV.page.evaluate(LIRE))
        return f"{resume_page(NAV.page)}\n\n{texte[:max(1000, min(40000, max_caracteres))]}"
    return NAV.faire(f)


@outil("nav_elements", "Liste les éléments cliquables et champs de l'onglet actif, numérotés, pour nav_cliquer et "
       "nav_remplir.", zone)
def nav_elements() -> str:
    def f():
        els = NAV.page.evaluate(REPERER)
        lignes = [resume_page(NAV.page)]
        for e in els:
            lignes.append(f"{e['n']}. {e['tag']}{'/' + e['type'] if e['type'] else ''} « {e['t']} »{'' if e['visible'] else ' (plus bas)'}")
        return "\n".join(lignes)
    return NAV.faire(f)


def _question_clic(args: dict) -> str | None:
    cible = str(args.get("element", ""))
    texte, site = NAV.libelle(cible)
    if MOTS_SENSIBLES.search(texte) or MOTS_SENSIBLES.search(cible):
        return f"Cliquer sur « {texte[:80]} »" + (f" sur {site}" if site else "")
    return None


@outil("nav_cliquer", "Clique sur un élément de la page (numéro donné par nav_elements, ou texte du bouton/lien). "
       "Les boutons qui réservent, paient, envoient ou confirment demandent une confirmation.", zone,
       {"element": p("string", "Numéro ou texte de l'élément")}, requis=["element"], confirmer=_question_clic)
def nav_cliquer(element: str) -> str:
    def f():
        avant = len(NAV.onglets())
        NAV.element(element).click(timeout=10000)
        NAV.page.wait_for_timeout(900)
        apres = NAV.onglets()
        if len(apres) > avant:
            NAV.page = apres[-1]
        try:
            NAV.page.wait_for_load_state("domcontentloaded", timeout=8000)
        except Exception:
            pass
        return "Cliqué. " + resume_page(NAV.page)
    return NAV.faire(f)


@outil("nav_remplir", "Remplit un champ ou choisit une option dans une liste (numéro de nav_elements ou nom du champ).",
       zone, {"element": p("string", "Numéro ou nom du champ"), "valeur": p("string", "Texte ou option à choisir")},
       requis=["element", "valeur"])
def nav_remplir(element: str, valeur: str) -> str:
    def f():
        el = NAV.element(element)
        tag = el.evaluate("e => e.tagName.toLowerCase()")
        if tag == "select":
            try:
                el.select_option(label=valeur, timeout=5000)
            except Exception:
                el.select_option(valeur, timeout=5000)
        else:
            el.fill(valeur, timeout=8000)
        return f"Champ rempli avec « {valeur[:60]} »."
    return NAV.faire(f)


def _question_touche(args: dict) -> str | None:
    if str(args.get("touche", "")).lower() not in ("enter", "numpadenter"):
        return None
    boutons, site = NAV.formulaire_actif()
    if boutons and MOTS_SENSIBLES.search(boutons):
        return f"Valider le formulaire ({boutons[:80]})" + (f" sur {site}" if site else "")
    return None


@outil("nav_touche", "Appuie sur une touche dans la page (Enter, Escape, Tab, ArrowDown...). Entrée dans un formulaire "
       "qui réserve, paie ou envoie demande une confirmation.", zone,
       {"touche": p("string", "Nom de la touche (Playwright), ex. Enter")}, requis=["touche"], confirmer=_question_touche)
def nav_touche(touche: str) -> str:
    def f():
        NAV.page.keyboard.press(touche)
        NAV.page.wait_for_timeout(600)
        return f"Touche {touche}. " + resume_page(NAV.page)
    return NAV.faire(f)


@outil("nav_defiler", "Fait défiler la page vers le bas ou le haut.", zone,
       {"direction": p("string", "Sens", enum=["bas", "haut"])}, requis=["direction"])
def nav_defiler(direction: str) -> str:
    def f():
        NAV.page.mouse.wheel(0, 900 if direction == "bas" else -900)
        NAV.page.wait_for_timeout(500)
        return "Défilé."
    return NAV.faire(f)


@outil("nav_capture", "Capture de l'onglet actif en image, pour les pages qu'il faut voir (plan, calendrier, carte).",
       zone)
def nav_capture() -> Resultat:
    def f():
        img = NAV.page.screenshot(type="jpeg", quality=72, timeout=15000)
        return Resultat(resume_page(NAV.page), [(img, "image/jpeg")])
    return NAV.faire(f)


@outil("nav_onglets", "Liste les onglets ouverts dans le navigateur de Jarvis.", zone)
def nav_onglets() -> str:
    def f():
        return "\n".join(f"{i}. {'(actif) ' if pg == NAV.page else ''}{pg.title()[:80]} — {pg.url}"
                         for i, pg in enumerate(NAV.onglets())) or "Aucun onglet."
    return NAV.faire(f)


@outil("nav_onglet", "Active ou ferme un onglet (numéro de nav_onglets), ou en ouvre un nouveau.", zone,
       {"action": p("string", "Action", enum=["activer", "fermer", "nouveau"]), "numero": p("integer", "Numéro"),
        "url": p("string", "Adresse pour un nouvel onglet")}, requis=["action"])
def nav_onglet(action: str, numero: int | None = None, url: str = "") -> str:
    def f():
        pages = NAV.onglets()
        if action == "nouveau":
            NAV.page = NAV.ctx.new_page()
            if url:
                NAV.page.goto(adresse_web(url), wait_until="domcontentloaded", timeout=30000)
            NAV.page.bring_to_front()
            return "Nouvel onglet. " + resume_page(NAV.page)
        if numero is None or not 0 <= numero < len(pages):
            raise ErreurOutil(f"Numéro d'onglet invalide (0 à {len(pages) - 1}).")
        pg = pages[numero]
        if action == "activer":
            NAV.page = pg
            pg.bring_to_front()
            return resume_page(pg)
        pg.close()
        restantes = NAV.onglets()
        NAV.page = restantes[-1] if restantes else NAV.ctx.new_page()
        return "Onglet fermé."
    return NAV.faire(f)


SITES = {"restaurant": "https://www.thefork.fr/recherche?queryText={q}",
         "medecin": "https://www.doctolib.fr/search?keyword={q}",
         "coiffeur": "https://www.planity.com/recherche?q={q}"}


@outil("reservation_demarrer", "Commence une réservation sur le web (restaurant, médecin, coiffeur, ou un site donné) : "
       "ouvre le site ; ensuite nav_elements, nav_remplir et nav_cliquer jusqu'à la page de validation. Le clic final "
       "est confirmé par l'utilisateur.", "RESERVATIONS",
       {"type": p("string", "Type de réservation", enum=["restaurant", "medecin", "coiffeur", "autre"]),
        "recherche": p("string", "Ce qu'il faut chercher (nom, ville, spécialité)"),
        "site": p("string", "Adresse d'un site précis (facultatif)"),
        "details": p("string", "Date, heure, nombre de personnes, nom...")}, requis=["type", "recherche"])
def reservation_demarrer(type: str, recherche: str, site: str = "", details: str = "") -> str:
    url = adresse_web(site) if site else SITES.get(type, "https://duckduckgo.com/?q={q}").format(q=quote_plus(recherche))
    NAV.reservation_jusqua = time.time() + 15 * 60

    def f():
        NAV.page = NAV.ctx.new_page()
        NAV.page.goto(url, wait_until="domcontentloaded", timeout=30000)
        NAV.page.bring_to_front()
        return resume_page(NAV.page)
    r = NAV.faire(f)
    return (f"Mode réservation (15 min). {r}\nDétails demandés : {details or 'aucun'}. Continue avec nav_elements, "
            f"nav_remplir et nav_cliquer ; si une connexion est demandée, demande à l'utilisateur de se connecter dans "
            f"la fenêtre (ses connexions restent gardées ensuite).")
