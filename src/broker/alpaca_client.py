"""חיבור ל-Alpaca API – שליחת פקודות וקבלת פוזיציות"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Position:
    symbol: str
    qty: float
    avg_entry_price: float
    current_price: float


@dataclass
class AccountInfo:
    cash: float
    equity: float


class AlpacaClient:
    """Client למסחר דרך Alpaca API"""

    def __init__(self, api_key: str = None, api_secret: str = None, paper: bool = True):
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.api_secret = api_secret or os.getenv("ALPACA_API_SECRET")
        self.paper = paper
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self.api_key or not self.api_secret:
                raise ValueError("ALPACA_API_KEY and ALPACA_API_SECRET required. Set in .env")
            from alpaca.trading.client import TradingClient
            self._client = TradingClient(self.api_key, self.api_secret, paper=self.paper)
        return self._client

    def get_account(self) -> AccountInfo:
        """מחזיר מידע על החשבון"""
        client = self._get_client()
        acc = client.get_account()
        return AccountInfo(
            cash=float(acc.cash),
            equity=float(acc.equity),
        )

    def get_positions(self) -> list[Position]:
        """מחזיר רשימת פוזיציות פתוחות"""
        client = self._get_client()
        positions = client.get_all_positions()
        result = []
        for p in positions:
            result.append(Position(
                symbol=p.symbol,
                qty=float(p.qty),
                avg_entry_price=float(p.avg_entry_price),
                current_price=float(p.current_price),
            ))
        return result

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """מחזיר מחיר אחרון לנכס – משתמש ב-yfinance (כבר בפרויקט)"""
        try:
            import yfinance as yf
            t = yf.Ticker(symbol)
            hist = t.history(period="1d", interval="1m")
            if hist is not None and len(hist) > 0:
                return float(hist["Close"].iloc[-1])
            return None
        except Exception:
            return None

    def buy(self, symbol: str, notional: float) -> Optional[dict]:
        """קונה לפי סכום בדולרים (מניות חלקיות)"""
        client = self._get_client()
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
        try:
            order = MarketOrderRequest(
                symbol=symbol,
                notional=notional,
                side=OrderSide.BUY,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )
            return client.submit_order(order_data=order)
        except Exception as e:
            print(f"Buy error: {e}")
            return None

    def sell(self, symbol: str, qty: float) -> Optional[dict]:
        """מוכר כמות"""
        client = self._get_client()
        from alpaca.trading.requests import MarketOrderRequest
        from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
        try:
            order = MarketOrderRequest(
                symbol=symbol,
                qty=round(qty, 6),
                side=OrderSide.SELL,
                type=OrderType.MARKET,
                time_in_force=TimeInForce.DAY,
            )
            return client.submit_order(order_data=order)
        except Exception as e:
            print(f"Sell error: {e}")
            return None

    def close_position(self, symbol: str) -> Optional[dict]:
        """סוגר פוזיציה במלואה"""
        client = self._get_client()
        try:
            return client.close_position(symbol_or_asset_id=symbol)
        except Exception as e:
            print(f"Close error: {e}")
            return None
