# metrics.py

from datetime import date

import numpy as np

from config import ANALYSIS_DATE, N_SIMS
from src.utils import interpolate_rate


def calculate_npv(
    simulated_fx: dict[date, np.ndarray], cash_flows: list[tuple[date, float]]
) -> np.ndarray:
    """Calculate net present values for cashflows across simulated fx rates"""

    npv = np.zeros(N_SIMS)

    for cf_date, eur_amount in cash_flows:
        fx_rates = simulated_fx[cf_date]
        usd_amount = eur_amount * fx_rates

        years = (cf_date - ANALYSIS_DATE).days / 365.0
        rate = interpolate_rate(years)  # Get rate for this maturity
        discount_factor = np.exp(-rate * years)

        npv += usd_amount * discount_factor

    return npv


def calculate_var(npv_distribution: np.ndarray, confidence: float = 0.95) -> float:
    """Calculate Value at Risk at specified confidence level"""
    return np.percentile(npv_distribution, (1 - confidence) * 100)


def calculate_cvar(npv_distribution: np.ndarray, confidence: float = 0.95) -> float:
    """Calculate Conditional VaR (Expected Shortfall) at specified confidence level"""
    var_threshold = calculate_var(npv_distribution, confidence)
    return npv_distribution[npv_distribution <= var_threshold].mean()


def calculate_metrics(npv_distribution: np.ndarray) -> dict[str, float]:
    """Calculate comprehensive risk metrics for NPV distribution"""
    return {
        "mean": np.mean(npv_distribution),
        "median": np.median(npv_distribution),
        "std": np.std(npv_distribution),
        "var_95": calculate_var(npv_distribution, 0.95),
        "var_99": calculate_var(npv_distribution, 0.99),
        "cvar_95": calculate_cvar(npv_distribution, 0.95),
        "cvar_99": calculate_cvar(npv_distribution, 0.99),
    }


if __name__ == "__main__":
    from config import CASH_FLOWS  # Only need CASH_FLOWS here

    dummy_fx = {
        date(2025, 10, 1): np.random.normal(1.10, 0.05, N_SIMS),  # Just use N_SIMS
        date(2026, 10, 1): np.random.normal(1.12, 0.06, N_SIMS),
        date(2027, 10, 1): np.random.normal(1.15, 0.07, N_SIMS),
        date(2029, 10, 1): np.random.normal(1.18, 0.08, N_SIMS),
        date(2030, 10, 1): np.random.normal(1.20, 0.09, N_SIMS),
    }

    npv_dist = calculate_npv(dummy_fx, CASH_FLOWS)
    metrics = calculate_metrics(npv_dist)

    print("NPV Distribution Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: ${value:,.0f}")
