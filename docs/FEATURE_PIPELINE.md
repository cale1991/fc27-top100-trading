# Feature Pipeline

1. Immutable raw capture.
2. Normalize cards/content/general market data.
3. Classify market value inputs into reference, execution, or historical/context semantics.
4. Build point-in-time lags, liquidity, event, graph, regime and EA-intervention features.
5. Add reference-quality features: provider age, historical error, stated uncertainty, combined uncertainty and confidence.
6. Add execution features when available: fresh lowest BIN/bid/listing sample, age and reference-vs-execution gap.
7. Acquisition model estimates discount availability probability, acquisition price, search delay and available quantity by card/price tier/category/liquidity/time/regime/content timing/volatility.
8. Broad observable market is scored; only strong current candidates proceed to execution verification.
9. Feature/training rows retain source cutoff timestamps to prevent lookahead.

The fixed 50-card provider basket is not part of production feature candidate selection.
