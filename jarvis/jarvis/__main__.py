"""Lancement de Jarvis.

  python -m jarvis              tout : voix, cerveau à l'écran, Telegram, présence
  python -m jarvis --texte      conversation au clavier dans le terminal (pour essayer)
  python -m jarvis --demo       le cerveau à l'écran avec une activité simulée (sans clé ni micro)
  python -m jarvis --verifier   état de chaque module et de la configuration
  python -m jarvis --mcp        serveur MCP (lancé par Claude Desktop ou Claude Code)
  python -m jarvis --claude-desktop   ajoute Jarvis aux outils de Claude Desktop"""
from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser


def utf8() -> None:
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8")
        except Exception:
            pass


def mode_texte() -> None:
    from .demarrage import demarrer_fond, initialiser
    from .services import S
    app = initialiser(avec_voix=False)
    demarrer_fond(app)
    for p in app.problemes:
        print(f"! {p}")
    print(f"Jarvis (moteur {app.nom_moteur}). Écris ta demande, « quitter » pour sortir.")

    def canal(question, deja, ident):
        return input(f"\n🔐 {question} (oui/non) > ").strip().lower().startswith("o")

    while True:
        try:
            texte = input("\nToi > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if texte.lower() in ("quitter", "exit", "quit"):
            break
        print("Jarvis > ", end="", flush=True)
        S.cerveau.traiter(texte, origine="clavier", canal=canal, sur_phrase=lambda ph: print(ph, end=" ", flush=True))
        print()


def mode_verifier() -> None:
    from . import outils
    from .config import Config, dossier
    from .moteurs import trouver_claude
    from .services import S
    cfg = Config.charger()
    S.cfg = cfg
    from .memoire import Memoire
    S.memoire = Memoire(dossier() / "memoire.db")
    outils.charger_tous()
    print(f"Dossier de Jarvis : {dossier()}")
    print(f"Configuration : {'trouvée' if (dossier() / 'config.toml').exists() else 'ABSENTE (copie config.exemple.toml)'}")
    print(f"Clé d'API Claude : {'présente' if cfg.cle_api() else 'absente'} ; Claude Code : {trouver_claude() or 'absent'}")
    print(f"Moteur choisi : {cfg.get('cerveau.moteur')} ; modèle {cfg.get('cerveau.modele')} (effort {cfg.get('cerveau.effort')})")
    for nom, mod in [("sounddevice", "micro et haut-parleur"), ("openwakeword", "mot de réveil"),
                     ("faster_whisper", "transcription"), ("piper", "voix Piper"), ("pyttsx3", "voix Windows"),
                     ("webrtcvad", "détection de parole")]:
        try:
            __import__(nom)
            etat = "ok"
        except Exception:
            etat = "absent"
        print(f"  {nom:15} {etat:7} ({mod})")
    print("Modules :")
    for m in outils.etats_modules():
        print(f"  {m['zone']:13} {m['etat']:14} {m['message']}")


def mode_claude_desktop(fichier=None) -> int:
    """Ajoute le serveur MCP de Jarvis à la configuration de Claude Desktop (copie de l'ancienne gardée à côté)."""
    import json
    import os
    import shutil
    from pathlib import Path
    from .config import dossier
    f = Path(fichier) if fichier else Path(os.environ.get("APPDATA", str(Path.home()))) / "Claude" / "claude_desktop_config.json"
    bloc = {"command": sys.executable, "args": ["-m", "jarvis", "--mcp"],
            "env": {"JARVIS_DOSSIER": str(dossier()), "PYTHONIOENCODING": "utf-8"}}
    donnees = {}
    if f.exists():
        try:
            donnees = json.loads(f.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            print(f"! {f} est illisible : rien n'est changé. Ajoute ce bloc dans « mcpServers » à la main :")
            print(json.dumps({"jarvis": bloc}, indent=2, ensure_ascii=False))
            return 1
        shutil.copyfile(f, f.with_name(f.name + ".avant_jarvis"))
    donnees.setdefault("mcpServers", {})["jarvis"] = bloc
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(donnees, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Jarvis est ajouté à Claude Desktop ({f}). Quitte complètement Claude Desktop et rouvre-le.")
    print("Si ses outils n'apparaissent pas : Claude Desktop > Paramètres > Développeur > Modifier la configuration,")
    print("et colle ce bloc dans « mcpServers » :")
    print(json.dumps({"jarvis": bloc}, indent=2, ensure_ascii=False))
    return 0


def mode_complet(demo: bool) -> None:
    import uvicorn
    from .config import Config
    from .services import S
    if demo:                                   # la page joue elle-même les scènes de démonstration
        from . import outils
        S.cfg = Config.charger()
        outils.charger_tous()
        app_jarvis = None
    else:
        from .demarrage import demarrer_fond, initialiser
        app_jarvis = initialiser()
        demarrer_fond(app_jarvis)
        for p in app_jarvis.problemes:
            print(f"! {p}")
    from .config import jeton_local
    from .serveur import creer_app
    api = creer_app(app_jarvis, demo=demo)
    port = int(S.cfg.get("interface.port", 8765))
    hote = "0.0.0.0" if S.cfg.get("interface.reseau", False) else "127.0.0.1"
    if S.cfg.get("interface.ouvrir_navigateur", True):
        threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open(f"http://127.0.0.1:{port}/")), daemon=True).start()
    _ = jeton_local()
    print(f"Jarvis est prêt : http://127.0.0.1:{port}/  (Ctrl+C pour arrêter)")
    uvicorn.run(api, host=hote, port=port, log_level="warning")


def main() -> None:
    utf8()
    a = argparse.ArgumentParser(prog="jarvis", description="Jarvis, assistant vocal local")
    g = a.add_mutually_exclusive_group()
    g.add_argument("--texte", action="store_true", help="conversation au clavier dans le terminal")
    g.add_argument("--demo", action="store_true", help="cerveau à l'écran avec activité simulée")
    g.add_argument("--verifier", action="store_true", help="état des modules et de la configuration")
    g.add_argument("--mcp", action="store_true", help="serveur MCP sur l'entrée et la sortie standard")
    g.add_argument("--claude-desktop", action="store_true", help="ajoute Jarvis aux outils de Claude Desktop")
    args = a.parse_args()
    if args.claude_desktop:
        sys.exit(mode_claude_desktop())
    if args.mcp:
        from .mcp_serveur import lancer
        lancer()
    elif args.texte:
        mode_texte()
    elif args.verifier:
        mode_verifier()
    else:
        mode_complet(args.demo)


if __name__ == "__main__":
    main()
