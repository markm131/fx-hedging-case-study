# simulation.py

from datetime import date

import numpy as np
import pandas as pd

from config import ANALYSIS_DATE, CASH_FLOWS, EUR_RATES, MARKET_DATA_FILE, USD_RATES
from src.data_loader import load_market_data
from src.metrics import calculate_metrics, calculate_npv
from src.models import calibrate_heston_to_atm, simulate_fx_for_dates
from src.utils import interpolate_rate


def run_baseline_scenario() -> tuple[dict[date, np.ndarray], dict[str, float]]:
    """Run Monte Carlo simulation for unhedged FX exposure"""

    price_data = load_market_data(MARKET_DATA_FILE)
    market_snapshot = price_data.loc[pd.Timestamp(ANALYSIS_DATE)]

    current_spot = market_snapshot["spot"]
    implied_vols = {
        1.0: market_snapshot["vol_1y_atm"] / 100,
        5.0: market_snapshot["vol_5y_atm"] / 100,
    }

    domestic_rate = interpolate_rate(5.0, USD_RATES)
    foreign_rate = interpolate_rate(5.0, EUR_RATES)

    model_params = calibrate_heston_to_atm(
        current_spot, implied_vols, domestic_rate, foreign_rate
    )

    settlement_dates = [payment_date for payment_date, _ in CASH_FLOWS]
    rate_paths = simulate_fx_for_dates(
        current_spot, model_params, domestic_rate, foreign_rate, settlement_dates
    )

    pv_results = calculate_npv(rate_paths, CASH_FLOWS)
    risk_stats = calculate_metrics(pv_results)

    return rate_paths, risk_stats, current_spot, implied_vols


if __name__ == "__main__":
    fx_scenarios, baseline_metrics = run_baseline_scenario()

    print("\nBaseline Risk Metrics (Unhedged):")
    for metric_name, metric_value in baseline_metrics.items():
        print(f"  {metric_name}: ${metric_value:,.0f}")
