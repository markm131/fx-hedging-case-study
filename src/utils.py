# utils.py

import numpy as np


def interpolate_rate(maturity: float, rate_curve: dict[float, float]) -> float:
    """Interpolate interest rate from yield curve for given maturity in years"""
    maturities = list(rate_curve.keys())
    rates = list(rate_curve.values())
    return np.interp(maturity, maturities, rates)