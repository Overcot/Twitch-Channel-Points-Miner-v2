"""Characterisation tests for Bet: they pin the current behaviour so that
merges from upstream cannot silently change betting decisions."""
import copy

import pytest

from TwitchChannelPointsMiner.classes.entities import Bet as bet_module
from TwitchChannelPointsMiner.classes.entities.Bet import (
    Bet,
    BetSettings,
    Condition,
    FilterCondition,
    OutcomeKeys,
    Strategy,
)


def make_outcomes(users=(100, 300), points=(1000, 3000), top=((50, 20), (500, 100))):
    return [
        {
            "id": f"o{i}",
            "title": f"T{i}",
            "color": "BLUE" if i == 0 else "PINK",
            "total_users": users[i],
            "total_points": points[i],
            "top_predictors": [{"points": p} for p in top[i]],
        }
        for i in range(2)
    ]


def make_bet(strategy=Strategy.MOST_VOTED, outcomes=None, **kw):
    outcomes = outcomes or make_outcomes()
    settings = BetSettings(strategy=strategy, **kw)
    settings.default()
    for k, v in kw.items():
        setattr(settings, k, v)
    bet = Bet(copy.deepcopy(outcomes), settings)
    bet.update_outcomes(copy.deepcopy(outcomes))
    return bet


def test_update_outcomes_totals_and_percentages():
    bet = make_bet()
    assert bet.total_users == 400
    assert bet.total_points == 4000
    o0, o1 = bet.outcomes
    assert o0[OutcomeKeys.PERCENTAGE_USERS] == 25.0
    assert o1[OutcomeKeys.PERCENTAGE_USERS] == 75.0
    assert o0[OutcomeKeys.ODDS] == 4.0
    assert o1[OutcomeKeys.ODDS] == 1.33
    assert o0[OutcomeKeys.ODDS_PERCENTAGE] == 25.0
    assert o0[OutcomeKeys.TOP_POINTS] == 50  # highest single prediction
    assert o1[OutcomeKeys.TOP_POINTS] == 500


def test_update_outcomes_empty_pool_keeps_defaults():
    outcomes = make_outcomes(users=(0, 0), points=(0, 0), top=((), ()))
    bet = make_bet(outcomes=outcomes)
    for o in bet.outcomes:
        assert o[OutcomeKeys.PERCENTAGE_USERS] == 0
        assert o[OutcomeKeys.ODDS] == 0
        assert o[OutcomeKeys.TOP_POINTS] == 0


def test_update_outcomes_one_sided_pool_has_zero_odds_for_empty_side():
    bet = make_bet(outcomes=make_outcomes(users=(0, 10), points=(0, 500), top=((), (500,))))
    assert bet.outcomes[0][OutcomeKeys.ODDS] == 0
    assert bet.outcomes[1][OutcomeKeys.ODDS] == 1.0


@pytest.mark.parametrize(
    "strategy, expected",
    [
        (Strategy.MOST_VOTED, 1),
        (Strategy.HIGH_ODDS, 0),       # outcome 0 pays 4.0
        (Strategy.PERCENTAGE, 1),      # ODDS_PERCENTAGE 25.0 vs 75.0
        (Strategy.SMART_MONEY, 1),     # biggest single bet is on outcome 1
        (Strategy.NUMBER_1, 0),
        (Strategy.NUMBER_2, 1),
        (Strategy.NUMBER_3, 0),        # out of range falls back to 0
        (Strategy.NUMBER_8, 0),
    ],
)
def test_calculate_choice(strategy, expected):
    bet = make_bet(strategy)
    assert bet.calculate(10_000)["choice"] == expected


def test_smart_uses_odds_when_users_are_close():
    outcomes = make_outcomes(users=(200, 210), points=(4000, 1000), top=((10,), (10,)))
    bet = make_bet(Strategy.SMART, outcomes=outcomes, percentage_gap=20)
    assert bet.calculate(10_000)["choice"] == 1  # gap < 20 -> HIGH_ODDS (outcome 1 has the smaller pool)


