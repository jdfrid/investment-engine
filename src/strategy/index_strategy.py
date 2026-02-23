"""אסטרטגיית Backtrader – מדדים + כללים"""

import backtrader as bt
from .rules_engine import (
    evaluate_rules,
    RuleAction,
    calc_sell_profit_quantity,
    PositionState,
)


class IndexRulesStrategy(bt.Strategy):
    params = (
        ("stop_loss_pct", 0.20),
        ("take_profit_pct", 0.20),
        ("allocation_per_asset", 0.25),
        ("min_cash_for_buy", 100.0),
    )

    def __init__(self):
        self.entry_prices: dict = {}
        self.entry_dates: dict = {}
        self.initial_allocation_done = False

    def next(self):
        """נקרא בכל בר (יום)"""
        # הקצאה ראשונית – רק בבר הראשון
        if not self.initial_allocation_done and len(self) == 1:
            self._do_initial_allocation()
            self.initial_allocation_done = True
            return

        # בדיקת כללים על פוזיציות קיימות
        for data in self.datas:
            symbol = getattr(data, "_name", str(data))
            if not data or len(data) == 0:
                continue
            try:
                current_price = float(data.close[0])
            except (TypeError, IndexError):
                continue
            if current_price <= 0:
                continue

            pos = self.getposition(data)
            if pos.size > 0:
                entry_price = self.entry_prices.get(symbol, current_price)
                state = PositionState(
                    symbol=symbol,
                    entry_price=entry_price,
                    current_price=current_price,
                    quantity=pos.size,
                    entry_date=self.entry_dates.get(symbol, ""),
                )
                rules = {
                    "stop_loss_pct": self.p.stop_loss_pct,
                    "take_profit_pct": self.p.take_profit_pct,
                }
                action = evaluate_rules(state, rules)

                if action == RuleAction.SELL_ALL:
                    self.close(data=data)
                    self.entry_prices.pop(symbol, None)
                    self.entry_dates.pop(symbol, None)
                elif action == RuleAction.SELL_PROFIT:
                    qty = calc_sell_profit_quantity(state)
                    if qty > 0:
                        self.sell(data=data, size=round(qty, 6))

    def _do_initial_allocation(self):
        """הקצאה ראשונית – פיזור המזומן על כל הנכסים"""
        total_value = self.broker.getvalue()
        cash = self.broker.getcash()
        if cash < self.p.min_cash_for_buy:
            return
        num_assets = len(self.datas)
        value_per_asset = total_value * self.p.allocation_per_asset
        for data in self.datas:
            symbol = getattr(data, "_name", str(data))
            if not data or len(data) == 0:
                continue
            pos = self.getposition(data)
            if pos.size > 0:
                continue
            try:
                price = float(data.close[0])
            except (TypeError, IndexError):
                continue
            if price <= 0:
                continue
            size = value_per_asset / price
            if size > 0 and self.broker.getcash() > price * size:
                self.buy(data=data, size=round(size, 6))

    def notify_order(self, order):
        if order.status != order.Completed:
            return
        if order.isbuy() and hasattr(order, "data") and order.data is not None:
            symbol = getattr(order.data, "_name", str(order.data))
            self.entry_prices[symbol] = order.executed.price
            try:
                dt = getattr(order.executed, "dt", None)
                self.entry_dates[symbol] = str(dt) if dt else ""
            except Exception:
                self.entry_dates[symbol] = ""
