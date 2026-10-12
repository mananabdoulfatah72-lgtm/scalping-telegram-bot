"""Compétences avec les services extérieurs imités : météo, Hue, Discord, Instagram, ntfy, Telegram, présence,
appels (TwiML), mails (lecture du corps), agenda (dates), PC (hors Windows), voix (fin de phrase, nettoyage)."""
import base64
import time
import xml.dom.minidom

import numpy as np
import pytest

from jarvis.outils import ErreurOutil, executer
from jarvis.services import S

from conftest import FauxRequests, Reponse


def brancher(monkeypatch, routes):
    faux = FauxRequests(routes)
    monkeypatch.setattr("jarvis.reseau.requests.request", faux)
    return faux


def test_meteo(monkeypatch):
    brancher(monkeypatch, {
        "geocoding-api": {"results": [{"latitude": 45.76, "longitude": 4.84, "name": "Lyon", "country": "France"}]},
        "api.open-meteo.com": {"current": {"temperature_2m": 18.4, "apparent_temperature": 17.0, "relative_humidity_2m": 60,
                                           "weather_code": 61, "wind_speed_10m": 12.0, "precipitation": 0.2},
                               "daily": {"time": ["2026-10-13"], "weather_code": [3], "temperature_2m_max": [20.1],
                                         "temperature_2m_min": [11.0], "precipitation_probability_max": [40],
                                         "precipitation_sum": [1.2]}}})
    res, err = executer("meteo", {"ville": "Lyon"})
    assert not err and "Lyon, France maintenant : pluie faible, 18 °C" in res.texte and "pluie 40 %" in res.texte


def test_hue(monkeypatch):
    S.cfg.set("hue.bridge", "192.168.1.2", ecrire=False)
    S.cfg.set("hue.utilisateur", "u1", ecrire=False)
    faux = brancher(monkeypatch, {
        "/groups/": [{"success": {}}],
        "/groups": {"1": {"name": "Salon", "type": "Room", "state": {"any_on": False}}},
        "/lights": {"3": {"name": "Lampe bureau", "state": {"on": True, "bri": 127, "reachable": True}}},
        "/scenes": {"s1": {"name": "Détente", "group": "1"}},
    })
    res, err = executer("hue_regler", {"cible": "salon", "luminosite": 40, "couleur": "violet"})
    assert not err and "Salon allumé (40 %, violet)" in res.texte
    methode, url, kw = faux.appels[-1]
    assert methode == "PUT" and url.endswith("/groups/1/action") and kw["json"]["bri"] == 102 and len(kw["json"]["xy"]) == 2
    res, err = executer("hue_scene", {"scene": "détente"})
    assert not err and faux.appels[-1][2]["json"] == {"scene": "s1"}
    res, err = executer("hue_regler", {"cible": "cuisine"})
    assert err and "Salon" in res.texte


def test_hue_non_configure():
    res, err = executer("hue_lumieres", {})
    assert err and "bouton" in res.texte


def test_discord(monkeypatch):
    S.cfg.set("discord.jeton", "jt", ecrire=False)
    S.cfg.set("discord.utilisateur_id", "42", ecrire=False)
    maintenant = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    brancher(monkeypatch, {
        "/users/@me/guilds": [{"id": "g1", "name": "Team"}],
        "/guilds/g1/channels": [{"id": "c1", "name": "general", "type": 0}, {"id": "v1", "name": "vocal", "type": 2}],
        "/channels/c1/messages": [{"id": "2", "timestamp": maintenant, "author": {"username": "yanis"}, "content": "<@42> ce soir ?",
                                   "mentions": [{"id": "42"}]},
                                  {"id": "1", "timestamp": maintenant, "author": {"username": "sarah"}, "content": "planning dispo",
                                   "mentions": []},
                                  {"id": "0", "timestamp": "2020-01-01T00:00:00+00:00", "author": {"username": "ancien"},
                                   "content": "<@42> vieux message", "mentions": [{"id": "42"}]}],
    })
    res, err = executer("discord_mentions", {})
    assert not err and "yanis" in res.texte and "sarah" not in res.texte and "ancien" not in res.texte
    res, err = executer("discord_recap", {})
    assert "#general (2 messages)" in res.texte and res.texte.index("sarah") < res.texte.index("yanis")


