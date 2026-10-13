"""Moteur API : le vrai SDK Anthropic contre un faux serveur qui parle comme l'API (flux SSE). Vérifie la requête
(modèle, repli serveur, cache, outils en streaming), la boucle d'outils, l'image renvoyée dans le résultat d'outil,
l'historique jamais modifié, le texte en continu, et les erreurs."""
import json
import socket
import threading
import time

import pytest
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from jarvis import outils
from jarvis.moteurs import BETA_REPLI, ErreurCerveau, MoteurAPI
from jarvis.outils import Resultat
from jarvis.services import S


def sse(evts):
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in evts)


def debut(i):
    return {"type": "message_start", "message": {"id": f"msg_{i}", "type": "message", "role": "assistant",
            "model": "claude-opus-5-5", "content": [], "stop_reason": None, "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 1}}}


def appel_outil(i, nom, args_json):
    return [debut(i),
            {"type": "content_block_start", "index": 0, "content_block": {"type": "tool_use", "id": f"toolu_{i}", "name": nom, "input": {}}},
            {"type": "content_block_delta", "index": 0, "delta": {"type": "input_json_delta", "partial_json": args_json[:7]}},
            {"type": "content_block_delta", "index": 0, "delta": {"type": "input_json_delta", "partial_json": args_json[7:]}},
            {"type": "content_block_stop", "index": 0},
            {"type": "message_delta", "delta": {"stop_reason": "tool_use", "stop_sequence": None}, "usage": {"output_tokens": 20}},
            {"type": "message_stop"}]


def texte(i, morceaux):
    evts = [debut(i), {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}]
    evts += [{"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": m}} for m in morceaux]
    evts += [{"type": "content_block_stop", "index": 0},
             {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None}, "usage": {"output_tokens": 9}},
             {"type": "message_stop"}]
    return evts


class FauxAnthropic:
    def __init__(self, reponses):
        self.reponses, self.requetes = list(reponses), []
        app = FastAPI()

        @app.post("/v1/messages")
        async def messages(request: Request):
            corps = await request.json()
            self.requetes.append({"corps": corps, "entetes": dict(request.headers)})
            r = self.reponses.pop(0)
            if isinstance(r, int):
                return JSONResponse({"type": "error", "error": {"type": "authentication_error", "message": "clé"}}, status_code=r)
            if isinstance(r, str):
                return JSONResponse({"type": "error", "error": {"type": "invalid_request_error", "message": r}}, status_code=400)
            return StreamingResponse(iter([sse(r)]), media_type="text/event-stream")

        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        self.port = s.getsockname()[1]
        s.close()
        self.serveur = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=self.port, log_level="error"))
        threading.Thread(target=self.serveur.run, daemon=True).start()
        for _ in range(100):
            if self.serveur.started:
                break
            time.sleep(0.05)

    def fermer(self):
        self.serveur.should_exit = True


def moteur(port):
    import anthropic
    client = anthropic.Anthropic(api_key="cle-de-test", base_url=f"http://127.0.0.1:{port}", max_retries=0)
    m = MoteurAPI(S.cfg, client=client)
    m.nouvelle_conversation("Tu es Jarvis.", outils.definitions_api())
    return m


@pytest.fixture
def outil_test():
    vus = []

    @outils.outil("test_capture", "Outil de test qui renvoie une image.", "VISION",
                  {"ville": outils.p("string", "Ville")}, requis=["ville"])
    def test_capture(ville):
        vus.append(ville)
        return Resultat(f"capture pour {ville}", [(b"\xff\xd8\xff\xe0image", "image/jpeg")])
    yield vus
    outils.REGISTRE.pop("test_capture", None)


