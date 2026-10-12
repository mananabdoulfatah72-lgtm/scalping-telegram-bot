"""Serveur local (jeton obligatoire, websocket, outils pour le MCP, webhooks Twilio signés), serveur MCP (liste et
appel d'outils par le vrai SDK MCP), moteur Claude Code (avec un faux programme `claude`)."""
import json
import stat
import sys
import textwrap

import pytest
from fastapi.testclient import TestClient

from jarvis.config import jeton_local
from jarvis.services import S


class AppFactice:
    def __init__(self):
        from jarvis.cerveau import Cerveau

        class M:
            nom = "factice"

            def nouvelle_conversation(self, c, o):
                pass

            def taille(self):
                return 0

            def repondre(self, contenu, sur_texte, executer):
                sur_texte("Bonjour.")
                return "Bonjour."
        self.cerveau = Cerveau(S.cfg, M(), S.memoire, S.confirmations)
        self.synthese = None
        self.boucle = None
        self.problemes = []
        self.nom_moteur = "factice"


@pytest.fixture
def client():
    from jarvis.serveur import creer_app
    app = AppFactice()
    return TestClient(creer_app(app), base_url="http://127.0.0.1:8765", client=("127.0.0.1", 50000)), app


def test_page_et_jeton(client):
    c, _ = client
    r = c.get("/")
    assert r.status_code == 200 and jeton_local() in r.text and "__JETON__" not in r.text
    assert c.post("/api/message", json={"texte": "salut"}).status_code == 403
    assert c.post("/api/message", json={"texte": "salut"}, headers={"x-jarvis-jeton": "faux"}).status_code == 403
    assert c.get("/api/outils").status_code == 403
    assert c.get("/ui/app.js").status_code == 200 and c.get("/ui/vendor/three.min.js").status_code == 200


def test_websocket_refuse_sans_jeton(client):
    c, _ = client
    with pytest.raises(Exception):
        with c.websocket_connect("/ws") as ws:
            ws.receive_text()


def test_websocket_et_message(client):
    c, app = client
    with c.websocket_connect(f"/ws?jeton={jeton_local()}") as ws:
        premier = json.loads(ws.receive_text())
        while premier["type"] != "modules":
            premier = json.loads(ws.receive_text())
        assert premier["moteur"] == "factice" and any(m["zone"] == "DOMOTIQUE" for m in premier["liste"])
        r = c.post("/api/message", json={"texte": "salut"}, headers={"x-jarvis-jeton": jeton_local()})
        assert r.json()["ok"]
        types = set()
        for _ in range(40):
            e = json.loads(ws.receive_text())
            types.add(e["type"])
            if e["type"] == "reponse_fin":
                assert e["texte"] == "Bonjour."
                break
        assert {"transcription", "reponse", "reponse_fin"} <= types


def test_outil_par_api_locale(client):
    c, _ = client
    h = {"x-jarvis-jeton": jeton_local()}
    noms = [d["name"] for d in c.get("/api/outils", headers=h).json()]
    assert "hue_regler" in noms and "voir_ecran" in noms
    r = c.post("/api/outil", json={"nom": "memoire_retenir", "arguments": {"texte": "Il joue au foot le jeudi"}}, headers=h).json()
    assert r["erreur"] is False and "Retenu" in r["contenu"][-1]["text"]
    r = c.post("/api/outil", json={"nom": "pc_commande", "arguments": {"commande": "dir"}}, headers=h).json()
    assert "annulée" in r["contenu"][-1]["text"]                     # personne n'a confirmé à l'écran


def test_page_refusee_depuis_le_reseau():
    from jarvis.serveur import creer_app
    c = TestClient(creer_app(AppFactice()), base_url="http://192.168.1.20:8765", client=("192.168.1.50", 50000))
    assert c.get("/").status_code == 403


