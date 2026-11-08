"""Strategie du labo zipline (labo_zipline/REGLES.md, fixee avant calcul) : tendance EMA 20 / 50, stop 2 ATR, objectif
4 ATR, achat seulement, sans levier. L'actif et la famille de frais sont donnes par l'environnement :
ACTIF=BTC FAMILLE=crypto zipline run -f strategie.py -b crypto ..."""
import os

import numpy as np
from zipline.api import order_target_percent, record, set_commission, set_slippage, symbol
from zipline.finance import commission, slippage

PART = 0.98
actif, famille = os.environ["ACTIF"], os.environ["FAMILLE"]


def initialize(context):
    context.a = symbol(actif)
    if famille == "crypto":
        set_commission(us_equities=commission.PerDollar(cost=0.0026))
    else:
        set_commission(us_equities=commission.PerShare(cost=0.005, min_trade_cost=1.0))
    set_slippage(us_equities=slippage.FixedBasisPointsSlippage(basis_points=5, volume_limit=1.0))
    context.entree = context.stop = context.objectif = context.atr_entree = None
    context.en_position = False; context.fixe = False


def ema(x, n):
    a = 2.0 / (n + 1); e = x[0]
    for v in x[1:]:
        e = a * v + (1 - a) * e
    return e


def atr_wilder(h, l, c, n=14):
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    a = tr[:n].mean()
    for v in tr[n:]:
        a = (a * (n - 1) + v) / n
    return a


def handle_data(context, data):
    a = context.a
    if not data.can_trade(a):
        return
    hist = data.history(a, ["high", "low", "close"], 250, "1d").dropna()
    if len(hist) < 120:
        return
    c, h, l = hist.close.values, hist.high.values, hist.low.values
    e20, e50, atr, prix = ema(c, 20), ema(c, 50), atr_wilder(h, l, c), c[-1]
    tendance = e20 > e50 and prix > e20
    pos = context.portfolio.positions[a].amount
    motif = ""
    if context.en_position and pos > 0 and not context.fixe:      # stop et objectif fixes sur le prix d'entree reel
        context.entree = context.portfolio.positions[a].cost_basis
        context.stop = context.entree - 2 * context.atr_entree; context.objectif = context.entree + 4 * context.atr_entree
        context.fixe = True
    if context.en_position and pos > 0:
        if prix <= context.stop:
            motif = "stop"
        elif prix >= context.objectif:
            motif = "objectif"
        elif e20 < e50:
            motif = "fin de tendance"
        if motif:
            order_target_percent(a, 0.0); context.en_position = False
    elif not context.en_position and pos == 0 and tendance and not get_open_orders_count(context):
        order_target_percent(a, PART)
        context.en_position = True; context.fixe = False; context.atr_entree = atr
        context.entree = prix; context.stop = prix - 2 * atr; context.objectif = prix + 4 * atr
        motif = "entrée"
    record(prix=prix, ema20=e20, ema50=e50, atr=atr, stop=context.stop if context.en_position else np.nan,
           objectif=context.objectif if context.en_position else np.nan, motif=motif)


def get_open_orders_count(context):
    from zipline.api import get_open_orders
    return len(get_open_orders(context.a))
