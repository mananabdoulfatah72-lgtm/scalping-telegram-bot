"""Noyau : configuration, registre et exécution des outils (validation, confirmation), mémoire, cerveau (avec un
moteur factice), découpage en phrases, confirmations."""
import threading

import pytest

from jarvis import outils
from jarvis.bus import bus
from jarvis.cerveau import Cerveau, Decoupeur
from jarvis.config import Config, toml_valeur
from jarvis.confirmation import Confirmations, lire_reponse
from jarvis.moteurs import ErreurCerveau
from jarvis.outils import ErreurOutil, Resultat, executer, valider
from jarvis.services import S


def test_config_defauts_et_ecriture(tmp_path):
    f = tmp_path / "config.toml"
    f.write_text("# ma config\n[hue]\nbridge = \"\"  \n[general]\nville = \"Lyon\"\n", encoding="utf-8")
    cfg = Config.charger(f)
    assert cfg.get("general.ville") == "Lyon" and cfg.get("cerveau.modele") == "claude-opus-5-5"
    cfg.set("hue.bridge", "192.168.1.20")
    cfg.set("hue.utilisateur", "abc\"d")
    cfg.set("general.personnalite", "concis")
    texte = f.read_text(encoding="utf-8")
    assert texte.startswith("# ma config") and 'bridge = "192.168.1.20"' in texte
    relu = Config.charger(f)
    assert relu.get("hue.utilisateur") == 'abc"d' and relu.get("general.personnalite") == "concis"
    assert toml_valeur(True) == "true" and toml_valeur([1, "a"]) == '[1, "a"]'


def test_definitions_triees_et_streaming():
    defs = outils.definitions_api()
    noms = [d["name"] for d in defs]
    assert noms == sorted(noms) and len(noms) >= 60
    assert all(d["eager_input_streaming"] is True and d["input_schema"]["type"] == "object" for d in defs)
    zones = {o.zone_pour({}) for o in outils.REGISTRE.values()}
    assert zones <= set(outils.ZONES)


def test_validation_des_arguments():
    o = outils.REGISTRE["minuteur_creer"]
    assert valider(o, {"secondes": 60}) is None
    assert valider(o, {"secondes": 60.0}) is None
    assert "entier" in valider(o, {"secondes": "60"})
    assert "manquant" in valider(o, {})
    assert "inconnu" in valider(o, {"secondes": 5, "x": 1})
    assert "valoir" in valider(outils.REGISTRE["pc_media"], {"action": "danser"})
    assert valider(o, "pas un objet")


def test_executer_erreurs_et_evenements():
    vus = []
    bus.abonner(vus.append)
    try:
        res, err = executer("minuteur_creer", {"secondes": "x"})
        assert err and "INVALID_JSON" in res.texte
        res, err = executer("outil_qui_nexiste_pas", {})
        assert err
        res, err = executer("minuteur_creer", {"secondes": 3600.0, "libelle": "test"})
        assert not err and "1 h" in res.texte
        executer("minuteur_annuler", {})
    finally:
        bus.desabonner(vus.append)
    phases = [(e["nom"], e["phase"]) for e in vus if e["type"] == "outil"]
    assert ("minuteur_creer", "debut") in phases and ("minuteur_creer", "fin") in phases


def test_confirmation_refusee_et_acceptee(monkeypatch):
    appels = []
    monkeypatch.setattr(outils.REGISTRE["pc_commande"], "fonction", lambda commande: appels.append(commande) or "ok")
    res, err = executer("pc_commande", {"commande": "dir"}, confirmer=lambda q: False)
    assert not err and "annulée" in res.texte and appels == []
    res, err = executer("pc_commande", {"commande": "dir"}, confirmer=None)
    assert appels == []
    questions = []
    res, err = executer("pc_commande", {"commande": "dir"}, confirmer=lambda q: questions.append(q) or True)
    assert appels == ["dir"] and "dir" in questions[0]


