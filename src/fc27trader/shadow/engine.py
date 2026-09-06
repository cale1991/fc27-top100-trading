"""Shadow portfolio state machine.

Rules:
- decision/prediction rows are immutable;
- fills may only reference market observations strictly after the decision timestamp;
- every fill stores the exact market snapshot used;
- realized P/L includes EA tax and simulated slippage;
- no backfilling a better price after a later observation is known.
"""
