"""Contrôle du PC Windows : applications, son, lecture média, raccourcis clavier, frappe de texte, fenêtres,
presse-papiers, fichiers, statistiques (CPU, RAM, GPU, disque, batterie), verrouillage, alimentation et
commandes PowerShell (avec confirmation)."""
from __future__ import annotations

import ctypes
import difflib
import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

from ..services import S
from . import ErreurOutil, module, outil, p

WINDOWS = sys.platform == "win32"
SANS_FENETRE = getattr(subprocess, "CREATE_NO_WINDOW", 0)

APPS = {  # nom parlé -> commande, adresse d'application ou exécutable (complété par [pc] applications)
    "chrome": "chrome", "google chrome": "chrome", "edge": "msedge", "firefox": "firefox",
    "spotify": "spotify:", "discord": "discord://", "steam": "steam://open/main", "teams": "msteams:",
    "whatsapp": "whatsapp:", "explorateur": "explorer", "explorateur de fichiers": "explorer",
    "calculatrice": "calc", "bloc-notes": "notepad", "bloc notes": "notepad", "paramètres": "ms-settings:",
    "gestionnaire des tâches": "taskmgr", "vs code": "code", "visual studio code": "code", "word": "winword",
    "excel": "excel", "powerpoint": "powerpnt", "outlook": "outlook", "terminal": "wt", "invite de commandes": "cmd",
    "paint": "mspaint", "capture d'écran": "ms-screenclip:", "musique": "mswindowsmusic:", "photos": "ms-photos:",
    "horloge": "ms-clock:", "calendrier": "outlookcal:", "météo": "bingweather:", "store": "ms-windows-store:",
}
TOUCHES = {"ctrl": 0x11, "control": 0x11, "alt": 0x12, "shift": 0x10, "maj": 0x10, "win": 0x5B, "windows": 0x5B,
           "entree": 0x0D, "entrée": 0x0D, "enter": 0x0D, "echap": 0x1B, "échap": 0x1B, "esc": 0x1B, "tab": 0x09,
           "espace": 0x20, "space": 0x20, "retour": 0x08, "backspace": 0x08, "suppr": 0x2E, "delete": 0x2E,
           "inser": 0x2D, "debut": 0x24, "début": 0x24, "home": 0x24, "fin": 0x23, "end": 0x23, "pageup": 0x21,
           "pagedown": 0x22, "haut": 0x26, "up": 0x26, "bas": 0x28, "down": 0x28, "gauche": 0x25, "left": 0x25,
           "droite": 0x27, "right": 0x27, "impr": 0x2C, "printscreen": 0x2C}
TOUCHES.update({f"f{i}": 0x6F + i for i in range(1, 13)})
MEDIA = {"lecture_pause": 0xB3, "suivant": 0xB0, "precedent": 0xB1, "stop": 0xB2}


@module("pc", "PC")
def etat() -> tuple[str, str]:
    if not WINDOWS:
        return "pret", "statistiques seulement (contrôle complet sous Windows)"
    try:
        import pycaw  # noqa: F401
        son = "son précis"
    except ImportError:
        son = "son par touches (pycaw absent)"
    return "pret", f"contrôle complet, {son}"


def windows_seulement() -> None:
    if not WINDOWS:
        raise ErreurOutil("Cette action n'est possible que sur le PC Windows.")


# ------------------------------------------------------------------ clavier (ctypes, sans bibliothèque)
def _touche(vk: int, relache: bool = False) -> None:
    ctypes.windll.user32.keybd_event(vk, 0, 0x0002 if relache else 0, 0)


def appuyer(vks: list[int]) -> None:
    windows_seulement()
    for vk in vks:
        _touche(vk)
        time.sleep(0.02)
    for vk in reversed(vks):
        _touche(vk, True)
        time.sleep(0.02)


if WINDOWS:
    from ctypes import wintypes

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

    class _UNION(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT), ("mi", MOUSEINPUT)]

    class INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _UNION)]


