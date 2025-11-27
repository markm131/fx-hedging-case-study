# config.py

from pathlib import Path
from datetime import date

PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
MARKET_DATA_FILE = DATA_DIR / "QuantResearch-CaseStudy-MarketData-25.xlsx"

ANALYSIS_DATE = date(2025, 8, 1)

BASE_CURRENCY = "EUR"
QUOTE_CURRENCY = "USD"
FX_PAIR = f"{BASE_CURRENCY}{QUOTE_CURRENCY}"

CASH_FLOWS = [
    (date(2025, 10, 1), -10_000_000),
    (date(2026, 10, 1),   1_000_000),
    (date(2027, 10, 1),   1_000_000),
    (date(2029, 10, 1),   1_000_000),
    (date(2030, 10, 1),  11_000_000),
]

N_SIMS = 10_000

# USD yield curve (as of Aug 1, 2025)
USD_RATES = {
    0.25: 0.0435,  # DGS3MO
    1.0: 0.0387,  # DGS1
    2.0: 0.0369,  # DGS2
    5.0: 0.0377,  # DGS5
    10.0: 0.0423,  # DGS10
}

EUR_RATES = {
    0.25: 0.0200,  # 3M - ECB deposit facility rate
    1.0:  0.0210,  # 1Y
    2.0:  0.0223,  # 2Y - derived from 10Y/2Y spread
    5.0:  0.0250,  # 5Y - interpolated
    10.0: 0.0278,  # 10Y - market data
}