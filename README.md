# FX Hedging Case Study

Monte Carlo analysis of FX hedging strategies for a USD-denominated private credit fund with EUR cash flows.

## Setup

Python 3.9+

```bash
pip install -r requirements.txt
```

## Running

```bash
python main.py
```

---

## Problem

A USD-denominated private credit fund invests in EUR assets:

| Date     | Cash Flow (EUR)                  |
| -------- | -------------------------------- |
| Oct 2025 | -10,000,000 (invest)             |
| Oct 2026 | +1,000,000                       |
| Oct 2027 | +1,000,000                       |
| Oct 2029 | +1,000,000                       |
| Oct 2030 | +11,000,000 (return + principal) |

**The risk:** EUR weakens → EUR inflows convert to fewer USD → fund underperforms.

**Decision:** Hedge the inflows only. The initial outflow is 2 months away (minimal exposure) and has opposite FX sensitivity.

---

## Approach

### Performance Metric: NPV

> **Decision:** NPV puts all cash flows on common footing (today's USD). Allows direct comparison across strategies.

Risk quantified through:
- Standard deviation (volatility of outcomes)
- VaR 95%/99% (worst-case threshold)
- CVaR 95%/99% (expected loss in tail - coherent risk measure, captures severity beyond VaR)

---

### Model Choice: Heston Stochastic Volatility

> **Decision:** Heston captures realistic time-varying volatility. My thesis was on Heston calibration - I know its strengths and pitfalls.

> **Simplification:** Calibrated to ATM vols only (1Y, 5Y). The RR/BF data would enable full smile calibration, but significantly increases complexity. For 95%/105% collar strikes, smile effect is second-order.

> **Fixed parameters:** ρ = -0.7 (negative - vol rises when spot falls), ξ = 0.3 (vol of vol). Not identified from ATM data alone.

---

### Data Sources

| Input                  | Source                                               |
| ---------------------- | ---------------------------------------------------- |
| Spot, ATM vols, RR, BF | Provided Excel file                                  |
| USD rates              | Treasury FRED API                                    |
| EUR rates              | 10Y German Bund, 10Y/2Y spread, ECB 3M, interpolated |

> **Production improvement:** Use OIS curves for discounting.

---

## Hedging Strategies

### 1. Forward Contracts
- Lock in forward rate for each inflow
- Zero premium
- Eliminates FX risk entirely
- **Trade-off:** No upside if EUR strengthens

### 2. Put Options (ATM)
- Buy puts at current spot
- Downside protection, uncapped upside
- **Trade-off:** Expensive premium (~$577k)

### 3. Collar (95% put / 105% call)
- Buy 95% put, sell 105% call
- Net premium **received** (~$683k)
- **Trade-off:** Upside capped at 105%

> **Why receive premium?** USD rates > EUR rates → forward > spot → 105% call is closer to ATM-forward than 95% put. Selling the more valuable option.

---

## Results

### Unhedged Baseline

| Metric   | Value       |
| -------- | ----------- |
| Mean NPV | $2,921,508  |
| Std Dev  | $4,153,349  |
| VaR 95%  | -$3,466,342 |
| CVaR 95% | -$4,855,114 |

**Interpretation:** Huge uncertainty. 5% chance of losing \$3.5M+. When it goes wrong, average loss is \$4.9M.

---

### Strategy Comparison

| Metric              | Forward        | Put Options    | Collar         |
| ------------------- | -------------- | -------------- | -------------- |
| Mean NPV            | $2,941,985     | $3,738,959     | $2,878,964     |
| Std Dev             | $712,620       | $2,795,677     | $826,552       |
| VaR 95%             | $1,896,904     | $934,360       | $1,538,564     |
| CVaR 95%            | $1,668,931     | $680,844       | $1,275,497     |
| Hedge Cost          | $0             | $576,954       | -$683,264      |
| **Vol Reduction**   | **82.8%**      | **32.7%**      | **80.1%**      |
| **VaR Improvement** | **$5,363,246** | **$4,400,702** | **$5,004,906** |

---

### Key Observations

**Forward:**
- Near-complete risk elimination (82.8%)
- Residual variance from unhedged initial outflow
- Locks in rate - no participation if EUR rallies

**Put Options:**
- Highest mean ($3.74M) - uncapped upside, floored downside
- Still high variance (32.7% reduction only)
- Expensive: $577k premium

**Collar:**
- Nearly matches forward on risk (80.1% reduction)
- **Receives** $683k premium
- Caps upside at 105%, floors downside at 95%

---

## Recommendation: Forward

| Reason         | Detail                                         |
| -------------- | ---------------------------------------------- |
| Risk reduction | 82.8% vol reduction - best of all strategies   |
| VaR 95%        | $1.90M - best worst-case outcome               |
| CVaR 95%       | $1.67M - best tail performance                 |
| Cost           | Zero upfront premium                           |
| Simplicity     | Lock in forward rate, no optionality to manage |

The forward eliminates FX risk on all inflows by locking in the forward rate (above spot due to USD/EUR rate differential).

> **When to choose collar instead:** If the fund wants upfront cash ($683k) or has a bullish EUR view. But on pure risk metrics, forward wins.

> **When to choose puts  instead:** If strongly bullish EUR but wanting protection. Highest mean but expensive and still volatile.

## Limitations & Extensions

| Simplification               | Improvement                                                  |
| ---------------------------- | ------------------------------------------------------------ |
| ATM-only calibration         | Use RR/BF → 6 calibration points → properly identify ρ and ξ |
| Black-Scholes option pricing | Price OTM options with calibrated Heston surface             |
| Constant rates in simulation | Interpolate rates at each time step                          |
| No transaction costs         | Include bid-ask spreads                                      |

---

## Key Assumptions

- 10,000 Monte Carlo simulations (seeded for reproducibility)
- Daily time steps (252 per year)
- Continuous compounding
- Initial EUR outflow unhedged (2 months, minimal exposure)
- Forwards priced via covered interest rate parity

---

## Project Structure

```
config.py           - Cash flows, rates, parameters
src/
  data_loader.py    - Load market data from Excel
  models.py         - Heston calibration and simulation
  metrics.py        - NPV, VaR, CVaR calculations
  hedging.py        - Forward, Option, Collar strategies
  simulation.py     - Monte Carlo orchestration
  utils.py          - Rate interpolation
main.py             - Run analysis and print results
```

## Time Spent

2 days