def taper_unicode(texte: str) -> None:
    """Tape du texte comme au clavier (accents compris), caractère par caractère (SendInput Unicode)."""
    windows_seulement()
    envoyer = ctypes.windll.user32.SendInput
    for ch in texte:
        if ch == "\n":
            appuyer([0x0D])
            continue
        code = ch.encode("utf-16-le")                         # 1 ou 2 unités UTF-16 (émojis)
        for i in range(0, len(code), 2):
            u = int.from_bytes(code[i:i + 2], "little")
            for flags in (0x0004, 0x0004 | 0x0002):              # KEYEVENTF_UNICODE, puis relâché
                inp = INPUT(type=1, u=_UNION(ki=KEYBDINPUT(wVk=0, wScan=u, dwFlags=flags, time=0, dwExtraInfo=None)))
                envoyer(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        time.sleep(0.004)


# ------------------------------------------------------------------ applications
def raccourcis_menu() -> dict[str, Path]:
    """Raccourcis du menu Démarrer (nom en minuscules -> fichier .lnk)."""
    dossiers = [Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "Microsoft/Windows/Start Menu/Programs",
                Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
                Path.home() / "Desktop", Path(os.environ.get("PUBLIC", r"C:\Users\Public")) / "Desktop"]
    out: dict[str, Path] = {}
    for d in dossiers:
        if d.is_dir():
            for f in d.rglob("*.lnk"):
                nom = f.stem.lower()
                if "uninstall" in nom or "désinstaller" in nom:
                    continue
                out.setdefault(nom, f)
    return out


def trouver_application(nom: str) -> str | Path | None:
    n = nom.lower().strip()
    perso = {k.lower(): v for k, v in (S.cfg.get("pc.applications", {}) or {}).items()}
    if n in perso:
        return perso[n]
    if n in APPS:
        return APPS[n]
    menu = raccourcis_menu() if WINDOWS else {}
    if n in menu:
        return menu[n]
    contient = [k for k in menu if n in k]
    if contient:
        return menu[min(contient, key=len)]
    proche = difflib.get_close_matches(n, list(menu) + list(APPS), n=1, cutoff=0.72)
    if proche:
        return menu.get(proche[0]) or APPS.get(proche[0])
    return None


@outil("pc_ouvrir_application", "Ouvre une application (Spotify, Chrome, Discord, OBS, Word, un jeu...).", "PC",
       {"nom": p("string", "Nom de l'application")}, requis=["nom"])
def pc_ouvrir_application(nom: str) -> str:
    windows_seulement()
    cible = trouver_application(nom)
    if cible is None:
        raise ErreurOutil(f"Je ne trouve pas l'application « {nom} ». Tu peux l'ajouter dans [pc] applications de config.toml.")
    if isinstance(cible, Path) or ":" in str(cible):
        os.startfile(str(cible))
    else:
        subprocess.Popen(["cmd", "/c", "start", "", str(cible)], creationflags=SANS_FENETRE)
    return f"{nom} est lancé."


PROTEGES = {"system", "registry", "smss", "csrss", "wininit", "winlogon", "services", "lsass", "lsaiso", "svchost",
            "fontdrvhost", "dwm", "explorer", "sihost", "ctfmon", "conhost", "memcompression", "msmpeng", "securityhealthservice"}


def processus_vises(nom: str) -> list:
    """Processus dont le nom contient `nom`, sans ceux de Windows ni Jarvis lui-même."""
    import psutil
    n = nom.lower().replace(" ", "")
    if len(n) < 3:
        raise ErreurOutil("Nom d'application trop court pour savoir laquelle fermer.")
    moi = {os.getpid(), os.getppid()}
    vises = []
    for pr in psutil.process_iter(["name", "pid"]):
        court = (pr.info["name"] or "").lower().replace(" ", "").removesuffix(".exe")
        if court and n in court and court not in PROTEGES and pr.info["pid"] not in moi:
            vises.append(pr)
    return vises


def _question_fermer(args: dict) -> str:
    try:
        noms = sorted({pr.info["name"] for pr in processus_vises(args.get("nom", ""))})
    except Exception:
        noms = []
    return f"Fermer {', '.join(noms[:6]) if noms else args.get('nom', '')} (le travail non enregistré sera perdu)"


@outil("pc_fermer_application", "Ferme une application (les données non enregistrées peuvent être perdues).", "PC",
       {"nom": p("string", "Nom de l'application ou du processus")}, requis=["nom"], confirmer=_question_fermer)
def pc_fermer_application(nom: str) -> str:
    vises = processus_vises(nom)
    if not vises:
        raise ErreurOutil(f"Aucune application ouverte ne correspond à « {nom} » (les processus de Windows sont protégés).")
    for pr in vises:
        try:
            pr.terminate()
        except Exception:
            pass
    return f"{nom} fermé ({len(vises)} processus)."


# ------------------------------------------------------------------ son et média
def volume_windows():
    from ctypes import POINTER, cast
    import comtypes
    try:
        comtypes.CoInitialize()
    except OSError:
        pass
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    dev = AudioUtilities.GetSpeakers()
    if hasattr(dev, "EndpointVolume"):                # pycaw récent
        return dev.EndpointVolume
    interface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


@outil("pc_volume", "Règle le son du PC : niveau précis, monter, baisser, couper ou remettre.", "PC",
       {"action": p("string", "Action", enum=["regler", "monter", "baisser", "muet", "son"]),
        "niveau": p("integer", "Niveau en % pour regler, ou pas en % pour monter/baisser (défaut 10)")},
       requis=["action"])
def pc_volume(action: str, niveau: int | None = None) -> str:
    windows_seulement()
    try:
        v = volume_windows()
        actuel = round(v.GetMasterVolumeLevelScalar() * 100)
        if action == "muet":
            v.SetMute(1, None)
            return "Son coupé."
        if action == "son":
            v.SetMute(0, None)
            return f"Son remis ({actuel} %)."
        cible = {"regler": niveau if niveau is not None else actuel, "monter": actuel + (niveau or 10),
                 "baisser": actuel - (niveau or 10)}[action]
        cible = max(0, min(100, int(cible)))
        v.SetMute(0, None)
        v.SetMasterVolumeLevelScalar(cible / 100, None)
        return f"Volume à {cible} %."
    except ImportError:
        pas = max(1, (niveau or 10) // 2)
        vk = {"monter": 0xAF, "baisser": 0xAE, "muet": 0xAD, "son": 0xAD}.get(action)
        if vk is None:
            raise ErreurOutil("Réglage précis impossible sans le module pycaw (installé par installer.bat).")
        for _ in range(1 if action in ("muet", "son") else pas):
            appuyer([vk])
        return "C'est fait."


@outil("pc_media", "Contrôle la lecture en cours (Spotify, YouTube...) : lecture/pause, suivant, précédent, stop.",
       "PC", {"action": p("string", "Action", enum=list(MEDIA))}, requis=["action"])
def pc_media(action: str) -> str:
    appuyer([MEDIA[action]])
    return {"lecture_pause": "Lecture ou pause.", "suivant": "Piste suivante.", "precedent": "Piste précédente.",
            "stop": "Lecture arrêtée."}[action]


# ------------------------------------------------------------------ statistiques
_NVML: list = []          # [module pynvml] si une carte NVIDIA répond, [None] sinon (essayé une seule fois)


def nvml():
    if not _NVML:
        try:
            import pynvml
            pynvml.nvmlInit()
            _NVML.append(pynvml)
        except Exception:
            _NVML.append(None)
    return _NVML[0]


def gpu() -> str:
    try:
        pynvml = nvml()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        u = pynvml.nvmlDeviceGetUtilizationRates(h)
        m = pynvml.nvmlDeviceGetMemoryInfo(h)
        t = pynvml.nvmlDeviceGetTemperature(h, 0)
        return f"GPU {u.gpu} %, mémoire vidéo {m.used / 2**30:.1f} sur {m.total / 2**30:.1f} Go, {t} °C"
    except Exception:
        return "GPU : non mesuré (pas de carte NVIDIA détectée)"


def mesures() -> dict:
    """Mesures légères pour l'écran (appelées chaque seconde)."""
    import psutil
    vm = psutil.virtual_memory()
    d = {"cpu": psutil.cpu_percent(interval=None), "ram": vm.percent, "ram_go": round(vm.used / 2**30, 1),
         "ram_total": round(vm.total / 2**30, 1)}
    b = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    if b:
        d["batterie"] = round(b.percent)
        d["secteur"] = bool(b.power_plugged)
    pynvml = nvml()
    if pynvml is not None:
        try:
            d["gpu"] = pynvml.nvmlDeviceGetUtilizationRates(pynvml.nvmlDeviceGetHandleByIndex(0)).gpu
        except Exception:
            pass
    return d


@outil("pc_stats", "État du PC en direct : processeur, mémoire, carte graphique, disque, batterie, programmes gourmands.",
       "PC")
def pc_stats() -> str:
    import psutil
    cpu = psutil.cpu_percent(interval=0.5)
    vm = psutil.virtual_memory()
    disque = psutil.disk_usage("C:\\" if WINDOWS else "/")
    lignes = [f"Processeur {cpu:.0f} % ({psutil.cpu_count()} cœurs)",
              f"Mémoire {vm.percent:.0f} % ({vm.used / 2**30:.1f} sur {vm.total / 2**30:.1f} Go)", gpu(),
              f"Disque {disque.percent:.0f} % utilisé ({disque.free / 2**30:.0f} Go libres)"]
    b = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    if b:
        lignes.append(f"Batterie {b.percent:.0f} %{' sur secteur' if b.power_plugged else ''}")
    procs = []
    for pr in psutil.process_iter(["name", "memory_info"]):
        try:
            procs.append((pr.info["memory_info"].rss, pr.info["name"]))
        except Exception:
            pass
    top = sorted(procs, reverse=True)[:5]
    lignes.append("Plus gourmands en mémoire : " + ", ".join(f"{n} ({r / 2**20:.0f} Mo)" for r, n in top))
    return "\n".join(lignes)


# ------------------------------------------------------------------ clavier, fenêtres, presse-papiers
@outil("pc_raccourci", "Appuie sur une touche ou un raccourci clavier, ex. « ctrl+c », « alt+tab », « win+d », « f5 ».",
       "PC", {"touches": p("string", "Touches séparées par +")}, requis=["touches"])
def pc_raccourci(touches: str) -> str:
    vks = []
    for t in touches.lower().replace(" ", "").split("+"):
        if t in TOUCHES:
            vks.append(TOUCHES[t])
        elif len(t) == 1 and (t.isalnum()):
            vks.append(ord(t.upper()))
        else:
            raise ErreurOutil(f"Touche inconnue : {t}")
    appuyer(vks)
    return f"Raccourci {touches} envoyé."


CONSOLES = {"cmd.exe", "powershell.exe", "pwsh.exe", "windowsterminal.exe", "openconsole.exe", "conhost.exe",
            "wsl.exe", "bash.exe", "mintty.exe", "regedit.exe"}


def fenetre_active() -> tuple[str, str]:
    """(titre, programme) de la fenêtre au premier plan."""
    if not WINDOWS:
        return "", ""
    import psutil
    u = ctypes.windll.user32
    hwnd = u.GetForegroundWindow()
    n = u.GetWindowTextLengthW(hwnd)
    buf = ctypes.create_unicode_buffer(n + 1)
    u.GetWindowTextW(hwnd, buf, n + 1)
    pid = ctypes.c_ulong()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        programme = psutil.Process(pid.value).name()
    except Exception:
        programme = ""
    return buf.value, programme


def _question_frappe(args: dict) -> str | None:
    """Taper dans un terminal ou la fenêtre Exécuter revient à lancer une commande : on demande d'abord."""
    try:
        titre, programme = fenetre_active()
    except Exception:
        return None
    if programme.lower() in CONSOLES or titre.strip().lower() in ("exécuter", "run"):
        return f"Taper dans {titre or programme} : {args.get('texte', '')[:200]}"
    return None


@outil("pc_taper_texte", "Tape du texte dans la fenêtre active, comme au clavier.", "PC",
       {"texte": p("string", "Texte à taper")}, requis=["texte"], confirmer=_question_frappe)
def pc_taper_texte(texte: str) -> str:
    taper_unicode(texte)
    return "Texte tapé."


def fenetres_visibles() -> list[tuple[int, str]]:
    windows_seulement()
    u = ctypes.windll.user32
    out: list[tuple[int, str]] = []
    PROTO = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def rappel(hwnd, _):
        if u.IsWindowVisible(hwnd):
            n = u.GetWindowTextLengthW(hwnd)
            if n:
                buf = ctypes.create_unicode_buffer(n + 1)
                u.GetWindowTextW(hwnd, buf, n + 1)
                if buf.value.strip() and buf.value not in ("Program Manager",):
                    out.append((hwnd, buf.value))
        return True

    u.EnumWindows(PROTO(rappel), 0)
    return out


@outil("pc_fenetres", "Liste les fenêtres ouvertes.", "PC")
def pc_fenetres() -> str:
    return "\n".join(t for _, t in fenetres_visibles()) or "Aucune fenêtre."


@outil("pc_activer_fenetre", "Met une fenêtre au premier plan (par un morceau de son titre).", "PC",
       {"titre": p("string", "Morceau du titre")}, requis=["titre"])
def pc_activer_fenetre(titre: str) -> str:
    u = ctypes.windll.user32 if WINDOWS else None
    for hwnd, t in fenetres_visibles():
        if titre.lower() in t.lower():
            if u.IsIconic(hwnd):
                u.ShowWindow(hwnd, 9)               # restaure seulement une fenêtre réduite
            appuyer([0x12])                     # un appui sur Alt autorise le changement de premier plan
            u.SetForegroundWindow(hwnd)
            return f"Fenêtre « {t} » au premier plan."
    raise ErreurOutil(f"Aucune fenêtre ne contient « {titre} ».")


UTF8 = "try { [Console]::OutputEncoding = [Text.Encoding]::UTF8; [Console]::InputEncoding = [Text.Encoding]::UTF8 } catch {}; "


def powershell(script: str, entree: str | None = None, delai: int = 60) -> subprocess.CompletedProcess:
    windows_seulement()
    return subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", UTF8 + script], input=entree,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=delai,
                          creationflags=SANS_FENETRE)


@outil("pc_presse_papiers", "Lit ou remplit le presse-papiers.", "PC",
       {"action": p("string", "Action", enum=["lire", "ecrire"]), "texte": p("string", "Texte à copier (pour ecrire)")},
       requis=["action"])
def pc_presse_papiers(action: str, texte: str = "") -> str:
    if action == "lire":
        r = powershell("Get-Clipboard -Raw")
        return r.stdout.strip() or "Le presse-papiers est vide."
    powershell("Set-Clipboard -Value ([Console]::In.ReadToEnd())", entree=texte)
    return "Copié dans le presse-papiers."


# ------------------------------------------------------------------ fichiers
@outil("pc_fichiers_chercher", "Cherche des fichiers par nom dans les dossiers de l'utilisateur (Bureau, Documents, "
       "Téléchargements, Images, Vidéos, Musique).", "PC",
       {"nom": p("string", "Morceau du nom"), "dossier": p("string", "Dossier où chercher (facultatif)")},
       requis=["nom"])
def pc_fichiers_chercher(nom: str, dossier: str = "") -> str:
    racines = [Path(dossier)] if dossier else [Path.home() / d for d in
                                               ("Desktop", "Documents", "Downloads", "Pictures", "Videos", "Music",
                                                "OneDrive")]
    n, trouves, debut = nom.lower(), [], time.time()
    for r in racines:
        if not r.is_dir():
            continue
        for racine, dirs, fichiers in os.walk(r):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "AppData", "__pycache__")]
            for f in fichiers + dirs:
                if n in f.lower():
                    trouves.append(os.path.join(racine, f))
            if len(trouves) >= 25 or time.time() - debut > 6:
                break
    return "\n".join(trouves[:25]) or f"Aucun fichier ne contient « {nom} »."


