from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://fc27:fc27@localhost:5432/fc27"
    redis_url: str = "redis://localhost:6379/0"

    raw_store_mode: str = "filesystem"
    raw_store_path: Path = Path("./data/raw")
    upload_store_path: Path = Path("./data/uploads")
    raw_s3_bucket: str | None = None
    raw_s3_endpoint_url: str | None = None
    raw_s3_region: str = "auto"
    raw_s3_access_key_id: str | None = None
    raw_s3_secret_access_key: str | None = None

    futdb_api_key: str | None = None
    thecoinprinter_api_key: str | None = None
    futdb_premium_prices_enabled: bool = False
    futdb_universe_max_pages_per_run: int = 500
    futdb_price_requests_per_cycle: int = 25
    thecoinprinter_pages_per_cycle: int = 4

    futzip_movers_url: str = "https://futzip.com/feed/movers.xml"
    futzip_new_url: str = "https://futzip.com/feed/new.xml"
    futzip_sbc_url: str = "https://futzip.com/feed/sbc.xml"
    futzip_enabled: bool = True
    parse_api_key: str | None = None
    parse_futbin_enabled: bool = False
    parse_futbin_base_url: str = "https://api.parse.bot/scraper/21963078-8a17-40ff-a896-9b0b0ec3e828"
    parse_futbin_catalogue_pages_per_cycle: int = 1
    parse_futbin_hot_requests_per_cycle: int = 10
    parse_futbin_credit_cost_per_call: int = 1

    x_user_access_token: str | None = None
    x_api_base_url: str = "https://api.x.com/2"

    ea_news_fc26_url: str = "https://www.ea.com/games/ea-sports-fc/fc-26/news"
    ea_news_fc27_url: str = "https://www.ea.com/games/ea-sports-fc/fc-27/news"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
