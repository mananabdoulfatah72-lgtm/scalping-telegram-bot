"""Univers fixe de l'etude des secteurs (liste arretee le 28 septembre 2026, avant les donnees).

Les actions sont une liste arretee de memoire parmi les plus grosses de chaque secteur en 2025-2026,
pas la composition exacte de l'indice : il en manque (par exemple PLTR dans la technologie), six n'ont
pas de donnees (AVB, CTRA, EA, EQR, IPG, MMC) et IPG n'est plus cotee. Un backtest sur ces listes a un
biais de survie (les entreprises disparues ou sorties de l'indice manquent). C'est pourquoi les
strategies 1 et 4 utilisent l'ETF du secteur, et les resultats des strategies 2 et 3 sont lus avec
prudence avant 2020.
"""
MARCHE = "SPY"
SECTEURS = {  # ETF SPDR -> nom
    "XLE": "Energie", "XLU": "Services publics", "XLK": "Technologie", "XLC": "Communication",
    "XLF": "Finance", "XLV": "Sante", "XLI": "Industrie", "XLY": "Consommation cyclique",
    "XLP": "Consommation de base", "XLB": "Materiaux", "XLRE": "Immobilier",
}
ACTIONS = {
    "XLE": ["XOM", "CVX", "COP", "EOG", "SLB", "WMB", "KMI", "OKE", "PSX", "MPC", "VLO", "OXY", "BKR",
            "HAL", "FANG", "DVN", "EQT", "CTRA", "TRGP", "APA"],
    "XLU": ["NEE", "SO", "DUK", "CEG", "AEP", "SRE", "D", "EXC", "XEL", "PEG", "ED", "VST", "ETR", "WEC",
            "PCG", "EIX", "DTE", "AEE", "PPL", "NRG"],
    "XLK": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "AMD", "ADBE", "CSCO", "ACN", "IBM", "INTU",
            "TXN", "QCOM", "AMAT", "NOW", "MU", "LRCX", "KLAC", "ADI"],
    "XLC": ["META", "GOOGL", "NFLX", "DIS", "TMUS", "T", "VZ", "CMCSA", "CHTR", "EA", "TTWO", "WBD",
            "OMC", "LYV", "IPG"],
    "XLF": ["BRK-B", "JPM", "V", "MA", "BAC", "WFC", "GS", "MS", "AXP", "SPGI", "C", "BLK", "SCHW", "PGR",
            "CB", "MMC", "BX", "ICE", "CME", "KKR"],
    "XLV": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "ISRG", "AMGN", "DHR", "PFE", "BSX", "SYK",
            "VRTX", "GILD", "MDT", "BMY", "ELV", "CVS", "REGN"],
    "XLI": ["GE", "CAT", "RTX", "UBER", "HON", "UNP", "ETN", "BA", "LMT", "DE", "ADP", "GEV", "PH", "WM",
            "TT", "UPS", "PWR", "GD", "NOC", "EMR"],
    "XLY": ["AMZN", "TSLA", "HD", "MCD", "BKNG", "LOW", "TJX", "SBUX", "NKE", "ORLY", "CMG", "MAR", "ABNB",
            "GM", "AZO", "ROST", "HLT", "F", "DHI", "LULU"],
    "XLP": ["WMT", "COST", "PG", "KO", "PEP", "PM", "MDLZ", "MO", "CL", "TGT", "KMB", "GIS", "KDP", "STZ",
            "SYY", "KHC", "HSY", "KR", "ADM", "EL"],
    "XLB": ["LIN", "SHW", "APD", "ECL", "FCX", "NEM", "CTVA", "DOW", "DD", "NUE", "VMC", "MLM", "PPG", "IFF",
            "LYB", "STLD", "BALL", "PKG", "IP", "CF"],
    "XLRE": ["PLD", "AMT", "EQIX", "WELL", "SPG", "PSA", "O", "CCI", "DLR", "CBRE", "EXR", "AVB", "VICI",
             "EQR", "IRM", "SBAC", "VTR", "WY", "ARE", "INVH"],
}
# Test T6 (fenetre 5 ans) : les 20 plus grosses actions de XLK a la fin septembre 2021, de memoire (poids
# approximatifs). V, MA et PYPL sont passees en finance en mars 2023 ; INTC et PYPL ont beaucoup baisse depuis.
XLK_2021 = ["AAPL", "MSFT", "NVDA", "V", "MA", "ADBE", "PYPL", "CRM", "ACN", "INTC", "CSCO", "AVGO", "ORCL",
            "QCOM", "TXN", "AMD", "INTU", "AMAT", "IBM", "NOW"]

INDUSTRIES = ["XOP", "OIH", "XES", "AMLP", "URA", "NLR", "ICLN", "TAN", "SMH", "SOXX", "IGV", "KRE", "KBE",
              "XBI", "IBB", "ITA", "XHB", "ITB", "GDX", "XME", "COPX", "LIT", "VNQ", "XRT"]
MACRO = ["^TNX", "^IRX", "^VIX", "CL=F", "NG=F", "HG=F", "GC=F", "DX-Y.NYB"]
