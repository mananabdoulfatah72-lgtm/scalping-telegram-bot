"""Les deux moteurs du cerveau, au choix dans config.toml ([cerveau] moteur) :

- « api » : l'API Claude avec une clé (console.anthropic.com). Le plus rapide et le plus fiable. Boucle d'outils
  écrite ici : texte en continu, outils exécutés par Jarvis, captures d'écran renvoyées en images, consigne et
  outils mis en cache, repli automatique du serveur si le modèle décline une demande.
- « claude_code » : Claude Code installé sur le PC (commande `claude`, connectée à l'abonnement Claude). Pas de
  clé ni de facture à l'usage en plus de l'abonnement. Il reste ouvert, prêt dès le démarrage de Jarvis, et
  appelle les outils de Jarvis par le serveur MCP de Jarvis (mcp_serveur.py), qui les fait exécuter ici.

L'historique d'une conversation n'est jamais modifié, seulement complété (les blocs de réflexion du modèle sont
liés à leur conversation) ; Jarvis repart d'une conversation neuve après un silence ou quand elle devient longue."""
from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable

from .bus import bus
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
                    texte_ouvert = False
                    for evt in flux:
                        if evt.type == "text":
                            texte_ouvert = True
                            sur_texte(evt.text)
                        elif evt.type == "content_block_stop" and texte_ouvert:
                            texte_ouvert = False
                            sur_texte("\n")             # fin du texte (avant un outil) : la phrase part tout de suite
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


