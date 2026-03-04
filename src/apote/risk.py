"""ניהול סיכונים – APOTE"""

from typing import Optional
import pandas as pd

from src.config.apote_config import RISK_MANAGEMENT


class RiskManager:
    """בודק כללי סיכון לפני ביצוע עסקאות"""

    def __init__(self, config: dict = None):
        self.config = config or RISK_MANAGEMENT
        self.max_trade_risk = self.config.get("max_trade_risk", 0.01)
        self.max_drawdown = self.config.get("max_drawdown", 0.15)
        self.max_asset_exposure = self.config.get("max_asset_exposure", 0.25)
        self.atr_mult = self.config.get("atr_stop_multiplier", 2.0)

    def max_position_value(self, portfolio_value: float) -> float:
        """ערך מקסימלי לעסקה בודדת (1% מהתיק)"""
        return portfolio_value * self.max_trade_risk

    def can_trade(self, portfolio_value: float, current_drawdown: float) -> bool:
        """האם מותר לסחור (לא חרגנו מ-drawdown)"""
        return current_drawdown < self.max_drawdown

    def atr_stop_loss(self, atr: float, entry_price: float) -> float:
        """מחיר Stop-Loss דינמי לפי ATR"""
        return entry_price - self.atr_mult * atr

    def within_exposure_limit(self, position_value: float, portfolio_value: float) -> bool:
        """האם הפוזיציה בתוך מגבלת החשיפה"""
        if portfolio_value <= 0:
            return False
        return (position_value / portfolio_value) <= self.max_asset_exposure
