from fc27trader.services.portfolio import EA_TAX_RATE


def test_ea_tax_rate_locked():
    assert EA_TAX_RATE == 0.05