def test_boucle_complete_avec_le_vrai_sdk(outil_test):
    faux = FauxAnthropic([appel_outil(1, "test_capture", '{"ville": "Lyon"}'),
                          texte(2, ["Il fait ", "beau à Lyon. ", "Vingt degrés."])])
    try:
        m = moteur(faux.port)
        recu = []
        rep = m.repondre([{"type": "text", "text": "[Contexte] lundi"}, {"type": "text", "text": "Météo ?"}],
                         recu.append, lambda nom, args: outils.executer(nom, args, confirmer=lambda q: True))
    finally:
        faux.fermer()
    assert rep == "Il fait beau à Lyon. Vingt degrés." and "".join(recu).strip() == rep    # + fin de bloc "\n"
    assert outil_test == ["Lyon"]
    r1, r2 = faux.requetes[0], faux.requetes[1]
    c1 = r1["corps"]
    assert c1["model"] == "claude-opus-5-5" and c1["fallbacks"] == "default"
    assert BETA_REPLI in r1["entetes"].get("anthropic-beta", "")
    assert c1["output_config"] == {"effort": "low"} and c1["cache_control"] == {"type": "ephemeral"}
    assert c1["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert all(t.get("eager_input_streaming") is True for t in c1["tools"])
    assert [t["name"] for t in c1["tools"]] == sorted(t["name"] for t in c1["tools"])
    c2 = r2["corps"]
    assert c2["messages"][:1] == c1["messages"]                                   # historique seulement complété
    assert c2["messages"][1]["role"] == "assistant" and c2["messages"][1]["content"][0]["type"] == "tool_use"
    resultat = c2["messages"][2]["content"][0]
    assert resultat["type"] == "tool_result" and resultat["tool_use_id"] == "toolu_1" and "is_error" not in resultat
    assert resultat["content"][0]["type"] == "image" and resultat["content"][1]["text"] == "capture pour Lyon"
    assert c2["system"] == c1["system"] and c2["tools"] == c1["tools"]
    assert m.taille() == 4


def test_arguments_invalides_renvoyes_en_erreur(outil_test):
    faux = FauxAnthropic([appel_outil(1, "test_capture", '{"pays": "France"}'), texte(2, ["Il me faut une ville."])])
    try:
        m = moteur(faux.port)
        rep = m.repondre([{"type": "text", "text": "Météo ?"}], lambda t: None,
                         lambda nom, args: outils.executer(nom, args))
    finally:
        faux.fermer()
    res = faux.requetes[1]["corps"]["messages"][2]["content"][0]
    assert res["is_error"] is True and "INVALID_JSON" in res["content"][-1]["text"] and outil_test == []
    assert rep == "Il me faut une ville."


def test_cle_refusee():
    faux = FauxAnthropic([401])
    try:
        m = moteur(faux.port)
        with pytest.raises(ErreurCerveau, match="clé"):
            m.repondre([{"type": "text", "text": "salut"}], lambda t: None, lambda n, a: None)
    finally:
        faux.fermer()


def test_pas_de_repli_pour_haiku():
    faux = FauxAnthropic([texte(1, ["Bonjour."])])
    try:
        S.cfg.set("cerveau.modele", "claude-haiku-5-5", ecrire=False)
        m = moteur(faux.port)
        assert m.repondre([{"type": "text", "text": "salut"}], lambda t: None, lambda n, a: None) == "Bonjour."
    finally:
        faux.fermer()
    corps, entetes = faux.requetes[0]["corps"], faux.requetes[0]["entetes"]
    assert corps["model"] == "claude-haiku-5-5" and "fallbacks" not in corps
    assert BETA_REPLI not in entetes.get("anthropic-beta", "")


def test_repli_refuse_relance_sans_repli():
    faux = FauxAnthropic(["fallbacks: not supported for this model", texte(2, ["Voilà."])])
    try:
        m = moteur(faux.port)
        rep = m.repondre([{"type": "text", "text": "salut"}], lambda t: None, lambda n, a: None)
    finally:
        faux.fermer()
    assert rep == "Voilà." and len(faux.requetes) == 2
    assert faux.requetes[0]["corps"]["fallbacks"] == "default" and "fallbacks" not in faux.requetes[1]["corps"]
    assert faux.requetes[1]["corps"]["messages"] == faux.requetes[0]["corps"]["messages"]
