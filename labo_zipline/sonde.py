"""Sonde : ce que la strategie voit a chaque seance (lancee par zipline run -f sonde.py). Imprime la date de la seance, la
cloture courante et les trois dernieres clotures de l'historique, pour verifier l'alignement des dates sur le calendrier."""
import os

from zipline.api import get_datetime, symbol


def initialize(context):
    context.a = symbol(os.environ.get("ACTIF", "BTC")); context.n = 0


def handle_data(context, data):
    context.n += 1
    if context.n <= 4:
        h = data.history(context.a, "close", 3, "1d")
        print("SONDE", get_datetime(), "courant", data.current(context.a, "close"), "historique", [(str(i.date()), round(v, 3)) for i, v in h.items()])