EXECUTABLES = {".exe", ".bat", ".cmd", ".com", ".ps1", ".vbs", ".vbe", ".js", ".jse", ".wsf", ".msi", ".msix",
               ".appx", ".scr", ".hta", ".jar", ".reg", ".lnk", ".pif", ".cpl", ".url"}


def _question_ouvrir(args: dict) -> str | None:
    cible = str(args.get("cible", ""))
    if cible.startswith(("http://", "https://")):
        return None
    if Path(cible).suffix.lower() in EXECUTABLES:
        return f"Lancer le programme {cible}"
    return None


@outil("pc_ouvrir", "Ouvre un fichier, un dossier ou une adresse web avec le programme par défaut.", "PC",
       {"cible": p("string", "Chemin ou adresse web")}, requis=["cible"], confirmer=_question_ouvrir)
def pc_ouvrir(cible: str) -> str:
    if cible.startswith(("http://", "https://")):
        webbrowser.open(cible)
        return "Page ouverte."
    windows_seulement()
    if not Path(cible).exists():
        raise ErreurOutil(f"Ce chemin n'existe pas : {cible}")
    os.startfile(cible)
    return "Ouvert."


# ------------------------------------------------------------------ session et alimentation
@outil("pc_verrouiller", "Verrouille la session Windows.", "PC")
def pc_verrouiller() -> str:
    windows_seulement()
    ctypes.windll.user32.LockWorkStation()
    return "Session verrouillée."