def test_instagram(monkeypatch):
    from datetime import date, timedelta
    S.cfg.set("instagram.comptes", [{"nom": "studio", "id": "17841", "jeton": "t"}], ecrire=False)
    S.memoire.noter_valeur("instagram:17841:abonnes", (date.today() - timedelta(days=1)).isoformat(), 12443)

    def insights(m, url, kw):
        return {"data": [{"name": "views", "total_value": {"value": 1180 if kw["params"]["since"] % 2 else 1000}}]}
    brancher(monkeypatch, {"/17841/insights": insights, "/17841/media": {"data": []},
                           "/17841": {"username": "monstudio", "followers_count": 12480}})
    res, err = executer("instagram_stats", {})
    assert not err and "@monstudio : 12480 abonnés (+37 depuis hier)" in res.texte and "vues hier" in res.texte


def test_ntfy_et_telegram(monkeypatch):
    faux = brancher(monkeypatch, {"ntfy.sh": None, "api.telegram.org": {"ok": True}})
    res, err = executer("telephone_notifier", {"message": "Pâtes prêtes"})
    assert err and "ntfy" in res.texte
    S.cfg.set("ntfy.sujet", "jarvis-secret", ecrire=False)
    res, err = executer("telephone_notifier", {"message": "Pâtes prêtes", "titre": "Cuisine é"})
    assert not err and faux.appels[-1][2]["params"]["title"] == "Cuisine é" and faux.appels[-1][2]["data"] == "Pâtes prêtes".encode()
    S.cfg.set("telegram.jeton", "123:abc", ecrire=False)
    S.cfg.set("telegram.chat_id", "999", ecrire=False)
    res, err = executer("telegram_envoyer", {"texte": "x" * 4500})
    envois = [a for a in faux.appels if "sendMessage" in a[1]]
    assert not err and len(envois) == 2 and envois[0][2]["json"]["chat_id"] == "999"


def test_presence_logique(monkeypatch):
    from jarvis.outils.presence import Surveillant
    annonces, outils_lances = [], []
    monkeypatch.setattr("jarvis.outils.presence.annoncer", annonces.append)
    S.cfg.set("presence.arrivee", [{"outil": "hue_scene", "arguments": {"scene": "Détente"}}], ecrire=False)
    monkeypatch.setattr("jarvis.outils.executer", lambda nom, args, **kw: outils_lances.append((nom, args)))
    s = Surveillant()
    assert s.observer(True) is None and s.present is True                  # premier état : pas d'événement
    for _ in range(Surveillant.ABSENCES - 1):
        assert s.observer(False) is None
    assert s.observer(False) == "depart"
    assert s.observer(True) == "arrivee"
    assert outils_lances == [("hue_scene", {"scene": "Détente"})] and annonces == ["Bon retour à la maison."]


def test_appels_numeros_et_twiml(monkeypatch):
    from jarvis.outils import appels
    S.cfg.set("contacts", {"Maman": "06 12 34 56 78"}, ecrire=False)
    assert appels.numero("maman") == ("+33612345678", "maman")
    assert appels.numero("+44 20 7946 0958")[0] == "+442079460958"
    with pytest.raises(ErreurOutil):
        appels.numero("inconnu")
    S.cfg.set("twilio.url_publique", "https://j.exemple.fr", ecrire=False)
    appels.SESSIONS["s1"] = {"nom": "garage", "numero": "+33600000000", "objectif": "voiture prête ?", "tours": [],
                             "debut": time.time(), "statut": "lancé", "sid": "CA1"}
    reponses = iter(["Bonjour, ici l'assistant de Manan. La voiture est-elle prête ?", "Merci, au revoir & bonne journée. [FIN]"])
    monkeypatch.setattr(appels, "reponse_ia", lambda s: next(reponses))
    t1 = appels.webhook_voix("s1", {})
    xml.dom.minidom.parseString(t1)
    assert "<Gather" in t1 and "https://j.exemple.fr/twilio/voix/s1" in t1
    t2 = appels.webhook_voix("s1", {"SpeechResult": "Oui elle est prête"})
    xml.dom.minidom.parseString(t2)
    assert "<Hangup/>" in t2 and "&amp;" in t2 and "[FIN]" not in t2
    assert appels.SESSIONS["s1"]["tours"][1] == ("personne", "Oui elle est prête")
    machine = appels.webhook_voix("s1", {"AnsweredBy": "machine_start"})
    assert "<Hangup/>" in machine
    m = appels.messages_appel([("jarvis", "Bonjour."), ("personne", "Oui ?"), ("jarvis", "La voiture ?")])
    assert [x["role"] for x in m] == ["user", "assistant", "user", "assistant", "user"]       # silence : finit par la personne
    m = appels.messages_appel([("personne", "Allô"), ("personne", "Allô ?")])
    assert m == [{"role": "user", "content": "Allô\nAllô ?"}]


