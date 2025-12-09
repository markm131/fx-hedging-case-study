# main.py

from config import CASH_FLOWS
from src.hedging import CollarHedge, ForwardHedge, OptionHedge
from src.metrics import calculate_metrics
from src.simulation import run_baseline_scenario


def main():
    print("\nRunning FX hedging analysis...")

    fx_scenarios, unhedged_stats, spot_rate, atm_vols = run_baseline_scenario()
    
    forward_hedge = ForwardHedge(spot_rate, CASH_FLOWS)
    option_hedge = OptionHedge(spot_rate, atm_vols, CASH_FLOWS)
    collar_hedge = CollarHedge(spot_rate, atm_vols, CASH_FLOWS)

    fwd_npv = forward_hedge.hedge(fx_scenarios)
    opt_npv = option_hedge.hedge(fx_scenarios)
    col_npv = collar_hedge.hedge(fx_scenarios)

    fwd_metrics = calculate_metrics(fwd_npv)
    opt_metrics = calculate_metrics(opt_npv)
    col_metrics = calculate_metrics(col_npv)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print("\nUnhedged:")
    for metric, value in unhedged_stats.items():
        print(f"  {metric}: ${value:,.0f}")

    print("\nForward Hedge:")
    for metric, value in fwd_metrics.items():
        print(f"  {metric}: ${value:,.0f}")
    print(f"  hedge_cost: ${forward_hedge.total_cost:,.0f}")

    print("\nPut Options:")
    for metric, value in opt_metrics.items():
        print(f"  {metric}: ${value:,.0f}")
    print(f"  hedge_cost: ${option_hedge.premium_paid:,.0f}")

    print("\nCollar:")
    for metric, value in col_metrics.items():
        print(f"  {metric}: ${value:,.0f}")
    print(f"  hedge_cost: ${collar_hedge.net_cost:,.0f}")

    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)

    base_std = unhedged_stats["std"]
    print("\nVolatility reduction:")
    print(f"  Forward: {(1 - fwd_metrics['std'] / base_std) * 100:.1f}%")
    print(f"  Options: {(1 - opt_metrics['std'] / base_std) * 100:.1f}%")
    print(f"  Collar: {(1 - col_metrics['std'] / base_std) * 100:.1f}%")

    base_var = unhedged_stats["var_95"]
    print("\nVaR 95% improvement:")
    print(f"  Forward: ${fwd_metrics['var_95'] - base_var:,.0f}")
    print(f"  Options: ${opt_metrics['var_95'] - base_var:,.0f}")
    print(f"  Collar: ${col_metrics['var_95'] - base_var:,.0f}")

    print("\n")


if __name__ == "__main__":
    main()
