"""etude_large/README.md : les 29 marches de la partie A (ETF Alpaca 5 minutes -> future CME suivi).
Chaque ligne : ETF, future suivi, fichier Yahoo (niveau de prix du future), plus petit contrat CME, $ par unite de prix
de Yahoo, tick (en unite de prix de Yahoo), commission par ordre ($), decision (True) ou information (False).
Frais d'un aller-retour : 2 commissions + 2 ticks, divises par la valeur du contrat (prix Yahoo de la veille x $ par
unite). Yahoo cote les grains en cents par boisseau, le yen en $ par yen."""

MICRO, STANDARD = 1.0, 2.5

MARCHES = [
    # etf, future, yahoo, contrat, $ par unite, tick, commission, decision
    ("SPY", "ES", "ES", "MES", 5.0, 0.25, MICRO, True),
    ("QQQ", "NQ", "NQ", "MNQ", 2.0, 0.25, MICRO, True),
    ("DIA", "YM", "YM", "MYM", 0.5, 1.0, MICRO, True),
    ("IWM", "RTY", "RTY", "M2K", 5.0, 0.1, MICRO, True),
    ("TLT", "ZB", "ZB", "ZB", 1000.0, 1 / 32, STANDARD, True),
    ("IEF", "ZN", "ZN", "ZN", 1000.0, 1 / 64, STANDARD, True),
    ("IEI", "ZF", "ZF", "ZF", 1000.0, 1 / 128, STANDARD, True),
    ("SHY", "ZT", "ZT", "ZT", 2000.0, 1 / 256, STANDARD, True),
    ("GLD", "GC", "GC", "MGC", 10.0, 0.1, MICRO, True),
    ("SLV", "SI", "SI", "SIL", 1000.0, 0.005, MICRO, True),
    ("CPER", "HG", "HG", "MHG", 2500.0, 0.0005, MICRO, True),
    ("PPLT", "PL", "PL", "PL", 50.0, 0.1, STANDARD, True),
    ("PALL", "PA", "PA", "PA", 100.0, 0.5, STANDARD, True),
    ("USO", "CL", "CL", "MCL", 100.0, 0.01, MICRO, True),
    ("BNO", "BZ", "BZ", "BZ", 1000.0, 0.01, STANDARD, True),
    ("UNG", "NG", "NG", "QG", 2500.0, 0.005, STANDARD, True),
    ("UGA", "RB", "RB", "RB", 42000.0, 0.0001, STANDARD, True),
    ("FXE", "6E", "6E", "M6E", 12500.0, 0.0001, MICRO, True),
    ("FXY", "6J", "6J", "MJY", 1250000.0, 0.000001, MICRO, True),
    ("FXB", "6B", "6B", "M6B", 6250.0, 0.0001, MICRO, True),
    ("FXA", "6A", "6A", "M6A", 10000.0, 0.0001, MICRO, True),
    ("FXC", "6C", "6C", "MCD", 10000.0, 0.0001, MICRO, True),
    ("FXF", "6S", "6S", "MSF", 12500.0, 0.0001, MICRO, True),
    ("CORN", "ZC", "ZC", "XC", 10.0, 0.125, STANDARD, True),
    ("SOYB", "ZS", "ZS", "XK", 10.0, 0.125, STANDARD, True),
    ("WEAT", "ZW", "ZW", "XW", 10.0, 0.125, STANDARD, True),
    ("BITO", "BTC", "BTC", "MBT", 0.1, 5.0, MICRO, True),
    ("UUP", "DX", "DXY", "DX", 1000.0, 0.005, STANDARD, False),   # ICE, pas CME
    ("VXX", "VX", "VIX", "VXM", 100.0, 0.05, STANDARD, False),    # CFE, pas CME ; niveau du VIX au comptant
]