def test_mail_corps():
    from jarvis.outils.mail import corps_texte
    enc = lambda t: base64.urlsafe_b64encode(t.encode()).decode().rstrip("=")     # noqa: E731
    msg = {"mimeType": "multipart/alternative", "parts": [
        {"mimeType": "text/html", "body": {"data": enc("<p>Bonjour <b>Manan</b></p><script>x()</script>")}}]}
    assert "Bonjour" in corps_texte(msg) and "Manan" in corps_texte(msg) and "x()" not in corps_texte(msg)
    msg["parts"].append({"mimeType": "text/plain", "body": {"data": enc("Bonjour Manan, texte brut é")}})
    assert corps_texte(msg) == "Bonjour Manan, texte brut é"
    latin = base64.urlsafe_b64encode("Réunion déplacée à 15 h".encode("latin-1")).decode()
    msg = {"mimeType": "text/plain", "headers": [{"name": "Content-Type", "value": 'text/plain; charset="ISO-8859-1"'}],
           "body": {"data": latin}}
    assert corps_texte(msg) == "Réunion déplacée à 15 h"


def test_agenda_dates():
    from zoneinfo import ZoneInfo
    from jarvis.outils.agenda import jour_fr, lire_date
    d = lire_date("2026-10-13T14:30", ZoneInfo("Europe/Paris"))
    assert d.utcoffset().total_seconds() == 7200 and jour_fr(d) == "mar. 13 oct."
    with pytest.raises(ErreurOutil):
        lire_date("demain", ZoneInfo("Europe/Paris"))


def test_pc_hors_windows(monkeypatch):
    from jarvis.outils import pc
    monkeypatch.setattr(pc, "WINDOWS", False)
    res, err = executer("pc_ouvrir_application", {"nom": "spotify"})
    assert err and "Windows" in res.texte
    res, err = executer("pc_stats", {})
    assert not err and "Processeur" in res.texte and "Mémoire" in res.texte
    S.cfg.set("pc.applications", {"Mon Jeu": "steam://rungameid/123"}, ecrire=False)
    assert pc.trouver_application("mon jeu") == "steam://rungameid/123"
    assert pc.trouver_application("Calculatrice") == "calc"
    res, err = executer("pc_raccourci", {"touches": "ctrl+machin"})
    assert err and "inconnue" in res.texte



def test_pc_garde_fous(monkeypatch):
    import os
    import psutil
    from jarvis.outils import pc
    moi = psutil.Process(os.getpid()).name().lower().removesuffix(".exe")      # ex. « python3 »
    assert all(pr.info["pid"] != os.getpid() for pr in pc.processus_vises(moi[:6]))   # jamais Jarvis lui-même
    monkeypatch.setattr(psutil, "process_iter", lambda attrs: [
        type("P", (), {"info": {"name": "svchost.exe", "pid": 4242}})(),
        type("P", (), {"info": {"name": "Discord.exe", "pid": 4343}})()])
    assert [pr.info["name"] for pr in pc.processus_vises("svchost")] == []
    assert [pr.info["name"] for pr in pc.processus_vises("discord")] == ["Discord.exe"]
    assert "Discord.exe" in pc._question_fermer({"nom": "discord"})
    assert pc._question_ouvrir({"cible": "C:/Users/moi/Downloads/facture.exe"}).startswith("Lancer le programme")
    assert pc._question_ouvrir({"cible": "C:/Users/moi/Documents/cv.pdf"}) is None
    assert pc._question_ouvrir({"cible": "https://exemple.fr/a.exe"}) is None
    monkeypatch.setattr(pc, "fenetre_active", lambda: ("Windows PowerShell", "powershell.exe"))
    assert "PowerShell" in pc._question_frappe({"texte": "Remove-Item -Recurse C:/"})
    monkeypatch.setattr(pc, "fenetre_active", lambda: ("Sans titre - Bloc-notes", "notepad.exe"))
    assert pc._question_frappe({"texte": "Bonjour"}) is None