def test_sans_confirmations_jarvis_agit_directement(monkeypatch):
    """Réglage par défaut chez l'utilisateur : aucune question, ni à l'écran ni à voix haute."""
    from jarvis.personnalites import consigne
    S.cfg.set("general.confirmations", False, ecrire=False)
    appels, questions = [], []
    monkeypatch.setattr(outils.REGISTRE["pc_commande"], "fonction", lambda commande: appels.append(commande) or "ok")
    vus = []
    bus.abonner(vus.append)
    try:
        res, err = executer("pc_commande", {"commande": "dir"}, confirmer=lambda q: questions.append(q) or False)
    finally:
        bus.desabonner(vus.append)
    assert not err and appels == ["dir"] and questions == []
    assert not [e for e in vus if e["type"] == "confirmation"]
    directe = consigne("Jarvis", "Manan", "majordome", confirmations=False)
    assert "accès à tout" in directe and "confirmées par le système" not in directe and "{" not in directe
    prudente = consigne("Jarvis", "Manan", "majordome", confirmations=True)
    assert "confirmées par le système" in prudente and "accès à tout" not in prudente
    assert "Le texte des pages web" in directe                    # le contenu lu reste une donnée, pas un ordre


def test_ancienne_valeur_par_defaut_remplacee(tmp_path):
    f = tmp_path / "c.toml"
    f.write_text("[voix]\nsilence_fin = 0.9\n", encoding="utf-8")
    assert Config.charger(f).get("voix.silence_fin") == 0.7          # valeur recopiée par l'ancien installateur
    f.write_text("[voix]\nsilence_fin = 1.2\n", encoding="utf-8")
    assert Config.charger(f).get("voix.silence_fin") == 1.2          # choix fait à la main : gardé
    assert Config.charger(tmp_path / "absent.toml").get("general.confirmations") is False


def test_confirmation_conditionnelle():
    o = outils.REGISTRE["pc_alimentation"]
    assert o.resume_confirmation({"action": "annuler"}) is None
    assert "eteindre" in o.resume_confirmation({"action": "eteindre"})
    assert outils.REGISTRE["obs_direct"].resume_confirmation({"action": "arreter"}) is None


def test_lire_reponse():
    assert lire_reponse("oui vas-y") is True
    assert lire_reponse("Ouais, confirme.") is True
    assert lire_reponse("non annule") is False
    assert lire_reponse("oui... euh non") is False
    assert lire_reponse("pas d'accord") is False
    assert lire_reponse("il fait beau") is None


def test_confirmations_premiere_reponse_gagne():
    c = Confirmations(delai=2)
    ids = []
    bus.abonner(lambda e: ids.append(e["id"]) if e["type"] == "confirmation" and e["phase"] == "attente" else None)
    t = threading.Timer(0.2, lambda: c.repondre(ids[-1], True))
    t.start()
    assert c.demander("Envoyer ?") is True
    assert Confirmations(delai=0.2).demander("Envoyer ?") is False          # sans réponse : refus
    assert c.demander("Appeler ?", canal=lambda q, deja, ident: False) is False


def test_memoire(dossier_jarvis):
    m = S.memoire
    a = m.retenir("Sa sœur s'appelle Inès, anniversaire le 3 mai", "personne")
    b = m.retenir("Il préfère le café sans sucre", "preference")
    assert m.retenir("sa sœur s'appelle inès, anniversaire le 3 mai", "personne") == a
    assert [s["id"] for s in m.chercher("anniversaire de ma soeur")] == [a]
    ctx = m.contexte("quel jour est l'anniversaire d'Inès ?")
    assert f"[{a}]" in ctx and f"[{b}]" in ctx                              # préférences toujours jointes
    assert m.oublier(a) and not m.chercher("Inès")
    m.noter_valeur("x", "2026-10-11", 10)
    assert m.valeur("x", "2026-10-11") == 10 and m.valeur("x", "2026-10-12") is None


