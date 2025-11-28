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

## Approach

### Performance Metrics

I use NPV as the primary performance metric, measuring present value of EUR cash flows converted to USD and discounted using the USD yield curve. Risk is quantified through:

- Standard deviation (volatility of outcomes)
- Value at Risk (95%, 99%) - worst-case losses at given confidence levels
- Conditional VaR (95%, 99%) - expected loss in tail scenarios

### FX Risk Impact

The fund has long EUR exposure - EUR depreciation against USD reduces fund value. With €4M net inflows over 5 years, even a 10% EUR decline costs ~$400k in NPV. Volatility around 6-7% creates significant uncertainty in final outcomes.

### Model Choice

I chose Heston stochastic volatility over simpler alternatives like GBM because:

- Captures time-varying volatility observed in FX markets
- Calibrates directly to market data (1Y and 5Y ATM implied vols)
- Consistent with academic research on FX dynamics
- My thesis work was on stochastic volatility modeling so I'm familiar with implementation

Parameters calibrated by minimizing squared errors to market ATM vol surface.

### Hedging Strategies

I implemented three strategies covering the spectrum from full protection to cost-efficient compromise:

**Forward Contracts**

- Lock in forward rates for all EUR inflows
- Zero premium cost
- Complete FX risk elimination
- Sacrifices upside if EUR strengthens

**Put Options (ATM)**

- Buy puts at current spot for all inflows
- Downside protection while keeping upside participation
- Expensive premium (~$577k)
- Best if expecting EUR appreciation

**Collar (95% put / 105% call)**

- Buy OTM put for protection, sell OTM call to offset cost
- Net premium received (~$684k) due to USD/EUR rate differential
- Balanced risk/reward - some protection, some upside
- Most practical for corporate treasuries

The choice between strategies depends on risk tolerance and market view. Forwards eliminate uncertainty entirely but give up potential gains. Options provide asymmetric payoffs but at significant cost. Collars offer a middle ground.

## Results & Recommendation

Unhedged volatility is ~\$4.2M with VaR 95% of -$3.6M. All hedging strategies significantly reduce risk:

- **Forward:** 82.9% volatility reduction, eliminates downside
- **Put Options:** 34.3% reduction, preserves most upside
- **Collar:** 80.0% reduction, caps upside at 105% of spot

**Recommendation:** I would choose the collar strategy. It provides substantial risk reduction (80%) at negative net cost (we receive $684k premium due to the USD/EUR rate differential). While it caps upside at the call strike, the protection against EUR weakness and the premium received make it the most attractive risk-adjusted outcome. The forward eliminates slightly more risk but foregoes all upside potential.

## Key Assumptions

- 10,000 Monte Carlo simulations
- Daily time steps (252 per year)
- Continuous compounding for discounting
- USD and EUR yield curves interpolated from market data (Aug 1, 2025)
- Black-Scholes pricing for options (assumes constant vol, no jumps)
- No transaction costs or bid-ask spreads
- Forwards priced via covered interest rate parity

## Project Structure

```
src/
  data_loader.py    - Load market data from Excel
  models.py         - Heston calibration and simulation
  metrics.py        - NPV and risk calculations
  hedging.py        - Hedge strategy implementations
  simulation.py     - Monte Carlo orchestration
  utils.py          - Rate interpolation
main.py             - Run analysis and print results
config.py           - Parameters and constants
```

## Time Spent

2 days