"""Global neural temporal model contract.

Training intentionally waits for the RTX 5080 worker. The implementation is global across cards,
not one network per card: card/version embeddings + temporal market features + event/regime/context
features feed shared temporal blocks and multi-head targets for sell price, profitable exit,
time-to-sale, downside and acquisition/execution outcomes.

The 24/7 cloud system only consumes exported artifacts; it never depends on the RTX machine being on.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GlobalTemporalModelConfig:
    card_embedding_dim: int = 64
    hidden_dim: int = 256
    layers: int = 4
    dropout: float = 0.1
    context_steps: int = 180
    horizons_seconds: tuple[int, ...] = (300, 900, 3600, 10800, 21600, 86400, 259200, 604800)


def requires_rtx_worker() -> bool:
    return True