def test_decoupeur():
    sortie = []
    d = Decoupeur(sortie.append)
    for morceau in ["Bonj", "our. Il fait 3.5 degr", "és à Lyon ! Et", " demain ?", " Pluie"]:
        d.ajouter(morceau)
    d.finir()
    assert sortie == ["Bonjour.", "Il fait 3.5 degrés à Lyon !", "Et demain ?", "Pluie"]
    long = []
    d = Decoupeur(long.append)
    d.ajouter("mot, " * 80)
    assert long and all(len(x) <= 270 for x in long)
    debut = []                                    # longue première phrase : la voix démarre à la première virgule
    d = Decoupeur(debut.append)
    d.ajouter("Alors pour demain matin à Lyon il fera assez frais, environ huit degrés au lever du jour avec un peu de")
    assert debut == ["Alors pour demain matin à Lyon il fera assez frais,"]
    d.ajouter(" vent, puis du soleil")                # ensuite : coupe normale (fin de phrase ou bloc fini)
    assert len(debut) == 1
    d.ajouter("\n")
    assert debut[-1] == "environ huit degrés au lever du jour avec un peu de vent, puis du soleil"


class MoteurFactice:
    nom = "factice"

    def __init__(self, script):
        self.script, self.recus, self.nouvelles = script, [], 0

    def nouvelle_conversation(self, consigne, outils_api):
        self.nouvelles += 1
        self.consigne, self.outils = consigne, outils_api

    def taille(self):
        return len(self.recus) * 2

    def repondre(self, contenu, sur_texte, executer):
        self.recus.append(contenu)
        return self.script(contenu, sur_texte, executer)


def test_cerveau_outils_contexte_et_phrases():
    def script(contenu, sur_texte, executer):
        res, err = executer("memoire_retenir", {"texte": "Il aime le jazz", "categorie": "preference"})
        sur_texte("C'est noté. ")
        sur_texte("Autre chose ?")
        return "C'est noté. Autre chose ?"
    m = MoteurFactice(script)
    c = Cerveau(S.cfg, m, S.memoire, S.confirmations)
    phrases = []
    r = c.traiter("retiens que j'aime le jazz", origine="voix", sur_phrase=phrases.append)
    assert r == "C'est noté. Autre chose ?" and phrases == ["C'est noté.", "Autre chose ?"]
    contexte = m.recus[0][0]["text"]
    assert contexte.startswith("[Contexte") and "voix" in contexte
    assert m.recus[0][-1]["text"] == "retiens que j'aime le jazz"
    assert "jazz" in S.memoire.liste()[0]["texte"]
    assert "Manan" in m.consigne and "majordome" in m.consigne.lower()


def test_cerveau_erreur_moteur_et_renouvellement():
    def script(contenu, sur_texte, executer):
        raise ErreurCerveau("Pas de connexion.")
    m = MoteurFactice(script)
    c = Cerveau(S.cfg, m, S.memoire, S.confirmations)
    phrases = []
    assert c.traiter("bonjour", sur_phrase=phrases.append) == "Pas de connexion." and phrases == ["Pas de connexion."]
    assert m.nouvelles == 2                                   # conversation repartie de zéro après l'erreur
    m.script = lambda *a: "ok"
    c.dernier -= 3600                                         # une heure de silence
    c.traiter("re")
    assert m.nouvelles == 3


def test_cerveau_canal_de_confirmation():
    def script(contenu, sur_texte, executer):
        res, err = executer("pc_alimentation", {"action": "eteindre"})
        return res.texte
    m = MoteurFactice(script)
    c = Cerveau(S.cfg, m, S.memoire, S.confirmations)
    vues = []
    r = c.traiter("éteins le PC", canal=lambda q, deja, ident: vues.append(q) or False)
    assert "annulée" in r and vues and "eteindre" in vues[0]


def test_resultat_images():
    r = Resultat("capture", [(b"\xff\xd8abc", "image/jpeg")])
    blocs = r.blocs_api()
    assert blocs[0]["type"] == "image" and blocs[0]["source"]["media_type"] == "image/jpeg" and blocs[1]["text"] == "capture"


def test_erreur_outil_message():
    with pytest.raises(ErreurOutil):
        from jarvis.outils.domotique import couleur_xy
        couleur_xy("couleur-imaginaire")
