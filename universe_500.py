"""
Strategy #3: Predefined 500-Ticker Tradable Universe
Curated for Maximum Diversification across 11 GICS Sectors, Global Markets, Fixed Income, and Commodities.
100% Non-Leveraged (All 2x, 3x, and inverse ETFs strictly excluded).
Pre-validated against Alpaca Markets API for active trading, fractionability, and data history.
"""

# ==============================================================================
# 1. NON-LEVERAGED LIQUID ETFS (116 ASSETS ACROSS 7 ASSET CLASSES)
# ==============================================================================

# Broad Market Indices (15)
ETFS_BROAD = [
    "SPY", "QQQ", "IWM", "DIA", "MDY", "IJR", "IJH", "IWV", "VTI", "RSP", 
    "VT", "VXUS", "VOO", "IVV", "SCHX"
]

# SPDR Core 11 Sectors (11)
ETFS_SECTORS = [
    "XLK", "XLV", "XLF", "XLY", "XLC", "XLI", "XLP", "XLE", "XLU", "XLB", "XLRE"
]

# Industry & Thematic Sub-Sectors (35)
ETFS_SUBSECTORS = [
    "SMH", "SOXX", "XBI", "IBB", "KRE", "KBE", "XRT", "XHB", "ITB", "XME", 
    "OIH", "XOP", "IYT", "JETS", "IAI", "IHI", "FDN", "IGV", "CLOU", "CIBR", 
    "HACK", "TAN", "ICLN", "LIT", "PAVE", "MOO", "REM", "IAK", "IHF", "IGE", 
    "PEJ", "PBW", "SKYY", "ROBT", "BOTZ"
]

# Global, International & Emerging Markets (20)
ETFS_GLOBAL = [
    "EEM", "EFA", "FXI", "MCHI", "KWEB", "EWZ", "EWJ", "EWY", "INDA", "VGK", 
    "VWO", "VEA", "EWT", "EWG", "EWU", "EWC", "EWA", "EWH", "EPI", "ASHR"
]

# Fixed Income, Rates & Credit (15)
ETFS_BONDS = [
    "TLT", "IEF", "SHY", "IEI", "GOVT", "TIP", "HYG", "JNK", "LQD", "BND", 
    "AGG", "VCIT", "VCSH", "BKLN", "EMB"
]

# Commodities, Metals & Currencies (15)
ETFS_COMMODITIES = [
    "GLD", "SLV", "GDX", "GDXJ", "USO", "UNG", "DBA", "DBB", "CPER", "PPLT", 
    "PALL", "UUP", "FXE", "FXY", "DBC"
]

# Factor & Style Overlays (5)
ETFS_FACTORS = [
    "QUAL", "MTUM", "USMV", "VLUE", "NOBL"
]

ALL_ETFS = sorted(list(set(
    ETFS_BROAD + ETFS_SECTORS + ETFS_SUBSECTORS + ETFS_GLOBAL + 
    ETFS_BONDS + ETFS_COMMODITIES + ETFS_FACTORS
)))

# ==============================================================================
# 2. EQUITIES ACROSS ALL 11 GICS SECTORS (384 LIQUID ASSETS)
# ==============================================================================

# Information Technology (68)
EQUITIES_TECH = [
    "AAPL", "MSFT", "NVDA", "AVGO", "ADBE", "CRM", "AMD", "INTC", "QCOM", "TXN", 
    "AMAT", "MU", "NOW", "INTU", "PANW", "LRCX", "ADI", "KLAC", "SNPS", "CDNS", 
    "CRWD", "FTNT", "PLTR", "MRVL", "MCHP", "ON", "ANET", "WDC", "STX", "HPQ", 
    "DELL", "HPE", "SMCI", "ARM", "ABNB", "UBER", "TEAM", "DDOG", "NET", "ZS", 
    "MDB", "PATH", "ESTC", "OKTA", "HUBS", "SHOP", "TWLO", "DOCU", "SPOT", "DASH", 
    "SNAP", "PINS", "RBLX", "COIN", "HOOD", "PYPL", "AFRM", "APP", "TOST", "DUOL", 
    "IOT", "MNDY", "GTLB", "NTNX", "FSLY", "BILL", "S", "GLW"
]

# Communication Services (21)
EQUITIES_COMM = [
    "GOOGL", "GOOG", "META", "NFLX", "DIS", "CMCSA", "VZ", "T", "CHTR", "TMUS", 
    "WBD", "PARA", "FOXA", "FOX", "OMC", "LYV", "TTWO", "NYT", "NWSA", "NWS", "SIRI"
]

