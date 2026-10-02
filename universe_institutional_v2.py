"""
Institutional Universe Version 2 (ORB-15 Cond 4 V2)
===================================================
Forensically Audited across 459 1-minute assets (2003 - 2026).
- Vetted Momentum Universe: 43 Assets
- Alpha Superstars (Core Priority): 2 Assets
- Confirmed Toxic Blacklist: 228 Assets
"""

ALPHA_SUPERSTARS = ['MRNA', 'RBLX']

VETTED_INSTITUTIONAL_UNIVERSE = ['AA', 'ABNB', 'ALB', 'AMD', 'AMZN', 'BSX', 'CARR', 'CBRE', 'CHTR', 'CMG', 'CNC', 'DOW', 'EFX', 'EXPD', 'F', 'FAST', 'FSLY', 'HIG', 'HUM', 'IAI', 'ILMN', 'INCY', 'IWV', 'LEN', 'LYV', 'MO', 'MRNA', 'NFLX', 'NVDA', 'NWSA', 'PTON', 'RBLX', 'REM', 'SIRI', 'SPOT', 'STZ', 'TAP', 'TMUS', 'TSLA', 'TSN', 'TWLO', 'WMB', 'WY']

TOXIC_BLACKLIST = set(['A', 'AAL', 'ABBV', 'ABT', 'ADI', 'AEP', 'AFL', 'AJG', 'ALGN', 'AMCR', 'AMGN', 'AMP', 'AMT', 'ANET', 'AON', 'APA', 'APTV', 'ARE', 'AWK', 'BAC', 'BAX', 'BDX', 'BMY', 'BNY', 'BP', 'BRO', 'C', 'CAG', 'CAH', 'CCI', 'CF', 'CFG', 'CHD', 'CHRW', 'CINF', 'CL', 'CLX', 'COF', 'COIN', 'COST', 'CPB', 'CPER', 'CSCO', 'CTAS', 'CTVA', 'CVX', 'DAL', 'DASH', 'DBA', 'DDOG', 'DE', 'DG', 'DHR', 'DIS', 'DLR', 'DLTR', 'DOCU', 'DTE', 'DUK', 'ECL', 'ED', 'EIX', 'EMR', 'EQIX', 'ESTC', 'ETN', 'EW', 'EWC', 'EWH', 'EWT', 'EWU', 'EWW', 'EXPE', 'EXR', 'FCX', 'FE', 'FITB', 'FOX', 'FXI', 'GDX', 'GIS', 'GLD', 'GM', 'GOOG', 'GPC', 'GS', 'GTLB', 'HBAN', 'HD', 'HLT', 'HON', 'HPE', 'HSY', 'IAK', 'IBM', 'IDXX', 'IGE', 'IHF', 'IHI', 'IJR', 'INTU', 'IQV', 'ITW', 'IVV', 'IVZ', 'IWM', 'IYT', 'JBHT', 'JNJ', 'JPM', 'KBE', 'KEY', 'KMB', 'KO', 'KR', 'KRE', 'LIN', 'LLY', 'LMT', 'LOW', 'MCD', 'MCK', 'MDLZ', 'MDT', 'MDY', 'MET', 'MLM', 'MMM', 'MOO', 'MOS', 'MPC', 'MRK', 'MRVL', 'MS', 'MTB', 'MU', 'NCLH', 'NEM', 'NET', 'NKE', 'NOW', 'NSC', 'NTNX', 'NTRS', 'NUE', 'NWS', 'O', 'ODFL', 'OKTA', 'OMC', 'ORCL', 'ORLY', 'PEG', 'PEJ', 'PEP', 'PG', 'PGR', 'PHM', 'PINS', 'PLD', 'PLTR', 'PM', 'PNC', 'PPG', 'PPL', 'PRU', 'PSA', 'PSX', 'PWR', 'RF', 'RMD', 'ROP', 'ROST', 'RSG', 'SBAC', 'SHW', 'SJM', 'SLB', 'SLV', 'SO', 'SOFI', 'SPG', 'SPGI', 'SRE', 'STE', 'SYK', 'SYY', 'TEAM', 'TECH', 'TFC', 'TGT', 'TJX', 'TLT', 'TSCO', 'TXN', 'UAL', 'ULTA', 'UNH', 'UNP', 'UPS', 'URI', 'USB', 'USO', 'V', 'VICI', 'VTRS', 'VZ', 'WEC', 'WELL', 'WM', 'WST', 'WTW', 'XBI', 'XEL', 'XLB', 'XLE', 'XLF', 'XLK', 'XLU', 'XLV', 'XLY', 'XME', 'XOM', 'XOP', 'XRT', 'XYL', 'YUM', 'ZS'])

def is_tradable_asset(symbol: str) -> bool:
    """Returns True if asset is in the vetted institutional universe and not blacklisted."""
    sym = symbol.upper().replace("-", "_")
    if sym in TOXIC_BLACKLIST:
        return False
    return sym in VETTED_INSTITUTIONAL_UNIVERSE
