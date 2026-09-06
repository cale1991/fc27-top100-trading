# Shadow Trading Execution Contract

Reference price != achievable acquisition price.

## Buy path A — execution observation
A later trusted/manual PC execution observation may fill only if its actual listing price remains within the order limit after conservative slippage.

## Buy path B — learned acquisition search
If only a reference anchor exists, shadow execution uses empirical undercut distributions segmented by card/price tier/category/liquidity/time/regime/content timing/volatility. It models acquisition probability, delay, available quantity and expected acquisition price. No universal undercut percentage is encoded.

Older/less reliable reference anchors reduce execution quality/fill probability. They do not become fills by themselves.

## Sell path
Requires later confirming market evidence, realistic competitiveness and EA tax.

`shadow_execution_attempts` records signal-quality and execution-quality scores separately, plus reference/execution provenance, modeled probability, delay, quantity and outcome.