def test_voix_fin_de_phrase():
    from jarvis.voix.audio import TRAME, DetecteurParole, enregistrer_phrase
    rng = np.random.default_rng(1)
    silence = lambda: (rng.normal(0, 40, TRAME)).astype(np.int16)                         # noqa: E731
    voix = lambda: (np.sin(np.arange(TRAME) / 6) * 6000 + rng.normal(0, 200, TRAME)).astype(np.int16)   # noqa: E731
    trames = [silence() for _ in range(5)] + [voix() for _ in range(15)] + [silence() for _ in range(30)]
    flux = iter(trames)
    det = DetecteurParole()
    det.vad = None                                       # seuil d'énergie (webrtcvad absent du test)
    audio = enregistrer_phrase(lambda: next(flux), attente=3, silence_fin=0.8, detecteur=det)
    assert audio is not None and 15 * TRAME <= len(audio) <= 32 * TRAME
    flux2 = iter([silence() for _ in range(60)])
    assert enregistrer_phrase(lambda: next(flux2), attente=1.0, detecteur=det) is None


def test_voix_nettoyage():
    from jarvis.voix.reconnaissance import nettoyer
    from jarvis.voix.synthese import pour_la_voix
    assert nettoyer("Sous-titres réalisés par la communauté d'Amara.org") == ""
    assert nettoyer(" Allume le salon. ") == "Allume le salon."
    assert pour_la_voix("**C'est fait** ✅ voir [ici](https://x.fr) ou https://y.fr") == "C'est fait voir ici ou le lien"


def attendre(condition, delai=3.0):
    fin = time.time() + delai
    while time.time() < fin:
        if condition():
            return True
        time.sleep(0.02)
    return False


def test_bot_telegram_message_et_bouton_de_confirmation(monkeypatch):
    from jarvis import telegram as tg
    from jarvis.confirmation import Confirmations
    envoyes = []
    monkeypatch.setattr(tg.requests, "post", lambda url, json=None, timeout=None:
                        (envoyes.append((url.rsplit("/", 1)[-1], json)), Reponse({"ok": True, "result": True}))[1])
    conf = Confirmations(delai=5)

    class CerveauFactice:
        def traiter(self, texte, origine, canal, images=None):
            ok = conf.demander("Envoyer le mail à Paul ?", canal=canal)
            return f"{texte} : {'envoyé' if ok else 'annulé'}"

    S.cfg.set("telegram.jeton", "123:abc", ecrire=False)
    S.cfg.set("telegram.chat_id", "999", ecrire=False)
    t = tg.Telegram(S.cfg, CerveauFactice(), conf)
    t.message({"chat": {"id": 555}, "text": "intrus"})                    # autre conversation : ignorée
    t.message({"chat": {"id": 999}, "text": "mail"})
    assert attendre(lambda: conf.en_attente())
    ident = conf.en_attente()[0]
    question = [j for m, j in envoyes if m == "sendMessage" and "reply_markup" in j][0]
    assert question["reply_markup"]["inline_keyboard"][0][0]["callback_data"] == f"conf:{ident}:1"
    t.bouton({"id": "q1", "data": f"conf:{ident}:1", "message": {"chat": {"id": 555}}})   # bouton d'un intrus
    assert conf.en_attente() == [ident]
    t.bouton({"id": "q2", "data": f"conf:{ident}:1", "message": {"chat": {"id": 999}}})
    assert attendre(lambda: any(m == "sendMessage" and j.get("text") == "mail : envoyé" for m, j in envoyes))
    assert not any(j.get("chat_id") == "555" for m, j in envoyes if j)


