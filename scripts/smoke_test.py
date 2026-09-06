from fc27trader.collectors.restricted import RESTRICTED_AUTOMATED_SOURCES
from fc27trader.features.definitions import PREDICTION_HORIZONS_SECONDS
from fc27trader.shadow.rules import price_tick

assert PREDICTION_HORIZONS_SECONDS["7d"] == 604800
assert price_tick(50_000) == 250
assert price_tick(50_001) == 500
assert "futbin" in RESTRICTED_AUTOMATED_SOURCES
print("smoke test passed")
