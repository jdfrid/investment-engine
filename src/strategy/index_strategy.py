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
        ("stop_loss_pct", 0.25),      # 25% – אופטימלי
        ("take_profit_pct", 0.20),    # 20% – אופטימלי
        ("allocation_per_asset", 0.25),
        ("min_cash_for_buy", 100.0),
        ("re_entry_days", 3),         # 3 ימים – אופטימלי
        ("dca_interval", 21),         # DCA: הקצאה נוספת כל 21 ימי מסחר (~חודש)
    )

    @staticmethod
    def _format_date(d):
        """ממיר תאריך לפורמט YYYY-MM-DD"""
        if d is None:
            return ""
        if hasattr(d, "strftime"):
            return d.strftime("%Y-%m-%d")
        if isinstance(d, (int, float)):
            try:
                dt_obj = bt.num2date(d)
                return dt_obj.strftime("%Y-%m-%d")
            except Exception:
                pass
            try:
                from datetime import datetime as dt
                if 700000 < d < 800000:  # ordinal (matplotlib/Excel)
                    return dt.fromordinal(int(d)).strftime("%Y-%m-%d")
            except Exception:
                pass
        s = str(d)
        if len(s) >= 10 and s[:10].replace("-", "").isdigit():
            return s[:10]
        return s[:10] if len(s) >= 10 else s

    def __init__(self):
        self.entry_prices: dict = {}
        self.entry_dates: dict = {}
        self.sell_dates: dict = {}    # symbol -> bar index כשמכרנו (Stop-Loss)
        self.initial_allocation_done = False
        self.last_dca_bar = 0
        self.closed_trades: list = []  # פירוט עסקאות לניתוח
        self._pending_sells: dict = {}  # symbol -> (entry_price, entry_date) לפני סגירה

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
                    self._pending_sells[symbol] = (entry_price, self.entry_dates.get(symbol, ""))
                    self.close(data=data)
                    self.entry_prices.pop(symbol, None)
                    self.entry_dates.pop(symbol, None)
                    self.sell_dates[symbol] = bar_num  # רישום לתזמון Re-Entry
                elif action == RuleAction.SELL_PROFIT:
                    qty = calc_sell_profit_quantity(state)
                    if qty > 0:
                        self._pending_sells[symbol] = (entry_price, self.entry_dates.get(symbol, ""), qty)
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
                exec_dt = getattr(order.executed, "dt", None)
                self.entry_dates[symbol] = self._format_date(exec_dt)
            except Exception:
                self.entry_dates[symbol] = ""
        elif order.issell() and hasattr(order, "data") and order.data is not None:
            symbol = getattr(order.data, "_name", str(order.data))
            pending = self._pending_sells.pop(symbol, None)
            if pending:
                entry_price = pending[0]
                entry_date = pending[1] if len(pending) > 1 else ""
                exit_price = order.executed.price
                qty = abs(float(order.executed.size))
                cost_buy = entry_price * qty
                cost_sell = exit_price * qty
                pnl = cost_sell - cost_buy
                pct = (exit_price - entry_price) / entry_price * 100 if entry_price else 0
                try:
                    exec_dt = getattr(order.executed, "dt", None)
                    exit_date = self._format_date(exec_dt) or self._format_date(self.datas[0].datetime.date(0))
                except Exception:
                    exit_date = self._format_date(self.datas[0].datetime.date(0)) if len(self.datas) else ""
                self.closed_trades.append({
                    "symbol": symbol,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "qty": qty,
                    "cost_buy": cost_buy,
                    "cost_sell": cost_sell,
                    "pnl": pnl,
                    "pct": pct,
                    "trend": "רווח" if pnl >= 0 else "הפסד",
                    "entry_date": entry_date,
                    "exit_date": exit_date,
                    "type": "Stop-Loss" if len(pending) == 2 else "Take-Profit",
                })