def test_synthese_stop_coupe_le_reste_de_la_reponse(monkeypatch):
    from jarvis.voix import synthese
    monkeypatch.setattr(synthese.Synthese, "_boucle", lambda self: None)     # pas de son ici : on regarde la file
    s = synthese.Synthese(S.cfg)
    contenu = lambda: list(s.file.queue)                                      # noqa: E731
    s.ajouter("Première phrase **importante**.")
    assert contenu() == ["Première phrase importante."]
    s.stop()
    s.ajouter("Suite de la réponse coupée.")
    assert contenu() == []
    s.dire("Minuteur terminé.")                                               # annonce : toujours dite
    s.reprendre()                                                             # nouvelle demande
    s.ajouter("Nouvelle réponse.")
    assert contenu() == ["Minuteur terminé.", "Nouvelle réponse."]


def test_navigateur_adresses_et_entree(monkeypatch):
    from jarvis.outils import navigateur as nav
    assert nav.adresse_web("doctolib.fr") == "https://doctolib.fr"
    assert nav.adresse_web("http://exemple.fr/a?b=1") == "http://exemple.fr/a?b=1"
    for interdite in ("file:///C:/Users/moi/mots_de_passe.txt", "javascript:alert(1)", "chrome://settings"):
        with pytest.raises(ErreurOutil):
            nav.adresse_web(interdite)
    res, err = executer("nav_ouvrir", {"url": "file:///etc/passwd"})
    assert err and "http" in res.texte
    monkeypatch.setattr(nav.NAV, "formulaire_actif", lambda: ("Retour | Payer 42 €", "boutique.fr"))
    assert "Payer" in nav._question_touche({"touche": "Enter"})
    assert nav._question_touche({"touche": "ArrowDown"}) is None
    monkeypatch.setattr(nav.NAV, "formulaire_actif", lambda: ("Rechercher", "duckduckgo.com"))
    assert nav._question_touche({"touche": "Enter"}) is None


class FauxSynthese:
    def __init__(self):
        self.journal = []

    def __getattr__(self, nom):                       # stop, jouer_son, attendre, dire, ajouter, reprendre
        return lambda *a, **k: self.journal.append((nom, a[0] if a and isinstance(a[0], str) else None))


def test_boucle_vocale_reveil_demande_suivi_et_confirmation(monkeypatch):
    import threading
    from jarvis.voix import boucle as b
    synth = FauxSynthese()
    micro = type("Micro", (), {"vider": lambda self: None, "lire": lambda self, d=0.5: None})()
    demandes = []

    class CerveauFactice:
        def traiter(self, texte, origine, canal, sur_phrase):
            demandes.append(texte)
            if "mail" in texte:
                demandes.append(("confirmé", canal("Envoyer le mail à Paul ?", threading.Event(), "x")))
            sur_phrase("C'est fait.")
            return "C'est fait."

    v = b.BoucleVocale(S.cfg, CerveauFactice(), micro, None, None, synth)
    paroles = iter(["allume le salon", "envoie le mail à Paul", "euh", "oui vas-y", "merci"])
    monkeypatch.setattr(v, "ecouter", lambda attente: next(paroles, ""))
    reveils = iter([True])

    def attendre_reveil():
        r = next(reveils, False)
        if not r:
            v.arret.set()
        return r
    monkeypatch.setattr(v, "attendre_reveil", attendre_reveil)
    v.run()                                           # s'arrête quand plus de réveil
    assert demandes == ["allume le salon", "envoie le mail à Paul", ("confirmé", True)]
    noms = [n for n, _ in synth.journal]
    assert noms.count("reprendre") == 2 and ("ajouter", "C'est fait.") in synth.journal
    assert ("dire", "Envoyer le mail à Paul ? Tu confirmes ?") in synth.journal
    assert ("dire", "Envoyer le mail à Paul ? Réponds par oui ou par non.") in synth.journal    # « euh » : redemande
    assert ("dire", "Je reste à l'écoute.") in synth.journal                                    # « merci » : fin
    deja = threading.Event()
    deja.set()                                        # déjà répondu à l'écran : la voix ne demande rien
    assert v.confirmer("Fermer Discord ?", deja) is None
