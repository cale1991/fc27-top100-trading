from fc27trader.services.manual_verification import verification_value


def test_manual_verification_only_interrupts_when_information_value_positive():
    yes = verification_value(probability_decision_changes=0.5, expected_profit_if_actionable=20000,
                             confidence_gain=0.5, interruption_cost=1000)
    no = verification_value(probability_decision_changes=0.1, expected_profit_if_actionable=1000,
                            confidence_gain=0.2, interruption_cost=500)
    assert yes.should_request
    assert not no.should_request
