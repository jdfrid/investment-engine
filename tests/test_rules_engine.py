"""בדיקות מנוע הכללים"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.strategy.rules_engine import (
    RuleAction,
    PositionState,
    evaluate_rules,
    calc_sell_profit_quantity,
)


def test_stop_loss_triggers_at_minus_20():
    state = PositionState("SPY", 100.0, 79.0, 10.0, "2024-01-01")
    rules = {"stop_loss_pct": 0.20, "take_profit_pct": 0.20}
    assert evaluate_rules(state, rules) == RuleAction.SELL_ALL


def test_stop_loss_triggers_at_exactly_minus_20():
    state = PositionState("SPY", 100.0, 80.0, 10.0, "2024-01-01")
    rules = {"stop_loss_pct": 0.20, "take_profit_pct": 0.20}
    assert evaluate_rules(state, rules) == RuleAction.SELL_ALL


def test_take_profit_triggers_at_plus_20():
    state = PositionState("SPY", 100.0, 121.0, 10.0, "2024-01-01")
    rules = {"stop_loss_pct": 0.20, "take_profit_pct": 0.20}
    assert evaluate_rules(state, rules) == RuleAction.SELL_PROFIT


def test_take_profit_triggers_at_exactly_plus_20():
    state = PositionState("SPY", 100.0, 120.0, 10.0, "2024-01-01")
    rules = {"stop_loss_pct": 0.20, "take_profit_pct": 0.20}
    assert evaluate_rules(state, rules) == RuleAction.SELL_PROFIT


def test_hold_when_in_range():
    state = PositionState("SPY", 100.0, 105.0, 10.0, "2024-01-01")
    rules = {"stop_loss_pct": 0.20, "take_profit_pct": 0.20}
    assert evaluate_rules(state, rules) == RuleAction.HOLD


def test_hold_when_small_loss():
    state = PositionState("SPY", 100.0, 95.0, 10.0, "2024-01-01")
    rules = {"stop_loss_pct": 0.20, "take_profit_pct": 0.20}
    assert evaluate_rules(state, rules) == RuleAction.HOLD


def test_calc_sell_profit_quantity():
    state = PositionState("SPY", 100.0, 120.0, 10.0, "2024-01-01")
    # invested=1000, current=1200, profit=200
    # qty = 200/120 = 1.666...
    qty = calc_sell_profit_quantity(state)
    assert abs(qty - 200 / 120) < 0.001


def test_calc_sell_profit_zero_profit():
    state = PositionState("SPY", 100.0, 100.0, 10.0, "2024-01-01")
    assert calc_sell_profit_quantity(state) == 0.0


def test_calc_sell_profit_loss():
    state = PositionState("SPY", 100.0, 80.0, 10.0, "2024-01-01")
    assert calc_sell_profit_quantity(state) == 0.0


if __name__ == "__main__":
    test_stop_loss_triggers_at_minus_20()
    test_stop_loss_triggers_at_exactly_minus_20()
    test_take_profit_triggers_at_plus_20()
    test_take_profit_triggers_at_exactly_plus_20()
    test_hold_when_in_range()
    test_hold_when_small_loss()
    test_calc_sell_profit_quantity()
    test_calc_sell_profit_zero_profit()
    test_calc_sell_profit_loss()
    print("כל הבדיקות עברו בהצלחה!")
