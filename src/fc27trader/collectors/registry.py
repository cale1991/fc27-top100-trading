from fc27trader.settings import Settings

from .ea_official import EAOfficialNewsCollector
from .futdb import FutDbCollector
from .thecoinprinter import TheCoinPrinterCollector
from .parse_futbin import ParseBotFutbinCollector


def build_collectors(settings: Settings) -> dict[str, object]:
    collectors: dict[str, object] = {
        "ea_news_fc26": EAOfficialNewsCollector(settings.ea_news_fc26_url, game_year=26),
        "ea_news_fc27": EAOfficialNewsCollector(settings.ea_news_fc27_url, game_year=27),
    }
    if settings.futdb_api_key:
        collectors["futdb"] = FutDbCollector(settings.futdb_api_key)
    if settings.thecoinprinter_api_key:
        collectors["thecoinprinter"] = TheCoinPrinterCollector(settings.thecoinprinter_api_key)
    if settings.parse_futbin_enabled and settings.parse_api_key:
        collectors["parse_futbin"] = ParseBotFutbinCollector(settings.parse_api_key, base_url=settings.parse_futbin_base_url)
    return collectors
