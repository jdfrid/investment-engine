"""אסטרטגיית Backtrader – מדדים + כללים + Re-Entry + DCA"""

import backtrader as bt
from .rules_engine import (
    evaluate_rules,
    RuleAction,
    calc_sell_profit_quantity,
    PositionState,
)


class IndexRulesStrategy(bt.Strategy):
    params = (
        ("stop_loss_pct", 0.25),      # 25% – פחות רגיש מ-20%
        ("take_profit_pct", 0.15),    # 15% – רווח מוקדם יותר
        ("allocation_per_asset", 0.25),
        ("min_cash_for_buy", 100.0),
        ("re_entry_days", 5),         # ימים להמתנה אחרי Stop-Loss לפני כניסה מחדש
        ("dca_interval", 21),         # DCA: הקצאה נוספת כל 21 ימי מסחר (~חודש)
    )

    def __init__(self):
        self.entry_prices: dict = {}
        self.entry_dates: dict = {}
        self.sell_dates: dict = {}    # symbol -> bar index כשמכרנו (Stop-Loss)
        self.initial_allocation_done = False
        self.last_dca_bar = 0

    def next(self):
        """נקרא בכל בר (יום)"""
        bar_num = len(self)
        # הקצאה ראשונית – בבר הראשון
        if not self.initial_allocation_done and bar_num == 1:
            self._do_allocation()
            self.initial_allocation_done = True
            self.last_dca_bar = bar_num
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
                    self.sell_dates[symbol] = bar_num  # רישום לתזמון Re-Entry
                elif action == RuleAction.SELL_PROFIT:
                    qty = calc_sell_profit_quantity(state)
                    if qty > 0:
                        self.sell(data=data, size=round(qty, 6))

        # Re-Entry: קנייה מחדש אחרי Stop-Loss (כל יום – בודק אם עבר re_entry_days)
        # DCA: הקצאה חודשית נוספת (כל 21 ימי מסחר)
        run_allocation = bar_num - self.last_dca_bar >= self.p.dca_interval
        if run_allocation:
            self.last_dca_bar = bar_num
        self._do_allocation()

    def _can_reenter(self, symbol: str, bar_num: int) -> bool:
        """האם מותר לקנות מחדש אחרי Stop-Loss"""
        if symbol not in self.sell_dates:
            return True
        days_since_sell = bar_num - self.sell_dates[symbol]
        return days_since_sell >= self.p.re_entry_days

    def _do_allocation(self):
        """הקצאה – פיזור מזומן על נכסים (גם Re-Entry וגם DCA)"""
        total_value = self.broker.getvalue()
        cash = self.broker.getcash()
        if cash < self.p.min_cash_for_buy:
            return
        bar_num = len(self)
        value_per_asset = total_value * self.p.allocation_per_asset
        for data in self.datas:
            symbol = getattr(data, "_name", str(data))
            if not data or len(data) == 0:
                continue
            pos = self.getposition(data)
            if pos.size > 0:
                continue
            if not self._can_reenter(symbol, bar_num):
                continue
            try:
                price = float(data.close[0])
            except (TypeError, IndexError):
                continue
            if price <= 0:
                continue
            size = value_per_asset / price
            if size > 0 and self.broker.getcash() >= price * size:
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