def test_smart_uses_users_when_gap_is_large():
    bet = make_bet(Strategy.SMART, percentage_gap=20)  # 25% vs 75% -> gap 50
    assert bet.calculate(10_000)["choice"] == 1  # MOST_VOTED


def test_amount_is_percentage_capped_by_max_points():
    bet = make_bet(percentage=5, max_points=50_000, stealth_mode=False)
    assert bet.calculate(10_000)["amount"] == 500
    assert bet.calculate(2_000_000)["amount"] == 50_000
    bet = make_bet(percentage=5, max_points=300, stealth_mode=False)
    assert bet.calculate(10_000)["amount"] == 300


def test_decision_carries_outcome_id():
    bet = make_bet(Strategy.MOST_VOTED)
    assert bet.calculate(1000)["id"] == "o1"


def test_stealth_mode_goes_below_top_prediction(monkeypatch):
    monkeypatch.setattr(bet_module, "uniform", lambda a, b: 2)
    bet = make_bet(Strategy.MOST_VOTED, percentage=50, max_points=10**9, stealth_mode=True)
    # outcome 1 top bet = 500; wanted 5000 >= 500 -> 500 - 2
    assert bet.calculate(10_000)["amount"] == 498


def test_stealth_mode_keeps_amount_below_top_prediction(monkeypatch):
    monkeypatch.setattr(bet_module, "uniform", lambda a, b: 2)
    bet = make_bet(Strategy.MOST_VOTED, percentage=1, max_points=10**9, stealth_mode=True)
    assert bet.calculate(10_000)["amount"] == 100  # 100 < 500, untouched


def test_stealth_mode_without_top_predictors_does_not_bet(monkeypatch):
    """No top bet to stay under -> stealth cannot be satisfied -> amount is 0
    (the caller then logs that it is below the minimum and places no bet)."""
    monkeypatch.setattr(bet_module, "uniform", lambda a, b: 2)
    outcomes = make_outcomes(top=((), ()))
    bet = make_bet(Strategy.MOST_VOTED, outcomes=outcomes, percentage=5, stealth_mode=True)
    assert bet.calculate(10_000)["amount"] == 0


def test_no_stealth_without_top_predictors_still_bets():
    outcomes = make_outcomes(top=((), ()))
    bet = make_bet(Strategy.MOST_VOTED, outcomes=outcomes, percentage=5, stealth_mode=False)
    assert bet.calculate(10_000)["amount"] == 500


def _skip(by, where, value, strategy=Strategy.MOST_VOTED):
    bet = make_bet(strategy, filter_condition=FilterCondition(by=by, where=where, value=value))
    bet.calculate(10_000)
    return bet.skip()


def test_skip_without_filter_never_skips():
    bet = make_bet()
    bet.calculate(1000)
    assert bet.skip() == (False, 0)


@pytest.mark.parametrize(
    "where, value, skipped",
    [
        (Condition.GT, 399, False),
        (Condition.GT, 400, True),
        (Condition.GTE, 400, False),
        (Condition.GTE, 401, True),
        (Condition.LT, 401, False),
        (Condition.LT, 400, True),
        (Condition.LTE, 400, False),
        (Condition.LTE, 399, True),
    ],
)
def test_skip_on_total_users(where, value, skipped):
    # `skip()` returns (should_skip, compared_value); the condition describes when to BET.
    assert _skip(OutcomeKeys.TOTAL_USERS, where, value) == (skipped, 400)


def test_skip_on_decision_points_uses_chosen_outcome():
    # MOST_VOTED picks outcome 1 (3000 points)
    assert _skip(OutcomeKeys.DECISION_POINTS, Condition.GT, 2999) == (False, 3000)
    assert _skip(OutcomeKeys.DECISION_POINTS, Condition.GT, 3000) == (True, 3000)


def test_skip_on_odds_uses_chosen_outcome():
    assert _skip(OutcomeKeys.ODDS, Condition.GT, 1.0) == (False, 1.33)
