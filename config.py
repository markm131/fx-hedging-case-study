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