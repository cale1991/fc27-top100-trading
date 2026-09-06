from fc27trader.db.session import SessionLocal
from fc27trader.services.strategy_backtesting import refresh_strategy_backtests

if __name__ == "__main__":
    with SessionLocal() as session:
        result = refresh_strategy_backtests(session)
        session.commit()
        print(result)
