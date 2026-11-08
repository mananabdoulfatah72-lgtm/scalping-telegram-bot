"""Vague 2, Z9 / Z10 rejoues dans zipline (deuxieme moteur) : chaque dimanche, investi 7 jours si le rendement des
28 derniers jours est positif. ACTIF=BTC FAMILLE=crypto zipline run -f elan_crypto.py -b crypto ..."""
import os

import pandas as pd
from zipline.api import get_datetime, order_target_percent, record, set_commission, set_slippage, symbol
from zipline.finance import commission, slippage


def initialize(context):
    context.a = symbol(os.environ["ACTIF"])
    set_commission(us_equities=commission.PerDollar(cost=0.0026))
    set_slippage(us_equities=slippage.FixedBasisPointsSlippage(basis_points=5, volume_limit=1.0))


def handle_data(context, data):
    seance = (get_datetime() - pd.Timedelta(minutes=1)).date()       # calendrier 24/7 : date de la seance qui se clot
    if seance.weekday() != 6 or not data.can_trade(context.a):
        return
    c = data.history(context.a, "close", 29, "1d")
    hausse = c.iloc[-1] / c.iloc[0] - 1 > 0
    order_target_percent(context.a, 0.99 if hausse else 0.0)
    record(signal=int(hausse))
