# models.py

import numpy as np
from datetime import date
from scipy.optimize import minimize
from config import ANALYSIS_DATE, N_SIMS, RANDOM_SEED


def simulate_heston_paths(spot: float, v0: float, kappa: float, theta: float, 
                          xi: float, rho: float, r_domestic: float, r_foreign: float,
                          years: float, dt: float = 1/252) -> tuple[np.ndarray, np.ndarray]:
    """Simulate FX and variance paths using Heston stochastic volatility model"""
    rng = np.random.default_rng(RANDOM_SEED)

    steps = int(years / dt)
    spot_paths = np.zeros((steps + 1, N_SIMS))
    var_paths = np.zeros((steps + 1, N_SIMS))
    
    spot_paths[0] = spot
    var_paths[0] = v0
    
    for i in range(1, steps + 1):
        z1 = rng.normal(0, 1, N_SIMS)
        z2 = rng.normal(0, 1, N_SIMS)
        
        dw_spot = z1
        dw_var = rho * z1 + np.sqrt(1 - rho**2) * z2
        
        var_pos = np.maximum(var_paths[i-1], 0)
        
        drift = (r_domestic - r_foreign - 0.5 * var_pos) * dt
        diffusion = np.sqrt(var_pos * dt) * dw_spot
        spot_paths[i] = spot_paths[i-1] * np.exp(drift + diffusion)
        
        var_paths[i] = var_paths[i-1] + kappa * (theta - var_pos) * dt + xi * np.sqrt(var_pos * dt) * dw_var
    
    return spot_paths, var_paths


def heston_atm_vol(v0: float, kappa: float, theta: float, xi: float, rho: float, years: float) -> float:
    """Calculate ATM implied volatility under Heston model"""
    term1 = v0 * (1 - np.exp(-kappa * years)) / (kappa * years)
    term2 = theta * (1 - (1 - np.exp(-kappa * years)) / (kappa * years))
    return np.sqrt(term1 + term2)


def calibrate_heston_to_atm(spot: float, atm_vols: dict[float, float], 
                            r_domestic: float, r_foreign: float) -> dict[str, float]:
    """Calibrate Heston parameters to ATM volatility term structure"""
    
    maturities = list(atm_vols.keys())
    market_vols = list(atm_vols.values())
    
    def objective(params: np.ndarray) -> float:
        v0, kappa, theta, xi, rho = params
        
        if v0 <= 0 or theta <= 0 or xi <= 0 or kappa <= 0:
            return 1e10
        if abs(rho) >= 1:
            return 1e10
        if 2 * kappa * theta < xi**2:
            return 1e10
        
        model_vols = [heston_atm_vol(v0, kappa, theta, xi, rho, T) for T in maturities]
        return np.sum((np.array(model_vols) - np.array(market_vols))**2)
    
    initial = [0.04, 2.0, 0.04, 0.3, -0.7]
    bounds = [(0.001, 0.5), (0.1, 10), (0.001, 0.5), (0.01, 2), (-0.99, 0.99)]
    
    result = minimize(objective, initial, method='L-BFGS-B', bounds=bounds)
    
    v0, kappa, theta, xi, rho = result.x
    
    return {'v0': v0, 'kappa': kappa, 'theta': theta, 'xi': xi, 'rho': rho}


def simulate_fx_for_dates(spot: float, params: dict[str, float], r_domestic: float, 
                          r_foreign: float, dates: list[date]) -> dict[date, np.ndarray]:
    """Generate Heston FX paths and extract rates at specified dates"""
    
    max_years = max((d - ANALYSIS_DATE).days / 365.0 for d in dates)
    
    spot_paths, _ = simulate_heston_paths(
        spot, params['v0'], params['kappa'], params['theta'], 
        params['xi'], params['rho'], r_domestic, r_foreign, max_years
    )
    
    fx_rates = {}
    dt = 1/252
    
    for target_date in dates:
        days = (target_date - ANALYSIS_DATE).days
        step = int(days / 365.0 / dt)
        fx_rates[target_date] = spot_paths[step]
    
    return fx_rates


if __name__ == "__main__":
    from data_loader import load_market_data
    from config import MARKET_DATA_FILE
    import pandas as pd
    
    data = load_market_data(MARKET_DATA_FILE)
    today = data.loc[pd.Timestamp(ANALYSIS_DATE)]
    
    spot = today['spot']
    vols = {1.0: today['vol_1y_atm'] / 100, 5.0: today['vol_5y_atm'] / 100}
    
    print("Calibrating Heston...")
    params = calibrate_heston_to_atm(spot, vols, 0.04, 0.025)
    
    print("\nCalibrated parameters:")
    for k, v in params.items():
        print(f"  {k}: {v:.6f}")