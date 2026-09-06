from datetime import UTC, datetime
from decimal import Decimal
import uuid

from fc27trader.db.models import (
    ActivityFeedItem,
    Card,
    ExecutionObservation,
    PortfolioPosition,
    PortfolioTransaction,
    TradingAccount,
)
from fc27trader.services.portfolio import record_purchase, record_sale


class FakeSession:
    def __init__(self, *, position=None, execution=None):
        self.position = position
        self.latest_execution = execution
        self.added = []
        self._execution_id = 100

    def scalar(self, statement):
        sql = str(statement)
        if "portfolio_positions" in sql:
            return self.position
        if "execution_observations" in sql:
            return self.latest_execution
        raise AssertionError(f"unexpected scalar query: {sql}")

    def add(self, row):
        if getattr(row, "id", None) is None:
            if isinstance(row, ExecutionObservation):
                self._execution_id += 1
                row.id = self._execution_id
            else:
                row.id = uuid.uuid4()
        if isinstance(row, PortfolioPosition):
            self.position = row
        if isinstance(row, ExecutionObservation):
            self.latest_execution = row
        self.added.append(row)

    def flush(self):
        return None


def make_account(coins=500_000):
    now = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
    return TradingAccount(
        id=uuid.uuid4(), name="main", platform="pc", starting_coins=coins,
        current_coins=coins, realized_profit=0, ea_tax_paid=0,
        created_at=now, updated_at=now, metadata_json={},
    )


def make_card():
    now = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
    return Card(
        id=uuid.uuid4(), game_year=26, name="Rehearsal Card", rating=88, rarity="Gold",
        attributes_json={}, playstyles_json={}, roles_json={}, created_at=now, updated_at=now,
    )


def test_full_buy_hold_sell_rehearsal_accounting_and_consumed_listing():
    now = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
    card = make_card()
    account = make_account(500_000)
    source_id = uuid.uuid4()
    original_execution = ExecutionObservation(
        id=10, observed_at=now, source_timestamp=None, card_id=card.id, source_id=source_id,
        platform="pc", observation_type="manual_exact", lowest_bin=95_000, best_bid=None,
        listing_prices_json=[95_000, 95_500, 96_000, 96_500, 97_000], listing_count=5,
        confidence=Decimal("0.95"), expires_at=None, metadata_json={},
    )
    session = FakeSession(execution=original_execution)

    buy = record_purchase(session, account=account, card=card, quantity=1, unit_price=95_000, occurred_at=now)
    assert buy.account_coins == 405_000
    assert session.position.quantity == 1
    assert session.position.average_acquisition_price == 95_000

    # The immutable 95k verification remains in history, but the local current mark moves to
    # the next observed listing rather than pretending the purchased listing is still available.
    derived = session.latest_execution
    assert derived is not original_execution
    assert original_execution.lowest_bin == 95_000
    assert derived.lowest_bin == 95_500
    assert derived.listing_prices_json == [95_500, 96_000, 96_500, 97_000]
    assert derived.source_timestamp == original_execution.observed_at

    sale = record_sale(session, account=account, card=card, quantity=1, unit_price=101_000, occurred_at=now)
    assert sale.ea_tax == 5_050
    assert sale.realized_profit == 950
    assert sale.account_coins == 500_950
    assert account.current_coins == 500_950
    assert account.realized_profit == 950
    assert account.ea_tax_paid == 5_050
    assert session.position.quantity == 0


def test_partial_sale_releases_only_sold_quantity_cost_basis():
    now = datetime(2026, 9, 4, 12, 0, tzinfo=UTC)
    card = make_card()
    account = make_account(600_000)
    session = FakeSession()

    record_purchase(session, account=account, card=card, quantity=2, unit_price=95_000, occurred_at=now)
    assert account.current_coins == 410_000
    assert session.position.quantity == 2
    assert session.position.total_cost_basis == 190_000

    sale = record_sale(session, account=account, card=card, quantity=1, unit_price=101_000, occurred_at=now)
    assert sale.ea_tax == 5_050
    assert sale.realized_profit == 950
    assert sale.quantity_remaining == 1
    assert account.current_coins == 505_950
    assert account.realized_profit == 950
    assert session.position.quantity == 1
    assert session.position.average_acquisition_price == 95_000
    assert session.position.total_cost_basis == 95_000

    sell_transactions = [x for x in session.added if isinstance(x, PortfolioTransaction) and x.transaction_type == "sell"]
    assert sell_transactions[-1].cost_basis_released == 95_000
    assert sell_transactions[-1].net_coin_flow == 95_950