def _question_alimentation(args: dict) -> str | None:
    return None if args.get("action") == "annuler" else f"Mettre le PC en {args.get('action')}"


@outil("pc_alimentation", "Veille, redémarrage ou arrêt du PC (arrêt et redémarrage dans 30 s, annulables).", "PC",
       {"action": p("string", "Action", enum=["veille", "redemarrer", "eteindre", "annuler"])}, requis=["action"],
       confirmer=_question_alimentation)
def pc_alimentation(action: str) -> str:
    windows_seulement()
    if action == "veille":
        ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        return "Mise en veille."
    cmd = {"redemarrer": ["shutdown", "/r", "/t", "30"], "eteindre": ["shutdown", "/s", "/t", "30"],
           "annuler": ["shutdown", "/a"]}[action]
    subprocess.run(cmd, creationflags=SANS_FENETRE)
    return {"redemarrer": "Redémarrage dans 30 secondes.", "eteindre": "Arrêt dans 30 secondes.",
            "annuler": "Arrêt annulé."}[action]


def _question_commande(args: dict) -> str:
    return f"Exécuter la commande PowerShell : {args.get('commande', '')[:300]}"


@outil("pc_commande", "Exécute une commande PowerShell et renvoie sa sortie (pour ce qu'aucun autre outil ne fait).",
       "PC", {"commande": p("string", "Commande PowerShell")}, requis=["commande"], confirmer=_question_commande)
def pc_commande(commande: str) -> str:
    if not S.cfg.get("pc.commandes", True):
        raise ErreurOutil("Les commandes PowerShell sont désactivées ([pc] commandes = false).")
    try:
        r = powershell(commande, delai=90)
    except subprocess.TimeoutExpired:
        raise ErreurOutil("La commande a dépassé 90 secondes et a été arrêtée.")
    sortie = (r.stdout or "") + (("\nErreurs :\n" + r.stderr) if r.stderr.strip() else "")
    return f"Code de sortie {r.returncode}.\n{sortie.strip()[:6000]}"
