# hedging.py

from datetime import date

import numpy as np
from scipy.stats import norm

from config import ANALYSIS_DATE, EUR_RATES, N_SIMS, USD_RATES
from src.metrics import calculate_npv
from src.utils import interpolate_rate


def black_scholes_price(
    rate_spot: float,
    K: float,
    T: float,
    domestic_rate: float,
    foreign_rate: float,
    sigma: float,
    option_type: str,
) -> float:
    """Black-Scholes price for FX options"""
    d1 = (
        np.log(rate_spot / K) + (domestic_rate - foreign_rate + 0.5 * sigma**2) * T
    ) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == "call":
        return rate_spot * np.exp(-foreign_rate * T) * norm.cdf(d1) - K * np.exp(
            -domestic_rate * T
        ) * norm.cdf(d2)
    else:
        return K * np.exp(-domestic_rate * T) * norm.cdf(-d2) - rate_spot * np.exp(
            -foreign_rate * T
        ) * norm.cdf(-d1)


class ForwardHedge:
    """Lock in forward FX rates for EUR inflows"""

    def __init__(self, spot_rate: float, cf_schedule: list[tuple[date, float]]):
        self.spot_rate = spot_rate
        self.cf_schedule = cf_schedule
        self.locked_rates = {}
        self.total_cost = 0

        for cf_date, eur_notional in cf_schedule:
            if eur_notional > 0:
                maturity = (cf_date - ANALYSIS_DATE).days / 365.25
                usd_rate = interpolate_rate(maturity, USD_RATES)
                eur_rate = interpolate_rate(maturity, EUR_RATES)
                self.locked_rates[cf_date] = spot_rate * np.exp(
                    (usd_rate - eur_rate) * maturity
                )

    def hedge(self, fx_paths: dict[date, np.ndarray]) -> np.ndarray:
        """Replace simulated rates with locked forward rates"""
        hedged_paths = {}
        for cf_date in fx_paths.keys():
            if cf_date in self.locked_rates:
                hedged_paths[cf_date] = np.full(N_SIMS, self.locked_rates[cf_date])
            else:
                hedged_paths[cf_date] = fx_paths[cf_date]

        return calculate_npv(hedged_paths, self.cf_schedule)


class OptionHedge:
    """Buy ATM put options on EUR inflows"""

    def __init__(
        self,
        fx_spot: float,
        vol_surface: dict[float, float],
        payment_schedule: list[tuple[date, float]],
    ):
        self.fx_spot = fx_spot
        self.vol_surface = vol_surface
        self.payment_schedule = payment_schedule
        self.premium_paid = 0

        for flow_date, eur_amount in payment_schedule:
            if eur_amount > 0:
                tenor = (flow_date - ANALYSIS_DATE).days / 365.25
                r_usd = interpolate_rate(tenor, USD_RATES)
                r_eur = interpolate_rate(tenor, EUR_RATES)
                volatility = self._get_vol(tenor)

                option_premium = black_scholes_price(
                    fx_spot, fx_spot, tenor, r_usd, r_eur, volatility, "put"
                )
                self.premium_paid += eur_amount * option_premium

    def _get_vol(self, time_to_maturity: float) -> float:
        tenors = list(self.vol_surface.keys())
        vols = []
        for tenor in tenors:
            vols.append(self.vol_surface[tenor])
        return np.interp(time_to_maturity, tenors, vols)

    def hedge(self, simulated_fx: dict[date, np.ndarray]) -> np.ndarray:
        """Apply put option protection to FX exposure"""
        present_value = np.zeros(N_SIMS)

        for flow_date, eur_amount in self.payment_schedule:
            fx_rates = simulated_fx[flow_date]

            if eur_amount > 0:
                protected_fx = np.maximum(fx_rates, self.fx_spot)
                usd_proceeds = eur_amount * protected_fx
            else:
                usd_proceeds = eur_amount * fx_rates

            tenor = (flow_date - ANALYSIS_DATE).days / 365.25
            discount_rate = interpolate_rate(tenor, USD_RATES)
            discount_factor = np.exp(-discount_rate * tenor)

            present_value += usd_proceeds * discount_factor

        return present_value - self.premium_paid


class CollarHedge:
    """Buy OTM put and sell OTM call on EUR inflows"""

    def __init__(
        self,
        current_spot: float,
        market_vols: dict[float, float],
        cash_flows: list[tuple[date, float]],
        put_level: float = 0.95,
        call_level: float = 1.05,
    ):
        self.current_spot = current_spot
        self.market_vols = market_vols
        self.cash_flows = cash_flows
        self.put_strike = current_spot * put_level
        self.call_strike = current_spot * call_level
        self.net_cost = 0

        for payment_date, notional in cash_flows:
            if notional > 0:
                years_to_expiry = (payment_date - ANALYSIS_DATE).days / 365.25
                domestic_r = interpolate_rate(years_to_expiry, USD_RATES)
                foreign_r = interpolate_rate(years_to_expiry, EUR_RATES)
                implied_vol = self._interpolate_volatility(years_to_expiry)

                put_cost = black_scholes_price(
                    current_spot,
                    self.put_strike,
                    years_to_expiry,
                    domestic_r,
                    foreign_r,
                    implied_vol,
                    "put",
                )
                call_proceeds = black_scholes_price(
                    current_spot,
                    self.call_strike,
                    years_to_expiry,
                    domestic_r,
                    foreign_r,
                    implied_vol,
                    "call",
                )

                net_premium = put_cost - call_proceeds
                self.net_cost += abs(notional) * net_premium

    def _interpolate_volatility(self, maturity: float) -> float:
        maturities = list(self.market_vols.keys())
        volatilities = []
        for m in maturities:
            volatilities.append(self.market_vols[m])
        return np.interp(maturity, maturities, volatilities)

    def hedge(self, fx_scenarios: dict[date, np.ndarray]) -> np.ndarray:
        """Apply collar protection to FX exposure"""
        npv_result = np.zeros(N_SIMS)

        for payment_date, notional in self.cash_flows:
            scenario_rates = fx_scenarios[payment_date]

            if notional > 0:
                collared_fx = np.clip(scenario_rates, self.put_strike, self.call_strike)
                usd_converted = notional * collared_fx
            else:
                usd_converted = notional * scenario_rates

            years_to_expiry = (payment_date - ANALYSIS_DATE).days / 365.25
            disc_rate = interpolate_rate(years_to_expiry, USD_RATES)
            pv_factor = np.exp(-disc_rate * years_to_expiry)

            npv_result += usd_converted * pv_factor

        return npv_result - self.net_cost


if __name__ == "__main__":
    from config import CASH_FLOWS

    test_spot = 1.10
    test_vols = {1.0: 0.06, 5.0: 0.07}

    forward = ForwardHedge(test_spot, CASH_FLOWS)
    puts = OptionHedge(test_spot, test_vols, CASH_FLOWS)
    collar = CollarHedge(test_spot, test_vols, CASH_FLOWS)

    print(f"Forward hedge cost: ${forward.total_cost:,.0f}")
    print(f"Option hedge cost: ${puts.premium_paid:,.0f}")
    print(f"Collar hedge cost: ${collar.net_cost:,.0f}")