class ProcessusClaude:
    """Un Claude Code lancé une fois et gardé ouvert (entrée et sortie stream-json) : chaque demande lui arrive en
    une ligne JSON, sans relancer le programme ni le serveur MCP de Jarvis."""

    def __init__(self, commande: list[str], consigne: str):
        self.consigne, self.utilise = consigne, False
        self.en_retard = 0               # fins de tour pas encore arrivées pour des réponses déjà rendues
        self.proc = subprocess.Popen(commande, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     text=True, encoding="utf-8", errors="replace", cwd=str(dossier()),
                                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        self.file: queue.Queue = queue.Queue()
        self.erreurs: list[str] = []
        threading.Thread(target=self._lire, daemon=True, name="claude-sortie").start()
        self._fil_erreurs = threading.Thread(target=self._lire_erreurs, daemon=True, name="claude-erreurs")
        self._fil_erreurs.start()

    def _lire(self) -> None:
        assert self.proc.stdout
        for ligne in self.proc.stdout:
            try:
                self.file.put(json.loads(ligne))
            except json.JSONDecodeError:
                continue
        self.file.put(None)                              # programme arrêté

    def _lire_erreurs(self) -> None:
        assert self.proc.stderr
        for ligne in self.proc.stderr:                   # lu à part : un tuyau plein bloquerait Claude Code
            self.erreurs = (self.erreurs + [ligne])[-40:]

    def vivant(self) -> bool:
        return self.proc.poll() is None

    def envoyer(self, contenu: list[dict]) -> None:
        self.utilise = True
        assert self.proc.stdin
        message = {"type": "user", "message": {"role": "user", "content": contenu},
                   "parent_tool_use_id": None, "session_id": "default"}
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def texte_erreurs(self) -> str:
        return "".join(self.erreurs)

    def attendre_fin(self) -> None:
        """Après l'arrêt du programme : laisse finir la lecture de ses messages d'erreur."""
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        self._fil_erreurs.join(2)

    def fermer(self) -> None:
        try:
            if self.proc.stdin:
                self.proc.stdin.close()                  # fin de l'entrée : Claude Code s'arrête proprement
        except OSError:
            pass
        try:
            self.proc.kill()
        except OSError:
            pass


class MoteurClaudeCode:
    """Claude Code en mode non interactif, **gardé ouvert** : il démarre avec Jarvis (prêt avant le premier « Hey
    Jarvis ») et reçoit chaque demande en continu, sans les 2 à 4 secondes d'un nouveau lancement. Un second
    Claude Code attend en réserve, pour qu'une nouvelle conversation démarre aussi sans attente.

    Allégé pour la voix : la consigne de Jarvis remplace celle de Claude Code (pas les règles de programmeur), pas
    d'outils de programmeur (seulement ceux de Jarvis, par le serveur MCP), réflexion rapide (--effort low). Les
    images partent directement dans le message. Si la version de Claude Code refuse une option récente, Jarvis
    repasse aux options de base."""
    nom = "claude_code"

    def __init__(self, cfg: Config, executable: str | None = None):
        self.cfg = cfg
        self.exe = executable or trouver_claude()
        if not self.exe:
            raise ErreurCerveau("Claude Code est introuvable : installe-le (npm install -g @anthropic-ai/claude-code) "
                                "puis connecte-toi une fois avec la commande claude.")
        self.consigne = ""
        self.n = 0
        self.config_mcp = dossier() / "mcp_claude_code.json"
        self.config_mcp.write_text(json.dumps({"mcpServers": {"jarvis": {
            "command": sys.executable, "args": ["-m", "jarvis", "--mcp"],
            "env": {"JARVIS_DOSSIER": str(dossier()), "PYTHONIOENCODING": "utf-8",
                    "PYTHONPATH": str(Path(__file__).resolve().parent.parent)}}}}, indent=2), encoding="utf-8")
        self.options = True          # options récentes (consigne seule, sans outils de programmeur, effort...) ; retirées si refusées
        self.debut, self.par_cmd = lancement(self.exe)
        self.delai = float(cfg.get("cerveau.delai_claude_code", 600))
        self.avec_reserve = bool(cfg.get("cerveau.reserve_claude_code", True))
        self.actuel: ProcessusClaude | None = None
        self.reserve: ProcessusClaude | None = None
        self._verrou = threading.Lock()

    # ------------------------------------------------------------------ processus
    def commande(self, consigne: str) -> list[str]:
        cmd = self.debut + ["-p", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
                            "--mcp-config", str(self.config_mcp), "--allowedTools", "mcp__jarvis"]
        if self.options:
            fichier = dossier() / f"consigne_{hashlib.sha1(consigne.encode('utf-8')).hexdigest()[:10]}.txt"
            if not fichier.exists():
                fichier.write_text(consigne, encoding="utf-8")
            cmd += ["--system-prompt-file", str(fichier), "--tools", "", "--strict-mcp-config",
                    "--include-partial-messages", "--effort", str(self.cfg.get("cerveau.effort_claude_code", "low"))]
        else:
            cmd += ["--append-system-prompt", pour_cmd(consigne) if self.par_cmd else consigne]
        modele = self.cfg.get("cerveau.modele_claude_code", "")
        if modele:
            cmd += ["--model", modele]
        return cmd

    def _demarrer(self, consigne: str) -> ProcessusClaude:
        return ProcessusClaude(self.commande(consigne), consigne)

    def _preparer_reserve(self) -> None:
        if not self.avec_reserve:
            return
        r = self.reserve
        if r is not None and r.vivant() and r.consigne == self.consigne:
            return
        if r is not None:
            r.fermer()
        try:
            self.reserve = self._demarrer(self.consigne)
        except OSError:
            self.reserve = None

    def _processus(self) -> ProcessusClaude:
        """Le Claude Code de la conversation en cours, prêt à recevoir (la réserve s'il le faut)."""
        p = self.actuel
        if p is not None and p.vivant() and p.consigne == self.consigne:
            return p
        if p is not None:
            p.fermer()
        r = self.reserve
        if r is not None and r.vivant() and r.consigne == self.consigne and not r.utilise:
            self.actuel, self.reserve = r, None
        else:
            self.actuel = self._demarrer(self.consigne)
        self._preparer_reserve()
        return self.actuel

    def nouvelle_conversation(self, consigne: str, outils: list[dict]) -> None:
        with self._verrou:
            self.consigne, self.n = consigne, 0
            p = self.actuel
            if p is not None and (p.utilise or p.consigne != consigne):
                p.fermer()
                self.actuel = None
            try:
                self._processus()                        # lancé tout de suite : prêt pour la première demande
            except OSError:
                self.actuel = None

    def taille(self) -> int:
        return self.n

    def arreter(self) -> None:
        for p in (self.actuel, self.reserve):
            if p is not None:
                p.fermer()
        self.actuel = self.reserve = None

    # ------------------------------------------------------------------ une demande
    def repondre(self, contenu: list[dict], sur_texte: SurTexte, executer: Executer) -> str:
        blocs = [b for b in contenu if b.get("type") in ("text", "image")]
        for essai in range(2):
            with self._verrou:
                try:
                    p = self._processus()
                except OSError as e:
                    raise ErreurCerveau(f"Impossible de lancer Claude Code ({e}).")
            fini, texte = self._echanger(p, blocs, sur_texte)
            if fini:
                self.n += 2
                return texte
            erreurs = p.texte_erreurs()
            with self._verrou:
                if self.actuel is p:
                    self.actuel = None
                if self.options and "unknown option" in erreurs.lower():
                    self.options = False                 # ancienne version de Claude Code : options de base
                    if self.reserve is not None:
                        self.reserve.fermer()
                        self.reserve = None
                    continue
            raise ErreurCerveau("Claude Code n'a pas répondu (" + (texte or (erreurs.strip().splitlines() or ["erreur inconnue"])[-1])[:200]
                                + "). Lance « claude » une fois dans un terminal pour vérifier la connexion.")
        raise ErreurCerveau("Claude Code refuse ses options de lancement : mets-le à jour (claude update).")

    def _echanger(self, p: ProcessusClaude, blocs: list[dict], sur_texte: SurTexte) -> tuple[bool, str]:
        """Envoie la demande et suit la réponse jusqu'au résultat. (True, texte) si fini ; (False, raison) si le
        programme s'est arrêté ou a dépassé le délai (il est alors fermé)."""
        try:
            p.envoyer(blocs)
        except OSError:
            pass                                         # déjà arrêté : la fin de sortie le dira
        limite = time.time() + self.delai
        vu_continu = texte_ouvert = False
        morceaux: list[str] = []
        while True:
            reste = limite - time.time()
            if reste <= 0:
                p.fermer()
                return False, f"délai de {self.delai:.0f} s dépassé"
            try:
                obj = p.file.get(timeout=min(reste, 1.0))
            except queue.Empty:
                continue
            if obj is None:
                p.attendre_fin()
                return False, ""
            t = obj.get("type")
            if p.en_retard > 0:
                # tant que la fin d'un tour déjà rendu n'est pas arrivée, tout ce qui arrive lui appartient
                if t == "result":
                    p.en_retard -= 1
                continue
            if t == "system" and obj.get("subtype") == "init":
                for serveur in obj.get("mcp_servers") or []:
                    if serveur.get("name") == "jarvis" and serveur.get("status") == "failed":
                        bus.publier("erreur", message="Claude Code n'a pas pu lancer les outils de Jarvis (serveur MCP).")
            elif t == "stream_event" and not obj.get("parent_tool_use_id"):
                ev = obj.get("event") or {}
                d = ev.get("delta") or {}
                if ev.get("type") == "content_block_delta" and d.get("type") == "text_delta":
                    vu_continu = texte_ouvert = True
                    morceaux.append(d.get("text", ""))
                    sur_texte(d.get("text", ""))
                elif ev.get("type") == "content_block_stop" and texte_ouvert:
                    texte_ouvert = False
                    sur_texte("\n")                     # fin du texte (avant un outil) : la phrase part tout de suite
                elif ev.get("type") == "message_delta" and d.get("stop_reason") in ("end_turn", "stop_sequence"):
                    # réponse finie : Jarvis reprend la main sans attendre le résumé que Claude Code fait ensuite
                    # (environ 3 s) ; la fin de tour arrivera plus tard et sera ignorée
                    p.en_retard += 1
                    return True, "".join(morceaux).strip()
            elif t == "assistant" and not vu_continu and not obj.get("parent_tool_use_id"):
                for b in (obj.get("message") or {}).get("content", []):
                    if b.get("type") == "text":
                        morceaux.append(b.get("text", ""))
                        sur_texte(b.get("text", ""))
            elif t == "result":
                if obj.get("is_error"):
                    raise ErreurCerveau("Claude Code : " + str(obj.get("result") or obj.get("subtype") or "erreur")[:200])
                return True, obj.get("result", "") or "".join(morceaux).strip()


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
