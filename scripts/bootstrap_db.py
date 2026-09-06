from sqlalchemy import text

from fc27trader.db.base import Base
from fc27trader.db import models  # noqa: F401
from fc27trader.db.session import engine


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        for table, column in [
            ("market_snapshots", "observed_at"),
            ("market_index_snapshots", "observed_at"),
            ("market_listing_observations", "observed_at"),
            ("completed_sale_observations", "observed_at"),
            ("portfolio_snapshots", "observed_at"),
        ]:
            try:
                conn.execute(text(f"SELECT create_hypertable('{table}', '{column}', if_not_exists => TRUE, migrate_data => TRUE)"))
            except Exception:
                pass
    print("database schema ready")