def test_page_refusee_par_tunnel_ou_autre_nom(client):
    c, _ = client
    assert c.get("/").status_code == 200
    assert c.get("/", headers={"host": "localhost:8765"}).status_code == 200
    assert c.get("/", headers={"host": "[::1]:8765"}).status_code == 200
    # tunnel ngrok / cloudflared ouvert pour Twilio : il vient de ce PC mais relaie Internet
    assert c.get("/", headers={"host": "abcd.ngrok-free.app", "x-forwarded-for": "203.0.113.9"}).status_code == 403
    assert c.get("/", headers={"cf-connecting-ip": "203.0.113.9"}).status_code == 403
    # site qui redirige son nom vers 127.0.0.1 pour lire la page (rebinding DNS)
    assert c.get("/", headers={"host": "site-piege.com:8765"}).status_code == 403


def test_mode_reseau_avec_cle():
    from jarvis.serveur import creer_app
    S.cfg.set("interface.reseau", True, ecrire=False)
    S.cfg.set("interface.cle", "cle-du-salon", ecrire=False)
    c = TestClient(creer_app(AppFactice()), base_url="http://192.168.1.20:8765", client=("192.168.1.50", 50000))
    assert c.get("/").status_code == 403 and c.get("/?cle=faux").status_code == 403
    r = c.get("/?cle=cle-du-salon")
    assert r.status_code == 200 and jeton_local() in r.text


def test_twilio_signature_obligatoire(client):
    c, _ = client
    assert c.post("/twilio/voix/abc", data={"SpeechResult": "bonjour"}).status_code == 403


def test_twilio_signature_valide(client, monkeypatch):
    pytest.importorskip("twilio")
    from twilio.request_validator import RequestValidator
    S.cfg.set("twilio.jeton", "secret", ecrire=False)
    S.cfg.set("twilio.url_publique", "https://jarvis.exemple.fr", ecrire=False)
    params = {"SpeechResult": "bonjour", "CallSid": "CA1"}
    sig = RequestValidator("secret").compute_signature("https://jarvis.exemple.fr/twilio/voix/inconnue", params)
    c, _ = client
    r = c.post("/twilio/voix/inconnue", data=params, headers={"x-twilio-signature": sig})
    assert r.status_code == 200 and "<Hangup/>" in r.text


def test_mcp_liste_et_appel():
    import anyio
    from mcp.client import Client
    from jarvis.mcp_serveur import creer_serveur

    async def scenario():
        async with Client(creer_serveur()) as cl:
            liste = await cl.list_tools()
            noms = [t.name for t in liste.tools]
            assert "hue_regler" in noms and "memoire_retenir" in noms
            r = await cl.call_tool("memoire_retenir", {"texte": "Projet : finir Jarvis", "categorie": "projet"})
            assert not r.is_error and "Retenu" in r.content[-1].text
            r = await cl.call_tool("pc_commande", {"commande": "dir"})
            assert "annulée" in r.content[-1].text                     # sans écran : action sensible refusée
    anyio.run(scenario)


FAUX_CLAUDE = textwrap.dedent('''\
    #!{python}
    import json, sys
    args = sys.argv[1:]
    open({journal!r}, "a").write(json.dumps(args) + "\\n")
    prompt = sys.stdin.read()
    if "--include-partial-messages" in args and {refuse!r}:
        print("error: unknown option '--include-partial-messages'", file=sys.stderr); sys.exit(1)
    sortie = [{{"type": "system", "subtype": "init", "session_id": "sess-42"}}]
    if "--include-partial-messages" in args:
        sortie += [{{"type": "stream_event", "event": {{"type": "content_block_delta", "delta": {{"type": "text_delta", "text": "Salut "}}}}}},
                   {{"type": "stream_event", "event": {{"type": "content_block_delta", "delta": {{"type": "text_delta", "text": "Manan."}}}}}}]
    sortie += [{{"type": "assistant", "message": {{"content": [{{"type": "text", "text": "Salut Manan."}}]}}}},
               {{"type": "result", "subtype": "success", "is_error": False, "result": "Salut Manan.", "session_id": "sess-42"}}]
    for o in sortie:
        print(json.dumps(o))
    ''')


