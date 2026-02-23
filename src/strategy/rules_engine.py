"""מנוע כללים – לוגיקה טהורה ללא תלות ב-Backtrader"""

from dataclasses import dataclass
from enum import Enum


class RuleAction(Enum):
    HOLD = "hold"
    SELL_ALL = "sell_all"       # Stop-Loss: מכור הכל
    SELL_PROFIT = "sell_profit"  # Take-Profit: מכור רווח, השאר השקעה


@dataclass
class PositionState:
    symbol: str
    entry_price: float
    current_price: float
    quantity: float
    entry_date: str


def evaluate_rules(position: PositionState, rules_config: dict) -> RuleAction:
    """
    בודק כללים על פוזיציה בודדת.
    rules_config: { "stop_loss_pct": 0.20, "take_profit_pct": 0.20 }
    """
    if position.entry_price <= 0:
        return RuleAction.HOLD
    pct_change = (position.current_price - position.entry_price) / position.entry_price

    stop_loss = rules_config.get("stop_loss_pct", 0.20)
    take_profit = rules_config.get("take_profit_pct", 0.20)

    if pct_change <= -stop_loss:
        return RuleAction.SELL_ALL
    if pct_change >= take_profit:
        return RuleAction.SELL_PROFIT

    return RuleAction.HOLD


def calc_sell_profit_quantity(position: PositionState) -> float:
    """
    מחזיר כמות למכירה כך שהערך שנמכר = רווח (העודף מעל ההשקעה).
    השארית נשארת בתיק.
    """
    invested = position.entry_price * position.quantity
    current_value = position.current_price * position.quantity
    profit = current_value - invested
    if profit <= 0 or position.current_price <= 0:
        return 0.0
    return profit / position.current_price
