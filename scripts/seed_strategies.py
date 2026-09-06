from fc27trader.db.session import SessionLocal
from fc27trader.services.strategy_research import seed_strategy_library

if __name__ == "__main__":
    with SessionLocal() as session:
        result = seed_strategy_library(session)
        session.commit()
        print(result)
