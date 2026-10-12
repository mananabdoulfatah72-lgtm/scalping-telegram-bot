"""Vision de l'écran : Jarvis prend une capture et la regarde (« c'est quoi cette erreur ? », « lis ça »,
« traduis ce texte »). La capture part au modèle en image, réduite pour rester lisible et légère."""
from __future__ import annotations

import io

from . import ErreurOutil, Resultat, module, outil, p

COTE_MAX = 1568


@module("vision", "VISION")
def etat() -> tuple[str, str]:
    try:
        import mss  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return "absent", "modules mss et pillow à installer (installer.bat)"
    return "pret", "capture d'écran"


def capture(ecran: int = 1) -> tuple[bytes, int, int, int]:
    """Capture JPEG de l'écran voulu (1 = principal, 0 = tous). Renvoie (octets, largeur, hauteur, nb d'écrans)."""
    try:
        import mss
        from PIL import Image
    except ImportError:
        raise ErreurOutil("La vision a besoin des modules mss et pillow (relance installer.bat).")
    with mss.mss() as sct:
        moniteurs = sct.monitors                     # [0] = tous les écrans, [1..] = chaque écran
        if ecran < 0 or ecran >= len(moniteurs):
            raise ErreurOutil(f"Il y a {len(moniteurs) - 1} écran(s) ; l'écran {ecran} n'existe pas.")
        brut = sct.grab(moniteurs[ecran])
        img = Image.frombytes("RGB", brut.size, brut.bgra, "raw", "BGRX")
    img.thumbnail((COTE_MAX, COTE_MAX))
    tampon = io.BytesIO()
    img.save(tampon, "JPEG", quality=82)
    return tampon.getvalue(), img.width, img.height, len(moniteurs) - 1


@outil("voir_ecran", "Regarde l'écran du PC (capture) pour répondre à une question sur ce qui est affiché : "
       "erreur, texte à lire ou traduire, page, jeu, vidéo.", "VISION",
       {"question": p("string", "Ce qu'il faut regarder ou faire avec l'image"),
        "ecran": p("integer", "Numéro de l'écran : 1 = principal (défaut), 2 = second, 0 = tous")})
def voir_ecran(question: str = "", ecran: int = 1) -> Resultat:
    octets, l, h, n = capture(ecran)
    texte = f"Capture de l'écran {ecran or 'tous'} sur {n} ({l} x {h} pixels)." + (f" Demande : {question}" if question else "")
    return Resultat(texte, [(octets, "image/jpeg")])
