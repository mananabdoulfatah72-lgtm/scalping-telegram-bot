"""Streaming : OBS Studio par son serveur WebSocket (OBS 28 et plus : Outils > Paramètres du serveur WebSocket).
Direct, enregistrement, scènes, replay, micro."""
from __future__ import annotations

from contextlib import contextmanager

from ..services import S
from . import ErreurOutil, module, outil, p


@module("streaming", "STREAMING")
def etat() -> tuple[str, str]:
    try:
        import obsws_python  # noqa: F401
    except ImportError:
        return "absent", "module obsws-python à installer (installer.bat)"
    return "pret", f"OBS sur {S.cfg.get('obs.hote', 'localhost')}:{S.cfg.get('obs.port', 4455)}"


@contextmanager
def obs():
    try:
        import obsws_python
    except ImportError:
        raise ErreurOutil("Le contrôle d'OBS a besoin du module obsws-python (relance installer.bat).")
    try:
        client = obsws_python.ReqClient(host=S.cfg.get("obs.hote", "localhost"), port=int(S.cfg.get("obs.port", 4455)),
                                        password=S.cfg.get("obs.mot_de_passe", ""), timeout=4)
    except Exception as e:
        raise ErreurOutil("OBS ne répond pas : lance OBS et active son serveur WebSocket (Outils > Paramètres du "
                          f"serveur WebSocket), mot de passe dans [obs] de config.toml. ({type(e).__name__})")
    try:
        yield client
    except ErreurOutil:
        raise
    except Exception as e:
        raise ErreurOutil(f"OBS a refusé : {e}")
    finally:
        try:
            client.disconnect()
        except Exception:
            pass


def _noms_scenes(c) -> tuple[list[str], str]:
    r = c.get_scene_list()
    return [s.get("sceneName", "") for s in reversed(r.scenes)], r.current_program_scene_name


@outil("obs_etat", "État d'OBS : direct, enregistrement, scène affichée, liste des scènes.", "STREAMING")
def obs_etat() -> str:
    with obs() as c:
        st, rec = c.get_stream_status(), c.get_record_status()
        scenes, actuelle = _noms_scenes(c)
    return (f"Direct : {'en cours depuis ' + st.output_timecode if st.output_active else 'arrêté'}. "
            f"Enregistrement : {'en pause' if getattr(rec, 'output_paused', False) else ('en cours depuis ' + rec.output_timecode) if rec.output_active else 'arrêté'}. "
            f"Scène : {actuelle}. Scènes : {', '.join(scenes)}.")


def _question_direct(args: dict) -> str | None:
    return "Lancer le direct sur OBS" if args.get("action") == "demarrer" else None


@outil("obs_direct", "Lance ou arrête le direct (stream) dans OBS.", "STREAMING",
       {"action": p("string", "Action", enum=["demarrer", "arreter"])}, requis=["action"], confirmer=_question_direct)
def obs_direct(action: str) -> str:
    with obs() as c:
        actif = c.get_stream_status().output_active
        if action == "demarrer":
            if actif:
                return "Le direct est déjà lancé."
            c.start_stream()
            return "Direct lancé."
        if not actif:
            return "Le direct n'était pas lancé."
        c.stop_stream()
        return "Direct arrêté."


@outil("obs_enregistrement", "Démarre, arrête, met en pause ou reprend l'enregistrement OBS.", "STREAMING",
       {"action": p("string", "Action", enum=["demarrer", "arreter", "pause", "reprendre"])}, requis=["action"])
def obs_enregistrement(action: str) -> str:
    with obs() as c:
        {"demarrer": c.start_record, "arreter": c.stop_record, "pause": c.pause_record,
         "reprendre": c.resume_record}[action]()
    return {"demarrer": "Enregistrement lancé.", "arreter": "Enregistrement arrêté et sauvegardé.",
            "pause": "Enregistrement en pause.", "reprendre": "Enregistrement repris."}[action]


@outil("obs_scene", "Change la scène affichée dans OBS.", "STREAMING",
       {"scene": p("string", "Nom de la scène")}, requis=["scene"])
def obs_scene(scene: str) -> str:
    with obs() as c:
        scenes, _ = _noms_scenes(c)
        n = scene.lower().strip()
        choix = next((s for s in scenes if s.lower() == n), None) or next((s for s in scenes if n in s.lower()), None)
        if not choix:
            raise ErreurOutil(f"Pas de scène « {scene} » dans OBS. Scènes : {', '.join(scenes)}.")
        c.set_current_program_scene(choix)
    return f"Scène {choix} affichée."


@outil("obs_replay", "Replay d'OBS : sauvegarder les dernières secondes, ou démarrer / arrêter le tampon de replay.",
       "STREAMING", {"action": p("string", "Action", enum=["sauvegarder", "demarrer", "arreter"])}, requis=["action"])
def obs_replay(action: str) -> str:
    with obs() as c:
        if action == "sauvegarder":
            if not c.get_replay_buffer_status().output_active:
                c.start_replay_buffer()
                return "Le tampon de replay n'était pas actif : je viens de le démarrer, redemande dans un moment."
            c.save_replay_buffer()
            return "Replay sauvegardé."
        (c.start_replay_buffer if action == "demarrer" else c.stop_replay_buffer)()
    return "Tampon de replay démarré." if action == "demarrer" else "Tampon de replay arrêté."


@outil("obs_micro", "Coupe ou remet une source audio d'OBS (micro, son du bureau...).", "STREAMING",
       {"source": p("string", "Nom de la source audio (ex. Mic/Aux)"), "couper": p("boolean", "true = couper")},
       requis=["source", "couper"])
def obs_micro(source: str, couper: bool) -> str:
    with obs() as c:
        noms = [i.get("inputName", "") for i in c.get_input_list().inputs]
        n = source.lower()
        choix = next((x for x in noms if x.lower() == n), None) or next((x for x in noms if n in x.lower()), None)
        if not choix:
            raise ErreurOutil(f"Pas de source « {source} ». Sources : {', '.join(noms)}.")
        c.set_input_mute(choix, couper)
    return f"{choix} {'coupé' if couper else 'remis'}."
