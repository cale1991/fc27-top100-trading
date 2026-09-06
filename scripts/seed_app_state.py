from fc27trader.db.session import SessionLocal
from fc27trader.services.portfolio import get_or_create_account
from fc27trader.services.market_segments import ensure_account_market_access, ensure_market_segments


if __name__ == "__main__":
    with SessionLocal() as session:
        account = get_or_create_account(session, name="main", starting_coins=0)
        ensure_market_segments(session, game_year=26)
        ensure_market_segments(session, game_year=27)
        ensure_account_market_access(session, account, game_year=26)
        session.commit()
        print(f"application account ready: {account.name}")
