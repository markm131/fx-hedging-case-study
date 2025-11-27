# data_loader.py

from pathlib import Path

import pandas as pd


def load_market_data(filepath: Path) -> pd.DataFrame:
    """Load EUR-USD market data"""

    df = pd.read_excel(filepath, header=None, skiprows=6)

    # Multi-row headers present in Excel with duplicate column names
    # Using position index to extract needed columns

    data = pd.DataFrame(
        {
            "date": pd.to_datetime(df[0]),
            "spot": df[3],
            "vol_1y_atm": df[6],
            "vol_1y_25d_rr": df[9],
            "vol_1y_25d_bf": df[12],
            "vol_5y_atm": df[15],
            "vol_5y_25d_rr": df[18],
            "vol_5y_25d_bf": df[21],
        }
    )

    # We need complete data so we delete entire row if any rates are missing
    data = data.dropna().set_index("date").sort_index()

    return data

if __name__ == "__main__":
    data_file = (
        Path(__file__).parent.parent
        / "data"
        / "QuantResearch-CaseStudy-MarketData-25.xlsx"
    )
    df = load_market_data(data_file)
    print(f"Loaded {len(df)} rows from Excel file")
    print(df.head())