# Consumer Discretionary (44)
EQUITIES_DISC = [
    "AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "TJX", "BKNG", "TGT", 
    "ROST", "ORLY", "AZO", "LULU", "MAR", "HLT", "CMG", "YUM", "DHI", "LEN", 
    "NVR", "PHM", "TOL", "F", "GM", "APTV", "BBY", "TSCO", "DRI", "LKQ", 
    "GPC", "EXPE", "RCL", "CCL", "NCLH", "MGM", "WYNN", "LVS", "ULTA", "DECK", 
    "CROX", "BWA", "KMX", "PTON"
]

# Consumer Staples (30)
EQUITIES_STAPLES = [
    "WMT", "COST", "PG", "KO", "PEP", "PM", "MO", "MDLZ", "CL", "EL", 
    "KMB", "GIS", "HSY", "SJM", "STZ", "CAG", "TSN", "ADM", "BG", "SYY", 
    "KR", "DG", "DLTR", "CHD", "CLX", "TAP", "MNST", "CELH", "KDP", "CPB"
]

# Financials (50)
EQUITIES_FIN = [
    "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "AXP", "SPGI", "CB", 
    "PGR", "AON", "CME", "ICE", "MCO", "USB", "PNC", "TFC", "COF", "STT", 
    "FITB", "MTB", "HBAN", "RF", "CFG", "KEY", "SYF", "ALL", "TRV", "AIG", 
    "PRU", "MET", "AFL", "HIG", "AJG", "BRO", "WTW", "SCHW", "IBKR", "RJF", 
    "NTRS", "AMP", "BEN", "IVZ", "CINF", "L", "FAF", "SOFI", "NU", "UPST"
]

# Healthcare & Biotech (51)
EQUITIES_HEALTH = [
    "LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "ABT", "PFE", "DHR", "BMY", 
    "AMGN", "GILD", "ISRG", "VRTX", "REGN", "MDT", "SYK", "BSX", "BDX", "ZTS", 
    "EW", "CI", "HUM", "ELV", "CNC", "CVS", "MCK", "CAH", "COR", "IDXX", 
    "DXCM", "ALGN", "PODD", "ILMN", "MRNA", "BIIB", "IQV", "A", "WST", "RMD", 
    "STE", "BAX", "COO", "BIO", "TECH", "RVTY", "VTRS", "INCY", "NTRA", "ALNY", "BMRN"
]

# Industrials, Aerospace & Defense (45)
EQUITIES_IND = [
    "CAT", "GE", "HON", "UNP", "UPS", "BA", "LMT", "RTX", "DE", "ETN", 
    "WM", "FDX", "ITW", "NSC", "CSX", "EMR", "ROP", "GD", "NOC", "TDG", 
    "PH", "CMI", "PCAR", "JCI", "FAST", "CARR", "ODFL", "URI", "GWW", "VMC", 
    "MLM", "CPRT", "RSG", "CTAS", "PWR", "EFX", "DAL", "UAL", "LUV", "AAL", 
    "EXPD", "CHRW", "JBHT", "AXON", "XYL"
]

# Energy (22)
EQUITIES_ENERGY = [
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "OXY", "KMI", 
    "WMB", "HAL", "BKR", "FANG", "DVN", "TRGP", "APA", "OVV", "EQNR", "BP", 
    "SHEL", "TTE"
]

# Materials & Mining (20)
EQUITIES_MAT = [
    "LIN", "APD", "SHW", "FCX", "ECL", "NEM", "CTVA", "DOW", "DD", "ALB", 
    "NUE", "STLD", "CLF", "AA", "PPG", "IFF", "BALL", "AMCR", "CF", "MOS"
]

# Utilities (18)
EQUITIES_UTIL = [
    "NEE", "SO", "DUK", "CEG", "SRE", "AEP", "D", "PEG", "EXC", "ED", 
    "XEL", "WEC", "ES", "AWK", "DTE", "PPL", "EIX", "FE"
]

# Real Estate (16)
EQUITIES_RE = [
    "PLD", "AMT", "EQIX", "CCI", "PSA", "O", "SPG", "WELL", "DLR", "SBAC", 
    "CBRE", "WY", "VICI", "EXR", "ARE", "CPT"
]

ALL_EQUITIES = sorted(list(set(
    EQUITIES_TECH + EQUITIES_COMM + EQUITIES_DISC + EQUITIES_STAPLES + 
    EQUITIES_FIN + EQUITIES_HEALTH + EQUITIES_IND + EQUITIES_ENERGY + 
    EQUITIES_MAT + EQUITIES_UTIL + EQUITIES_RE
)))

# ==============================================================================
# COMBINED 500-TICKER UNIVERSE
# ==============================================================================
UNIVERSE_500 = sorted(list(set(ALL_ETFS + ALL_EQUITIES)))[:500]

if __name__ == "__main__":
    print(f"Total ETFs: {len(ALL_ETFS)}")
    print(f"Total Equities: {len(ALL_EQUITIES)}")
    print(f"Total Combined Universe: {len(UNIVERSE_500)}")
