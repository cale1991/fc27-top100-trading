# Model Training and Evaluation Structure

Model families map one-to-one to modules in `src/fc27trader/models/`:

- `structured.py` — LightGBM/XGBoost.
- `neural_global.py` — one global neural time-series model across cards, not one network per card.
- `event_response.py` — content shock response.
- `liquidity.py` — fill probability, time-to-sale, capacity.
- `anomaly.py` — mispricing/anomaly detection.
- `regime.py` — market-regime detection.
- `ea_intervention.py` — documented EA supply/demand/substitute/price-range risk.
- `historical_analogue.py` — normalized prior-cycle analogue retrieval.
- `portfolio.py` — capital allocation by expected net profit/turnover/capacity.
- `ensemble.py` — calibrated combination of independently useful signals.

## Dataset rules

Every training row has a prediction timestamp. Features may only use source data observed/detected at or before that timestamp. Labels are generated later from market observations. No random train/test split; chronological walk-forward folds only.

## Targets

Per horizon (5m, 15m, 1h, 3h, 6h, 24h, 3d, 7d): future executable sell price, profitable-exit probability, expected net profit after tax/slippage, time-to-sale, profit/hour, profit/capital, position capacity, downside risk and catalyst-failure probability.

## Retention gate

A model is kept only when it raises out-of-sample shadow Transfer Profit or supplies independently useful information to the ensemble without unacceptable drawdown/turnover degradation. Calibration and time-to-sale accuracy are secondary diagnostics, not the optimization objective.

## Observation semantics added 2026-09-04

Model inputs must distinguish reference anchors from execution observations. Reference age, provider historical error and uncertainty are explicit features. Acquisition probability/price/delay/quantity is learned separately from reference value; no universal undercut percentage is assumed.

Community/trader intelligence remains an input to candidate scoring (`community_intelligence_score`) and is intended to be calibrated by source/trader accuracy. The public AI trader/X subsystem and anti-AI-slop persona layer remain separate presentation/intelligence subsystems and were not removed by this market-data patch.
