from enum import StrEnum


class Platform(StrEnum):
    PC = "pc"
    CONSOLE = "console"
    SWITCH = "switch"
    UNKNOWN = "unknown"
    ALL = "all"


class MarketSegmentKey(StrEnum):
    PC = "PC"
    PLAYSTATION = "PLAYSTATION"
    CONSOLE_GENERIC = "CONSOLE_GENERIC"
    CONSOLE_SHARED = "CONSOLE_SHARED"
    SWITCH = "SWITCH"
    UNKNOWN = "UNKNOWN"


class ObservationSemantics(StrEnum):
    EXECUTION_OBSERVATION = "EXECUTION_OBSERVATION"
    REFERENCE_PRICE = "REFERENCE_PRICE"
    MARKET_CONTEXT = "MARKET_CONTEXT"
    CONTENT_EVENT = "CONTENT_EVENT"


class DataQualityStatus(StrEnum):
    VALID = "VALID"
    SUSPECT = "SUSPECT"
    QUARANTINED = "QUARANTINED"
    REJECTED_NORMALIZATION = "REJECTED_NORMALIZATION"


class IdentityStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"
    PROBABLE = "PROBABLE"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"


class GapStatus(StrEnum):
    COMPLETE_WINDOW = "COMPLETE_WINDOW"
    POSSIBLE_GAP = "POSSIBLE_GAP"
    CONFIRMED_GAP = "CONFIRMED_GAP"
    UNKNOWN_COVERAGE = "UNKNOWN_COVERAGE"


class ProviderAccessMode(StrEnum):
    FULL_UNIVERSE = "FULL_UNIVERSE"
    HOT_SET = "HOT_SET"
    WATCH_SET = "WATCH_SET"
    EVENT_TRIGGERED = "EVENT_TRIGGERED"
    ON_DEMAND = "ON_DEMAND"


class EvidenceClass(StrEnum):
    CONFIRMED = "confirmed"
    MEASURED = "measured"
    MODEL_INFERENCE = "model_inference"
    CREDIBLE_LEAK = "credible_leak"
    SPECULATION = "speculation"


class EventType(StrEnum):
    EA_ANNOUNCEMENT = "ea_announcement"
    SBC_RELEASED = "sbc_released"
    SBC_UPDATED = "sbc_updated"
    SBC_EXPIRED = "sbc_expired"
    EVOLUTION_RELEASED = "evolution_released"
    EVOLUTION_UPDATED = "evolution_updated"
    EVOLUTION_EXPIRED = "evolution_expired"
    PROMO_RELEASED = "promo_released"
    OBJECTIVE_RELEASED = "objective_released"
    LIVE_EVENT_RELEASED = "live_event_released"
    REWARD_CHANGED = "reward_changed"
    STORE_PACK_CHANGED = "store_pack_changed"
    PACK_PROBABILITY_CHANGED = "pack_probability_changed"
    PRICE_RANGE_CHANGED = "price_range_changed"
    CARD_RELEASED = "card_released"
    CARD_ENTERED_PACKS = "card_entered_packs"
    CARD_LEFT_PACKS = "card_left_packs"
    GAMEPLAY_CHANGE = "gameplay_change"
    SCHEDULED_CONTENT = "scheduled_content"
    LEAK = "leak"
    COMMUNITY_SIGNAL = "community_signal"
    SOCIAL_MARKET_IMPACT = "social_market_impact"
    PUBLIC_PREDICTION = "public_prediction"


class SignalType(StrEnum):
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WATCH = "watch"
    HOLD = "hold"
    REDUCE = "reduce"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    VERIFY = "verify"
