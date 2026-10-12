"""Les deux moteurs du cerveau, au choix dans config.toml ([cerveau] moteur) :

- « api » : l'API Claude avec une clé (console.anthropic.com). Le plus rapide et le plus fiable. Boucle d'outils
  écrite ici : texte en continu, outils exécutés par Jarvis, captures d'écran renvoyées en images, consigne et
  outils mis en cache, repli automatique du serveur si le modèle décline une demande.
- « claude_code » : Claude Code installé sur le PC (commande `claude`, connectée à l'abonnement Claude). Pas de
  clé ni de facture à l'usage en plus de l'abonnement ; un peu plus lent (un processus par demande). Claude Code
  appelle les outils de Jarvis par le serveur MCP de Jarvis (mcp_serveur.py), qui les fait exécuter ici.

L'historique d'une conversation n'est jamais modifié, seulement complété (les blocs de réflexion du modèle sont
liés à leur conversation) ; Jarvis repart d'une conversation neuve après un silence ou quand elle devient longue."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable

from .config import Config, dossier

SurTexte = Callable[[str], None]
Executer = Callable[[str, Any], tuple[Any, bool]]       # (nom, arguments) -> (Resultat, est_erreur)
BETA_REPLI = "server-side-fallback-2026-07-01"
SANS_REPLI = ("claude-haiku",)          # modèles sans repli côté serveur : l'envoyer ferait refuser la demande


class ErreurCerveau(Exception):
    """Problème du moteur expliqué à l'utilisateur (clé absente, pas d'internet, quota...)."""


class MoteurAPI:
    nom = "api"

    def __init__(self, cfg: Config, client: Any = None):
        self.cfg = cfg
        if client is None:
            import anthropic
            cle = cfg.cle_api()
            client = anthropic.Anthropic(api_key=cle or None, max_retries=3, timeout=120.0)
        self.client = client
        self.messages: list[dict] = []
        self.consigne = ""
        self.outils: list[dict] = []
        self.repli = not str(cfg.get("cerveau.modele", "")).startswith(SANS_REPLI)

    def nouvelle_conversation(self, consigne: str, outils: list[dict]) -> None:
        self.messages, self.consigne, self.outils = [], consigne, outils

    def taille(self) -> int:
        return len(self.messages)

    def _requete(self) -> dict:
        requete = dict(
            model=self.cfg.get("cerveau.modele"),
            max_tokens=int(self.cfg.get("cerveau.max_tokens", 16000)),
            system=[{"type": "text", "text": self.consigne, "cache_control": {"type": "ephemeral"}}],
            tools=self.outils,
            messages=self.messages,
            output_config={"effort": self.cfg.get("cerveau.effort", "low")},
            cache_control={"type": "ephemeral"},
        )
        if self.repli:
            requete.update(betas=[BETA_REPLI], fallbacks="default")
        return requete

    def repondre(self, contenu: list[dict], sur_texte: SurTexte, executer: Executer) -> str:
        import anthropic
        debut = len(self.messages)
        self.messages.append({"role": "user", "content": contenu})
        textes: list[str] = []
        essais_json = 0
        while True:
            try:
                with self.client.beta.messages.stream(**self._requete()) as flux:
                    for evt in flux:
                        if evt.type == "text":
                            sur_texte(evt.text)
                    reponse = flux.get_final_message()
                essais_json = 0
            except ValueError:
                # arguments d'outil illisibles (JSON coupé) : le tour est relancé, sans rien ajouter à l'historique
                essais_json += 1
                if essais_json > 2:
                    raise ErreurCerveau("Je n'ai pas réussi à formuler l'action, peux-tu reformuler ?")
                continue
            except anthropic.AuthenticationError:
                raise ErreurCerveau("Ma clé d'API est refusée. Vérifie la clé dans le fichier de configuration.")
            except anthropic.PermissionDeniedError:
                raise ErreurCerveau("Ma clé d'API n'a pas accès à ce modèle.")
            except anthropic.RateLimitError:
                raise ErreurCerveau("Trop de demandes d'un coup, réessaie dans un instant.")
            except anthropic.BadRequestError as e:
                if self.repli and "fallback" in str(getattr(e, "message", e)).lower():
                    self.repli = False          # modèle sans repli côté serveur : même demande, sans repli
                    continue
                raise ErreurCerveau(f"Demande refusée par l'API : {getattr(e, 'message', e)}")
            except anthropic.APIConnectionError:
                raise ErreurCerveau("Je n'arrive pas à joindre mon cerveau en ligne. La connexion internet est-elle coupée ?")
            except anthropic.APIStatusError as e:
                raise ErreurCerveau(f"Le service est indisponible pour l'instant (erreur {e.status_code}).")

            if reponse.stop_reason == "refusal" or not reponse.content:
                # demande déclinée (ou réponse vide) : ce tour est retiré de la fin de l'historique, le début reste
                # intact ; un message vide dans l'historique ferait refuser toutes les demandes suivantes
                del self.messages[debut:]
                textes += [b.text for b in reponse.content if getattr(b, "type", "") == "text" and b.text.strip()]
                return " ".join(textes) or ("Je ne peux pas faire ça." if reponse.stop_reason == "refusal" else "")
            self.messages.append({"role": "assistant", "content": reponse.content})
            textes += [b.text for b in reponse.content if getattr(b, "type", "") == "text" and b.text.strip()]
            if reponse.stop_reason == "pause_turn":
                continue
            appels = [b for b in reponse.content if getattr(b, "type", "") == "tool_use"]
            if not appels:
                return " ".join(textes)
            if reponse.stop_reason == "max_tokens":
                raise ErreurCerveau("Ma réponse a été coupée avant la fin de l'action ; rien n'a été lancé.")
            resultats = []
            for b in appels:
                res, err = executer(b.name, b.input)
                bloc = {"type": "tool_result", "tool_use_id": b.id, "content": res.blocs_api()}
                if err:
                    bloc["is_error"] = True
                resultats.append(bloc)
            self.messages.append({"role": "user", "content": resultats})


def trouver_claude() -> str | None:
    candidats: list[Path] = []
    if sys.platform == "win32":
        candidats.append(Path.home() / ".local" / "bin" / "claude.exe")          # installateur officiel
    for nom in ("claude.exe", "claude", "claude.cmd"):
        chemin = shutil.which(nom)
        if chemin:
            candidats.append(Path(chemin))
    if sys.platform == "win32":
        for base in (os.environ.get("APPDATA", ""), os.environ.get("LOCALAPPDATA", "")):
            if base:
                candidats += [Path(base) / "npm" / "claude.cmd", Path(base) / "Programs" / "claude" / "claude.exe"]
    candidats.append(Path.home() / ".local" / "bin" / "claude")
    for c in candidats:
        if c.is_file():
            return str(c)
    return None


def lancement(exe: str) -> tuple[list[str], bool]:
    """Début de la commande, et vrai si elle passe par cmd.exe. Installé par npm, `claude` est un script .cmd :
    cmd.exe couperait la consigne (plusieurs lignes, guillemets) ; on lance alors directement node avec le
    programme de Claude Code."""
    if not exe.lower().endswith((".cmd", ".bat")):
        return [exe], False
    dossier_npm = Path(exe).parent
    cli = dossier_npm / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
    node = dossier_npm / "node.exe"
    node = str(node) if node.is_file() else shutil.which("node")
    if cli.is_file() and node:
        return [node, str(cli)], False
    return [exe], True


def pour_cmd(texte: str) -> str:
    """Dernier recours si cmd.exe est inévitable : une seule ligne, sans caractère spécial de cmd."""
    return re.sub(r"\s+", " ", re.sub(r'[%^&|<>"!]', " ", texte)).strip()


class MoteurClaudeCode:
    """Claude Code en mode non interactif (`claude -p`, sortie stream-json), reprise de la session pour suivre
    la conversation. Seuls les outils du serveur MCP « jarvis » sont autorisés sans question ; les autres
    outils de Claude Code qui demandent une permission sont refusés d'office en mode -p."""
    nom = "claude_code"

    def __init__(self, cfg: Config, executable: str | None = None):
        self.cfg = cfg
        self.exe = executable or trouver_claude()
        if not self.exe:
            raise ErreurCerveau("Claude Code est introuvable : installe-le (npm install -g @anthropic-ai/claude-code) "
                                "puis connecte-toi une fois avec la commande claude.")
        self.session: str | None = None
        self.consigne = ""
        self.n = 0
        self.config_mcp = dossier() / "mcp_claude_code.json"
        self.config_mcp.write_text(json.dumps({"mcpServers": {"jarvis": {
            "command": sys.executable, "args": ["-m", "jarvis", "--mcp"],
            "env": {"JARVIS_DOSSIER": str(dossier()), "PYTHONIOENCODING": "utf-8",
                    "PYTHONPATH": str(Path(__file__).resolve().parent.parent)}}}}, indent=2), encoding="utf-8")
        self.options = True          # options récentes (texte en continu, MCP strict) ; retirées si refusées
        self.debut, self.par_cmd = lancement(self.exe)
        self.delai = float(cfg.get("cerveau.delai_claude_code", 600))

    def nouvelle_conversation(self, consigne: str, outils: list[dict]) -> None:
        self.session, self.consigne, self.n = None, consigne, 0

    def taille(self) -> int:
        return self.n

    def commande(self) -> list[str]:
        cmd = self.debut + ["-p", "--output-format", "stream-json", "--verbose",
                            "--mcp-config", str(self.config_mcp), "--allowedTools", "mcp__jarvis",
                            "--append-system-prompt", pour_cmd(self.consigne) if self.par_cmd else self.consigne]
        if self.options:
            cmd += ["--strict-mcp-config", "--include-partial-messages"]
        modele = self.cfg.get("cerveau.modele_claude_code", "")
        if modele:
            cmd += ["--model", modele]
        if self.session:
            cmd += ["--resume", self.session]
        return cmd

    def repondre(self, contenu: list[dict], sur_texte: SurTexte, executer: Executer) -> str:
        texte = "\n\n".join(b["text"] for b in contenu if b.get("type") == "text")
        for b in contenu:
            if b.get("type") == "image" and (b.get("source") or {}).get("type") == "base64":
                texte += f"\n\n(Image jointe par l'utilisateur, à regarder avec l'outil Read : {self._image(b)})"
        erreurs = ""
        for essai in range(3):
            code, sortie, erreurs, final = self._lancer(texte, sur_texte)
            if code == 0 or final is not None:
                self.n += 2
                return final or ""
            if self.options and "unknown option" in erreurs.lower():
                self.options = False                    # ancienne version de Claude Code : options de base seulement
                continue
            if self.session and ("session" in erreurs.lower() or "resume" in erreurs.lower()):
                self.session = None                     # session introuvable : nouvelle conversation
                continue
            break
        raise ErreurCerveau("Claude Code n'a pas répondu (" + (erreurs.strip().splitlines() or ["erreur inconnue"])[-1][:200]
                            + "). Lance « claude » une fois dans un terminal pour vérifier la connexion.")

    @staticmethod
    def _image(bloc: dict) -> str:
        import base64
        import uuid
        src = bloc["source"]
        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif"}.get(src.get("media_type"), ".png")
        d = dossier() / "images"
        d.mkdir(exist_ok=True)
        f = d / f"{uuid.uuid4().hex[:12]}{ext}"
        f.write_bytes(base64.standard_b64decode(src["data"]))
        return str(f)

    def _lancer(self, texte: str, sur_texte: SurTexte) -> tuple[int, str, str, str | None]:
        proc = subprocess.Popen(self.commande(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", errors="replace", cwd=str(dossier()),
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        assert proc.stdin and proc.stdout and proc.stderr
        morceaux_err: list[str] = []
        lecteur = threading.Thread(target=lambda: morceaux_err.append(proc.stderr.read()), daemon=True)
        lecteur.start()                                  # stderr lu à part : un tuyau plein bloquerait Claude Code
        expire = threading.Event()

        def couper() -> None:                            # jamais bloqué indéfiniment
            expire.set()
            proc.kill()
        minuterie = threading.Timer(self.delai, couper)
        minuterie.start()
        try:
            proc.stdin.write(texte)
            proc.stdin.close()
        except OSError:                                  # programme déjà arrêté (option refusée...) : vu plus bas
            pass
        final: str | None = None
        vu_continu = False
        lignes = []
        for ligne in proc.stdout:
            lignes.append(ligne)
            try:
                obj = json.loads(ligne)
            except json.JSONDecodeError:
                continue
            t = obj.get("type")
            if t == "system" and obj.get("session_id"):
                self.session = obj["session_id"]
            elif t == "stream_event":
                ev = obj.get("event") or {}
                d = ev.get("delta") or {}
                if ev.get("type") == "content_block_delta" and d.get("type") == "text_delta":
                    vu_continu = True
                    sur_texte(d.get("text", ""))
            elif t == "assistant" and not vu_continu:
                for b in (obj.get("message") or {}).get("content", []):
                    if b.get("type") == "text":
                        sur_texte(b.get("text", ""))
            elif t == "result":
                if obj.get("session_id"):
                    self.session = obj["session_id"]
                if not obj.get("is_error"):
                    final = obj.get("result", "") or ""
        code = proc.wait()
        minuterie.cancel()
        lecteur.join(5)
        erreurs = "".join(morceaux_err)
        if expire.is_set():
            erreurs += f"\ndélai de {self.delai:.0f} s dépassé"
        return code, "".join(lignes), erreurs, final


def creer_moteur(cfg: Config) -> Any:
    choix = cfg.get("cerveau.moteur", "auto")
    if choix == "api" or (choix == "auto" and cfg.cle_api()):
        return MoteurAPI(cfg)
    if choix in ("claude_code", "auto") and trouver_claude():
        return MoteurClaudeCode(cfg)
    if choix == "auto":
        raise ErreurCerveau("Aucun cerveau disponible : mets ta clé d'API Claude dans config.toml ([cerveau] cle_api), "
                            "ou installe Claude Code et connecte-toi à ton abonnement.")
    raise ErreurCerveau(f"Moteur inconnu dans la configuration : {choix}")