@pytest.mark.parametrize("refuse", [False, True])
def test_moteur_claude_code(tmp_path, refuse):
    if sys.platform == "win32":
        pytest.skip("faux programme en script shell")
    journal = tmp_path / "appels.txt"
    exe = tmp_path / "claude"
    exe.write_text(FAUX_CLAUDE.format(python=sys.executable, journal=str(journal), refuse=refuse), encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    from jarvis.moteurs import MoteurClaudeCode
    m = MoteurClaudeCode(S.cfg, executable=str(exe))
    m.nouvelle_conversation("Tu es Jarvis.", [])
    recu = []
    assert m.repondre([{"type": "text", "text": "Bonjour"}], recu.append, None) == "Salut Manan."
    assert "".join(recu) == "Salut Manan."
    assert m.repondre([{"type": "text", "text": "Encore"}], recu.append, None) == "Salut Manan."
    appels = [json.loads(l) for l in journal.read_text().splitlines()]
    dernier = appels[-1]
    assert "--resume" in dernier and dernier[dernier.index("--resume") + 1] == "sess-42"
    assert "mcp__jarvis" in dernier and "--append-system-prompt" in dernier
    config = json.loads((tmp_path / "mcp_claude_code.json").read_text())
    assert config["mcpServers"]["jarvis"]["args"] == ["-m", "jarvis", "--mcp"]
    if refuse:
        assert "--include-partial-messages" not in dernier and m.options is False


def test_claude_cmd_lance_par_node(tmp_path, monkeypatch):
    from jarvis import moteurs
    npm = tmp_path / "npm"
    cli = npm / "node_modules" / "@anthropic-ai" / "claude-code" / "cli.js"
    cli.parent.mkdir(parents=True)
    cli.write_text("// cli", encoding="utf-8")
    (npm / "claude.cmd").write_text("@node cli.js %*", encoding="utf-8")
    monkeypatch.setattr(moteurs.shutil, "which", lambda nom: "/usr/bin/node" if nom == "node" else None)
    assert moteurs.lancement(str(npm / "claude.cmd")) == (["/usr/bin/node", str(cli)], False)
    assert moteurs.lancement("/opt/claude") == (["/opt/claude"], False)
    cli.unlink()                                                   # programme introuvable : cmd.exe en dernier recours
    assert moteurs.lancement(str(npm / "claude.cmd")) == ([str(npm / "claude.cmd")], True)
    assert moteurs.pour_cmd('Ligne 1\nLigne "2" & 100%') == "Ligne 1 Ligne 2 100"


def test_claude_code_bloque_est_coupe(tmp_path):
    if sys.platform == "win32":
        pytest.skip("faux programme en script shell")
    exe = tmp_path / "claude"
    exe.write_text(f"#!{sys.executable}\nimport time\ntime.sleep(30)\n", encoding="utf-8")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    from jarvis.moteurs import ErreurCerveau, MoteurClaudeCode
    S.cfg.set("cerveau.delai_claude_code", 1, ecrire=False)
    m = MoteurClaudeCode(S.cfg, executable=str(exe))
    m.nouvelle_conversation("Tu es Jarvis.", [])
    with pytest.raises(ErreurCerveau, match="délai"):
        m.repondre([{"type": "text", "text": "Bonjour"}], lambda t: None, None)


def test_branchement_claude_desktop(tmp_path, capsys):
    from jarvis.__main__ import mode_claude_desktop
    f = tmp_path / "Claude" / "claude_desktop_config.json"
    f.parent.mkdir()
    f.write_text(json.dumps({"mcpServers": {"autre": {"command": "x"}}, "theme": "dark"}), encoding="utf-8")
    assert mode_claude_desktop(f) == 0
    d = json.loads(f.read_text(encoding="utf-8"))
    assert d["theme"] == "dark" and d["mcpServers"]["autre"] == {"command": "x"}
    assert d["mcpServers"]["jarvis"]["args"] == ["-m", "jarvis", "--mcp"]
    assert d["mcpServers"]["jarvis"]["command"] == sys.executable
    assert (tmp_path / "Claude" / "claude_desktop_config.json.avant_jarvis").exists()
    f.write_text("{ cassé", encoding="utf-8")
    assert mode_claude_desktop(f) == 1 and f.read_text(encoding="utf-8") == "{ cassé"
