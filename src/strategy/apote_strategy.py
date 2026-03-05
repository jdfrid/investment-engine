"""
אסטרטגיית APOTE – לפי המפרט המלא
מקטעי סיכון, דירוג נכסים, מצב שוק, ניהול סיכונים
"""

import backtrader as bt
import pandas as pd

from src.apote.regime import detect_market_regime, MarketRegime
from src.apote.ranking import rank_assets
from src.apote.risk import RiskManager
from src.apote.rules import should_exit_trend_reversal, atr_value
from src.apote.logger import ApoteLogger
from src.config.apote_config import (
    PORTFOLIO_SEGMENTS,
    RISK_MANAGEMENT,
    HIGH_RISK_SYMBOLS,
)


class ApoteStrategy(bt.Strategy):
    params = (
        ("top_n", 5),
        ("ma_regime", 50),
        ("ma_trend_exit", 20),
        ("atr_period", 14),
        ("trailing_stop_pct", 0.10),
    )

    def __init__(self):
        self.entry_prices = {}
        self.entry_dates = {}
        self.entry_bars = {}
        self.closed_trades = []
        self._pending_sells = {}
        self.risk_manager = RiskManager(RISK_MANAGEMENT)
        self.logger = ApoteLogger()
        self.peak_value = self.broker.getvalue()

    def _get_prices_dict(self) -> dict:
        """מחזיר dict של symbol -> Series מחירים (150 בר אחרונים)"""
        d = {}
        for data in self.datas:
            sym = getattr(data, "_name", str(data))
            if data and len(data) >= 120:
                try:
                    n = min(150, len(data))
                    closes = pd.Series([float(data.close[-i]) for i in range(n, 0, -1)])
                    d[sym] = closes
                except Exception:
                    pass
        return d

    def _get_regime(self) -> MarketRegime:
        """מזהה מצב שוק (מבוסס על SPY או הנכס הראשון)"""
        for data in self.datas:
            sym = getattr(data, "_name", "")
            if sym in ["SPY", "IVV", "VOO"] or data is self.datas[0]:
                if len(data) >= 50:
                    n = min(60, len(data))
                    s = pd.Series([float(data.close[-i]) for i in range(n, 0, -1)])
                    return detect_market_regime(s, ma_period=50)
        return MarketRegime.RISK_OFF

    def next(self):
        if len(self) < 120:
            return

        portfolio_value = self.broker.getvalue()
        self.peak_value = max(self.peak_value, portfolio_value)
        drawdown = (self.peak_value - portfolio_value) / self.peak_value if self.peak_value > 0 else 0

        if not self.risk_manager.can_trade(portfolio_value, drawdown):
            return

        regime = self._get_regime()
        prices_dict = self._get_prices_dict()
        if not prices_dict:
            return

        prices_df = pd.DataFrame(prices_dict)
        ranked = rank_assets(prices_df, top_n=self.p.top_n)
        top_symbols = ranked["symbol"].tolist() if not ranked.empty else []

        # יציאות: היפוך מגמה, Stop-Loss (ATR), Trailing Stop
        for data in self.datas:
            symbol = getattr(data, "_name", str(data))
            pos = self.getposition(data)
            if pos.size <= 0:
                continue

            entry_price = self.entry_prices.get(symbol)
            if not entry_price:
                continue

            current_price = float(data.close[0])
            exit_reason = None

            # היפוך מגמה
            n = min(25, len(data))
            s = pd.Series([float(data.close[-i]) for i in range(n, 0, -1)])
            if should_exit_trend_reversal(s, self.p.ma_trend_exit):
                exit_reason = "trend_reversal"

            # Stop-Loss דינמי (ATR)
            if not exit_reason:
                atr = atr_value(data.high, data.low, data.close, self.p.atr_period)
                if atr > 0:
                    sl = self.risk_manager.atr_stop_loss(atr, entry_price)
                    if current_price <= sl:
                        exit_reason = "stop_loss"

            # Trailing Stop
            if not exit_reason and self.peak_value > 0:
                trail = entry_price * (1 - self.p.trailing_stop_pct)
                if current_price <= trail:
                    exit_reason = "trailing_stop"

            if exit_reason:
                self._pending_sells[symbol] = (entry_price, self.entry_dates.get(symbol, ""), exit_reason, data)
                self.close(data=data)
                self.entry_prices.pop(symbol, None)
                self.entry_dates.pop(symbol, None)

        # כניסות: רק נכסים בדירוג העליון, מצב שוק מאפשר
        if regime == MarketRegime.RISK_OFF:
            top_symbols = [s for s in top_symbols if s not in HIGH_RISK_SYMBOLS]

        cash = self.broker.getcash()
        max_trade = self.risk_manager.max_position_value(portfolio_value)
        target_per_asset = portfolio_value * (1.0 / max(len(top_symbols), 1)) * 0.33
        target_per_asset = min(target_per_asset, max_trade)

        for data in self.datas:
            symbol = getattr(data, "_name", str(data))
            if symbol not in top_symbols:
                continue
            pos = self.getposition(data)
            if pos.size > 0:
                continue
            if cash < target_per_asset * 0.5:
                break

            price = float(data.close[0])
            if price <= 0:
                continue
            size = min(target_per_asset / price, max_trade / price)
            if size > 0 and cash >= price * size:
                self.buy(data=data, size=round(size, 6))

    def notify_order(self, order):
        if order.status != order.Completed:
            return
        if order.isbuy() and hasattr(order, "data") and order.data:
            symbol = getattr(order.data, "_name", str(order.data))
            self.entry_prices[symbol] = order.executed.price
            self.entry_bars[symbol] = len(self)
            try:
                dt = getattr(order.executed, "dt", None)
                self.entry_dates[symbol] = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10]
            except Exception:
                self.entry_dates[symbol] = ""
            self.logger.log(symbol, "BUY", order.executed.size, order.executed.price, "top_ranked_entry")
        elif order.issell() and hasattr(order, "data") and order.data:
            symbol = getattr(order.data, "_name", str(order.data))
            pending = self._pending_sells.pop(symbol, None)
            if pending:
                entry_price = pending[0]
                entry_date = pending[1] if len(pending) > 1 else ""
                exit_reason = pending[2] if len(pending) > 2 else "exit"
                data_feed = pending[3] if len(pending) > 3 else order.data
                exit_price = order.executed.price
                qty = abs(float(order.executed.size))
                cost_buy = entry_price * qty
                cost_sell = exit_price * qty
                pnl = cost_sell - cost_buy
                pct = (exit_price - entry_price) / entry_price * 100 if entry_price else 0
                try:
                    dt = getattr(order.executed, "dt", None)
                    exit_date = dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10]
                except Exception:
                    exit_date = ""
                entry_bar = self.entry_bars.pop(symbol, 0)
                exit_bar = len(self)
                actual_high = actual_low = entry_price
                try:
                    n_held = min(max(1, exit_bar - entry_bar + 1), len(data_feed))
                    for i in range(n_held):
                        h = float(data_feed.high[-i])
                        l = float(data_feed.low[-i])
                        actual_high = max(actual_high, h)
                        actual_low = min(actual_low, l)
                except (IndexError, TypeError, ValueError):
                    pass
                days_held = exit_bar - entry_bar
                what_happened = f"קניה {entry_date} ב-${entry_price:.2f} → מכירה {exit_date} ב-${exit_price:.2f}. בתקופה: שיא ${actual_high:.2f}, שפל ${actual_low:.2f}, {days_held} ימים. תוצאה: {'רווח' if pnl >= 0 else 'הפסד'} ${abs(pnl):,.2f} ({pct:+.1f}%)"
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
                    "type": "APOTE",
                    "what_happened": what_happened,
                })
                self.logger.log(symbol, "SELL", qty, exit_price, "exit_rule")
